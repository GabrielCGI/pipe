SET PIPELINE_DIR=R:\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=R:\pipeline\networkInstall
SET LIB_DIR=R:\lib


SET PATH_TO_LENTIL=R:\pipeline\networkInstall\lentil\lentil2.5.0-Windows-ai7.1.1.0
SET ARNOLD_PLUGIN_PATH=%PATH_TO_LENTIL%\bin
SET MTOA_TEMPLATES_PATH=%PATH_TO_LENTIL%\ae


rem \---- IMPROVE MAYA STARTUP AND SHUTDOWN TIME
SET MAYA_DISABLE_CIP=1
SET MAYA_DISABLE_CER=1

rem \---- Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons\trashtown_icon;%PIPELINE_DIR_MAYA%\icons

rem \---- ARNOLD SETUP
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\arnold\7.1.4.3_lentil\maya2022;
rem \---- LENTILS


rem \---- HDRLigthStudio
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\HDRLightStudioConnectionMaya\2022

rem \---- ENVIT
SET PATH=%PATH%;%NETWORK_INSTALL%\EnvIt

rem \ BRAVE RABBIT PLACER TOOL
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;R:\pipeline\networkInstall\placeReflection_braveRabbit;

rem \---- BIFRSOT 
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\bifrost\2.6.0.0;
SET BIFROST_LIB_CONFIG_FILES=R:\pipeline\networkInstall\bifrost\MJCG_compounds_2_1_2\MJCG_compounds\bifrost_lib_config.json;R:\pipeline\networkInstall\bifrost\rebel_pack.0.4.2\rebel_pack\bifrost_lib_config.json;

rem \ MAYA SECURITY TOOL
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;R:\pipeline\networkInstall\MayaScanner;

rem \---- YETI SETUP
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\Yeti-v4.1.1_Maya2022-windows;
rem SET ARNOLD_PLUGIN_PATH=%ARNOLD_PLUGIN_PATH%;%NETWORK_INSTALL%\Yeti-v4.1.1_Maya2022-windows\bin
rem SET peregrinel_LICENSE=54132@192.168.0.100

rem \---- Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%\common;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings\battlestar;%SCRIPT_MAYA%\shaderTransferTool;%SCRIPT_MAYA%\assetBrowser;%SCRIPT_MAYA%\assetizer_pymel;%NETWORK_INSTALL%\script

rem \---- Color
rem \---- SET OCIO=<MAYA_RESOURCES>\OCIO-configs\Maya2022-default\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces2.0.xml

rem \----DEADLINE
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;R:\deadline\submission\Maya\Client;

rem \---- Mgears
rem SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\mgear_4.0.3\release;

SET CURRENT_PROJECT=trashtown_2112
SET CURRENT_PROJECT_DIR=B:/trashtown_2112
SET ASSETS_DIR=B:/trashtown_2112/assets
REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2022\bin\maya.exe -file %1 -command "python(\"import startupSettings\"); python (\"startupSettings.run()\"); global proc CgAbBlastPanelOptChangeCallback(string $pass){};"  %*
