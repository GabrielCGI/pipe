echo off

echo ___NatronMovBat___

set input_file=%1
set output_file=%2
set start=%3
set end=%4
set hd=%5
set range=%start%-%end%

set command="output_file=\"%output_file%\";input_file=\"%input_file%\";hd=\"%hd%\""
echo %command%
R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe R:\pipeline\pipe\nuke\exr2mov\data\exr2mov.py -c %command% -w MyWriter %range%