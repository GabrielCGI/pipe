@echo off
call r:\pipeline\pipe\windows\temperature_alert\.venv\Scripts\Activate.bat
call "R:\pipeline\networkInstall\python\Python.3.11.9\python.exe" "R:\pipeline\pipe\windows\temperature_alert\alarm.py"
call r:\pipeline\pipe\windows\temperature_alert\.venv\Scripts\deactivate.bat