echo off

set input_file=%~1
set output_file=%~2
set range=%~3

echo %input_file%
echo %output_file%
echo %range%



set command="output_file=\"%output_file%\";input_file=\"%input_file%\""
echo c: %command%

start R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe R:\pipeline\pipe\nuke\exr2mov\data\exr2mov.py -c %command% -w MyWriter %range%
