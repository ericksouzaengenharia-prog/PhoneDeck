"""
Controle de áudio do Windows (Core Audio) para:
  - mutar/desmutar o microfone padrão (e saber se está mutado)
  - ler volume e mudo dos alto-falantes (para o bloco "Volume")

Usa as interfaces COM expostas pela biblioteca pycaw.
IMPORTANTE: todas as funções daqui devem rodar na mesma thread que chamou
comtypes.CoInitialize() — o main.py cuida disso com uma thread dedicada.
"""
from __future__ import annotations

import sys

IS_WINDOWS = sys.platform == "win32"

E_RENDER, E_CAPTURE = 0, 1
ROLE_CONSOLE, ROLE_MULTIMEDIA, ROLE_COMMUNICATIONS = 0, 1, 2

_available = False
_err = ""
if IS_WINDOWS:
    try:
        import comtypes
        from comtypes import GUID
        from pycaw.pycaw import IAudioEndpointVolume, IMMDeviceEnumerator
        _CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
        _available = True
    except Exception as e:  # pycaw não instalado
        _err = str(e)


def com_init() -> None:
    """Chamar uma vez na thread que vai usar o áudio."""
    if IS_WINDOWS:
        try:
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass


def _endpoint(flow: int, role: int):
    enum = comtypes.CoCreateInstance(_CLSID_MMDeviceEnumerator, IMMDeviceEnumerator,
                                     comtypes.CLSCTX_INPROC_SERVER)
    dev = enum.GetDefaultAudioEndpoint(flow, role)
    iface = dev.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
    return iface.QueryInterface(IAudioEndpointVolume)


# Estado simulado para o modo demonstração (fora do Windows)
_demo = {"mic_muted": False, "vol": 50, "spk_muted": False}


def available() -> bool:
    return _available or not IS_WINDOWS


def mic_toggle() -> bool:
    """Alterna o mudo do microfone. Retorna True se ficou MUTADO."""
    if not IS_WINDOWS:
        _demo["mic_muted"] = not _demo["mic_muted"]
        return _demo["mic_muted"]
    if not _available:
        raise RuntimeError(f"pycaw não disponível ({_err}). Rode o iniciar.bat de novo.")
    # Muta o microfone de "comunicação" e o de "console" (podem ser diferentes)
    vol = _endpoint(E_CAPTURE, ROLE_CONSOLE)
    new_state = not bool(vol.GetMute())
    vol.SetMute(int(new_state), None)
    try:
        vol2 = _endpoint(E_CAPTURE, ROLE_COMMUNICATIONS)
        vol2.SetMute(int(new_state), None)
    except Exception:
        pass
    return new_state


def read_state() -> dict:
    """{'mic_muted': bool|None, 'volume': int|None, 'spk_muted': bool|None}"""
    if not IS_WINDOWS:
        return {"mic_muted": _demo["mic_muted"], "volume": _demo["vol"], "spk_muted": _demo["spk_muted"]}
    out = {"mic_muted": None, "volume": None, "spk_muted": None}
    if not _available:
        return out
    try:
        mic = _endpoint(E_CAPTURE, ROLE_CONSOLE)
        out["mic_muted"] = bool(mic.GetMute())
    except Exception:
        pass  # sem microfone conectado
    try:
        spk = _endpoint(E_RENDER, ROLE_MULTIMEDIA)
        out["volume"] = round(spk.GetMasterVolumeLevelScalar() * 100)
        out["spk_muted"] = bool(spk.GetMute())
    except Exception:
        pass
    return out


def demo_media(key: str) -> None:
    """Simula teclas de volume no modo demonstração."""
    if key == "volup":
        _demo["vol"] = min(100, _demo["vol"] + 2)
    elif key == "voldown":
        _demo["vol"] = max(0, _demo["vol"] - 2)
    elif key == "mute":
        _demo["spk_muted"] = not _demo["spk_muted"]
