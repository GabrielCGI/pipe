@echo off
set PYTHON=R:\pipeline\networkInstall\python\Python.3.11.9\python.exe
set SCRIPT=R:\pipeline\pipe\prism\connected_assets\connected_assets.py

:: Drag-and-drop input file
%PYTHON% "%SCRIPT%" %1

pause
