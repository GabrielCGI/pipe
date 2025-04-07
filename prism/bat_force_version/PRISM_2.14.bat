@echo off
set "A_PRISM_VER=2.0.14"
set "PRISM_ROOT=C:\ILLOGIC_APP\Prism\%A_PRISM_VER%\app"
set "PRISM_PLUGIN_SEARCH_PATHS=C:\ILLOGIC_APP\Prism\%A_PRISM_VER%\plugins"

echo Start killing Prism...
taskkill /f /im Prism.exe >nul 2>&1
echo Prism killed.

echo Starting Prism %A_PRISM_VER%...
start "" "%PRISM_ROOT%\Python311\Prism.exe" "%PRISM_ROOT%\Scripts\PrismTray.py" projectBrowser
