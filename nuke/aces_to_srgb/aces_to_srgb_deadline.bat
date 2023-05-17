echo off

set folder=%1
set folder=%folder:\=/%
set folder=%folder:"=%
set command="folder=\"%folder%\""

start R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe %~dp0/aces_to_srgb.py -c %command%
