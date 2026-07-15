@echo off

:: Ensure the input path is provided
if "%1"=="" (
    echo Usage: script.bat <folder_path>
    pause
    exit /b
)
pause
:: Normalize the input path
set "input_path=%~1"
echo Input Path: %input_path%
pause

set "input_path=%input_path:\=/%"
echo Normalized Input Path: %input_path%
pause

set "input_path=%input_path:"=%"
echo Final Input Path: %input_path%
pause

:: List all files in the folder and iterate through them
for /R "%~1" %%F in (*) do (
    echo Processing file: %%F
    pause
    set "file_path=%%F"
    set "file_path=!file_path:\=/!"
    echo Normalized File Path: !file_path!
    pause
    set "file_path=!file_path:"=!"
    echo Final File Path: !file_path!
    pause
    
    :: Build the command for each file
    set "command="input_path=\"!file_path!\""
    echo Command: %command%
    pause
    
    :: Run the command
    start "" R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe %~dp0/output_srgb_to_aces_version_louis.py -c !command!
    echo Command executed for file: %%F
    pause
)