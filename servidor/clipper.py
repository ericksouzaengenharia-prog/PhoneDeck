"""
"Replay buffer": grava a tela continuamente em pedacinhos de 2 segundos
(numa pasta temporária, sobrescrevendo os antigos) e, quando você aperta o
botão, junta os últimos N segundos num arquivo .mp4 — com o som do PC e
o microfone (gravados em paralelo pelo audiocap.py).

Captura (Windows):
  - ddagrab : Desktop Duplication API, captura pela GPU — leve e funciona com jogos
  - gdigrab : método antigo, compatível com qualquer ffmpeg
Codificador: tenta NVIDIA (nvenc) -> AMD (amf) -> Intel (qsv) -> CPU (x264).

Modo "hotkey": em vez de gravar, só aperta um atalho (ex.: Alt+F10 do
NVIDIA Instant Replay, ou o atalho "Salvar replay" do OBS).
"""
from __future__ import annotations

import datetime as dt
import glob
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import audiocap
from config import base_dir

IS_WINDOWS = sys.platform == "win32"
CREATE_NO_WINDOW = 0x08000000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
SEG = 2  # segundos por pedaço


def find_ffmpeg(custom: str = "") -> str | None:
    cands = []
    if custom:
        cands.append(custom)
    w = shutil.which("ffmpeg")
    if w:
        cands.append(w)
    b = base_dir()
    cands += [str(b / "ffmpeg" / "bin" / "ffmpeg.exe"), str(b / "ffmpeg" / "ffmpeg.exe"), str(b / "ffmpeg.exe")]
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands.append(os.path.join(la, "Microsoft", "WinGet", "Links", "ffmpeg.exe"))
        cands += glob.glob(os.path.join(la, "Microsoft", "WinGet", "Packages", "*FFmpeg*", "**", "bin", "ffmpeg.exe"),
                           recursive=True)
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None


def videos_dir() -> Path:
    """Pasta 'Vídeos' do usuário (respeita OneDrive/pasta movida)."""
    if IS_WINDOWS:
        try:
            import ctypes
            from ctypes import wintypes

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD),
                            ("Data4", ctypes.c_ubyte * 8)]

            fid = GUID(0x18989B1D, 0x99B5, 0x455B, (ctypes.c_ubyte * 8)(0x84, 0x1C, 0xAB, 0x7C, 0x74, 0xE4, 0xDD, 0xFC))
            p = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(fid), 0, None, ctypes.byref(p)) == 0:
                path = Path(p.value)
                ctypes.windll.ole32.CoTaskMemFree(p)
                return path
        except Exception:
            pass
    return Path.home() / "Videos"


def _run(cmd, timeout=20) -> subprocess.CompletedProcess:
    kw = {"creationflags": CREATE_NO_WINDOW} if IS_WINDOWS else {}
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, **kw)


