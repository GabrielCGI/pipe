echo off

set input_path=%1
set input_path=%input_path:\=/%
set command="input_path=\"%input_path%\""

start R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe %~dp0/output_srgb_to_aces.py -c %command%
