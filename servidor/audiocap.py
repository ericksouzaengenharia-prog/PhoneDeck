"""
Captura de áudio para os clipes, sem precisar de "Mixagem estéreo":
  - som do PC  -> WASAPI loopback do alto-falante/fone padrão
  - microfone  -> microfone padrão do Windows

Cada fonte grava continuamente numa "fita" na memória (só os últimos
segundos, nada vai para o disco). Ao salvar um clipe, o pedaço de tempo
certo é recortado das duas fontes, misturado e juntado ao vídeo.

Cada pedaço de áudio guarda o horário em que foi gravado, então a mistura
fica alinhada mesmo quando o PC fica em silêncio.
"""
from __future__ import annotations

import collections
import math
import sys
import threading
import time
import wave

try:
    import numpy as np
except Exception:  # numpy vem junto com o soundcard
    np = None

IS_WINDOWS = sys.platform == "win32"
SR = 48000          # taxa de amostragem usada em tudo
BLOCK = 960         # 20 ms por leitura


def available() -> bool:
    if np is None:
        return False
    if not IS_WINDOWS:
        return True  # modo demonstração: tom sintético
    try:
        import soundcard  # noqa: F401
        return True
    except Exception:
        return False


class AudioTap:
    """Uma fonte de áudio gravando sem parar numa fita circular."""

    def __init__(self, kind: str, keep_seconds: float):
        self.kind = kind                  # "system" ou "mic"
        self.channels = 2 if kind == "system" else 1
        self.keep = keep_seconds + 5
        self.chunks: collections.deque = collections.deque()
        self.lock = threading.Lock()
        self.ok = False
        self.error = ""
        self.device = ""
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._next_start: float | None = None

    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name=f"audio-{self.kind}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.ok = False

    # ------------------------------------------------------------------
    def _push(self, t_end: float, data) -> None:
        n = len(data)
        if n == 0:
            return
        start = t_end - n / SR
        # mantém a linha do tempo contínua (sem estalos); só "reancora" se desviar muito
        if self._next_start is not None and abs(start - self._next_start) < 0.08:
            start = self._next_start
        self._next_start = start + n / SR
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        with self.lock:
            self.chunks.append((start, data.astype(np.float32, copy=False)))
            limit = t_end - self.keep
            while self.chunks and self.chunks[0][0] + len(self.chunks[0][1]) / SR < limit:
                self.chunks.popleft()

    def extract(self, t0: float, t1: float):
        """Áudio entre os horários t0 e t1 (segundos de time.time()), shape (N, canais)."""
        n = max(0, int(round((t1 - t0) * SR)))
        out = np.zeros((n, self.channels), dtype=np.float32)
        with self.lock:
            chunks = list(self.chunks)
        for start, data in chunks:
            i0 = int(round((start - t0) * SR))
            i1 = i0 + len(data)
            if i1 <= 0 or i0 >= n:
                continue
            a0, a1 = max(i0, 0), min(i1, n)
            out[a0:a1, :data.shape[1]] = data[a0 - i0:a1 - i0, :self.channels]
        return out

    # ------------------------------------------------------------------
    def _run(self) -> None:
        if not IS_WINDOWS:
            self._run_demo()
            return
        try:
            import ctypes
            ctypes.windll.ole32.CoInitializeEx(None, 0)  # COM multithread nesta thread
        except Exception:
            pass
        import warnings
        warnings.filterwarnings("ignore", message=".*discontinuity.*")
        try:
            import soundcard as sc
        except Exception as e:
            self.error = f"biblioteca de áudio ausente ({e})"
            return
        while not self._stop.is_set():
            try:
                if self.kind == "system":
                    spk = sc.default_speaker()
                    dev = sc.get_microphone(spk.id, include_loopback=True)
                    dev_id, self.device = spk.id, spk.name
                else:
                    dev = sc.default_microphone()
                    dev_id, self.device = dev.id, dev.name
                with dev.recorder(samplerate=SR, channels=self.channels) as rec:
                    self.ok, self.error = True, ""
                    self._next_start = None
                    last_check = time.monotonic()
                    while not self._stop.is_set():
                        data = rec.record(numframes=BLOCK)
                        self._push(time.time(), data)
                        if time.monotonic() - last_check > 3:
                            last_check = time.monotonic()
                            cur = sc.default_speaker().id if self.kind == "system" else sc.default_microphone().id
                            if cur != dev_id:  # trocou o fone/microfone padrão -> segue o novo
                                break
            except Exception as e:
                self.ok = False
                self.error = str(e)
                self._stop.wait(3)
        self.ok = False

    def _run_demo(self) -> None:
        """Fora do Windows: gera um tom (som do PC) ou um bipe por segundo (microfone)."""
        self.ok, self.device = True, f"demo-{self.kind}"
        phase = 0
        freq = 440.0 if self.kind == "system" else 880.0
        t_next = time.time()
        while not self._stop.is_set():
            t = (np.arange(BLOCK) + phase) / SR
            wave_ = 0.2 * np.sin(2 * math.pi * freq * t)
            if self.kind == "mic":
                wave_ *= ((t % 1.0) < 0.1)
            data = np.repeat(wave_.reshape(-1, 1), self.channels, axis=1).astype(np.float32)
            phase += BLOCK
            t_next += BLOCK / SR
            delay = t_next - time.time()
            if delay > 0:
                time.sleep(delay)
            self._push(time.time(), data)
        self.ok = False


def write_mix(path, t0: float, t1: float, sources: list[tuple[AudioTap, float]]) -> bool:
    """Mistura as fontes no intervalo [t0, t1] e grava um WAV estéreo 16 bits."""
    n = max(1, int(round((t1 - t0) * SR)))
    mix = np.zeros((n, 2), dtype=np.float32)
    used = False
    for tap, vol in sources:
        if tap is None or vol <= 0:
            continue
        a = tap.extract(t0, t1)
        if a.shape[0] != n:
            a = np.resize(a, (n, a.shape[1]))
        if a.shape[1] == 1:
            a = np.repeat(a, 2, axis=1)
        mix += a[:, :2] * float(vol)
        used = True
    if not used:
        return False
    pcm = (np.clip(mix, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return True
