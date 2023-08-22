echo off

set input_file=%~1
set output_file=%~2
set range=%~3

echo Input file: %input_file%
echo Output file: %output_file%
echo Range: %range%

set command="output_file=\"%output_file%\";input_file=\"%input_file%\";hd=\"n\""
echo Command: %command%

set natron_path=R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe
set script_path=R:\pipeline\pipe\nuke\exr2mov\data\exr2mov.py

echo Starting Natron Renderer...
"%natron_path%" "%script_path%" -c %command% -w MyWriter %range%