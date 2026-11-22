"""
PhoneDeck — transforma o celular num Stream Deck do PC.

Este é o servidor que roda no PC. Ele:
  * entrega o app (página web) para o iPhone
  * recebe os toques nos botões por WebSocket e executa as ações
  * envia ao vivo CPU/RAM/GPU (com histórico para os gráficos), volume,
    microfone e a música tocando

Modos de abrir:
  (sem nada)    janela de console visível (para ver erros)        -> modo_console.bat
  --abrir       segundo plano + abre a página de conexão           -> ícone da área de trabalho
  --auto        segundo plano, sem abrir nada; avisa quando o cabo -> inicialização do Windows
                do iPhone é conectado
  --instalar-atalhos / --remover-atalhos / --esperar               -> usados pelos .bat
"""
from __future__ import annotations

import asyncio
import collections
import html
import json
import os
import re
import secrets
import socket
import sys
import time
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402

VERSION = "2.4"
IS_WINDOWS = sys.platform == "win32"
VIRTUAL_IF = re.compile(r"vethernet|virtualbox|vmware|hyper-v|loopback|wsl|docker|tailscale|zerotier|vpn|bluetooth",
                        re.I)
_NOPROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def local_ips() -> list[tuple[str, str]]:
    """[(ip, descrição)] — USB do iPhone primeiro."""
    import psutil
    found = []
    stats = psutil.net_if_stats()
    for name, addrs in psutil.net_if_addrs().items():
        if name in stats and not stats[name].isup:
            continue
        for a in addrs:
            if a.family != socket.AF_INET:
                continue
            ip = a.address
            if ip.startswith("127.") or ip.startswith("169.254."):
                continue
            if ip.startswith("172.20.10."):
                found.append((0, ip, "Cabo USB (Ponto de Acesso do iPhone)"))
            elif VIRTUAL_IF.search(name):
                found.append((2, ip, f"{name} (virtual)"))
            else:
                found.append((1, ip, f"Rede: {name}"))
    found.sort()
    real = [f for f in found if f[0] < 2] or found
    return [(ip, desc) for _, ip, desc in real]


def usb_connected() -> bool:
    return any(ip.startswith("172.20.10.") for ip, _ in local_ips())


def ping(port: int, timeout: float = 1.5) -> bool:
    try:
        with _NOPROXY.open(f"http://127.0.0.1:{port}/ping", timeout=timeout) as r:
            return r.read(20).decode() == "phonedeck"
    except Exception:
        return False


def ask_shutdown(port: int) -> None:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/desligar", data=b"", method="POST")
        _NOPROXY.open(req, timeout=3).read()
    except Exception:
        pass


