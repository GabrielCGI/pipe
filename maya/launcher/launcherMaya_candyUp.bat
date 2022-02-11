SET PIPELINE_DIR=I:\candyUp_partage\ressources\pipeline\pipe
SET PIPELINE_DIR_MAYA=%PIPELINE_DIR%\maya
SET SCRIPT_MAYA=%PIPELINE_DIR%\maya\scripts
SET LIB_DIR=I:\candyUp_partage\ressources
rem \---- Shelf
SET MAYA_SHELF_PATH=%PIPELINE_DIR_MAYA%\shelfs
SET XBMLANGPATH=%PIPELINE_DIR_MAYA%\icons

rem \---- Scripts
SET PYTHONPATH=%PYTHONPATH%;%SCRIPT_MAYA%\abcPipeline;%SCRIPT_MAYA%\scene;%SCRIPT_MAYA%\tools;%SCRIPT_MAYA%\startupSettings;%NETWORK_INSTALL%\script

rem \---- Color
rem \---- SET OCIO=<MAYA_RESOURCES>\OCIO-configs\Maya2022-default\config.ocio
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=%PIPELINE_DIR_MAYA%\colorManagement\cm_aces2.0.xml


REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2022\bin\maya.exe -file %1 -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*
