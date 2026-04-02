@echo off
cd /d "%~dp0"

:: Each user gets their own local venv (network-share safe, multi-user safe)
set VENV_DIR=C:\ProgramData\otio_review_tool\venv

:: Check if venv exists and is functional; recreate if broken
if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Existing venv is broken ^(wrong machine / Python removed^). Recreating...
        rmdir /s /q "%VENV_DIR%"
        call :setup_venv
        if errorlevel 1 exit /b 1
    )
) else (
    call :setup_venv
    if errorlevel 1 exit /b 1
)

echo [OK] Environment ready.

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
:setup_venv
    :: Find Python 3.12 or 3.11 via the Windows py launcher
    set PYTHON_EXE=
    py -3.12 --version >nul 2>&1
    if not errorlevel 1 set PYTHON_EXE=py -3.12

    if not defined PYTHON_EXE (
        py -3.11 --version >nul 2>&1
        if not errorlevel 1 set PYTHON_EXE=py -3.11
    )

    if not defined PYTHON_EXE (
        echo.
        echo ============================================================
        echo  ERROR: Python 3.11 or 3.12 is required.
        echo.
        echo  opentimelineio has no pre-built wheel for Python 3.14.
        echo.
        echo  Please install Python 3.11 or 3.12 from:
        echo    https://www.python.org/downloads/
        echo  Check "Add to PATH" during installation.
        echo ============================================================
        echo.
        pause
        exit /b 1
    )

    echo Using: %PYTHON_EXE%
    echo Creating virtual environment in %VENV_DIR%...
    mkdir "C:\ProgramData\otio_review_tool" 2>nul
    %PYTHON_EXE% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )

    echo Upgrading pip...
    "%VENV_DIR%\Scripts\python" -m pip install --upgrade pip --quiet

    echo Installing PySide6...
    "%VENV_DIR%\Scripts\pip" install PySide6 --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install PySide6.
        pause
        exit /b 1
    )

    echo Installing opentimelineio 0.16.0 (OpenRV compatible)...
    "%VENV_DIR%\Scripts\pip" install "opentimelineio==0.16.0" --only-binary :all: --quiet
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo  ERROR: Could not install opentimelineio==0.16.0.
        echo  Please install Python 3.11 or 3.12, then run this script again.
        echo ============================================================
        echo.
        pause
        exit /b 1
    )

    echo.
    echo Setup complete.
    echo.
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
