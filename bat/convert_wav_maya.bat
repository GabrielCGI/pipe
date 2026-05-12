@echo off
setlocal enabledelayedexpansion

set FFMPEG="C:\ILLOGIC_APP\Prism\2.1.1\app\Tools\FFmpeg\bin\ffmpeg.exe"

:: Check if a folder was dropped
if "%~1"=="" (
    echo.
    echo  [ERROR] Drag and drop a folder onto this .bat file.
    echo.
    pause
    exit /b 1
)

set FOLDER=%~1

:: Check it's actually a directory
if not exist "%FOLDER%\" (
    echo.
    echo  [ERROR] "%FOLDER%" is not a valid folder.
    echo.
    pause
    exit /b 1
)

echo.
echo  Folder  : %FOLDER%
echo  Converting all .wav to 16-bit PCM ...
echo.

set COUNT=0
set ERRORS=0

for %%F in ("%FOLDER%\*.wav") do (
    :: Skip files that already have the _converted suffix
    echo %%~nF | findstr /i /c:"_converted" >nul
    if errorlevel 1 (
        set /a COUNT+=1
        set INPUT=%%~fF
        set OUTPUT=%%~dpF%%~nF_converted%%~xF

        echo  [%%COUNT%%] %%~nxF  -^>  %%~nF_converted%%~xF
        %FFMPEG% -y -i "!INPUT!" -acodec pcm_s16le -ar 48000 "!OUTPUT!" -hide_banner -loglevel error

        if errorlevel 1 (
            echo      [FAILED]
            set /a ERRORS+=1
        ) else (
            echo      [OK]
        )
    )
)

echo.
if !COUNT!==0 (
    echo  No .wav files found in the folder.
) else (
    echo  Done. !COUNT! file(s) processed, !ERRORS! error(s).
)
echo.
pause