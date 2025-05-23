@echo off
chcp 65001 > NUL
setlocal ENABLEDELAYEDEXPANSION

rem --------------------------- PATHS TO MODIFY ---------------------------
set "path_source=I:\intermarche\"
set "path_destination=G:\Drive partagés\intermarche_drive\intermarche\"
rem --------------------------- PATHS TO MODIFY ---------------------------

rem Get the input path
set "filepath=%~1"

rem Remove the path_source and prepend path_destination (no embedded quotes!)
set "relpath=%filepath:%path_source%=%"
set "newpath=%path_destination%%relpath%"

rem Extract directory portion of new path
call :getPath "%newpath%" dirfilepath

rem Detect if source is directory or file
if exist "%filepath%\*" (
    echo Directory
    set /A isfile=0
) else (
    set /A isfile=1
)

echo From: "%filepath%"
echo To:   "%newpath%"

rem Create destination directory if needed
if not exist "%dirfilepath%" (
    echo Create the directory "%dirfilepath%"
    mkdir "%dirfilepath%"
)

rem Perform the copy
call :copy_fct "%filepath%" "%newpath%" %isfile%
echo Success!
timeout /t 10
exit /b

:getPath
set "%2=%~dp1"
exit /b

:copy_fct
rem Parameters: filepath, newpath, isfile
if %3==1 (
    if exist "%~2" (
        echo:
        echo ######################################################### /^^!\ #########################################################
        echo:
        echo   The file "%~2" already exists!
        echo:
        echo ######################################################### /^^!\ #########################################################
        echo:
    ) else (
        copy "%~1" "%~2"
    )
) else (
    robocopy "%~1" "%~2" /E
)
