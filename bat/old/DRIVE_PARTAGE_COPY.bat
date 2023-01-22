@echo off
chcp 65001 > NUL

rem Get the file path
set filepath=%~1
echo %dirfilepath%

rem Change the start of the path and get filename

set "newpath=%filepath:I:\battlestar_2206=G:\Drive partagés\battlestar_partage\battlestar_2206%"
rem Get the path directories of the newpath
call :getPath "%newpath%" dirfilepath

echo From: %filepath%
echo To:   %newpath%
echo dirfilepath:   %dirfilepath%

rem Check if the destination directory exists
if exist "%dirfilepath%" (
  rem Copy the file to the new path
  copy "%filepath%" "%newpath%"
  pause
  exit /b
)


set /p create=Do you want to create missing directories? [y/n]

if /i "%create%"=="y" (
    rem Create the directory
    echo Create the directory %dirfilepath%
    mkdir "%dirfilepath%"
    rem Copy the file to the new path
    copy "%filepath%" "%newpath%"
) else (
    echo Aborting execution.
)

pause
exit /b

:getPath
set "%2=%~dp1"
exit /b
