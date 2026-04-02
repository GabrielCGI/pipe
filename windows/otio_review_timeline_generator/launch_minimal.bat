@echo off
cd /d "%~dp0"

:: Each user gets their own local venv (network-share safe, multi-user safe)
set VENV_DIR=R:\pipeline\networkInstall\python_shares\python312_otio_timelines_pkgs

:: Patch OpenRV otio_reader.py for OTIO API compatibility
call :patch_rv

:: Launch the tool
echo Launching OTIO Review Tool...
echo Python: %VENV_DIR%\Scripts\python.exe
echo.
"%VENV_DIR%\Scripts\python" "%~dp0app.py" 2>&1
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  Application exited with an error.
    echo  Check the messages above.
    echo.
    echo  A crash log may have been written to:
    echo  %TEMP%\otio_review_error.log
    echo ============================================================
    echo.
    pause
)
exit /b 0

:: -------------------------------------------------------
:patch_rv
    set RV_READER=C:\ILLOGIC_APP\OpenRV\plugins\Python\otio_reader.py
    if not exist "%RV_READER%" (
        echo [WARN] OpenRV plugin not found, skipping patch.
        exit /b 0
    )
    findstr /c:"find_clips" "%RV_READER%" >nul 2>&1
    if not errorlevel 1 (
        exit /b 0
    )
    echo Patching OpenRV otio_reader.py for OTIO compatibility...
    powershell -Command "(Get-Content '%RV_READER%') -replace 'tl\.clip_if\(\)', 'tl.find_clips()' | Set-Content '%RV_READER%'"
    if errorlevel 1 (
        echo [WARN] Could not patch OpenRV plugin. Try running as administrator.
        exit /b 0
    )
    echo [OK] OpenRV otio_reader.py patched.
    exit /b 0
