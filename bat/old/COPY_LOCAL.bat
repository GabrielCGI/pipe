@echo off
chcp 65001 > NUL
setlocal ENABLEDELAYEDEXPANSION

rem "--------------------------- PATHS TO MODIFY ---------------------------"
set path_source=I:\swaLion_2401\
set path_destination=D:\LION_BACKUP\swaLion_2401\
rem "--------------------------- PATHS TO MODIFY ---------------------------"

rem Get the file path
set filepath=%~1

rem Change the start of the path and get filename
call set newpath=%%filepath:!path_source!=!path_destination!%%

rem Get the path directories of the newpath
call :getPath "%newpath%" dirfilepath

if exist %1\* (
  echo Directory
  set /A isfile = 0
) else (
  set /A isfile = 1
)

echo From: %filepath%
echo To:   %newpath%

rem Check if the destination directory exists
if exist "%dirfilepath%" (
  rem Copy the file to the new path
  call :copy_fct "%filepath%" "%newpath%" %isfile%
  pause
  exit /b
)

set /p create=Do you want to create previous missing directories? [y/n]

if /i "%create%"=="y" (
    rem Create the directory
    echo Create the directory %dirfilepath%
    mkdir "%dirfilepath%"
    rem Copy the file to the new path
    call :copy_fct "%filepath%" "%newpath%" %isfile%
) else (
    echo Aborting execution.
)

pause
exit /b

:getPath
set "%2=%~dp1"
exit /b

:copy_fct
rem parameters : filepath newpath isfile
if %3==1 (
  if exist %2 (
    echo:
    echo ######################################################### /^^!\ #########################################################
    echo:
    echo   The file %2 already exists !
    echo:
    echo ######################################################### /^^!\ #########################################################
    echo:
  ) else (
    copy %1 %2
  )
) else (
  robocopy %1 %2 /E 
)
