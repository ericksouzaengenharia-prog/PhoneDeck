"""
Configuração do PhoneDeck.

Dois arquivos ficam na pasta principal do projeto:
  - settings.json : coisas do PC (porta, código de acesso, gravação de clipes)
  - layout.json   : páginas e botões (o que você edita pelo celular)

Os dois são criados automaticamente na primeira execução.
"""
from __future__ import annotations

import copy
import json
import os
import secrets
import string
import sys
from pathlib import Path


def base_dir() -> Path:
    """Pasta do projeto (funciona também quando empacotado como .exe)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """Pasta onde estão os arquivos da interface (web/)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return base_dir()


SETTINGS_PATH = base_dir() / "settings.json"
LAYOUT_PATH = base_dir() / "layout.json"
WEB_DIR = resource_dir() / "web"


def _new_token() -> str:
    alphabet = string.ascii_lowercase + string.digits
    alphabet = alphabet.replace("l", "").replace("1", "").replace("o", "").replace("0", "")
    return "".join(secrets.choice(alphabet) for _ in range(8))


DEFAULT_SETTINGS = {
    "port": 8765,
    "token": "",
    "require_token": True,
    "open_browser_on_start": True,
    "ffmpeg_path": "",
    # liga/desliga a avisos do Windows quando o cabo do iPhone é conectado
    "notify_on_cable": True,
    # False = a gravação do clipe só roda com o cabo conectado ou o celular aberto (economiza PC)
    "buffer_always_on": False,
    # medidor de FPS (PresentMon). Vazio = usa ferramentas\\PresentMon.exe
    "fps": {"presentmon_path": ""},
    "fps_permission_asked": False,
    "clip": {
        # "ffmpeg" = o próprio PhoneDeck grava em segundo plano (padrão)
        # "hotkey" = só aperta um atalho (ex.: alt+f10 do NVIDIA Instant Replay / OBS)
        # "off"    = desligado
        "mode": "ffmpeg",
        "buffer_seconds": 30,
        "fps": 30,
        "capture": "auto",      # auto | ddagrab | gdigrab
        "monitor": 0,           # índice do monitor (ddagrab). 0 = principal
        "encoder": "auto",      # auto | h264_nvenc | h264_amf | h264_qsv | libx264
        "bitrate": "8M",
        "system_audio": True,   # grava o som do PC
        "microphone": True,     # grava o microfone
        "system_volume": 1.0,
        "mic_volume": 1.0,
        "video_delay_ms": 150,  # ajuste fino do sincronismo som/imagem
        "hotkey": "alt+f10",
        "output_dir": "",       # vazio = Vídeos\\PhoneDeck
    },
}


# ---------------------------------------------------------------------------
# Layout padrão (botões que já vêm prontos)
# ---------------------------------------------------------------------------
def _b(bid, label, icon, color, action, size="1x1", hold=False):
    b = {"id": bid, "label": label, "icon": icon, "color": color, "action": action, "size": size}
    if hold:
        b["hold"] = True  # precisa segurar o botão para acionar (evita toque sem querer)
    return b


# links fixos usados pela versão 2.0; na 2.1 esses botões viram "jogo instalado"
# (o PhoneDeck procura o jogo no PC e usa o launcher certo: Epic, EA app ou Steam)
OLD_GAME_LINKS = {
    "com.epicgames.launcher://apps/fn%3A4fe75bbc5a674f4f9b356b5c90567da5%3AFortnite?action=launch&silent=true": "Fortnite",
    "com.epicgames.launcher://apps/Sugar?action=launch&silent=true": "Rocket League",
    "steam://rungameid/2807960": "Battlefield 6",
}

FPS_TILE = _b("fps", "FPS", "speed", "#0e7490", {"type": "stat", "stat": "fps"}, "2x1")

