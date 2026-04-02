@echo off
setlocal enabledelayedexpansion

echo.
echo  ================================================
echo       EXR Analyzer — Analyse manuelle
echo  ================================================
echo.

:ask
set "SEQ_PATH="
set /p "SEQ_PATH=Sequence EXR (dossier ou fichier) : "
if "!SEQ_PATH!"=="" goto ask

set "SEQ_PATH=!SEQ_PATH:"=!"

set "PYTHON=C:\Program Files\Thinkbox\Deadline10\bin\python3\python.exe"
set "SITE_PKG=R:\pipeline\networkInstall\python_shares\python310_deadline_discord_pkgs\Lib\site-packages"
set "SCRIPT=%~dp0analyze_exr.py"

set "PYTHONPATH=!SITE_PKG!;!PYTHONPATH!"

echo.
echo  Lancement de l'analyse...
echo.

"!PYTHON!" "!SCRIPT!" "!SEQ_PATH!"

echo.
pause
