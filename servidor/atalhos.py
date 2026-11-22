"""
Atalhos do Windows e avisos:
  - ícone "PhoneDeck" na área de trabalho (abre/mostra a página de conexão)
  - item na Inicialização do Windows: o PhoneDeck fica esperando em segundo
    plano e liga sozinho quando o cabo do iPhone é conectado
  - notificação do Windows ("cabo conectado")
"""
from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

from config import base_dir, resource_dir

IS_WINDOWS = sys.platform == "win32"
CREATE_NO_WINDOW = 0x08000000
DESKTOP_NAME = "PhoneDeck.lnk"
STARTUP_NAME = "PhoneDeck (automático).lnk"


def _q(s: str) -> str:
    """String para PowerShell entre aspas simples."""
    return "'" + str(s).replace("'", "''") + "'"


def _powershell(script: str, wait: bool = True, timeout: int = 30):
    enc = base64.b64encode(script.encode("utf-16-le")).decode()
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc]
    if not wait:
        return subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=timeout)


def _launch_target() -> tuple[str, str]:
    """(programa, argumentos-base) que abre o PhoneDeck sem janela preta."""
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    script = Path(__file__).resolve().parent / "main.py"
    return str(pyw if pyw.exists() else exe), f'"{script}"'


def icon_path(for_shortcut: bool = False) -> str:
    if for_shortcut and getattr(sys, "frozen", False):
        return f"{sys.executable},0"  # o .exe já leva o ícone dentro
    return str(resource_dir() / "web" / "icon.ico")


def install() -> str:
    if not IS_WINDOWS:
        return "atalhos só existem no Windows"
    target, base_args = _launch_target()
    work = str(base_dir())
    script = f"""
$ErrorActionPreference = 'Stop'
$sh = New-Object -ComObject WScript.Shell
function Make($path, $arguments, $style, $desc) {{
  $l = $sh.CreateShortcut($path)
  $l.TargetPath = {_q(target)}
  $l.Arguments = $arguments
  $l.WorkingDirectory = {_q(work)}
  $l.IconLocation = {_q(icon_path(True))}
  $l.WindowStyle = $style
  $l.Description = $desc
  $l.Save()
}}
$desk = [Environment]::GetFolderPath('Desktop')
$start = [Environment]::GetFolderPath('Startup')
Make (Join-Path $desk {_q(DESKTOP_NAME)}) {_q((base_args + ' --abrir').strip())} 1 'PhoneDeck - celular como Stream Deck'
Make (Join-Path $start {_q(STARTUP_NAME)}) {_q((base_args + ' --auto').strip())} 7 'PhoneDeck - liga ao conectar o cabo do iPhone'
Write-Output $desk
"""
    r = _powershell(script)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "erro desconhecido").strip()[:300])
    return (r.stdout or "").strip()


def remove() -> None:
    if not IS_WINDOWS:
        return
    script = f"""
$desk = [Environment]::GetFolderPath('Desktop'); $start = [Environment]::GetFolderPath('Startup')
Remove-Item -LiteralPath (Join-Path $desk {_q(DESKTOP_NAME)}) -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $start {_q(STARTUP_NAME)}) -ErrorAction SilentlyContinue
"""
    _powershell(script)


def status() -> dict:
    if not IS_WINDOWS:
        return {"desktop": False, "startup": False}
    try:
        r = _powershell("[Environment]::GetFolderPath('Desktop'); [Environment]::GetFolderPath('Startup')", timeout=15)
        desk, start = (r.stdout or "").strip().splitlines()[:2]
        return {"desktop": (Path(desk) / DESKTOP_NAME).exists(), "startup": (Path(start) / STARTUP_NAME).exists()}
    except Exception:
        return {"desktop": False, "startup": False}


def notify(title: str, message: str) -> None:
    """Notificação do Windows (balão na área de notificação). Não bloqueia."""
    if not IS_WINDOWS:
        print(f"[aviso] {title}: {message}")
        return
    ico = icon_path()
    script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$n = New-Object System.Windows.Forms.NotifyIcon
try {{ $n.Icon = New-Object System.Drawing.Icon({_q(ico)}) }} catch {{ $n.Icon = [System.Drawing.SystemIcons]::Information }}
$n.Text = 'PhoneDeck'
$n.Visible = $true
$n.ShowBalloonTip(6000, {_q(title)}, {_q(message)}, [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 7
$n.Dispose()
"""
    try:
        _powershell(script, wait=False)
    except Exception:
        pass
