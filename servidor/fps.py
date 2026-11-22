"""
Medidor de FPS usando o PresentMon (ferramenta oficial e gratuita da Intel, código aberto).

O PresentMon escuta o Windows (ETW) e informa o tempo de cada quadro que cada
programa desenha. Aqui ele roda escondido, com a saída CSV lida linha a linha,
e o PhoneDeck calcula:
  - FPS do jogo que está em primeiro plano (último segundo)
  - tempo de quadro (ms)
  - 1% low (FPS dos 1% piores quadros do último minuto)

Permissão: o Windows só deixa o PresentMon medir se ele rodar como administrador
OU se o seu usuário estiver no grupo "Usuários de log de desempenho"
(Performance Log Users, SID S-1-5-32-559). O PhoneDeck oferece liberar isso uma vez.
"""
from __future__ import annotations

import base64
import collections
import csv
import glob
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from config import base_dir

IS_WINDOWS = sys.platform == "win32"
CREATE_NO_WINDOW = 0x08000000
SESSION = "PhoneDeck"
KEEP_S = 60.0                      # quanto tempo de quadros guardar (para o 1% low)
PM_LATEST_API = "https://api.github.com/repos/GameTechDev/PresentMon/releases/latest"
PM_FALLBACK_URL = "https://github.com/GameTechDev/PresentMon/releases/download/v2.6.0/PresentMon-2.6.0-x64.exe"
PERFLOG_SID = "S-1-5-32-559"

# programas que desenham na tela mas não são jogos (ignorados na escolha automática)
NOT_GAMES = re.compile(r"^(chrome|msedge|firefox|opera|brave|vivaldi|discord|steamwebhelper|epicwebhelper|"
                       r"epicgameslauncher|eadesktop|ea ?app|eabackgroundservice|explorer|spotify|obs64|obs32|dwm|"
                       r"applicationframehost|textinputhost|searchhost|searchapp|shellexperiencehost|"
                       r"startmenuexperiencehost|nvidia overlay|nvcontainer|radeonsoftware|gamebar|xboxgamebar|"
                       r"lockapp|python|pythonw|phonedeck|code|teams|ms-teams|whatsapp|telegram)(\.exe)?$", re.I)


def tools_dir() -> Path:
    return base_dir() / "ferramentas"


def find_presentmon(custom: str = "") -> str | None:
    cands = [custom] if custom else []
    cands += [str(tools_dir() / "PresentMon.exe")]
    cands += sorted(glob.glob(str(tools_dir() / "PresentMon*x64*.exe")), reverse=True)
    w = shutil.which("PresentMon") or shutil.which("PresentMon.exe")
    if w:
        cands.append(w)
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def download_presentmon(progress=print) -> str:
    """Baixa o PresentMon (console, 64 bits) do GitHub oficial da Intel para ferramentas\\PresentMon.exe."""
    tools_dir().mkdir(parents=True, exist_ok=True)
    dest = tools_dir() / "PresentMon.exe"
    url = PM_FALLBACK_URL
    try:
        req = urllib.request.Request(PM_LATEST_API, headers={"User-Agent": "PhoneDeck"})
        with urllib.request.urlopen(req, timeout=20) as r:
            rel = json.loads(r.read().decode("utf-8"))
        for a in rel.get("assets", []):
            if re.fullmatch(r"PresentMon-[\d.]+-x64\.exe", a.get("name", "")):
                url = a["browser_download_url"]
                break
    except Exception:
        pass  # sem acesso à API: usa a versão conhecida
    progress(f"  Baixando PresentMon: {url}")
    tmp = dest.with_suffix(".part")
    req = urllib.request.Request(url, headers={"User-Agent": "PhoneDeck"})
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    if tmp.stat().st_size < 100_000:
        tmp.unlink()
        raise RuntimeError("download incompleto")
    os.replace(tmp, dest)
    return str(dest)


# ---------------------------------------------------------------- permissão
def has_permission() -> bool:
    """Administrador (elevado) ou membro do grupo Usuários de log de desempenho (no token atual)."""
    if not IS_WINDOWS:
        return True
    try:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        sid = ctypes.c_void_p()
        if not ctypes.windll.advapi32.ConvertStringSidToSidW(PERFLOG_SID, ctypes.byref(sid)):
            return False
        member = ctypes.c_int(0)
        ok = ctypes.windll.advapi32.CheckTokenMembership(None, sid, ctypes.byref(member))
        ctypes.windll.kernel32.LocalFree(sid)
        return bool(ok and member.value)
    except Exception:
        return False