# Versão 4: botões grandes. Cada página cabe numa grade de 3 colunas (em pé) ou
# 5 colunas (deitado) sem rolar: 15 quadradinhos por página.
DEFAULT_LAYOUT = {
    "version": 5,
    "grid": {"portrait": 3, "landscape": 5},
    "showLabels": True,
    "theme": {"name": "classico", "mode": "auto"},
    "fullscreen": ["music", "gpu", "cpu", "ram", "fps"],  # o que aparece na tela cheia, nesta ordem
    "pages": [
        {
            "id": "principal",
            "name": "Principal",
            "buttons": [
                _b("spotify", "Spotify", "music", "#14532d", {"type": "player", "app": "spotify"}, "3x2"),
                _b("clip15", "Clipe 15s", "clip", "#b91c1c", {"type": "clip", "seconds": 15}),
                _b("mic", "Microfone", "mic", "#9a3412", {"type": "mic"}),
                _b("desk", "Área de trabalho", "desktop", "#334155", {"type": "desktop"}),
                _b("mute", "Mudo", "vol-mute", "#9a3412", {"type": "media", "key": "mute"}),
                _b("vdown", "Vol −", "vol-down", "#334155", {"type": "media", "key": "voldown"}),
                _b("vup", "Vol +", "vol-up", "#334155", {"type": "media", "key": "volup"}),
                _b("fortnite", "Fortnite", "🪂", "#7c3aed", {"type": "game", "name": "Fortnite", "target": ""}),
                _b("rocket", "Rocket League", "⚽", "#1d4ed8", {"type": "game", "name": "Rocket League", "target": ""}),
                _b("bf6", "Battlefield 6", "🪖", "#c2410c", {"type": "game", "name": "Battlefield 6", "target": ""}),
            ],
        },
        {
            "id": "pc",
            "name": "PC",
            "buttons": [
                FPS_TILE,
                _b("print", "Print", "camera", "#334155", {"type": "hotkey", "keys": "win+printscreen"}),
                _b("gpu", "GPU", "gpu", "#166534", {"type": "stat", "stat": "gpu"}, "2x1"),
                _b("clips", "Meus clipes", "folder", "#334155", {"type": "open_clips"}),
                _b("cpu", "CPU", "cpu", "#1e40af", {"type": "stat", "stat": "cpu"}, "2x1"),
                _b("taskmgr", "Gerenciador", "chart", "#166534", {"type": "hotkey", "keys": "ctrl+shift+esc"}),
                _b("ram", "RAM", "ram", "#6b21a8", {"type": "stat", "stat": "ram"}, "2x1"),
                _b("lock", "Bloquear PC", "lock", "#334155", {"type": "lock"}, hold=True),
                _b("gputemp", "Temp. GPU", "thermo", "#9a3412", {"type": "stat", "stat": "gputemp"}, "2x1"),
                _b("altf4", "Fechar janela", "close", "#7f1d1d", {"type": "hotkey", "keys": "alt+f4"}, hold=True),
            ],
        },
        {
            "id": "apps",
            "name": "Mais",
            "buttons": [
                _b("prev", "Anterior", "prev", "#334155", {"type": "media", "key": "prev"}),
                _b("play", "Play/Pause", "play-pause", "#065f46", {"type": "media", "key": "playpause"}),
                _b("next", "Próxima", "next", "#334155", {"type": "media", "key": "next"}),
                _b("discmute", "Mutar Discord", "headset", "#4338ca", {"type": "hotkey", "keys": "ctrl+shift+m"}),
                _b("spotapp", "Abrir Spotify", "music", "#15803d", {"type": "open", "target": "spotify:", "args": ""}),
                _b("browser", "Navegador", "globe", "#1e40af", {"type": "open", "target": "https://www.google.com", "args": ""}),
                _b("vram", "VRAM", "chip", "#166534", {"type": "stat", "stat": "vram"}, "2x1"),
                _b("vol", "Volume", "volume", "#334155", {"type": "stat", "stat": "volume"}),
                _b("hello", "Digitar texto", "type", "#334155", {"type": "text", "text": "gg wp!"}),
                _b("calc", "Calculadora", "calc", "#334155", {"type": "open", "target": "calc.exe", "args": ""}),
                _b("clock", "Hora", "clock", "#334155", {"type": "stat", "stat": "clock"}),
                _b("clip30", "Clipe 30s", "clip", "#991b1b", {"type": "clip", "seconds": 30}),
                _b("explorer", "Explorador", "folder", "#a16207", {"type": "open", "target": "explorer.exe", "args": ""}),
            ],
        },
    ],
}

# ids dos botões padrão das versões anteriores (para saber o que é seu e o que veio de fábrica)
OLD_DEFAULT_IDS = {
    "spotify", "gpu", "clip15", "cpu", "mic", "ram", "fortnite", "rocket", "bf6", "mute", "vdown", "vup", "desk",
    "print", "clips", "goapps", "back", "gputemp", "vram", "prev", "play", "next", "vol", "browser", "explorer",
    "taskmgr", "spotapp", "discmute", "hello", "altf4", "lock", "clip30", "clock", "calc",
}


