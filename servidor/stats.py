"""
Leitura de uso de CPU, RAM e GPU.

GPU:
  1) NVIDIA  -> NVML (biblioteca oficial, vem com o driver): uso %, temperatura, VRAM
  2) AMD/Intel/qualquer outra -> contador de desempenho do Windows "GPU Engine"
     (o mesmo que o Gerenciador de Tarefas usa): uso %
"""
from __future__ import annotations

import sys
import threading
import time

import psutil

IS_WINDOWS = sys.platform == "win32"


class _Nvml:
    def __init__(self):
        import pynvml  # pacote nvidia-ml-py
        self.n = pynvml
        pynvml.nvmlInit()
        self.h = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(self.h)
        self.name = name.decode() if isinstance(name, bytes) else str(name)

    def read(self) -> dict:
        n, h = self.n, self.h
        out = {"name": self.name}
        try:
            out["util"] = int(n.nvmlDeviceGetUtilizationRates(h).gpu)
        except Exception:
            pass
        try:
            out["temp"] = int(n.nvmlDeviceGetTemperature(h, 0))  # 0 = NVML_TEMPERATURE_GPU
        except Exception:
            pass
        try:
            m = n.nvmlDeviceGetMemoryInfo(h)
            out["mem_used"] = round(m.used / 2**30, 1)
            out["mem_total"] = round(m.total / 2**30, 1)
        except Exception:
            pass
        return out


class _Pdh:
    """Contador do Windows com nome em inglês (funciona em Windows em português)."""

    PATH = r"\GPU Engine(*)\Utilization Percentage"

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.ct = ctypes
        self.pdh = ctypes.WinDLL("pdh")

        class _U(ctypes.Union):
            _fields_ = [("longValue", ctypes.c_long), ("doubleValue", ctypes.c_double),
                        ("largeValue", ctypes.c_longlong), ("AnsiStringValue", ctypes.c_char_p),
                        ("WideStringValue", ctypes.c_wchar_p)]

        class FMT_VALUE(ctypes.Structure):
            _anonymous_ = ("u",)
            _fields_ = [("CStatus", wintypes.DWORD), ("u", _U)]

        class FMT_ITEM(ctypes.Structure):
            _fields_ = [("szName", ctypes.c_wchar_p), ("FmtValue", FMT_VALUE)]

        self.FMT_ITEM = FMT_ITEM
        self.query = ctypes.c_void_p()
        self.counter = ctypes.c_void_p()
        if self.pdh.PdhOpenQueryW(None, None, ctypes.byref(self.query)) != 0:
            raise OSError("PdhOpenQuery falhou")
        if self.pdh.PdhAddEnglishCounterW(self.query, ctypes.c_wchar_p(self.PATH), None,
                                          ctypes.byref(self.counter)) != 0:
            raise OSError("contador de GPU indisponível")
        self.pdh.PdhCollectQueryData(self.query)
        self.name = "GPU"

    def read(self) -> dict:
        ct = self.ct
        PDH_FMT_DOUBLE = 0x00000200
        PDH_FMT_NOCAP100 = 0x00008000
        if self.pdh.PdhCollectQueryData(self.query) != 0:
            return {"name": self.name}
        size = ct.c_ulong(0)
        count = ct.c_ulong(0)
        flags = PDH_FMT_DOUBLE | PDH_FMT_NOCAP100
        self.pdh.PdhGetFormattedCounterArrayW(self.counter, flags, ct.byref(size), ct.byref(count), None)
        if size.value == 0:
            return {"name": self.name, "util": 0}
        buf = (ct.c_byte * size.value)()
        r = self.pdh.PdhGetFormattedCounterArrayW(self.counter, flags, ct.byref(size), ct.byref(count), buf)
        if r != 0:
            return {"name": self.name}
        items = ct.cast(buf, ct.POINTER(self.FMT_ITEM))
        total = 0.0
        for i in range(count.value):
            it = items[i]
            # soma só os motores "3D" (o que o Gerenciador de Tarefas mostra como uso da GPU)
            if it.FmtValue.CStatus in (0, 1) and (it.szName or "").lower().endswith("engtype_3d"):
                total += it.FmtValue.doubleValue
        return {"name": self.name, "util": int(min(100, round(total)))}


class Stats:
    def __init__(self):
        self.gpu = None
        self.gpu_source = "nenhuma"
        try:
            self.gpu = _Nvml()
            self.gpu_source = f"NVIDIA ({self.gpu.name})"
        except Exception:
            if IS_WINDOWS:
                try:
                    self.gpu = _Pdh()
                    self.gpu_source = "contador do Windows (uso %)"
                except Exception:
                    self.gpu = None
        self._lock = threading.Lock()
        psutil.cpu_percent(interval=None)  # primeira leitura "zera" o contador
        self._demo_t = time.time()

    def read(self) -> dict:
        with self._lock:
            return self._read()

    def _read(self) -> dict:
        vm = psutil.virtual_memory()
        out = {
            "cpu": round(psutil.cpu_percent(interval=None)),
            "ram": round(vm.percent),
            "ram_used": round(vm.used / 2**30, 1),
            "ram_total": round(vm.total / 2**30, 1),
            "gpu": None,
        }
        if self.gpu is not None:
            try:
                out["gpu"] = self.gpu.read()
            except Exception:
                out["gpu"] = None
        elif not IS_WINDOWS:
            # modo demonstração: valores fictícios para visualizar a interface
            import math
            t = time.time() - self._demo_t
            out["gpu"] = {"name": "GPU demo", "util": int(45 + 35 * math.sin(t / 3)),
                          "temp": int(60 + 8 * math.sin(t / 7)), "mem_used": 5.2, "mem_total": 12.0}
        return out