def grant_permission() -> bool:
    """Coloca o usuário atual no grupo 'Usuários de log de desempenho'. Mostra o pedido de
    permissão de administrador do Windows (uma vez). Vale depois de sair e entrar na conta."""
    if not IS_WINDOWS:
        return True
    user = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}".strip("\\")
    q = "'" + user.replace("'", "''") + "'"
    inner = f"""
$u = {q}
try {{ Add-LocalGroupMember -SID '{PERFLOG_SID}' -Member $u -ErrorAction Stop }}
catch [Microsoft.PowerShell.Commands.MemberExistsException] {{ }}
catch {{
  $g = (Get-LocalGroup -SID '{PERFLOG_SID}').Name
  net localgroup "$g" $u /add
  if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 2) {{ exit 1 }}
}}
exit 0
"""
    enc = base64.b64encode(inner.encode("utf-16-le")).decode()
    outer = (f"try {{ $p = Start-Process powershell -Verb RunAs -WindowStyle Hidden -Wait -PassThru "
             f"-ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand','{enc}'; exit $p.ExitCode }} "
             f"catch {{ exit 5 }}")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", outer],
                       creationflags=CREATE_NO_WINDOW, capture_output=True, timeout=180)
    return r.returncode == 0


def _foreground() -> tuple[int | None, str]:
    if not IS_WINDOWS:
        return None, ""
    try:
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        hwnd = u.GetForegroundWindow()
        if not hwnd:
            return None, ""
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        buf = ctypes.create_unicode_buffer(256)
        u.GetWindowTextW(hwnd, buf, 256)
        return int(pid.value), buf.value.strip()
    except Exception:
        return None, ""


def _pname(pid: int, cache: dict) -> str:
    if pid not in cache:
        try:
            import psutil
            cache[pid] = psutil.Process(pid).name()
        except Exception:
            cache[pid] = ""
    return cache[pid]


def _pretty(title: str, exe: str) -> str:
    name = title or re.sub(r"(-Win64-Shipping|-Win64|_x64|\.exe)$", "", exe or "", flags=re.I)
    return name[:28] or "Jogo"


