@echo off
REM ================================================
REM Nuke 15.1 Launcher
REM Version: 1.0
REM Edit: 2025-11-06 Pablo
REM ================================================

ECHO [PIPELINE] Lancement de Nuke 15.1...

REM Licence Foundry
SET foundry_LICENSE=4101@rlm-illogic

ECHO.
ECHO Lancement de Nuke...
ECHO ==========================================
ECHO.

REM === LANCEMENT ===
"C:/Program Files/Nuke15.1v5/Nuke15.1.exe"
REM DEBUG
REM START "Nuke 15.1 Console" /WAIT cmd /K "C:/Program Files/Nuke15.1v5/Nuke15.1.exe" %* ^& EXIT

REM === FIN ===
IF ERRORLEVEL 1 (
    ECHO.
    ECHO [ERREUR] Nuke s'est ferme avec une erreur
    PAUSE
)