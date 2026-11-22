@echo off
title PhoneDeck - remover atalhos
cd /d "%~dp0"
rem Remove o icone da area de trabalho e o inicio automatico com o Windows.
if not exist ".venv\Scripts\python.exe" goto fim
".venv\Scripts\python.exe" servidor\main.py --remover-atalhos
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Method Post http://127.0.0.1:8765/desligar | Out-Null } catch {}"
:fim
echo Pronto. Para voltar a usar, rode o iniciar.bat.
pause
