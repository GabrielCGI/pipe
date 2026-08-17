cd /d "%~dp0"
rem Chemin LONG (pas de nom 8.3 HOUDIN~1 : instable selon l'ordre d'install / desactivable).
set "HOUDINI_ROOT=C:\Program Files\Side Effects Software\Houdini 21.0.596"
rem Epingle la version choisie et neutralise tout ce qui pourrait pointer une AUTRE version
rem (sinon hython charge un _hou.pyd / python311.dll d'une autre version -> segfault).
set "HFS=%HOUDINI_ROOT%"
set "PATH=%HOUDINI_ROOT%\bin;%PATH%"
set "HOUDINI_PATH="
set "PYTHONHOME="
rem NE PAS injecter le site-packages uv (PySide6 6.11) dans hython : Houdini a le sien
rem (6.5) et melanger les deux = meme classe de collision Qt/ABI que le segfault de hou.
set "PYTHONPATH=%CD%\src"
uv sync
"%HOUDINI_ROOT%\bin\hython.exe" main_recache.py