class Deck:
    def __init__(self, mode: str):
        from aiohttp import web  # noqa: F401  (confere a instalação cedo)

        import audio
        from clipper import Clipper
        from fps import FpsMeter
        from media import Media
        from stats import Stats
        self.mode = mode
        self.settings = config.load_settings()
        self.layout = config.load_layout()
        self.layout_mtime = self._layout_mtime()
        self.port = int(self.settings.get("port", 8765))
        self.token = str(self.settings["token"])
        self.clients: set = set()
        # Thread única para tudo que mexe com teclado/áudio do Windows (COM precisa disso)
        self.win = ThreadPoolExecutor(1, thread_name_prefix="win", initializer=audio.com_init)
        self.io = ThreadPoolExecutor(3, thread_name_prefix="io")
        self.stats = Stats()
        self.clipper = Clipper(self.settings)
        self.media = Media()
        self.fps = FpsMeter(self.settings)
        self.audio_state: dict = {}
        self.last_tick: dict = {}
        self.history: collections.deque = collections.deque(maxlen=300)  # 5 min (gráficos da tela cheia)
        self.usb = False
        self._last_need = 0.0
        self._tasks: set = set()
        self.stop_event: asyncio.Event | None = None

    # ----------------------------------------------------------------- util
    def layout_has(self, stat: str) -> bool:
        return any((b.get("action") or {}).get("type") == "stat" and b["action"].get("stat") == stat
                   for p in self.layout.get("pages", []) for b in p.get("buttons", []))

    def _layout_mtime(self) -> float:
        try:
            return config.LAYOUT_PATH.stat().st_mtime
        except OSError:
            return 0

    @staticmethod
    def is_local(request) -> bool:
        return request.remote in ("127.0.0.1", "::1")

    def authorized(self, request) -> bool:
        if not self.settings.get("require_token", True) or self.is_local(request):
            return True
        return secrets.compare_digest(str(request.query.get("t", "")), self.token)

    async def broadcast(self, payload: dict) -> None:
        if not self.clients:
            return
        data = json.dumps(payload, ensure_ascii=False)
        for ws in list(self.clients):
            try:
                await ws.send_str(data)
            except Exception:
                self.clients.discard(ws)

    # --------------------------------------------------------------- rotas
    async def index(self, request):
        from aiohttp import web
        page = (config.WEB_DIR / "index.html").read_text(encoding="utf-8")
        manifest = "manifest.webmanifest"
        if request.query.get("t") and self.authorized(request):
            manifest += f"?t={self.token}"
        page = page.replace("__MANIFEST__", manifest).replace("__VERSION__", VERSION)
        return web.Response(text=page, content_type="text/html")

    async def manifest(self, request):
        from aiohttp import web
        start = "./"
        if request.query.get("t") and self.authorized(request):
            start = f"./?t={self.token}"
        data = {
            "name": "PhoneDeck", "short_name": "PhoneDeck", "start_url": start, "scope": "./",
            "display": "standalone", "orientation": "any",
            "background_color": "#0b0d12", "theme_color": "#0b0d12",
            "icons": [{"src": "static/icon-192.png", "sizes": "192x192", "type": "image/png"},
                      {"src": "static/icon-512.png", "sizes": "512x512", "type": "image/png"}],
        }
        return web.json_response(data, content_type="application/manifest+json")

    async def ping_route(self, request):
        from aiohttp import web
        return web.Response(text="phonedeck")

    async def status_route(self, request):
        from aiohttp import web
        if not self.is_local(request):
            raise web.HTTPForbidden()
        return web.json_response({"ips": [ip for ip, _ in local_ips()], "usb": self.usb,
                                  "clip": self.clipper.info(), "clients": len(self.clients)})

    async def shutdown_route(self, request):
        from aiohttp import web
        if not self.is_local(request):
            raise web.HTTPForbidden()
        asyncio.get_running_loop().call_later(0.4, self.stop_event.set)
        body = ("<!doctype html><meta charset='utf-8'><body style='font-family:Segoe UI,system-ui;background:#0b0d12;"
                "color:#e5e7eb;padding:40px'><h2>PhoneDeck desligado.</h2><p>Para ligar de novo, use o ícone "
                "PhoneDeck na área de trabalho.</p>")
        return web.Response(text=body, content_type="text/html")

    async def fps_grant_route(self, request):
        from aiohttp import web

        import fps
        if not self.is_local(request):
            raise web.HTTPForbidden()
        ok = await asyncio.get_running_loop().run_in_executor(self.io, fps.grant_permission)
        msg = ("<h2>Pronto!</h2><p>Seu usuário foi liberado para medir FPS. <b>Saia e entre de novo na sua conta do "
               "Windows</b> (ou reinicie o PC) para valer.</p>") if ok else \
              ("<h2>Não foi liberado.</h2><p>O pedido de administrador foi cancelado ou falhou. "
               "Tente de novo pela página do PhoneDeck.</p>")
        body = ("<!doctype html><meta charset='utf-8'><body style='font-family:Segoe UI,system-ui;background:#0b0d12;"
                f"color:#e5e7eb;padding:40px'>{msg}<p><a style='color:#60a5fa' href='/conectar'>Voltar</a></p>")
        return web.Response(text=body, content_type="text/html")

    async def fps_download_route(self, request):
        from aiohttp import web

        import fps
        if not self.is_local(request):
            raise web.HTTPForbidden()
        try:
            path = await asyncio.get_running_loop().run_in_executor(self.io, fps.download_presentmon)
            self.fps.exe = path
            if self.fps.status == "no_exe":
                self.fps.status = "off"
        except Exception as e:
            print(f"[fps] download falhou: {e}")
        raise web.HTTPFound("/conectar")

    async def art_route(self, request):
        from aiohttp import web
        if not self.authorized(request):
            raise web.HTTPForbidden()
        item = self.media.art.get(request.match_info["key"])
        if not item:
            raise web.HTTPNotFound()
        return web.Response(body=item[1], content_type=item[2], headers={"Cache-Control": "max-age=86400"})

    async def connect_page(self, request):
        from aiohttp import web
        if not self.is_local(request):
            raise web.HTTPForbidden(text="Abra esta página no próprio PC.")
        import qrcode
        import qrcode.image.svg

        import atalhos
        import games
        found = await asyncio.get_running_loop().run_in_executor(self.io, games.scan, True)
        jogos = [g for g in found if g["platform"] != "Atalho"]
        jogos_html = "".join(f"<li><b>{html.escape(g['name'])}</b> <span>{html.escape(g['platform'])}</span></li>"
                             for g in jogos) or "<li>Nenhum jogo da Epic, EA app ou Steam encontrado.</li>"
        cards = []
        ips = local_ips()
        for ip, desc in ips:
            url = f"http://{ip}:{self.port}/?t={self.token}"
            qr = qrcode.QRCode(border=2, box_size=10)
            qr.add_data(url)
            qr.make(fit=True)
            svg = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage).to_string(encoding="unicode")
            svg = re.sub(r'\swidth="[^"]+"\sheight="[^"]+"', "", svg, count=1)
            usb = ip.startswith("172.20.10.")
            cards.append(f"""
            <div class="card{' usb' if usb else ''}">
              <div class="tag">{html.escape(desc)}</div>
              <div class="qr">{svg}</div>
              <code>{html.escape(url)}</code>
            </div>""")
        if not cards:
            cards.append('<p class="warn">Nenhuma rede encontrada. Ligue o Ponto de Acesso do iPhone com o cabo '
                         'conectado, ou conecte o PC ao Wi-Fi.</p>')
        usb_hint = "" if self.usb else """
          <p class="warn"><b>Cabo USB não detectado.</b> No iPhone: Ajustes &gt; Ponto de Acesso Pessoal &gt; ligar
          "Permitir Outros Conectarem". Conecte o cabo e toque em <i>Confiar</i>. Esta página atualiza sozinha.
          O Windows precisa do app <i>Dispositivos Apple</i> ou do iTunes instalado.</p>"""
        clip = self.clipper.info()
        clip_txt = {"running": "gravando em segundo plano ✔", "starting": "iniciando…",
                    "paused": "em espera (liga quando o cabo ou o celular conectar)",
                    "off": "em espera (liga quando o cabo ou o celular conectar)",
                    "ready": f"modo atalho ({html.escape(self.settings['clip'].get('hotkey', ''))})",
                    "error": f"erro: {html.escape(clip.get('error') or '')}"}.get(clip["status"], "")
        aud = clip.get("audio", {})
        aud_txt = ", ".join(f"{'som do PC' if k == 'system' else 'microfone'} {'✔' if v.get('ok') else '—'}"
                            for k, v in aud.items()) or "sem áudio"
        st = atalhos.status()
        fi = self.fps.info()
        if not fi["exe"] and IS_WINDOWS:
            fps_html = ('FPS: PresentMon não instalado <form method="post" action="/baixar-presentmon" style="display:inline">'
                        '<button class="mini">Baixar PresentMon</button></form>')
        elif not fi["permission"]:
            fps_html = ('FPS: falta liberar a medição no Windows <form method="post" action="/liberar-fps" '
                        'style="display:inline"><button class="mini">Liberar FPS</button></form> '
                        '<span class="hint2">(pede administrador uma vez; depois saia e entre na conta)</span>')
        else:
            fps_html = {"ok": "FPS: medindo ✔", "starting": "FPS: iniciando…", "error": f"FPS: erro ({html.escape(fi['msg'])})",
                        "off": "FPS: pronto (liga quando o celular conecta)"}.get(fi["status"], "FPS: —")
        body = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>PhoneDeck — conectar</title>
