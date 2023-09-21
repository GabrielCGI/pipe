echo off

set input_file=%1
set output_file=%2
set start=%3
set end=%4
set hd=%5
set range=%start%-%end%

set trim=%input_file:~0,-8%
set input_file=%trim%####.exr

set command="output_file=\"%output_file%\";input_file=\"%input_file%\";hd=\"%hd%\""
echo Command: %command%

set natron_path=R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe
set script_path=R:\pipeline\pipe\nuke\exr2mov\data\exr2mov.py

"%natron_path%" "%script_path%" -c %command% -w MyWriter %range%