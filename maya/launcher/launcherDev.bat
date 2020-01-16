SET PIPELINE_DIR=B:\ressources\pipedev\pipe
SET PIEPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=B:\ressources\networkInstall

REM == Shelf
SET MAYA_SHELF_PATH=%PIEPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIEPELINE_DIR_MAYA%\icons

REM == Arnold
SET MAYA_MODULE_PATH=%NETWORK_INSTALL%\maya2020
SET MAYA_RENDER_DESC_PATH=%NETWORK_INSTALL%\maya2020

REM == Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools

REM == Color
SET OCIO=%NETWORK_INSTALL%\openColorIo\aces_1.0.3\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIEPELINE_DIR_MAYA%\colorManagement\cm_ACES1.0.3.xml

REM == Yeti
SET peregrinel_LICENSE=5052@SPRINTER-08


REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2020\bin\maya.exe -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*
