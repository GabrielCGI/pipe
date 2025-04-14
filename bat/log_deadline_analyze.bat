@echo off
REM This assumes that "python" is on your system PATH. 
REM If it isn’t, replace "python" with the full path to your Python executable.

"R:\pipeline\networkInstall\python\Python310\python.exe" "R:\pipeline\pipe\bat\log_deadline_analyze.py" %1

pause
