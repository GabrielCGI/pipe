@echo off
:: Set the Python script name (assumed to be in the same folder)
set SCRIPT=meshai.py


:: Run the script with the image path from drag and drop
R:\pipeline\networkInstall\python\Python.3.11.9\python.exe "%~dp0%SCRIPT%"

pause
