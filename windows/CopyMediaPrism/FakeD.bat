@echo off

REM Base folder for fake D drive
set "BASE=C:\fakeD"
set "SUB=cache_resolve"

REM Create base + subfolder (mkdir creates intermediate folders)
if not exist "%BASE%\%SUB%" (
    mkdir "%BASE%\%SUB%"
)

REM Mount the folder as D: if not already mounted
if exist D:\ (
    echo D: already exists, skipping subst
) else (
    subst D: "%BASE%"
)

echo D: drive mounted to %BASE%
echo Cache folder: D:\%SUB%
pause