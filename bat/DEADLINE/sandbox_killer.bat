@echo off
:loop
"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe" "R:\pipeline\pipe\bat\DEADLINE\sandbox_killer.py"
timeout /t 180 /nobreak
goto loop