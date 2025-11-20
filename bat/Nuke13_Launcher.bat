@echo off
REM ================================================
REM Nuke 13.1 Launcher
REM Version: 1.0
REM Edit: 2025-11-06 Pablo
REM ================================================

ECHO [PIPELINE] Lancement de Nuke 13.1...

REM OCIO
SET OCIO=
SET OCIO_ACTIVE_DISPLAYS=
SET OCIO_ACTIVE_VIEWS=

ECHO OCIO: %OCIO%

ECHO.
ECHO Lancement de Nuke...
ECHO ==========================================
ECHO.

REM === LANCEMENT ===
"C:/Program Files/Nuke13.1v5/Nuke13.1.exe"
REM DEBUG
REM START "Nuke 13.1 Console" /WAIT cmd /K "C:/Program Files/Nuke13.1v5/Nuke13.1.exe" %* ^& EXIT

REM === FIN ===
IF ERRORLEVEL 1 (
    ECHO.
    ECHO [ERREUR] Nuke s'est ferme avec une erreur
    PAUSE
)