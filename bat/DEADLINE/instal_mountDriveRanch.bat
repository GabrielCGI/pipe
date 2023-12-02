@echo off
REM Delete all .bat files in the specified Startup directory
DEL "C:\Users\illogic\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\*.bat"

SET "sourcePath=R:\pipeline\pipe\bat\DEADLINE\mountDriveRanch.bat"
SET "destinationPath=C:\Users\illogic\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\mountDriveRanch.bat"


IF EXIST "%sourcePath%" (
    IF EXIST "%destinationPath%" (
        DEL "%destinationPath%"
    )
    COPY /Y "%sourcePath%" "%destinationPath%"
    IF ERRORLEVEL 1 (
        ECHO "Failed to copy the file."
        EXIT /B 1
    ) ELSE (
        ECHO "File copied successfully."
        START "" "%sourcePath%"
    )
) ELSE (
    ECHO "Source file does not exist."
    EXIT /B 1
)