class _KillWithParent:
    """No Windows, garante que o ffmpeg morra junto se o PhoneDeck for fechado à força."""

    def __init__(self):
        self.job = None
        if not IS_WINDOWS:
            return
        try:
            import ctypes
            from ctypes import wintypes
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [(n, ctypes.c_ulonglong) for n in
                            ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                             "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

            class BASIC(ctypes.Structure):
                _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
                            ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                            ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                            ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                            ("SchedulingClass", wintypes.DWORD)]

            class EXTENDED(ctypes.Structure):
                _fields_ = [("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                            ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                            ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

            k32.CreateJobObjectW.restype = wintypes.HANDLE
            job = k32.CreateJobObjectW(None, None)
            info = EXTENDED()
            info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
            if k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
                self.job, self.k32 = job, k32
                k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        except Exception:
            self.job = None

    def add(self, proc: subprocess.Popen) -> None:
        if self.job:
            try:
                self.k32.AssignProcessToJobObject(self.job, int(proc._handle))
            except Exception:
                pass


_JOB = _KillWithParent()


def media_duration(ffmpeg: str, path: Path) -> float | None:
    """Duração de um arquivo de vídeo lendo a saída do próprio ffmpeg."""
    try:
        r = _run([ffmpeg, "-hide_banner", "-i", str(path)], timeout=15)
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr.decode("utf-8", "replace"))
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return None


class Clipper:
    def __init__(self, settings: dict):
        self.cfg = settings.get("clip", {})
        self.mode = self.cfg.get("mode", "ffmpeg")
        self.ffmpeg = find_ffmpeg(settings.get("ffmpeg_path", ""))
        self.buf_dir = Path(tempfile.gettempdir()) / "phonedeck_buffer"
        self.buffer_seconds = max(10, min(300, int(self.cfg.get("buffer_seconds", 30))))
        self.status = "off"
        self.error = ""
        self.encoder = None
        self.capture = None
        self.active = False
        self.proc: subprocess.Popen | None = None
        self._gen = 0
        self._detected = False
        self._download = False
        self._lock = threading.Lock()
        self.taps: dict[str, audiocap.AudioTap] = {}
        if self.mode == "ffmpeg" and audiocap.available():
            if self.cfg.get("system_audio", True):
                self.taps["system"] = audiocap.AudioTap("system", self.buffer_seconds)
            if self.cfg.get("microphone", True):
                self.taps["mic"] = audiocap.AudioTap("mic", self.buffer_seconds)

    # ------------------------------------------------------------------ info
    def output_dir(self) -> Path:
        d = self.cfg.get("output_dir") or str(videos_dir() / "PhoneDeck")
        p = Path(os.path.expandvars(d))
        p.mkdir(parents=True, exist_ok=True)
        return p

    def info(self) -> dict:
        audio = {k: {"ok": t.ok, "device": t.device, "error": t.error} for k, t in self.taps.items()}
        return {"mode": self.mode, "status": self.status, "error": self.error, "active": self.active,
                "encoder": self.encoder, "capture": self.capture, "buffer": self.buffer_seconds, "audio": audio}

    # ------------------------------------------------------------- start/stop
    def start(self) -> None:
        """Liga a gravação em segundo plano (pode ser chamado várias vezes)."""
        if self.mode != "ffmpeg":
            self.status = "ready" if self.mode == "hotkey" else "off"
            return
        with self._lock:
            if self.active:
                return
            if not self.ffmpeg:
                self.status, self.error = "error", "ffmpeg não encontrado (veja o LEIA-ME)"
                return
            self.active = True
            self._gen += 1
            self.status = "starting"
            for t in self.taps.values():
                t.start()
            threading.Thread(target=self._supervise, args=(self._gen,), name="clipper", daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            if not self.active:
                return
            self.active = False
            self._gen += 1
            for t in self.taps.values():
                t.stop()
            self._kill()
            if self.mode == "ffmpeg":
                self.status, self.error = "paused", ""

    def _alive(self, gen: int) -> bool:
        return self.active and gen == self._gen

    def _kill(self) -> None:
        p = self.proc
        self.proc = None
        if p and p.poll() is None:
            try:
                p.stdin.write(b"q")
                p.stdin.flush()
                p.wait(3)
            except Exception:
                pass
            if p.poll() is None:
                p.kill()

    # ------------------------------------------------------------- detecção
    def _test(self, args: list[str], timeout=15) -> bool:
        try:
            r = _run([self.ffmpeg, "-hide_banner", "-loglevel", "error", *args, "-f", "null", "-"], timeout)
            return r.returncode == 0
        except Exception:
            return False

    def _detect(self) -> None:
        want_cap = self.cfg.get("capture", "auto")
        mon = int(self.cfg.get("monitor", 0))
        if want_cap == "test":
            self.capture = "test"
        elif want_cap in ("ddagrab", "gdigrab"):
            self.capture = want_cap
        elif IS_WINDOWS and self._test(["-f", "lavfi", "-i", f"ddagrab=output_idx={mon}:framerate=5,hwdownload,format=bgra",
                                        "-frames:v", "1"]):
            self.capture = "ddagrab"
        else:
            self.capture = "gdigrab" if IS_WINDOWS else "test"

        want_enc = self.cfg.get("encoder", "auto")
        if want_enc != "auto":
            self.encoder = want_enc
        else:
            self.encoder = "libx264"
            for enc in ("h264_nvenc", "h264_amf", "h264_qsv"):
                if self._test(["-f", "lavfi", "-i", "color=black:s=640x360:r=30", "-frames:v", "5", "-c:v", enc]):
                    self.encoder = enc
                    break
        self._detected = True

    def _build_cmd(self) -> list[str]:
        fps = int(self.cfg.get("fps", 30))
        mon = int(self.cfg.get("monitor", 0))
        br = str(self.cfg.get("bitrate", "8M"))
        enc = self.encoder
        pix = "nv12" if enc in ("h264_amf", "h264_qsv") else "yuv420p"
        cmd = [self.ffmpeg, "-hide_banner", "-loglevel", "warning", "-y"]
        vf = None
        if self.capture == "ddagrab":
            src = f"ddagrab=output_idx={mon}:framerate={fps}:draw_mouse=1"
            if enc != "h264_nvenc" or self._download:  # nvenc lê direto da GPU; os outros precisam baixar o quadro
                src += f",hwdownload,format=bgra,format={pix}"
            cmd += ["-f", "lavfi", "-i", src]
        elif self.capture == "gdigrab":
            cmd += ["-f", "gdigrab", "-framerate", str(fps), "-draw_mouse", "1", "-i", "desktop"]
            vf = f"crop=trunc(iw/2)*2:trunc(ih/2)*2,format={pix}"
        else:  # "test": imagem sintética (usado para testar fora do Windows)
            cmd += ["-re", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate={fps}"]
            vf = f"format={pix}"
        if vf:
            cmd += ["-vf", vf]
        if enc == "h264_nvenc":
            cmd += ["-c:v", enc, "-preset", "p2", "-b:v", br]
        elif enc == "h264_amf":
            cmd += ["-c:v", enc, "-quality", "speed", "-b:v", br]
        elif enc == "h264_qsv":
            cmd += ["-c:v", enc, "-preset", "veryfast", "-b:v", br]
        else:
            cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "25"]
        cmd += ["-g", str(fps), "-an"]  # 1 quadro-chave por segundo -> cortes precisos; áudio vem do audiocap
        wrap = math.ceil(self.buffer_seconds / SEG) + 4
        cmd += ["-f", "segment", "-segment_time", str(SEG), "-segment_wrap", str(wrap),
                "-segment_format", "mpegts", str(self.buf_dir / "buf_%03d.ts")]
        return cmd

    # ------------------------------------------------------------ supervisor
    def _clean_buffer(self) -> None:
        self.buf_dir.mkdir(parents=True, exist_ok=True)
        for f in self.buf_dir.glob("*.ts"):
            try:
                f.unlink()
            except OSError:
                pass

    def _newest_age(self) -> float | None:
        try:
            files = list(self.buf_dir.glob("buf_*.ts"))
            if not files:
                return None
            return time.time() - max(f.stat().st_mtime for f in files)
        except OSError:
            return None

    def _fallback(self) -> bool:
        auto_cap = self.cfg.get("capture", "auto") == "auto"
        auto_enc = self.cfg.get("encoder", "auto") == "auto"
        if self.capture == "ddagrab" and self.encoder == "h264_nvenc" and not self._download:
            self._download = True
            return True
        if self.capture == "ddagrab" and auto_cap:
            self.capture = "gdigrab"
            return True
        if self.encoder != "libx264" and auto_enc:
            self.encoder = "libx264"
            return True
        return False

    def _supervise(self, gen: int) -> None:
        if not self._detected:
            try:
                self._detect()
            except Exception as e:
                self.status, self.error = "error", f"falha ao testar o ffmpeg: {e}"
                return
            print(f"[clipe] captura: {self.capture} | codificador: {self.encoder} | buffer: {self.buffer_seconds}s")
        backoff, quick_fails = 2, 0
        while self._alive(gen):
            self._clean_buffer()
            log_path = self.buf_dir / "ffmpeg_log.txt"
            log = open(log_path, "ab")
            kw = {"creationflags": CREATE_NO_WINDOW | BELOW_NORMAL_PRIORITY_CLASS} if IS_WINDOWS else {}
            try:
                proc = subprocess.Popen(self._build_cmd(), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                        stderr=log, **kw)
            except Exception as e:
                log.close()
                self.status, self.error = "error", f"não consegui iniciar o ffmpeg: {e}"
                return
            _JOB.add(proc)
            self.proc = proc
            started = time.time()
            self.status, self.error = "starting", ""
            while self._alive(gen) and proc.poll() is None:
                time.sleep(1)
                age = self._newest_age()
                if age is not None and age < SEG * 4:
                    if self.status != "running":
                        self.status, backoff = "running", 2
                elif time.time() - started > 20:
                    self.error = "captura parada, reiniciando…"  # ex.: tela de bloqueio/UAC
                    if proc.poll() is None:
                        proc.kill()
                    break
            log.close()
            if not self._alive(gen):
                if proc.poll() is None:
                    proc.kill()
                break
            if self.status != "running" and time.time() - started < 15:
                quick_fails += 1
                if quick_fails >= 2 and self._fallback():
                    quick_fails, backoff = 0, 2
                    print(f"[clipe] trocando para captura: {self.capture} | codificador: {self.encoder}")
                    continue
            else:
                quick_fails = 0
            self.status = "error"
            if not self.error:
                self.error = f"ffmpeg fechou (veja {log_path})"
            time.sleep(backoff)
            backoff = min(30, backoff * 2)

    # ------------------------------------------------------------------ salvar
    def save(self, seconds: int) -> Path:
        if self.mode != "ffmpeg":
            raise RuntimeError("gravação interna desligada (modo do clipe não é 'ffmpeg')")
        if self.status != "running":
            raise RuntimeError(self.error or "a gravação ainda está iniciando, tente em alguns segundos")
        t_save = time.time()
        seconds = max(3, min(int(seconds), self.buffer_seconds))
        files = sorted(self.buf_dir.glob("buf_*.ts"), key=lambda p: p.stat().st_mtime)
        chosen = files[-(math.ceil(seconds / SEG) + 2):]
        if not chosen:
            raise RuntimeError("buffer vazio")
        stamp = int(t_save * 1000)
        tmp_ts = self.buf_dir / f"juntar_{stamp}.ts"
        tmp_mp4 = self.buf_dir / f"video_{stamp}.mp4"
        tmp_wav = self.buf_dir / f"audio_{stamp}.wav"
        with open(tmp_ts, "wb") as out:
            for f in chosen:
                try:
                    with open(f, "rb") as src:
                        shutil.copyfileobj(src, out)
                except OSError:
                    pass
        out_path = self.output_dir() / f"Clipe_{dt.datetime.now():%Y-%m-%d_%H-%M-%S}.mp4"
        try:
            # 1) corta os últimos N segundos do vídeo (sem recodificar)
            r = _run([self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-sseof", f"-{seconds + 0.5}",
                      "-i", str(tmp_ts), "-c", "copy", "-avoid_negative_ts", "make_zero", str(tmp_mp4)], timeout=60)
            if r.returncode != 0 or not tmp_mp4.exists() or tmp_mp4.stat().st_size < 2000:
                _run([self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp_ts), "-c", "copy",
                      str(tmp_mp4)], timeout=60)
            if not tmp_mp4.exists():
                raise RuntimeError("não consegui cortar o vídeo")

            # 2) recorta o mesmo trecho de tempo do som do PC + microfone e junta
            with_audio = False
            live = [(t, vol) for t, vol in ((self.taps.get("system"), float(self.cfg.get("system_volume", 1.0))),
                                            (self.taps.get("mic"), float(self.cfg.get("mic_volume", 1.0))))
                    if t is not None and t.ok]
            if live:
                dur = media_duration(self.ffmpeg, tmp_mp4) or float(seconds)
                end = t_save - float(self.cfg.get("video_delay_ms", 150)) / 1000.0
                if audiocap.write_mix(tmp_wav, end - dur, end, live):
                    r = _run([self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp_mp4),
                              "-i", str(tmp_wav), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                              "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                              str(out_path)], timeout=90)
                    with_audio = r.returncode == 0 and out_path.exists()
            if not with_audio:
                _run([self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp_mp4), "-c", "copy",
                      "-movflags", "+faststart", str(out_path)], timeout=60)
        finally:
            for f in (tmp_ts, tmp_mp4, tmp_wav):
                try:
                    f.unlink()
                except OSError:
                    pass
        if not out_path.exists():
            raise RuntimeError("não consegui salvar o clipe")
        return out_path
