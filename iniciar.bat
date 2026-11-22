@echo off
title PhoneDeck
cd /d "%~dp0"

rem ============================================================
rem  PhoneDeck - inicia o servidor no PC
rem  Na primeira vez cria o ambiente Python e instala tudo.
rem ============================================================

call :findpython
if defined PY goto pyok

echo.
echo  O Python 3 nao foi encontrado neste PC.
where winget >nul 2>nul
if errorlevel 1 goto nopython
echo.
choice /c SN /m " Quer que eu instale o Python automaticamente agora"
if errorlevel 2 goto nopython
echo.
echo  Instalando o Python 3.12 - pode levar alguns minutos.
echo  Se aparecer uma janela pedindo permissao, clique em Sim.
echo.
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
call :findpython
if defined PY goto pyok
echo.
echo  A instalacao terminou, mas o Python ainda nao apareceu.
echo  Feche esta janela e abra o iniciar.bat de novo.
echo.
pause
exit /b 1

:pyok
echo  Python encontrado: %PY%

if exist ".venv\Scripts\python.exe" goto venvok
echo  Preparando o PhoneDeck - so na primeira vez, leva 1 ou 2 minutos...
%PY% -m venv .venv
if errorlevel 1 goto erro
:venvok
set "VPY=.venv\Scripts\python.exe"

rem Instala/atualiza as bibliotecas quando o requirements.txt muda
fc /b requirements.txt .venv\req.ok >nul 2>nul
if not errorlevel 1 goto depsok
echo  Instalando bibliotecas...
"%VPY%" -m pip install --disable-pip-version-check -q --upgrade pip
"%VPY%" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto erro
copy /y requirements.txt .venv\req.ok >nul
:depsok

rem Avisa se o ffmpeg (usado no clipe dos ultimos segundos) nao existe
where ffmpeg >nul 2>nul
if not errorlevel 1 goto ffok
if exist "ffmpeg\bin\ffmpeg.exe" goto ffok
if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe" goto ffok
echo.
echo  [aviso] ffmpeg nao encontrado: o botao de clipe ainda nao vai funcionar.
echo          Para instalar, abra o terminal e rode:  winget install --id Gyan.FFmpeg -e
echo          Depois feche esta janela e abra o iniciar.bat de novo.
echo.
:ffok

rem Medidor de FPS: baixa o PresentMon (Intel) e oferece liberar a medicao no Windows
"%VPY%" servidor\main.py --preparar-fps

rem Cria o icone na area de trabalho e o inicio automatico ao conectar o cabo
"%VPY%" servidor\main.py --instalar-atalhos

rem Desliga uma copia antiga que esteja rodando, liga a atual em segundo plano
rem (sem janela) e abre a pagina de conexao
"%VPY%" servidor\main.py --parar
start "" ".venv\Scripts\pythonw.exe" "%~dp0servidor\main.py" --abrir
echo  Ligando o PhoneDeck...
"%VPY%" servidor\main.py --esperar
if errorlevel 1 goto naoligou
echo.
echo  Pronto! O PhoneDeck esta rodando em segundo plano.
echo  - Icone "PhoneDeck" na area de trabalho: abre a pagina de conexao.
echo  - Ao ligar o PC, ele fica esperando e ativa sozinho quando o cabo do iPhone conecta.
echo  Esta janela fecha sozinha.
timeout /t 6 >nul
exit /b 0

:naoligou
echo.
echo  O PhoneDeck nao respondeu. Abrindo no modo console para mostrar o erro:
echo.
"%VPY%" servidor\main.py
pause
exit /b 1

rem ------------------------------------------------------------
rem  Procura o Python: no PATH e nas pastas padrao de instalacao
rem  (acha mesmo se "Add python.exe to PATH" nao foi marcado)
rem ------------------------------------------------------------
:findpython
set "PY="
where py >nul 2>nul
if errorlevel 1 goto fp2
py -3 -c "import sys; sys.exit(sys.version_info[:2] < (3, 9))" >nul 2>nul
if errorlevel 1 goto fp2
set "PY=py -3"
exit /b 0
:fp2
where python >nul 2>nul
if errorlevel 1 goto fp3
python -c "import sys; sys.exit(sys.version_info[:2] < (3, 9))" >nul 2>nul
if errorlevel 1 goto fp3
set "PY=python"
exit /b 0
:fp3
if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" set PY="%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" -3
if exist "%WINDIR%\py.exe" set PY="%WINDIR%\py.exe" -3
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*") do if exist "%%~D\python.exe" set PY="%%~D\python.exe"
if not defined PY exit /b 0
%PY% -c "import sys; sys.exit(sys.version_info[:2] < (3, 9))" >nul 2>nul
if errorlevel 1 set "PY="
exit /b 0

:nopython
echo.
echo  Instale o Python 3 pelo site https://www.python.org/downloads/
echo  IMPORTANTE: na instalacao marque "Add python.exe to PATH".
echo  Depois feche esta janela e abra o iniciar.bat de novo.
echo.
pause
exit /b 1

:erro
echo.
echo  Algo deu errado na instalacao. Veja a mensagem acima.
echo  Dica: confira a internet e rode o iniciar.bat de novo.
pause
exit /b 1
