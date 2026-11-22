@echo off
title PhoneDeck (console)
cd /d "%~dp0"
rem Abre o PhoneDeck numa janela visivel, mostrando tudo o que acontece (bom para achar erros).
if not exist ".venv\Scripts\python.exe" (
  echo Rode o iniciar.bat primeiro.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" servidor\main.py
pause
