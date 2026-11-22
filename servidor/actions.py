"""
Executa a ação de cada botão. Cada função devolve uma mensagem curta
(mostrada no celular) ou lança uma exceção com o motivo do erro.

Tipos de ação:
  media      key = playpause | next | prev | stop | volup | voldown | mute
  mic        alterna o mudo do microfone padrão
  hotkey     keys = "ctrl+shift+m"  (ou sequência: "ctrl+c, alt+tab, ctrl+v")
  desktop    mostra a área de trabalho (Win+D)
  clip       seconds = 15  -> salva os últimos N segundos da tela
  open       target = programa, arquivo, pasta ou link; args = argumentos (opcional)
  run        command = comando do terminal (cmd)
  text       text = texto para digitar
  lock       bloqueia o PC
  open_clips abre a pasta dos clipes
  player     painel de música: sub = playpause | next | prev | shuffle (app = spotify | any)
  game       jogo instalado: name = "Battlefield 6", target = link exato (opcional, escolhido na lista)
  page/stat/none -> tratados no celular (não fazem nada no PC)
"""
from __future__ import annotations

import os
import subprocess
import sys

import audio
import games
import winkeys

IS_WINDOWS = sys.platform == "win32"

MEDIA_KEYS = {
    "playpause": "playpause", "next": "nexttrack", "prev": "prevtrack", "stop": "mediastop",
    "volup": "volumeup", "voldown": "volumedown", "mute": "volumemute",
}


def _open(target: str, args: str = "") -> None:
    target = os.path.expandvars(target.strip())
    if not target:
        raise ValueError("nada para abrir")
    if not IS_WINDOWS:
        print(f"[demo] abrir: {target} {args}")
        return
    if args.strip():
        subprocess.Popen(f'"{target}" {args}', shell=False, creationflags=0x00000008)  # DETACHED_PROCESS
    else:
        os.startfile(target)  # abre programa, arquivo, pasta ou link


def run_action(action: dict, clipper, media=None, sub: str = "") -> str:
    t = action.get("type")

    if t == "player":
        cmd = sub or "playpause"
        if cmd not in ("playpause", "next", "prev", "shuffle"):
            raise ValueError(f"comando de música inválido: {cmd}")
        if media is not None and media.available:
            return media.command(cmd, action.get("app", "spotify"))
        if cmd == "shuffle":
            raise RuntimeError("aleatório precisa do controle de mídia do Windows (rode o iniciar.bat de novo)")
        key = {"playpause": "playpause", "next": "nexttrack", "prev": "prevtrack"}[cmd]
        winkeys.press_combo([winkeys.VK[key]], hold=0.01)
        return ""

    if t == "media":
        key = action.get("key", "playpause")
        if key not in MEDIA_KEYS:
            raise ValueError(f"tecla de mídia inválida: {key}")
        winkeys.press_combo([winkeys.VK[MEDIA_KEYS[key]]], hold=0.01)
        if not IS_WINDOWS:
            audio.demo_media(key)
        return ""

    if t == "mic":
        muted = audio.mic_toggle()
        return "Microfone MUTADO" if muted else "Microfone ligado"

    if t == "hotkey":
        winkeys.send_hotkey(str(action.get("keys", "")))
        return ""

    if t == "desktop":
        winkeys.send_hotkey("win+d")
        return ""

    if t == "clip":
        if clipper.mode == "hotkey":
            winkeys.send_hotkey(str(clipper.cfg.get("hotkey", "alt+f10")))
            return "Atalho de replay enviado"
        path = clipper.save(int(action.get("seconds", 15) or 15))
        return f"Clipe salvo: {path.name}"

    if t == "open":
        _open(str(action.get("target", "")), str(action.get("args", "")))
        return ""

    if t == "game":
        return games.launch_action(action)

    if t == "run":
        cmd = str(action.get("command", "")).strip()
        if not cmd:
            raise ValueError("comando vazio")
        if not IS_WINDOWS:
            print(f"[demo] rodar: {cmd}")
            return ""
        subprocess.Popen(cmd, shell=True, creationflags=0x08000000)  # sem janela preta
        return ""

    if t == "text":
        winkeys.type_text(str(action.get("text", "")))
        return ""

    if t == "lock":
        winkeys.lock_workstation()
        return ""

    if t == "open_clips":
        d = clipper.output_dir()
        _open(str(d))
        return ""

    if t in ("page", "stat", "none", None):
        return ""

    raise ValueError(f"tipo de ação desconhecido: {t}")
