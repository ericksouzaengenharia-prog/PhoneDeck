"""
Painel de música: lê e controla o player pelo controle de mídia do Windows
(o mesmo que aparece no painel de volume do Windows). Funciona com o Spotify
e com qualquer app que se integre ao Windows (navegador, Deezer, YouTube Music…).

Mostra capa, música, artista, progresso e permite play/pause, próxima,
anterior e ligar/desligar o aleatório (shuffle).

As APIs do Windows (WinRT) rodam numa thread própria com seu próprio
loop asyncio, para não misturar com o resto do servidor.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import hashlib
import sys
import threading
import time

IS_WINDOWS = sys.platform == "win32"


def _friendly(aumid: str) -> str:
    a = (aumid or "").lower()
    for key, name in (("spotify", "Spotify"), ("chrome", "Chrome"), ("msedge", "Edge"), ("firefox", "Firefox"),
                      ("opera", "Opera"), ("deezer", "Deezer"), ("tidal", "TIDAL"), ("applemusic", "Apple Music"),
                      ("zunemusic", "Media Player"), ("vlc", "VLC")):
        if key in a:
            return name
    name = (aumid or "").split("!")[-1].replace(".exe", "")
    return name[:24] or "Player"


class Media:
    def __init__(self):
        self.available = False
        self.error = ""
        self.info: dict[str, dict] = {"spotify": {}, "any": {}}
        self.art: dict[str, tuple[str, bytes, str]] = {}   # chave -> (versão, bytes, tipo)
        self.loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._last_track: dict[str, str] = {}
        self._wake: asyncio.Event | None = None
        # modo demonstração
        self._demo = {"i": 0, "playing": True, "shuffle": False, "t0": time.time()}

    # ------------------------------------------------------------------ início
    def start(self) -> None:
        self._thread = threading.Thread(target=self._thread_main, name="media", daemon=True)
        self._thread.start()

    def _thread_main(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._wake = asyncio.Event()
        if not IS_WINDOWS:
            self.available = True
            self.loop.create_task(self._demo_poll())
            self.loop.run_forever()
            return
        try:
            try:
                from winrt.runtime import MTA, init_apartment
                init_apartment(MTA)
            except Exception:
                pass
            from winrt.windows.media.control import \
                GlobalSystemMediaTransportControlsSessionManager as Manager
            from winrt.windows.storage.streams import DataReader
            self._DataReader = DataReader
            self.mgr = self.loop.run_until_complete(Manager.request_async())
            self.available = True
        except Exception as e:
            self.error = f"controle de mídia indisponível ({e})"
            print(f"[música] {self.error} — os botões usarão as teclas de mídia.")
            return
        self.loop.create_task(self._poll())
        self.loop.run_forever()

    # ---------------------------------------------------------------- leitura
    def _session(self, prefer: str):
        try:
            if prefer == "spotify":
                for s in self.mgr.get_sessions():
                    if "spotify" in (s.source_app_user_model_id or "").lower():
                        return s
                return None
            return self.mgr.get_current_session()
        except Exception:
            return None

    async def _read(self, key: str, s) -> dict:
        if s is None:
            return {"present": False}
        out = {"present": True, "app": _friendly(s.source_app_user_model_id)}
        try:
            pi = s.get_playback_info()
            out["status"] = {4: "playing", 5: "paused", 3: "stopped"}.get(int(pi.playback_status), "stopped")
            shuffle = pi.is_shuffle_active
            out["shuffle"] = None if shuffle is None else bool(shuffle)
            c = pi.controls
            out["can_shuffle"] = bool(c.is_shuffle_enabled)
            out["can_next"] = bool(c.is_next_enabled)
            out["can_prev"] = bool(c.is_previous_enabled)
        except Exception:
            pass
        try:
            tl = s.get_timeline_properties()
            dur = tl.end_time.total_seconds()
            pos = tl.position.total_seconds()
            if out.get("status") == "playing":
                last = tl.last_updated_time
                if last.tzinfo is None:
                    last = last.replace(tzinfo=dt.timezone.utc)
                pos += max(0.0, (dt.datetime.now(dt.timezone.utc) - last).total_seconds())
            if dur > 0:
                out["duration"] = round(dur, 1)
                out["position"] = round(min(pos, dur), 1)
        except Exception:
            pass
        try:
            props = await s.try_get_media_properties_async()
            if props is not None:
                out["title"] = props.title or ""
                out["artist"] = props.artist or props.album_artist or ""
                out["album"] = props.album_title or ""
                track = f"{out['app']}|{out['title']}|{out['artist']}|{out['album']}"
                if self._last_track.get(key) != track:
                    self._last_track[key] = track
                    await self._load_art(key, props, track)
        except Exception:
            pass
        if key in self.art:
            out["art"] = self.art[key][0]
        return out

    async def _load_art(self, key: str, props, track: str) -> None:
        self.art.pop(key, None)
        try:
            ref = props.thumbnail
            if ref is None:
                return
            stream = await ref.open_read_async()
            size = int(stream.size)
            if not 0 < size < 5_000_000:
                return
            reader = self._DataReader(stream.get_input_stream_at(0))
            await reader.load_async(size)
            buf = bytearray(size)
            reader.read_bytes(buf)
            ctype = getattr(stream, "content_type", "") or "image/jpeg"
            ver = hashlib.md5(track.encode("utf-8", "replace")).hexdigest()[:10]
            self.art[key] = (ver, bytes(buf), ctype)
        except Exception:
            pass

    async def _poll(self) -> None:
        while True:
            try:
                sp = self._session("spotify")
                cur = self._session("any")
                self.info["spotify"] = await self._read("spotify", sp)
                same = sp is not None and cur is not None and \
                    sp.source_app_user_model_id == cur.source_app_user_model_id
                if same:
                    self.info["any"] = dict(self.info["spotify"])
                    if "spotify" in self.art:
                        self.art["any"] = self.art["spotify"]
                else:
                    self.info["any"] = await self._read("any", cur)
            except Exception as e:
                self.error = str(e)
            self._wake.clear()
            try:
                await asyncio.wait_for(self._wake.wait(), 1.0)
            except asyncio.TimeoutError:
                pass

    # --------------------------------------------------------------- comandos
    def command(self, cmd: str, prefer: str = "spotify") -> str:
        """Chamado de outra thread. Devolve uma mensagem curta ou lança erro."""
        if not self.available or self.loop is None:
            raise RuntimeError("controle de mídia indisponível")
        fut = asyncio.run_coroutine_threadsafe(self._command(cmd, prefer), self.loop)
        return fut.result(timeout=5)

    async def _command(self, cmd: str, prefer: str) -> str:
        if not IS_WINDOWS:
            return self._demo_command(cmd)
        s = self._session(prefer) or (self._session("any") if prefer == "spotify" else None)
        if s is None:
            raise RuntimeError("Nenhuma música tocando — abra o Spotify" if prefer == "spotify"
                               else "Nenhum player aberto")
        msg = ""
        if cmd == "playpause":
            ok = await s.try_toggle_play_pause_async()
        elif cmd == "next":
            ok = await s.try_skip_next_async()
        elif cmd == "prev":
            ok = await s.try_skip_previous_async()
        elif cmd == "shuffle":
            pi = s.get_playback_info()
            if not pi.controls.is_shuffle_enabled:
                raise RuntimeError(f"{_friendly(s.source_app_user_model_id)} não aceita aleatório por aqui")
            new = not bool(pi.is_shuffle_active)
            ok = await s.try_change_shuffle_active_async(new)
            msg = "Aleatório ligado" if new else "Aleatório desligado"
        else:
            raise RuntimeError(f"comando desconhecido: {cmd}")
        if not ok:
            raise RuntimeError("o player recusou o comando")
        await asyncio.sleep(0.25)
        self._wake.set()
        return msg

    # ---------------------------------------------------------- demonstração
    DEMO = [("Faixa de Demonstração", "Artista Exemplo", 214), ("Outra Música", "Banda Teste", 187),
            ("Terceira Canção", "Grupo Fictício", 243)]

    def _demo_art(self, i: int) -> None:
        try:
            import io
            from PIL import Image, ImageDraw
            cols = [((236, 72, 153), (99, 102, 241)), ((34, 197, 94), (14, 116, 144)), ((245, 158, 11), (220, 38, 38))]
            a, b = cols[i % 3]
            im = Image.new("RGB", (300, 300))
            d = ImageDraw.Draw(im)
            for y in range(300):
                t = y / 299
                d.line([(0, y), (300, y)], fill=tuple(int(a[k] * (1 - t) + b[k] * t) for k in range(3)))
            d.ellipse([90, 90, 210, 210], outline=(255, 255, 255), width=10)
            d.ellipse([140, 140, 160, 160], fill=(255, 255, 255))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=85)
            ver = f"demo{i}"
            self.art["spotify"] = self.art["any"] = (ver, buf.getvalue(), "image/jpeg")
        except Exception:
            pass

    async def _demo_poll(self) -> None:
        self._demo_art(0)
        while True:
            d = self._demo
            title, artist, dur = self.DEMO[d["i"] % 3]
            pos = (time.time() - d["t0"]) if d["playing"] else d.get("paused_at", 0)
            if pos > dur:
                d["i"] += 1
                d["t0"] = time.time()
                self._demo_art(d["i"])
                pos = 0
            info = {"present": True, "app": "Spotify", "title": title, "artist": artist, "album": "Álbum Demo",
                    "status": "playing" if d["playing"] else "paused", "shuffle": d["shuffle"],
                    "can_shuffle": True, "can_next": True, "can_prev": True,
                    "duration": dur, "position": round(pos, 1), "art": self.art.get("spotify", ("",))[0]}
            self.info["spotify"] = info
            self.info["any"] = dict(info)
            self._wake.clear()
            try:
                await asyncio.wait_for(self._wake.wait(), 1.0)
            except asyncio.TimeoutError:
                pass

    def _demo_command(self, cmd: str) -> str:
        d = self._demo
        if cmd == "playpause":
            if d["playing"]:
                d["paused_at"] = time.time() - d["t0"]
            else:
                d["t0"] = time.time() - d.get("paused_at", 0)
            d["playing"] = not d["playing"]
        elif cmd in ("next", "prev"):
            d["i"] = max(0, d["i"] + (1 if cmd == "next" else -1))
            d["t0"] = time.time()
            d["paused_at"] = 0
            self._demo_art(d["i"])
        elif cmd == "shuffle":
            d["shuffle"] = not d["shuffle"]
            self._wake.set()
            return "Aleatório ligado" if d["shuffle"] else "Aleatório desligado"
        self._wake.set()
        print(f"[demo] música: {cmd}")
        return ""
