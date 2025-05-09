SET PIPELINE_DIR=R:\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=R:\pipeline\networkInstall
SET LIB_DIR=R:\lib

SET PATH_TO_LENTIL=R:\pipeline\networkInstall\lentil\lentil2.4.1-Windows-ai7.1.1.0
SET DISK_I=I:
SET DISK_R=R:
rem \---- IMPROVE MAYA STARTUP AND SHUTDOWN TIME
SET MAYA_DISABLE_CIP=1
SET MAYA_DISABLE_CER=1

rem \---- Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons\redSwan_icon;%PIPELINE_DIR_MAYA%\icons

rem \---- ARNOLD SETUP
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\arnold\7.1.3.1\maya2022;

rem \---- LENTILS


rem \---- SET ARNOLD_PLUGIN_PATH=%PATH_TO_LENTIL%\bin


rem \---- SET MTOA_TEMPLATES_PATH=%PATH_TO_LENTIL%\ae

rem \---- HDRLigthStudio
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\HDRLightStudioConnectionMaya\2022

rem \ MAYA SECURITY TOOL
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;R:\pipeline\networkInstall\MayaScanner;

rem \---- PLace Reflection
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\placeReflection_braveRabbit

rem \---- YETI SETUP
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\Yeti-v4.1.1_Maya2022-windows;
rem SET ARNOLD_PLUGIN_PATH=%ARNOLD_PLUGIN_PATH%;%NETWORK_INSTALL%\Yeti-v4.1.1_Maya2022-windows\bin
rem SET peregrinel_LICENSE=61314@illogic-net.illogic.studios.com

rem \---- Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings;%SCRIPT_MAYA%\shaderTransferTool;%NETWORK_INSTALL%\script;

rem \---- Color
rem \---- SET OCIO=<MAYA_RESOURCES>\OCIO-configs\Maya2022-default\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces2.0.xml

rem \----DEADLINE
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;R:\deadline\submission\Maya\Client;


rem \---- Mgears
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\mgear_4.0.3\release;

SET CURRENT_PROJECT=swaRedSwan_2209

REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2022\bin\maya.exe -file %1 -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*
