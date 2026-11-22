"""
Encontra os jogos instalados no PC e abre cada um pelo launcher certo.

  Epic Games  -> lê os manifestos da Epic (ProgramData\\Epic\\...\\Manifests\\*.item)
                 e monta o mesmo link que o "Criar atalho" da Epic cria
  EA app      -> procura as pastas dos jogos EA e lê __Installer\\installerdata.xml
                 (IDs usados no link origin2://game/launch?offerIds=...);
                 sem esse arquivo, usa o .exe principal do jogo
  Steam       -> bibliotecas da Steam (appmanifest_*.acf) -> steam://rungameid/ID
  Atalhos     -> atalhos da Área de Trabalho e do Menu Iniciar (.lnk / .url)

Um botão do tipo "game" guarda o nome do jogo (e, se você escolheu na lista,
o link exato). Se o link falhar ou não existir, ele procura de novo pelo nome.
"""
from __future__ import annotations

import json
import os
import re
import string
import subprocess
import sys
import threading
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

IS_WINDOWS = sys.platform == "win32"
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

PLATFORM_ORDER = {"Epic Games": 0, "EA app": 0, "Steam": 0, "Atalho": 2}
SKIP_SHORTCUT = re.compile(r"unins|desinst|uninstall|readme|leia-?me|manual|help|ajuda|website|site|support|"
                           r"suporte|license|licen|release notes|notas|changelog|documenta", re.I)
SKIP_EXE = re.compile(r"unins|setup|install|crash|report|cleanup|touchup|anticheat|easyanti|eac_|helper|redist|"
                      r"vc_?redist|dxsetup|activation|launcherpatcher|ealink|update|bugsplat|prereq", re.I)
SKIP_STEAM = re.compile(r"steamworks|redistributable|proton|steam linux runtime|steamvr", re.I)


def norm(s: str) -> str:
    """'Battlefield™ 6' -> 'battlefield 6'"""
    s = re.sub("[\u2122\u00ae\u00a9\u2120]", "", s or "")  # tira ™ ® © ℠ (senão ™ vira "TM")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


# ---------------------------------------------------------------- registro
def _reg(root_name: str, path: str, value: str = "") -> str | None:
    if not IS_WINDOWS:
        return None
    import winreg
    root = getattr(winreg, root_name)
    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_READ | view) as k:
                return str(winreg.QueryValueEx(k, value)[0])
        except OSError:
            continue
    return None


