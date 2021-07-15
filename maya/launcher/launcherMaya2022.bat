SET PIPELINE_DIR=R:\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=R:\pipeline\networkInstall
SET LIB_DIR=R:\lib

SET MAYA_DISABLE_CIP=1
SET MAYA_DISABLE_CER=1
REM == Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons

REM == Arnold
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\arnold\6.2.1.0\maya2022
REM == SET MAYA_RENDER_DESC_PATH=%NETWORK_INSTALL%\arnold\6.2.1.0\maya2022

REM == Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings\paradise;%NETWORK_INSTALL%\script

REM == Color
REM == SET OCIO=<MAYA_RESOURCES>\OCIO-configs\Maya2022-default\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces2.0.xml



REM == Yeti
SET peregrinel_LICENSE=5053@BLOOM-NET
SET MAYA_MODULE_PATH=%NETWORK_INSTALL%\Yeti-v4.0.1_Maya2022-windows
SET MTOA_EXTENSIONS_PATH=%MTOA_EXTENSIONS_PATH%;%NETWORK_INSTALL%\Yeti-v4.0.1_Maya2022-windows\bin
SET PATH=%PATH%;%NETWORK_INSTALL%\Yeti-v4.0.1_Maya2022-windows\bin



REM == DEADLINE
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;R:\deadline\submission\Maya\Client



REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2022\bin\maya.exe -file %1 -command "file -prompt false; python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*