ACTION_TYPES = {
    "media", "mic", "hotkey", "desktop", "clip", "open", "run", "text",
    "lock", "page", "open_clips", "stat", "player", "game", "none",
}
SIZES = {"1x1", "2x1", "1x2", "2x2", "3x1", "3x2", "4x1", "4x2"}
THEMES = {"classico", "minimal", "neon", "fofo", "glass", "rgb"}
THEME_MODES = {"auto", "dark", "light"}
FULLSCREEN_VIEWS = {"music", "gpu", "cpu", "ram", "fps", "gputemp", "vram"}


# ---------------------------------------------------------------------------
def _deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _write_json(path: Path, data) -> None:
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{secrets.token_hex(3)}.tmp")  # nome único: 2 processos não colidem
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_settings() -> dict:
    data = {}
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except Exception as e:  # arquivo quebrado: avisa e usa o padrão
            print(f"[aviso] settings.json inválido ({e}); usando padrões.")
    settings = _deep_merge(DEFAULT_SETTINGS, data)
    if not settings.get("token"):
        settings["token"] = _new_token()
    if settings != data:  # só grava se faltava algo (arquivo novo ou campos novos)
        _write_json(SETTINGS_PATH, settings)
    return settings


LAYOUT_VERSION = DEFAULT_LAYOUT["version"]


def load_layout() -> dict:
    if LAYOUT_PATH.exists():
        try:
            data = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
            if int(data.get("version", 1)) < 2:
                # layout da versão 1: guarda uma cópia e passa a usar a nova tela principal
                backup = LAYOUT_PATH.with_name("layout_v1_backup.json")
                _write_json(backup, data)
                print(f"[layout] layout antigo salvo em {backup.name}; usando a nova tela principal.")
            else:
                version = int(data.get("version", 2))
                data = _migrate_games(data)
                if version < LAYOUT_VERSION:
                    _write_json(LAYOUT_PATH.with_name(f"layout_v{version}_backup.json"), data)
                if version < 4:
                    data = _migrate_big_buttons(data)
                    print(f"[layout] nova organização com botões maiores (cópia do anterior em layout_v{version}_backup.json)")
                elif version < 5:
                    data = _migrate_fps(data)
                    print("[layout] bloco de FPS adicionado na página PC")
                layout = validate_layout(data)
                if version < LAYOUT_VERSION:
                    _write_json(LAYOUT_PATH, layout)
                return layout
        except Exception as e:
            print(f"[aviso] layout.json inválido ({e}); usando o layout padrão.")
    layout = copy.deepcopy(DEFAULT_LAYOUT)
    _write_json(LAYOUT_PATH, layout)
    return layout


def _migrate_games(data: dict) -> dict:
    """Botões com os links fixos da 2.0 viram 'jogo instalado' (acha Epic/EA app/Steam sozinho)."""
    for p in data.get("pages", []):
        for b in p.get("buttons", []):
            a = b.get("action") or {}
            if a.get("type") == "open" and a.get("target") in OLD_GAME_LINKS:
                b["action"] = {"type": "game", "name": OLD_GAME_LINKS[a["target"]], "target": ""}
    return data


def _migrate_big_buttons(old: dict) -> dict:
    """Passa para a organização de botões grandes (v4) sem perder o que você mudou:
    - botões padrão continuam com o seu nome, ícone, cor e ação (ex.: o Fortnite que você reconfigurou)
    - botões que você criou vão para a página "Mais"; páginas que você criou continuam no fim
    - tema e "mostrar nomes" são mantidos"""
    new = default_layout()
    mine = {}
    for p in old.get("pages", []):
        for b in p.get("buttons", []):
            if isinstance(b, dict) and b.get("id"):
                mine[b["id"]] = b
    for p in new["pages"]:
        for b in p["buttons"]:
            o = mine.get(b["id"])
            if o and (o.get("action") or {}).get("type") != "page":
                for k in ("label", "icon", "color", "action"):
                    if o.get(k):
                        b[k] = o[k]
    extras = [b for p in old.get("pages", []) if p.get("id") in ("principal", "apps")
              for b in p.get("buttons", []) if isinstance(b, dict) and b.get("id") not in OLD_DEFAULT_IDS]
    new["pages"][2]["buttons"] += extras
    new["pages"] += [p for p in old.get("pages", []) if p.get("id") not in ("principal", "apps", "pc")]
    if isinstance(old.get("theme"), dict):
        new["theme"] = old["theme"]
    if "showLabels" in old:
        new["showLabels"] = bool(old["showLabels"])
    return new


