SET SHARED_MAYA_DIR=B:\ressources\pipedev\pipe


REM == Instale Bloom module AND Arnold 
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%SHARED_MAYA_DIR%\maya_scripts\modules\basic;


REM == Other Arnold variables
SET MAYA_RENDER_DESC_PATH=B:\ressources\networkInstall\maya2020

REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2020\bin\maya.exe -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*

