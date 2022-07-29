SET PIPELINE_DIR=R:\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=R:\pipeline\networkInstall
SET LIB_DIR=R:\lib
rem \SET PATH_TO_LENTIL=R:\pipeline\networkInstall\lentil_v2.0.2_20220216

rem \---- IMPROVE MAYA STARTUP AND SHUTDOWN TIME
SET MAYA_DISABLE_CIP=1
SET MAYA_DISABLE_CER=1

rem \---- Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons\trashtown_icon;%PIPELINE_DIR_MAYA%\icons

rem \---- ARNOLD SETUP



rem \---- HDRLigthStudio
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\HDRLightStudioConnectionMaya\2022


rem \---- YETI SETUP
SET MAYA_MODULE_PATH=R:\pipeline\networkInstall\Yeti-v4.1.1_Maya2022-windows;%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\arnold\7.0.0.1\maya2022
SET ARNOLD_PLUGIN_PATH=R:\pipeline\networkInstall\Yeti-v4.1.1_Maya2022-windows\bin
SET peregrinel_LICENSE=54373@illogic-net.illogic.studios.com

rem \---- Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings;%SCRIPT_MAYA%\shaderTransferTool;%NETWORK_INSTALL%\script

rem \---- Color
rem \---- SET OCIO=<MAYA_RESOURCES>\OCIO-configs\Maya2022-default\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces2.0.xml

rem \----DEADLINE
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;R:\deadline\submission\Maya\Client;

rem \---- Mgears

SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\mgear_4.0.3\release;

REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2022\bin\maya.exe -file %1 -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*
