SET PIPELINE_DIR=R:\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=R:\pipeline\networkInstall
SET LIB_DIR=R:\lib

REM == Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons

REM == Arnold
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\arnold\6.0.3.1\maya2020
SET MAYA_RENDER_DESC_PATH=%NETWORK_INSTALL%\arnold\6.0.3.1\maya2020

REM == Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings\paradise;%NETWORK_INSTALL%\script

REM == Color
SET OCIO=%NETWORK_INSTALL%\OpenColorIO-Configs\aces_1.2\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces1.2.xml
REM == Bifrost Compound 
SET BIFROST_LIB_CONFIG_FILES=%NETWORK_INSTALL%\bifrost\rebel_pack_0.3.0\bifrost_lib_config.json


REM == Yeti
REM SET peregrinel_LICENSE=5053@BLOOM-NET

REM == MEGASCAN REPO
SET megascan=R:\lib\megascan

REM == DEADLINE
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;R:\deadline\submission\Maya\Client


REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2020\bin\maya.exe -file %1 -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*
