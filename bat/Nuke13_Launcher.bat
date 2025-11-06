@echo off
REM ================================================
REM Nuke 13.1 Launcher
REM Version: 1.0
REM Edit: 2025-11-06 Pablo
REM ================================================

ECHO [PIPELINE] Lancement de Nuke 13.1...

REM Licence Foundry
SET foundry_LICENSE=4201@rlm-illogic

REM OCIO
SET OCIO=R:\pipeline\networkInstall\OpenColorIO-Configs\cg-config-v1.0.0_aces-v1.3_ocio-v2.0.ocio

REM === LANCEMENT ===
"C:\Program Files\Nuke13.1v5\Nuke13.1.exe" %*
REM === FIN ===
IF ERRORLEVEL 1 (
    ECHO [ERREUR] Nuke s'est fermé avec une erreur
    PAUSE
)