"""
Envio de teclas no Windows usando a API nativa SendInput (sem bibliotecas extras).

Exemplos de atalhos aceitos:
    "ctrl+shift+m"      "alt+f10"      "win+d"      "playpause"
    "ctrl+c, alt+tab, ctrl+v"   -> sequência (pequena macro), separada por vírgula
"""
from __future__ import annotations

import sys
import time

IS_WINDOWS = sys.platform == "win32"

# Nome da tecla -> Virtual-Key code
VK = {
    "ctrl": 0x11, "control": 0x11, "shift": 0x10, "alt": 0x12, "menu": 0x12,
    "win": 0x5B, "windows": 0x5B, "cmd": 0x5B, "super": 0x5B,
    "lctrl": 0xA2, "rctrl": 0xA3, "lshift": 0xA0, "rshift": 0xA1, "lalt": 0xA4, "ralt": 0xA5, "altgr": 0xA5,
    "enter": 0x0D, "return": 0x0D, "esc": 0x1B, "escape": 0x1B, "tab": 0x09, "space": 0x20, "espaco": 0x20,
    "backspace": 0x08, "delete": 0x2E, "del": 0x2E, "insert": 0x2D, "ins": 0x2D,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pgup": 0x21, "pagedown": 0x22, "pgdn": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "printscreen": 0x2C, "prtsc": 0x2C, "print": 0x2C, "pause": 0x13, "capslock": 0x14,
    "numlock": 0x90, "scrolllock": 0x91, "apps": 0x5D, "contextmenu": 0x5D,
    # mídia
    "playpause": 0xB3, "play": 0xB3, "nexttrack": 0xB0, "next": 0xB0, "prevtrack": 0xB1, "prev": 0xB1,
    "stop": 0xB2, "mediastop": 0xB2, "volumemute": 0xAD, "mute": 0xAD, "volumedown": 0xAE, "voldown": 0xAE,
    "volumeup": 0xAF, "volup": 0xAF,
    # teclado numérico
    "num*": 0x6A, "multiply": 0x6A, "add": 0x6B, "num-": 0x6D, "subtract": 0x6D,
    "num.": 0x6E, "decimal": 0x6E, "num/": 0x6F, "divide": 0x6F,
    # pontuação (layout US/ABNT2 pode variar)
    ";": 0xBA, "=": 0xBB, ",": 0xBC, "comma": 0xBC, "-": 0xBD, "minus": 0xBD, ".": 0xBE, "period": 0xBE,
    "/": 0xBF, "`": 0xC0, "[": 0xDB, "\\": 0xDC, "]": 0xDD, "'": 0xDE, "plus": 0xBB,
}
for _i in range(1, 25):
    VK[f"f{_i}"] = 0x70 + _i - 1
for _i in range(10):
    VK[str(_i)] = 0x30 + _i
    VK[f"num{_i}"] = 0x60 + _i
for _c in "abcdefghijklmnopqrstuvwxyz":
    VK[_c] = ord(_c.upper())

# Teclas que precisam da flag "extended"
EXTENDED = {
    0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2C, 0x2D, 0x2E, 0x5B, 0x5C, 0x5D,
    0x6F, 0x90, 0xA3, 0xA5, 0xAD, 0xAE, 0xAF, 0xB0, 0xB1, 0xB2, 0xB3,
}


class KeyError_(ValueError):
    pass


def parse_combo(combo: str) -> list[int]:
    combo = combo.strip().lower()
    if not combo:
        raise KeyError_("atalho vazio")
    parts = [p.strip() for p in combo.split("+")]
    # "ctrl++" -> tecla "+"
    if combo.endswith("++"):
        parts = [p for p in parts if p] + ["plus"]
    codes = []
    for p in parts:
        if not p:
            continue
        if p not in VK:
            raise KeyError_(f"tecla desconhecida: '{p}'")
        codes.append(VK[p])
    return codes


def parse_sequence(text: str) -> list[list[int]]:
    """'ctrl+c, alt+tab' -> [[ctrl,c],[alt,tab]]"""
    seq = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        if chunk:
            seq.append(parse_combo(chunk))
    if not seq:
        raise KeyError_("atalho vazio")
    return seq


