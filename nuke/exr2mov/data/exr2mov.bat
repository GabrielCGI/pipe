echo off
set /p start=Start frame:
set /p end=End frame:


set sequence=%1
set trim=%sequence:~0,-8%
set output_file=%trim%_preivew.mov
set output_file=%output_file:\=/%
set input_file=%trim%####.exr
set input_file=%input_file:\=/%
set range=%start%-%end%

set command="output_file=\"%output_file%\";input_file=\"%input_file%\""
echo c: %command%

start R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe %cd%/exr2mov.py -c %command% -w MyWriter %range%
