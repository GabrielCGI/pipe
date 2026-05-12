@echo off
setlocal enabledelayedexpansion

set "PYTHON=C:\Program Files\Thinkbox\Deadline10\bin\python3\python.exe"
set "SITE_PKG=R:\pipeline\networkInstall\python_shares\python310_deadline_discord_pkgs\Lib\site-packages"
set "SCRIPT=%~dp0analyze_exr.py"
set "REPORTS=R:\pipeline\pipe\deadline\exr_analyzer\reports"

set "PYTHONPATH=!SITE_PKG!;!PYTHONPATH!"

:main_loop
echo.
echo  ================================================
echo       EXR Analyzer  --  Analyse manuelle
echo  ================================================
echo.

:ask
set "SEQ_PATH="
set /p "SEQ_PATH=  Sequence EXR (dossier ou fichier) : "
if "!SEQ_PATH!"=="" goto ask
set "SEQ_PATH=!SEQ_PATH:"=!"

echo.
set "META_ONLY_INPUT="
set /p "META_ONLY_INPUT=  Metadonnees uniquement, sans analyse pixels ? [O/N, defaut N] : "

set "EXTRA_ARGS="
if /i "!META_ONLY_INPUT!"=="O" set "EXTRA_ARGS=--metadata-only"
if /i "!META_ONLY_INPUT!"=="Y" set "EXTRA_ARGS=--metadata-only"

echo.
echo  Lancement de l'analyse...
echo.

"!PYTHON!" "!SCRIPT!" "!SEQ_PATH!" --reports-dir "!REPORTS!" !EXTRA_ARGS!

echo.
echo  ================================================
echo.
set "AGAIN="
set /p "AGAIN=  Analyser une autre sequence ? [O/N] : "
if /i "!AGAIN!"=="O" goto main_loop
if /i "!AGAIN!"=="Y" goto main_loop

echo.
echo  Fermeture.
timeout /t 1 /nobreak >nul
