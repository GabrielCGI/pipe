@echo off
REM Delete all .bat files in the specified Startup directory
DEL "C:\Users\illogic\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\*.bat"

SET "sourcePath=I:\tmp\ranch.ffs_batch"
SET "destinationPath=C:\Users\sysadmin\Desktop\ranch.ffs_batch"


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
