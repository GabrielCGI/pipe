echo off

set folder=%1
set folder=%folder:\=/%
set folder=%folder:"=%
set command="folder=\"%folder%\""
echo %command%

start C:\"Program Files"\Natron\bin\NatronRenderer.exe %~dp0/aces_to_srgbPNG.py -c %command%
