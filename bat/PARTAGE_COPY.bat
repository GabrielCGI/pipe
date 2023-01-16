@echo off
chcp 65001 > NUL

rem Get the file path
set "filepath=%~1"

rem Change the start of the path

echo ----- TO BATTLESTAR PARTAGE ----
set "newpath=%filepath:I:\battlestar_2206=G:\Drive partagés\battlestar_partage\battlestar_2206%"
echo From: %filepath%
echo To:   %newpath%

pause
rem Copy the file to the new path
copy "%filepath%" "%newpath%"

pause