class FpsMeter:
    def __init__(self, settings: dict):
        self.cfg = settings.get("fps", {})
        self.exe = find_presentmon(self.cfg.get("presentmon_path", ""))
        self.status = "off"        # off | starting | ok | no_exe | no_permission | error
        self.msg = ""
        self.active = False
        self.downloading = False
        self.frames: dict[int, collections.deque] = {}
        self.names: dict[int, str] = {}
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None
        self._gen = 0
        self.target: int | None = None
        self.target_name = ""
        self._minimal = False      # usa só as opções básicas do PresentMon (versões antigas)

    # -------------------------------------------------------------- controle
    def info(self) -> dict:
        return {"status": self.status, "msg": self.msg, "exe": bool(self.exe), "permission": has_permission()}

    def start(self) -> None:
        if self.active:
            return
        if IS_WINDOWS and not self.exe:
            self.exe = find_presentmon(self.cfg.get("presentmon_path", ""))
            if not self.exe:
                self.status, self.msg = "no_exe", "PresentMon não instalado"
                return
        self.active = True
        self._gen += 1
        self.status, self.msg = "starting", ""
        threading.Thread(target=self._run, args=(self._gen,), name="fps", daemon=True).start()

    def stop(self) -> None:
        if not self.active:
            return
        self.active = False
        self._gen += 1
        p, self.proc = self.proc, None
        if p and p.poll() is None:
            try:
                p.kill()
            except Exception:
                pass
        if self.status in ("ok", "starting"):
            self.status = "off"

    def _alive(self, gen: int) -> bool:
        return self.active and gen == self._gen

    # ---------------------------------------------------------------- leitura
    def _add(self, pid: int, ms: float, now: float) -> None:
        if not (0.05 < ms < 1000):
            return
        with self.lock:
            dq = self.frames.get(pid)
            if dq is None:
                dq = self.frames[pid] = collections.deque()
            dq.append((now, ms))

    def _prune(self, now: float) -> None:
        with self.lock:
            for pid in list(self.frames):
                dq = self.frames[pid]
                while dq and dq[0][0] < now - KEEP_S:
                    dq.popleft()
                if not dq:
                    del self.frames[pid]

    def _run(self, gen: int) -> None:
        if not IS_WINDOWS:
            return self._run_demo(gen)
        from clipper import _JOB
        backoff = 2
        while self._alive(gen):
            args = [self.exe, "--output_stdout", "--no_console_stats", "--session_name", SESSION,
                    "--stop_existing_session"]
            if not self._minimal:
                args += ["--exclude", "dwm.exe", "--no_track_gpu", "--no_track_input"]
            try:
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                                     creationflags=CREATE_NO_WINDOW, text=True, encoding="utf-8", errors="replace",
                                     bufsize=1)
            except OSError as e:
                self.status, self.msg = "error", f"não consegui abrir o PresentMon: {e}"
                return
            _JOB.add(p)
            self.proc = p
            err_lines: collections.deque = collections.deque(maxlen=30)
            threading.Thread(target=lambda: [err_lines.append(l) for l in p.stderr], daemon=True).start()
            started = time.time()
            cols = None
            last_prune = time.monotonic()
            for line in p.stdout:
                if not self._alive(gen):
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    row = next(csv.reader([line]))
                except Exception:
                    continue
                if cols is None:
                    if "ProcessID" in row:
                        idx = {n: i for i, n in enumerate(row)}
                        ft = next((idx[c] for c in ("MsBetweenPresents", "FrameTime", "MsBetweenDisplayChange")
                                   if c in idx), None)
                        if ft is not None:
                            cols = (idx["ProcessID"], ft, idx.get("Application"))
                            self.status, self.msg = "ok", ""
                            backoff = 2
                    continue
                try:
                    pid, ms = int(row[cols[0]]), float(row[cols[1]])
                except (ValueError, IndexError):
                    continue
                if cols[2] is not None and pid not in self.names:
                    app = row[cols[2]] if cols[2] < len(row) else ""
                    if app and not app.startswith("<"):  # "<error>" = nome protegido (anti-cheat)
                        self.names[pid] = app
                now = time.monotonic()
                self._add(pid, ms, now)
                if now - last_prune > 1:
                    self._prune(now)
                    last_prune = now
            if not self._alive(gen):
                break
            try:
                p.wait(3)
            except Exception:
                p.kill()
            err = " ".join(err_lines)
            if "access denied" in err.lower() or "Performance Log Users" in err:
                self.status = "no_permission"
                self.msg = "o Windows bloqueou a medição: libere a permissão (página do PC)"
                self.active = False
                return
            if not self._minimal and time.time() - started < 10 and cols is None:
                self._minimal = True  # talvez uma versão sem alguma opção: tenta só com o básico
                continue
            self.status = "error"
            self.msg = (err.strip()[:160] or "o PresentMon fechou")
            time.sleep(backoff)
            backoff = min(30, backoff * 2)

    def _run_demo(self, gen: int) -> None:
        """Fora do Windows: um "jogo" fictício entre ~70 e ~160 FPS, com quedas de vez em quando."""
        self.status = "ok"
        self.names[4242] = "Jogo demo"
        t0 = time.monotonic()
        while self._alive(gen):
            now = time.monotonic()
            base = 115 + 35 * math.sin((now - t0) / 9)
            if random.random() < 0.004:
                base *= 0.45
            ms = 1000 / max(20, random.gauss(base, 6))
            self._add(4242, ms, now)
            if random.random() < 0.01:
                self._prune(now)
            time.sleep(ms / 1000)

    def read(self) -> dict:
        out = {"status": self.status, "msg": self.msg}
        if self.status != "ok":
            return out
        now = time.monotonic()
        fg_pid, fg_title = _foreground()
        with self.lock:
            recent = {pid: [ms for t, ms in dq if t >= now - 1.0] for pid, dq in self.frames.items()}
        recent = {pid: v for pid, v in recent.items() if len(v) >= 2}
        target = None
        if fg_pid in recent:
            target = fg_pid
        elif self.target in recent:
            target = self.target
        elif recent:
            games = [(len(v), pid) for pid, v in recent.items()
                     if not NOT_GAMES.match(_pname(pid, self.names) or "") and len(v) >= 20]
            if games:
                target = max(games)[1]
        if target is None:
            out["app"] = ""
            return out
        if target != self.target:
            self.target = target
            self.target_name = _pretty(fg_title if target == fg_pid else "", _pname(target, self.names))
        elif target == fg_pid and fg_title:
            self.target_name = _pretty(fg_title, "")
        last = recent[target]
        avg_ms = sum(last) / len(last)
        with self.lock:
            all_ms = sorted((ms for _, ms in self.frames.get(target, ())), reverse=True)
        low1 = None
        if len(all_ms) >= 100:
            worst = all_ms[:max(1, len(all_ms) // 100)]  # 1% piores quadros
            low1 = round(1000 / (sum(worst) / len(worst)))
        out.update({"fps": round(1000 / avg_ms), "ms": round(avg_ms, 1), "low1": low1, "app": self.target_name})
        return out
