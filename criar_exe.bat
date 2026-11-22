@echo off
title PhoneDeck - gerar .exe
cd /d "%~dp0"

rem Gera um PhoneDeck.exe unico, sem janela (opcional). Rode o iniciar.bat pelo menos uma vez antes.

if exist ".venv\Scripts\python.exe" goto ok
echo Rode o iniciar.bat uma vez antes de gerar o .exe.
pause
exit /b 1
:ok
set "VPY=.venv\Scripts\python.exe"
"%VPY%" -m pip install --disable-pip-version-check -q pyinstaller
if errorlevel 1 goto erro

"%VPY%" -m PyInstaller --noconfirm --clean --onefile --noconsole --name PhoneDeck ^
  --icon web\icon.ico --add-data "web;web" --paths servidor ^
  --collect-submodules pycaw --collect-submodules winrt --collect-all soundcard --hidden-import pynvml ^
  servidor\main.py
if errorlevel 1 goto erro

echo.
echo Pronto! O arquivo esta em: dist\PhoneDeck.exe
echo Ao abrir, ele roda em segundo plano e abre a pagina de conexao.
echo Para criar os atalhos com o .exe:  dist\PhoneDeck.exe --instalar-atalhos
echo Os arquivos settings.json e layout.json serao criados ao lado do .exe.
echo.
pause
exit /b 0

:erro
echo.
echo Nao consegui gerar o .exe. Veja a mensagem acima.
pause
exit /b 1
