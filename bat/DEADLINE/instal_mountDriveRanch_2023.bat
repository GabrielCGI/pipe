@echo off

SET "sourcePath=R:\pipeline\pipe\bat\DEADLINE\mountDriveRanch_2023.bat"
SET "destinationPath=C:\Users\illogic\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\mountDriveRanch_2023.bat"

IF EXIST "%sourcePath%" (
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
