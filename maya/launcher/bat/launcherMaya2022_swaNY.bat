SET PIPELINE_DIR=R:\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET NETWORK_INSTALL=R:\pipeline\networkInstall
#SET ROMBOTOOLS=R:\pipeline\networkInstall\romboTools\rtoa_WIN_ARN-7.1.3.1_2023-01-16_v.1.2.0



rem SET PATH_TO_LENTIL=R:\pipeline\networkInstall\lentil\lentil2.5.0-Windows-ai7.1.1.0
rem SET ARNOLD_PLUGIN_PATH=%PATH_TO_LENTIL%\bin
rem SET MTOA_TEMPLATES_PATH=%PATH_TO_LENTIL%\ae

rem \---- ROMBO TOOLS
#SET MTOA_TEMPLATES_PATH=%ROMBOTOOLS%\rtoa\DCCs\Maya\ae
#SET MAYA_CUSTOM_TEMPLATE_PATH=%ROMBOTOOLS%\rtoa\DCCs\Maya\aexml
#SET ARNOLD_PLUGIN_PATH=%ROMBOTOOLS%\rtoa\bin
rem \---- IMPROVE MAYA STARTUP AND SHUTDOWN TIME
SET MAYA_DISABLE_CIP=1
SET MAYA_DISABLE_CER=1

rem \---- Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons\swaChrystmas_2023;%PIPELINE_DIR_MAYA%\icons

rem \---- ARNOLD SETUP

SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;%NETWORK_INSTALL%\arnold\7.2.3.2\maya2022;

rem \ MAYA SECURITY TOOL
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;R:\pipeline\networkInstall\MayaScanner;

rem \ BRAVE RABBIT PLACER TOOL
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;R:\pipeline\networkInstall\placeReflection_braveRabbit;

rem \---- Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings\swaChristmas;%SCRIPT_MAYA%\shaderTransferTool;%SCRIPT_MAYA%\assetBrowser;%NETWORK_INSTALL%\python_lib;%NETWORK_INSTALL%\script;%SCRIPT_MAYA%\assetizer_pymel


rem \---- Color
rem \---- SET OCIO=<MAYA_RESOURCES>\OCIO-configs\Maya2022-default\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces2.0.xml

rem \----DEADLINE
SET MAYA_SCRIPT_PATH=%MAYA_SCRIPT_PATH%;R:\deadline\submission\Maya\Client;


SET CURRENT_PROJECT=swaNY_2308
SET CURRENT_PROJECT_DIR=I:/swaNY_2308
SET ASSETS_DIR=I:/swaNY_2308/assets

REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2022\bin\maya.exe -file %1 -command "python(\"import startupSettings\"); python (\"startupSettings.run()\")"  %*
