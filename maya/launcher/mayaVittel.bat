SET SHARED_MAYA_DIR=B:\\ressources\\sharedMaya

REM == Instal shelf
SET MAYA_SHELF_PATH=%MAYA_SHELF_PATH%;%SHARED_MAYA_DIR%\shelfs
SET XBMLANGPATH=%XBMLANGPATH%;%SHARED_MAYA_DIR%\\icons

REM == Color and Aces
SET MAYA_COLOR_MANAGEMENT_POLICY_FILE=B:\ressources\sharedMaya\colorManagement\cm.xml
SET OCIO=B:\ressources\networkInstall\openColorIo\aces_1.0.3\config.ocio

REM == Instale Bloom module AND Arnold 
SET MAYA_MODULE_PATH=%MAYA_MODULE_PATH%;B:\ressources\sharedMaya\modules\basic;B:\ressources\networkInstall\maya2020

REM == Other Arnold variables
SET MAYA_RENDER_DESC_PATH=B:\ressources\networkInstall\maya2020

REM == Start maya and launch statupSettings (FPS, Unit ect...)
start C:\"Program Files"\Autodesk\Maya2020\bin\maya.exe -command "python(\"import startupSettings\"); python (\"startupSettings.run()\");"  %*