<link rel="icon" href="static/icon-192.png">
<style>
 body{{font-family:Segoe UI,system-ui,sans-serif;background:#0b0d12;color:#e5e7eb;margin:0;padding:32px}}
 h1{{margin:0 0 4px;font-size:28px}} .sub{{color:#9ca3af;margin:0 0 24px}}
 .wrap{{max-width:1000px;margin:0 auto}}
 .cards{{display:flex;flex-wrap:wrap;gap:20px;margin:20px 0}}
 .card{{background:#151923;border:1px solid #262c3a;border-radius:16px;padding:18px;width:280px}}
 .card.usb{{border-color:#22c55e}}
 .tag{{font-weight:600;margin-bottom:12px}} .usb .tag{{color:#4ade80}}
 .qr{{background:#fff;border-radius:10px;padding:8px}} .qr svg{{width:100%;height:auto;display:block}}
 code{{display:block;margin-top:10px;font-size:12px;color:#9ca3af;word-break:break-all}}
 ol{{line-height:1.8}} .warn{{background:#3b2a12;border:1px solid #92400e;padding:12px 14px;border-radius:10px}}
 .pin{{font-size:22px;letter-spacing:3px;font-weight:700;color:#fbbf24}}
 a{{color:#60a5fa}} .meta{{color:#9ca3af;font-size:14px;line-height:1.7}}
 .row{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:18px}}
 .games ul{{columns:2;line-height:1.8;padding-left:18px}} .games li span{{color:#9ca3af;font-size:13px;margin-left:6px}}
 .games summary{{cursor:pointer;font-weight:600;margin-top:14px}}
 button.mini{{padding:4px 10px;margin-left:6px;border-color:#1d4ed8;background:#0f1a33;color:#93c5fd;font-size:13px}}
 .hint2{{font-size:12px;color:#9ca3af}}
 button{{font:inherit;font-weight:600;padding:10px 16px;border-radius:10px;border:1px solid #7f1d1d;
   background:#1c1013;color:#fca5a5;cursor:pointer}}
</style></head><body><div class="wrap">
<h1>PhoneDeck está rodando</h1><p class="sub">Aponte a câmera do iPhone para um dos códigos abaixo.</p>
{usb_hint}
<div class="cards">{''.join(cards)}</div>
<ol>
 <li>Escaneie o código com a câmera do iPhone e abra o link no Safari.</li>
 <li>No Safari, toque em <b>Compartilhar</b> &rarr; <b>Adicionar à Tela de Início</b>.</li>
 <li>Daí em diante, é só abrir o PhoneDeck pelo ícone no iPhone.</li>
</ol>
<p>Código de acesso (se o app pedir): <span class="pin">{html.escape(self.token)}</span></p>
<p><a href="/" target="_blank">Abrir o deck aqui no PC</a> (útil para editar os botões com mouse e teclado).</p>
<p class="meta">Clipe: {clip_txt} · Áudio no clipe: {aud_txt}<br>
 GPU: {html.escape(self.stats.gpu_source)} · Música: {'controle do Windows ✔' if self.media.available else 'teclas de mídia'}<br>
 {fps_html}<br>
 Ícone na área de trabalho: {'✔' if st['desktop'] else '—'} · Liga sozinho ao conectar o cabo: {'✔' if st['startup'] else '—'}<br>
 Clipes salvos em: {html.escape(str(self.clipper.output_dir()))}</p>
<details class="games"><summary>Jogos encontrados no PC ({len(jogos)})</summary><ul>{jogos_html}</ul>
<p class="meta">Os botões de jogo usam esta lista para abrir pelo launcher certo (Epic, EA app ou Steam).
 Também aparecem {len(found) - len(jogos)} atalhos da Área de Trabalho e do Menu Iniciar para escolher no editor.</p></details>
<form class="row" method="post" action="/desligar" onsubmit="return confirm('Desligar o PhoneDeck?')">
 <button type="submit">Desligar o PhoneDeck</button>
</form>
</div>
<script>
 // recarrega sozinha quando o cabo é conectado/desconectado
 let ips = {json.dumps([ip for ip, _ in ips])}.join();
 setInterval(async () => {{
   try {{ const r = await fetch('/status.json'); const s = await r.json();
     if (s.ips.join() !== ips) location.reload(); }} catch (e) {{}}
 }}, 3000);
</script></body></html>"""
        return web.Response(text=body, content_type="text/html")

    async def ws_handler(self, request):
        from aiohttp import WSMsgType, web
        ws = web.WebSocketResponse(heartbeat=10, max_msg_size=4 * 1024 * 1024)
        await ws.prepare(request)
        if not self.authorized(request):
            await ws.close(code=4001, message=b"codigo invalido")
            return ws
        self.clients.add(ws)
        self._last_need = time.time()
        print(f"[conexão] celular conectado: {request.remote}  (total: {len(self.clients)})")
        await ws.send_json({"type": "hello", "version": VERSION, "layout": self.layout,
                            "tick": self.last_tick, "history": list(self.history)})
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                except ValueError:
                    continue
                task = asyncio.create_task(self.handle(ws, data))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        finally:
            self.clients.discard(ws)
            self._last_need = time.time()
            print(f"[conexão] desconectado: {request.remote}  (total: {len(self.clients)})")
        return ws

    # ------------------------------------------------------------ mensagens
    async def handle(self, ws, data: dict) -> None:
        import actions
        kind = data.get("type")
        loop = asyncio.get_running_loop()

        if kind == "press":
            bid = str(data.get("id", ""))
            sub = str(data.get("sub", ""))[:20]
            btn = config.find_button(self.layout, bid)
            if not btn and bid.startswith("_player:"):  # controles de música da tela cheia
                app = bid.split(":", 1)[1]
                btn = {"label": "Tela cheia", "action": {"type": "player", "app": app if app in ("spotify", "any") else "spotify"}}
            if not btn:
                await ws.send_json({"type": "result", "id": bid, "ok": False, "msg": "botão não encontrado"})
                return
            action = btn.get("action") or {}
            t = action.get("type")
            pool = self.io if t in ("clip", "run", "player", "game") else self.win
            try:
                msg = await loop.run_in_executor(pool, actions.run_action, action, self.clipper, self.media, sub)
                await ws.send_json({"type": "result", "id": bid, "sub": sub, "ok": True, "msg": msg or ""})
                print(f"[botão] {btn.get('label') or bid}{' ' + sub if sub else ''}" + (f" -> {msg}" if msg else ""))
            except Exception as e:
                await ws.send_json({"type": "result", "id": bid, "sub": sub, "ok": False, "msg": str(e)})
                print(f"[erro] {btn.get('label') or bid}: {e}")
            if t in ("mic", "media", "player"):
                await asyncio.sleep(0.3)
                await self.tick()  # atualiza mic/volume/música na hora

        elif kind == "save_layout":
            try:
                self.layout = config.save_layout(data.get("layout"))
                self.layout_mtime = self._layout_mtime()
                await ws.send_json({"type": "result", "id": "_save", "ok": True, "msg": "Layout salvo"})
                await self.broadcast({"type": "layout", "layout": self.layout})
            except Exception as e:
                await ws.send_json({"type": "result", "id": "_save", "ok": False, "msg": f"Não salvou: {e}"})

        elif kind == "reset_layout":
            keep_theme = self.layout.get("theme")
            fresh = config.default_layout()
            if keep_theme:
                fresh["theme"] = keep_theme
            self.layout = config.save_layout(fresh)
            self.layout_mtime = self._layout_mtime()
            await self.broadcast({"type": "layout", "layout": self.layout})

        elif kind == "list_games":
            import games
            try:
                items = await loop.run_in_executor(self.io, games.scan, True)
            except Exception as e:
                items = []
                print(f"[jogos] erro ao procurar: {e}")
            await ws.send_json({"type": "games", "items": items})

        elif kind == "ping":
            await ws.send_json({"type": "pong", "t": data.get("t")})

    # ------------------------------------------------------- tarefas fundo
    async def tick(self) -> None:
        import audio
        loop = asyncio.get_running_loop()
        s = await loop.run_in_executor(self.io, self.stats.read)
        s["fps"] = await loop.run_in_executor(self.io, self.fps.read)
        self.audio_state = await loop.run_in_executor(self.win, audio.read_state)
        g = s.get("gpu") or {}
        vram = round(100 * g["mem_used"] / g["mem_total"]) if g.get("mem_total") else None
        self.history.append({"cpu": s.get("cpu"), "ram": s.get("ram"), "gpu": g.get("util"),
                             "gputemp": g.get("temp"), "vram": vram, "fps": s["fps"].get("fps")})
        self.last_tick = {"type": "tick", **s, "audio": self.audio_state, "clip": self.clipper.info(),
                          "media": self.media.info, "usb": self.usb, "time": time.strftime("%H:%M")}
        await self.broadcast(self.last_tick)

    async def ticker(self) -> None:
        while True:
            try:
                await self.tick()
            except Exception as e:
                print(f"[aviso] leitura de status falhou: {e}")
            await asyncio.sleep(1)

    async def watcher(self) -> None:
        """Liga a gravação do clipe quando o cabo (ou o celular) conecta; avisa no Windows."""
        import atalhos
        loop = asyncio.get_running_loop()
        first = True
        while True:
            try:
                usb = await loop.run_in_executor(self.io, usb_connected)
                if usb and not self.usb:
                    print("[cabo] iPhone conectado pelo cabo USB")
                    if self.settings.get("notify_on_cable", True) and not first:
                        atalhos.notify("PhoneDeck pronto", "iPhone conectado pelo cabo. Abra o PhoneDeck no celular.")
                elif self.usb and not usb:
                    print("[cabo] cabo USB desconectado")
                self.usb = usb
                first = False
                need = usb or bool(self.clients) or self.settings.get("buffer_always_on", False)
                if need:
                    self._last_need = time.time()
                want = need or (time.time() - self._last_need) < 600  # 10 min de folga
                if want and not self.clipper.active:
                    await loop.run_in_executor(self.io, self.clipper.start)
                elif not want and self.clipper.active:
                    print("[clipe] sem celular há 10 min: gravação em espera")
                    await loop.run_in_executor(self.io, self.clipper.stop)
                # FPS: só roda se algum botão mostra FPS e o celular está em uso
                want_fps = want and self.layout_has("fps")
                if want_fps and not self.fps.active and self.fps.status != "no_permission":
                    self.fps.start()
                elif not want_fps and self.fps.active:
                    self.fps.stop()
            except Exception as e:
                print(f"[aviso] verificação do cabo falhou: {e}")
            await asyncio.sleep(2)

    async def layout_watcher(self) -> None:
        """Se você editar o layout.json à mão, o celular atualiza sozinho."""
        while True:
            await asyncio.sleep(2)
            m = self._layout_mtime()
            if m and m != self.layout_mtime:
                self.layout_mtime = m
                try:
                    self.layout = config.load_layout()
                    await self.broadcast({"type": "layout", "layout": self.layout})
                    print("[layout] layout.json recarregado")
                except Exception as e:
                    print(f"[layout] erro no layout.json: {e}")

    # -------------------------------------------------------------- app
    def build_app(self):
        from aiohttp import web

        @web.middleware
        async def no_cache(request, handler):
            resp = await handler(request)
            if "Cache-Control" not in resp.headers:
                resp.headers["Cache-Control"] = "no-cache"
            return resp

        app = web.Application(middlewares=[no_cache])
        app.router.add_get("/", self.index)
        app.router.add_get("/manifest.webmanifest", self.manifest)
        app.router.add_get("/conectar", self.connect_page)
        app.router.add_get("/ping", self.ping_route)
        app.router.add_get("/status.json", self.status_route)
        app.router.add_post("/desligar", self.shutdown_route)
        app.router.add_get("/art/{key}", self.art_route)
        app.router.add_post("/liberar-fps", self.fps_grant_route)
        app.router.add_post("/baixar-presentmon", self.fps_download_route)
        app.router.add_get("/ws", self.ws_handler)
        app.router.add_static("/static", str(config.WEB_DIR))

        async def on_startup(app):
            self.media.start()
            app["bg"] = [asyncio.create_task(c) for c in (self.ticker(), self.watcher(), self.layout_watcher())]

        async def on_cleanup(app):
            for t in app.get("bg", []):
                t.cancel()
            for ws in list(self.clients):
                await ws.close()
            self.clipper.stop()
            self.fps.stop()

        app.on_startup.append(on_startup)
        app.on_cleanup.append(on_cleanup)
        return app

    def banner(self) -> None:
        line = "=" * 64
        print(line)
        print(f"  PhoneDeck {VERSION}  —  servidor rodando na porta {self.port}  (modo: {self.mode})")
        print(line)
        for ip, desc in local_ips():
            print(f"  {desc:<40}  http://{ip}:{self.port}/?t={self.token}")
        print(f"\n  Código de acesso: {self.token}")
        print(f"  Página com QR code: http://localhost:{self.port}/conectar")
        print(f"  GPU: {self.stats.gpu_source}")
        print(f"  Clipes: modo '{self.clipper.mode}' -> {self.clipper.output_dir()}")
        if not IS_WINDOWS:
            print("\n  [modo demonstração] fora do Windows as ações só aparecem aqui no console.")
        print(line)


async def serve(deck: Deck) -> int:
    from aiohttp import web
    deck.stop_event = asyncio.Event()
    runner = web.AppRunner(deck.build_app(), access_log=None)
    await runner.setup()
    try:
        await web.TCPSite(runner, "0.0.0.0", deck.port).start()
    except OSError as e:
        print(f"\n[erro] Não consegui abrir a porta {deck.port}: {e}")
        print("Outro programa está usando essa porta. Troque a porta no settings.json.")
        await runner.cleanup()
        return 1
    deck.banner()
    if deck.mode in ("console", "abrir") and deck.settings.get("open_browser_on_start", True):
        asyncio.get_running_loop().call_later(1.2, webbrowser.open, f"http://localhost:{deck.port}/conectar")
    try:
        await deck.stop_event.wait()
    finally:
        print("Desligando…")
        await runner.cleanup()
    return 0


def _background_log() -> None:
    """Sem janela (pythonw): manda as mensagens para phonedeck.log."""
    log = config.base_dir() / "phonedeck.log"
    try:
        if log.exists() and log.stat().st_size > 2_000_000:
            log.unlink()
        f = open(log, "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stderr = f
        print(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} =====")
    except Exception:
        pass


def main() -> int:
    args = set(sys.argv[1:])
    mode = "auto" if "--auto" in args else "abrir" if "--abrir" in args else "console"

    if "--instalar-atalhos" in args:
        import atalhos
        try:
            desk = atalhos.install()
            print(f"  Atalhos criados: ícone na área de trabalho ({desk}) e início automático com o Windows.")
            return 0
        except Exception as e:
            print(f"  [aviso] não consegui criar os atalhos: {e}")
            return 1
    if "--remover-atalhos" in args:
        import atalhos
        atalhos.remove()
        print("  Atalhos removidos.")
        return 0

    settings = config.load_settings()
    port = int(settings.get("port", 8765))

    if "--parar" in args:  # usado pelo iniciar.bat antes de ligar a versão nova
        if ping(port):
            ask_shutdown(port)
            for _ in range(20):
                time.sleep(0.5)
                if not ping(port, 0.5):
                    break
        return 0

    if "--preparar-fps" in args:  # usado pelo iniciar.bat: baixa o PresentMon e libera a medição
        import fps
        if not fps.find_presentmon(settings.get("fps", {}).get("presentmon_path", "")):
            try:
                fps.download_presentmon()
                print("  PresentMon instalado (medidor de FPS).")
            except Exception as e:
                print(f"  [aviso] não consegui baixar o PresentMon ({e}). O FPS fica desligado.")
        if not fps.has_permission() and not settings.get("fps_permission_asked") and sys.stdin and sys.stdin.isatty():
            print("\n  Para medir o FPS dos jogos, o Windows precisa liberar o seu usuário no grupo")
            print("  'Usuários de log de desempenho'. Isso pede permissão de administrador UMA vez.")
            ans = input("  Liberar agora? [S/N] ").strip().lower()
            settings["fps_permission_asked"] = True
            config._write_json(config.SETTINGS_PATH, settings)
            if ans.startswith("s"):
                if fps.grant_permission():
                    print("  Liberado! Saia e entre de novo na sua conta do Windows (ou reinicie) para valer.")
                else:
                    print("  Não foi liberado (cancelado). Dá para liberar depois pela página do PhoneDeck.")
        return 0

    if "--esperar" in args:  # usado pelo iniciar.bat: espera o servidor responder
        for _ in range(50):
            if ping(port):
                return 0
            time.sleep(0.5)
        return 1

    if ping(port):  # já está rodando
        if mode == "console":
            print("O PhoneDeck já estava rodando em segundo plano: desligando para abrir no console…")
            ask_shutdown(port)
            for _ in range(20):
                time.sleep(0.5)
                if not ping(port, 0.5):
                    break
        else:
            if mode == "abrir":
                webbrowser.open(f"http://localhost:{port}/conectar")
            return 0

    if mode != "console" or sys.stdout is None:
        _background_log()
    elif IS_WINDOWS:
        os.system("title PhoneDeck")

    deck = Deck(mode)
    try:
        code = asyncio.run(serve(deck))
    except KeyboardInterrupt:
        code = 0
    finally:
        deck.clipper.stop()
    if code and mode == "console" and IS_WINDOWS and sys.stdin and sys.stdin.isatty():
        input("Enter para sair...")
    return code


if __name__ == "__main__":
    sys.exit(main())