def _uninstall_entries():
    """(nome, editora, pasta) de cada programa em 'Aplicativos instalados'."""
    if not IS_WINDOWS:
        return []
    import winreg
    out = []
    spots = [("HKEY_LOCAL_MACHINE", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_64KEY),
             ("HKEY_LOCAL_MACHINE", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", winreg.KEY_WOW64_32KEY),
             ("HKEY_CURRENT_USER", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", 0)]
    for root_name, path, view in spots:
        try:
            with winreg.OpenKey(getattr(winreg, root_name), path, 0, winreg.KEY_READ | view) as k:
                for i in range(winreg.QueryInfoKey(k)[0]):
                    try:
                        with winreg.OpenKey(k, winreg.EnumKey(k, i)) as sub:
                            def val(n):
                                try:
                                    return str(winreg.QueryValueEx(sub, n)[0])
                                except OSError:
                                    return ""
                            out.append((val("DisplayName"), val("Publisher"), val("InstallLocation")))
                    except OSError:
                        continue
        except OSError:
            continue
    return out


def _drives() -> list[str]:
    if not IS_WINDOWS:
        return []
    return [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]


# ---------------------------------------------------------------- Epic
def scan_epic(manifest_dirs: list[Path] | None = None) -> list[dict]:
    if manifest_dirs is None:
        manifest_dirs = []
        app_data = _reg("HKEY_LOCAL_MACHINE", r"SOFTWARE\Epic Games\EpicGamesLauncher", "AppDataPath")
        if app_data:
            manifest_dirs.append(Path(app_data) / "Manifests")
        manifest_dirs.append(Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Epic" / "EpicGamesLauncher"
                             / "Data" / "Manifests")
    out, seen = [], set()
    for d in manifest_dirs:
        try:
            files = sorted(Path(d).glob("*.item"))
        except OSError:
            continue
        for f in files:
            try:
                m = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            app = m.get("AppName") or ""
            if not app or m.get("bIsIncompleteInstall"):
                continue
            if (m.get("MainGameAppName") or app) != app:        # DLC/complemento
                continue
            cats = [c.lower() for c in (m.get("AppCategories") or [])]
            if cats and "games" not in cats:                     # ex.: Unreal Engine
                continue
            ns, cid = m.get("CatalogNamespace") or "", m.get("CatalogItemId") or ""
            if not ns or not cid or app in seen:
                continue
            seen.add(app)
            uri = (f"com.epicgames.launcher://apps/{quote(ns, safe='')}%3A{quote(cid, safe='')}"
                   f"%3A{quote(app, safe='')}?action=launch&silent=true")
            out.append({"name": m.get("DisplayName") or app, "platform": "Epic Games", "target": uri,
                        "dir": m.get("InstallLocation") or ""})
    return out


# ---------------------------------------------------------------- EA app
def _main_exe(folder: Path) -> Path | None:
    try:
        exes = [p for p in folder.glob("*.exe") if not SKIP_EXE.search(p.name)]
        return max(exes, key=lambda p: p.stat().st_size) if exes else None
    except OSError:
        return None


def ea_game_from_folder(folder: Path, fallback_name: str = "") -> dict | None:
    folder = Path(folder)
    if not folder.is_dir() or "ea desktop" in str(folder).lower():
        return None
    xml = folder / "__Installer" / "installerdata.xml"
    name, ids = fallback_name or folder.name, []
    if xml.exists():
        try:
            text = xml.read_text(encoding="utf-8", errors="replace")
            ids = re.findall(r"<contentID>\s*([^<\s]+)\s*</contentID>", text)
            t = re.search(r'<gameTitle[^>]*locale="en_US"[^>]*>\s*([^<]+?)\s*</gameTitle>', text) or \
                re.search(r"<gameTitle[^>]*>\s*([^<]+?)\s*</gameTitle>", text)
            if t:
                name = t.group(1)
        except OSError:
            pass
    if ids:
        seen = list(dict.fromkeys(ids))
        return {"name": name, "platform": "EA app", "target": "origin2://game/launch?offerIds=" + ",".join(seen),
                "dir": str(folder)}
    exe = _main_exe(folder)
    if exe:
        return {"name": name, "platform": "EA app", "target": str(exe), "dir": str(folder)}
    return None


def scan_ea(extra_roots: list[Path] | None = None) -> list[dict]:
    cands: dict[str, str] = {}
    for name, pub, loc in _uninstall_entries():
        if loc and ("electronic arts" in pub.lower() or Path(loc, "__Installer").exists()):
            cands[os.path.normcase(loc.rstrip("\\/"))] = name
    roots = list(extra_roots or [])
    for d in _drives():
        roots += [Path(d, "Program Files", "EA Games"), Path(d, "EA Games"), Path(d, "Games", "EA Games"),
                  Path(d, "Program Files (x86)", "Origin Games"), Path(d, "Origin Games")]
    for r in roots:
        try:
            for sub in Path(r).iterdir():
                if sub.is_dir():
                    cands.setdefault(os.path.normcase(str(sub)), sub.name)
        except OSError:
            continue
    out, seen = [], set()
    for loc, name in cands.items():
        g = ea_game_from_folder(Path(loc), name)
        if g and norm(g["name"]) not in seen:
            seen.add(norm(g["name"]))
            out.append(g)
    return out


# ---------------------------------------------------------------- Steam
def scan_steam(steam_dir: Path | None = None) -> list[dict]:
    if steam_dir is None:
        p = _reg("HKEY_CURRENT_USER", r"Software\Valve\Steam", "SteamPath") or \
            _reg("HKEY_LOCAL_MACHINE", r"SOFTWARE\Valve\Steam", "InstallPath")
        if not p:
            return []
        steam_dir = Path(p)
    libs = [Path(steam_dir)]
    try:
        vdf = (Path(steam_dir) / "steamapps" / "libraryfolders.vdf").read_text(encoding="utf-8", errors="replace")
        libs += [Path(m.replace("\\\\", "\\")) for m in re.findall(r'"path"\s+"([^"]+)"', vdf)]
    except OSError:
        pass
    out, seen = [], set()
    for lib in libs:
        try:
            files = list((lib / "steamapps").glob("appmanifest_*.acf"))
        except OSError:
            continue
        for f in files:
            try:
                t = f.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            appid = re.search(r'"appid"\s+"(\d+)"', t)
            name = re.search(r'"name"\s+"([^"]+)"', t)
            if not appid or not name or SKIP_STEAM.search(name.group(1)) or appid.group(1) in seen:
                continue
            seen.add(appid.group(1))
            out.append({"name": name.group(1), "platform": "Steam", "target": f"steam://rungameid/{appid.group(1)}"})
    return out


# ---------------------------------------------------------------- atalhos
def scan_shortcuts(folders: list[Path] | None = None) -> list[dict]:
    if folders is None:
        folders = []
        if IS_WINDOWS:
            home = Path(os.environ.get("USERPROFILE", str(Path.home())))
            appdata = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
            progdata = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
            public = Path(os.environ.get("PUBLIC", r"C:\Users\Public"))
            folders = [home / "Desktop", home / "OneDrive" / "Desktop", home / "OneDrive" / "Área de Trabalho",
                       public / "Desktop", appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs",
                       progdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"]
    out, seen = [], set()
    for d in folders:
        try:
            walk = Path(d).rglob("*") if "start menu" in str(d).lower() else Path(d).glob("*")
            files = [p for p in walk if p.suffix.lower() in (".lnk", ".url")]
        except OSError:
            continue
        for f in files:
            name = f.stem
            if SKIP_SHORTCUT.search(name) or norm(name) in seen or name.lower().startswith("phonedeck"):
                continue
            seen.add(norm(name))
            out.append({"name": name, "platform": "Atalho", "target": str(f)})
    return out


# ---------------------------------------------------------------- busca
_cache: dict = {"t": 0.0, "items": []}
_lock = threading.Lock()

DEMO = [
    {"name": "Fortnite", "platform": "Epic Games",
     "target": "com.epicgames.launcher://apps/fn%3A4fe75bbc5a674f4f9b356b5c90567da5%3AFortnite?action=launch&silent=true"},
    {"name": "Rocket League®", "platform": "Epic Games",
     "target": "com.epicgames.launcher://apps/9773aa1aa54f4f7b80e44bef04986cea%3A530145df28a24424923f5828cc9031a1%3ASugar?action=launch&silent=true"},
    {"name": "Battlefield™ 6", "platform": "EA app", "target": "origin2://game/launch?offerIds=0000000"},
    {"name": "Counter-Strike 2", "platform": "Steam", "target": "steam://rungameid/730"},
    {"name": "Discord", "platform": "Atalho", "target": "Discord.lnk"},
    {"name": "OBS Studio", "platform": "Atalho", "target": "OBS Studio.lnk"},
]


def scan(force: bool = False) -> list[dict]:
    with _lock:
        if not force and time.time() - _cache["t"] < 60 and _cache["items"]:
            return _cache["items"]
        if not IS_WINDOWS:
            items = [dict(g) for g in DEMO]
        else:
            items = []
            for fn in (scan_epic, scan_ea, scan_steam, scan_shortcuts):
                try:
                    items += fn()
                except Exception as e:
                    print(f"[jogos] falha ao procurar ({fn.__name__}): {e}")
        items.sort(key=lambda g: (PLATFORM_ORDER.get(g["platform"], 1), g["platform"], norm(g["name"])))
        _cache.update(t=time.time(), items=items)
        return items


def find(name: str, items: list[dict] | None = None) -> dict | None:
    n = norm(name)
    if not n:
        return None
    items = items if items is not None else scan()
    rank = lambda g: (PLATFORM_ORDER.get(g["platform"], 1), len(norm(g["name"])))  # noqa: E731
    exact = [g for g in items if norm(g["name"]) == n]
    if exact:
        return min(exact, key=rank)
    words = n.split()
    near = [g for g in items if all(w in norm(g["name"]).split() for w in words)]
    return min(near, key=rank) if near else None


# ---------------------------------------------------------------- abrir
def _protocol_command(target: str) -> str | None:
    """Linha de comando que o Windows usaria para um link (ex.: com.epicgames.launcher://)."""
    m = re.match(r"([a-z][a-z0-9+.\-]*):", target, re.I)
    if not m or not IS_WINDOWS:
        return None
    cmd = _reg("HKEY_CLASSES_ROOT", rf"{m.group(1)}\shell\open\command", "")
    if not cmd:
        return None
    cmd = os.path.expandvars(cmd)  # ex.: %ProgramFiles% no registro
    arg = '"' + target.replace('"', "") + '"'
    if "%1" in cmd:
        return cmd.replace('"%1"', arg).replace("%1", arg)
    return f"{cmd} {arg}"


def _epic_launcher_exe() -> str | None:
    for base in (os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                 os.environ.get("ProgramFiles", r"C:\Program Files")):
        for arch in ("Win64", "Win32"):
            p = Path(base, "Epic Games", "Launcher", "Portal", "Binaries", arch, "EpicGamesLauncher.exe")
            if p.exists():
                return str(p)
    return None


def launch(target: str) -> None:
    if not IS_WINDOWS:
        print(f"[demo] abrir jogo: {target}")
        return
    if re.match(r"[a-z][a-z0-9+.\-]*://", target, re.I):
        errors = []
        cmd = _protocol_command(target)
        if cmd:  # chama o launcher direto, igual ao Windows faria ao clicar no atalho
            try:
                subprocess.Popen(cmd, creationflags=DETACHED_PROCESS)
                return
            except OSError as e:
                errors.append(str(e))
        if target.lower().startswith("com.epicgames.launcher://"):
            exe = _epic_launcher_exe()
            if exe:
                subprocess.Popen([exe, target], creationflags=DETACHED_PROCESS)
                return
        try:
            os.startfile(target)
            return
        except OSError as e:
            errors.append(str(e))
            launcher = "Epic Games" if "epicgames" in target.lower() else "EA app" if "origin2" in target.lower() \
                else "Steam" if target.lower().startswith("steam:") else "launcher"
            raise RuntimeError(f"o Windows não abriu o link do {launcher} ({'; '.join(errors)}). "
                               f"O {launcher} está instalado?") from e
    p = Path(target)
    if not p.exists():
        raise FileNotFoundError(f"arquivo não encontrado: {target}")
    if p.suffix.lower() == ".exe":
        subprocess.Popen([str(p)], cwd=str(p.parent), creationflags=DETACHED_PROCESS)
    else:
        os.startfile(str(p))


def launch_action(action: dict) -> str:
    name = str(action.get("name") or "").strip()
    target = str(action.get("target") or "").strip()
    if target:
        try:
            launch(target)
            return f"Abrindo {name or 'jogo'}…"
        except Exception as e:
            print(f"[jogos] link salvo falhou ({e}); procurando '{name}' de novo")
    g = find(name, scan(force=True)) if name else None
    if not g:
        raise RuntimeError(f"Não achei “{name or 'o jogo'}” instalado no PC. Edite o botão e escolha na lista de jogos.")
    launch(g["target"])
    return f"Abrindo {g['name']} ({g['platform']})…"
