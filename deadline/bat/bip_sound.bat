@echo off

REM Playing a bip sound using system bell
echo ^G

REM Calling the Python script using Maya's Python interpreter
"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe" R:\pipeline\pipe\deadline\bat\bip_sound.py

pause