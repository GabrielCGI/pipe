@echo off
setlocal

REM Full path to iautocrop
set "IAUTOCROP=C:\Program Files\Side Effects Software\Houdini 21.0.596\bin\iautocrop.exe"

REM Folder dragged onto the bat
set "FOLDER=%~1"

if "%FOLDER%"=="" (
    echo Please drag and drop a folder onto this .bat file.
    pause
    exit /b
)

echo Processing folder:
echo %FOLDER%
echo.

REM Loop over all EXR files in the folder
for %%F in ("%FOLDER%\*.exr") do (
    echo Processing: %%F
    "%IAUTOCROP%" -r "%%F"
)

echo.
echo Done!
pause
