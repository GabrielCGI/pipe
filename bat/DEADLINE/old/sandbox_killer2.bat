@echo off
setlocal enabledelayedexpansion

set "lock_file=%~dp0%COMPUTERNAME%_%~n0.lock"

:init
set "started="
2>nul (
 9>"%lock_file%" (
  set "started=1"
  call :start
 )
)
@if defined started (
    del "%lock_file%" >nul 2>nul
) else (
    echo Process aborted: "%~f0" is already running
    @ping localhost > nul
)

exit /b

:start
cd /d %~dp0

:loop
"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe" "R:\pipeline\pipe\bat\DEADLINE\sandbox_killer.py"
timeout /t 180 /nobreak
goto loop

:cleanup
del "%lock_file%"