def _migrate_fps(data: dict) -> dict:
    """v4 -> v5: põe o bloco de FPS no começo da página PC (Clipe 30s e Explorador vão para "Mais")."""
    pages = data.get("pages", [])
    has_fps = any((b.get("action") or {}).get("stat") == "fps" for p in pages for b in p.get("buttons", []))
    pc = next((p for p in pages if p.get("id") == "pc"), None)
    more = next((p for p in pages if p.get("id") == "apps"), None)
    if not has_fps:
        if pc is None:
            pc = {"id": "pc", "name": "PC", "buttons": []}
            pages.insert(1, pc)
        pc["buttons"].insert(0, copy.deepcopy(FPS_TILE))
        if more is not None:
            moved = [b for b in pc["buttons"] if b.get("id") in ("clip30", "explorer")]
            pc["buttons"] = [b for b in pc["buttons"] if b not in moved]
            more["buttons"] += moved
    return data


def save_layout(layout: dict) -> dict:
    layout = validate_layout(layout)
    _write_json(LAYOUT_PATH, layout)
    return layout


def default_layout() -> dict:
    return copy.deepcopy(DEFAULT_LAYOUT)


def _s(v, maxlen=500) -> str:
    return str(v if v is not None else "")[:maxlen]


def validate_layout(data) -> dict:
    """Confere a estrutura e limpa valores estranhos. Lança ValueError se não der."""
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        raise ValueError("layout sem 'pages'")
    if not data["pages"]:
        raise ValueError("o layout precisa de pelo menos uma página")
    grid = data.get("grid") or {}
    theme = data.get("theme") if isinstance(data.get("theme"), dict) else {}
    out = {
        "version": LAYOUT_VERSION,
        "grid": {
            "portrait": max(1, min(8, int(grid.get("portrait", 3)))),
            "landscape": max(1, min(12, int(grid.get("landscape", 5)))),
        },
        "showLabels": bool(data.get("showLabels", True)),
        "theme": {
            "name": theme.get("name") if theme.get("name") in THEMES else "classico",
            "mode": theme.get("mode") if theme.get("mode") in THEME_MODES else "auto",
        },
        "fullscreen": _fullscreen(data.get("fullscreen")),
        "pages": [],
    }
    seen_ids = set()
    for p in data["pages"][:50]:
        if not isinstance(p, dict):
            continue
        pid = _s(p.get("id"), 64) or f"p{len(out['pages'])}"
        page = {"id": pid, "name": _s(p.get("name"), 40) or "Página", "buttons": []}
        for b in (p.get("buttons") or [])[:120]:
            if not isinstance(b, dict):
                continue
            bid = _s(b.get("id"), 64) or secrets.token_hex(4)
            while bid in seen_ids:
                bid = secrets.token_hex(4)
            seen_ids.add(bid)
            action = b.get("action") if isinstance(b.get("action"), dict) else {"type": "none"}
            if action.get("type") not in ACTION_TYPES:
                action = {"type": "none"}
            action = {k: (v if isinstance(v, (int, float, bool)) else _s(v, 2000)) for k, v in action.items()}
            page["buttons"].append({
                "id": bid,
                "label": _s(b.get("label"), 40),
                "icon": _s(b.get("icon"), 40),
                "color": _s(b.get("color"), 20) or "#1f2937",
                "action": action,
                "size": b.get("size") if b.get("size") in SIZES else "1x1",
                **({"hold": True} if b.get("hold") else {}),
            })
        out["pages"].append(page)
    if not out["pages"]:
        raise ValueError("nenhuma página válida")
    return out


def _fullscreen(views) -> list:
    out = []
    for v in views if isinstance(views, list) else []:
        if v in FULLSCREEN_VIEWS and v not in out:
            out.append(v)
    return out or list(DEFAULT_LAYOUT["fullscreen"])


def find_button(layout: dict, button_id: str):
    for p in layout.get("pages", []):
        for b in p.get("buttons", []):
            if b.get("id") == button_id:
                return b
    return None