if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    INPUT_KEYBOARD = 1
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    ULONG_PTR = ctypes.c_size_t

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = (("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR))

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = (("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR))

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = (("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD))

    class _INPUTUNION(ctypes.Union):
        _fields_ = (("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT))

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = (("type", wintypes.DWORD), ("u", _INPUTUNION))

    user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
    user32.SendInput.restype = wintypes.UINT
    user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
    user32.MapVirtualKeyW.restype = wintypes.UINT

    def _key_input(vk: int, up: bool) -> INPUT:
        flags = KEYEVENTF_KEYUP if up else 0
        if vk in EXTENDED:
            flags |= KEYEVENTF_EXTENDEDKEY
        scan = user32.MapVirtualKeyW(vk, 0) & 0xFF
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
        return inp

    def _send(inputs: list) -> None:
        if not inputs:
            return
        arr = (INPUT * len(inputs))(*inputs)
        sent = user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))
        if sent != len(inputs):
            err = ctypes.get_last_error()
            raise OSError(f"SendInput bloqueado (erro {err}). Se a janela ativa roda como administrador, "
                          f"rode o PhoneDeck como administrador também.")

    def press_combo(codes: list[int], hold: float = 0.04) -> None:
        _send([_key_input(c, False) for c in codes])
        time.sleep(hold)  # alguns jogos/apps só reconhecem se a tecla ficar "apertada" um instante
        _send([_key_input(c, True) for c in reversed(codes)])

    def type_text(text: str) -> None:
        data = text.replace("\r\n", "\n").replace("\n", "\r").encode("utf-16-le")
        units = [int.from_bytes(data[i:i + 2], "little") for i in range(0, len(data), 2)]
        inputs = []
        for u in units:
            for up in (False, True):
                inp = INPUT(type=INPUT_KEYBOARD)
                inp.ki = KEYBDINPUT(wVk=0, wScan=u, dwFlags=KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0),
                                    time=0, dwExtraInfo=0)
                inputs.append(inp)
        # envia em blocos para não estourar apps lentos
        for i in range(0, len(inputs), 40):
            _send(inputs[i:i + 40])
            time.sleep(0.005)

    def lock_workstation() -> None:
        user32.LockWorkStation()

    # ---- mouse (touchpad do celular) ----
    INPUT_MOUSE = 0
    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_HWHEEL = 0x1000
    _BTN = {"left": (0x0002, 0x0004), "right": (0x0008, 0x0010), "middle": (0x0020, 0x0040)}

    def _mouse_input(flags: int, dx: int = 0, dy: int = 0, data: int = 0) -> INPUT:
        inp = INPUT(type=INPUT_MOUSE)
        inp.mi = MOUSEINPUT(dx=dx, dy=dy, mouseData=data & 0xFFFFFFFF, dwFlags=flags, time=0, dwExtraInfo=0)
        return inp

    def mouse_move(dx: int, dy: int) -> None:
        """Movimento relativo (como um mouse de verdade: respeita a velocidade do ponteiro do Windows)."""
        if dx or dy:
            _send([_mouse_input(MOUSEEVENTF_MOVE, int(dx), int(dy))])

    def mouse_button(button: str, action: str = "click") -> None:
        down, up = _BTN.get(button, _BTN["left"])
        if action == "down":
            _send([_mouse_input(down)])
        elif action == "up":
            _send([_mouse_input(up)])
        else:
            _send([_mouse_input(down), _mouse_input(up)])

    def mouse_wheel(dy: int = 0, dx: int = 0) -> None:
        """Rolagem: 120 = um "dente" da rodinha. Valores menores dão rolagem suave nos apps que aceitam."""
        inputs = []
        if dy:
            inputs.append(_mouse_input(MOUSEEVENTF_WHEEL, data=int(dy)))
        if dx:
            inputs.append(_mouse_input(MOUSEEVENTF_HWHEEL, data=int(dx)))
        _send(inputs)

    def key_tap(name: str, down: bool | None = None) -> None:
        """Aperta (down=True), solta (down=False) ou toca (None) uma tecla."""
        vk = VK[name]
        if down is None:
            press_combo([vk], hold=0.01)
        else:
            _send([_key_input(vk, not down)])

else:  # fora do Windows: modo demonstração (só registra no console)
    def press_combo(codes: list[int], hold: float = 0.04) -> None:
        print(f"[demo] teclas: {[hex(c) for c in codes]}")

    def type_text(text: str) -> None:
        print(f"[demo] digitar: {text!r}")

    def lock_workstation() -> None:
        print("[demo] bloquear PC")

    DEMO_MOUSE = {"x": 0, "y": 0, "clicks": [], "wheel": 0}  # estado simulado (testes fora do Windows)

    def mouse_move(dx: int, dy: int) -> None:
        DEMO_MOUSE["x"] += int(dx)
        DEMO_MOUSE["y"] += int(dy)

    def mouse_button(button: str, action: str = "click") -> None:
        DEMO_MOUSE["clicks"].append(f"{button}:{action}")
        print(f"[demo] mouse {button} {action}")

    def mouse_wheel(dy: int = 0, dx: int = 0) -> None:
        DEMO_MOUSE["wheel"] += int(dy)

    def key_tap(name: str, down: bool | None = None) -> None:
        VK[name]
        print(f"[demo] tecla {name} {'' if down is None else ('apertada' if down else 'solta')}")


def send_hotkey(text: str) -> None:
    seq = parse_sequence(text)
    for i, codes in enumerate(seq):
        if i:
            time.sleep(0.08)
        press_combo(codes)
