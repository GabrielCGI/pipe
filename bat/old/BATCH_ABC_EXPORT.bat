ECHO OFF 
SET CURRENT_PROJECT_DIR=I:/battlestar_2206
Rem #################################################################################
Rem see R:/pipeline/pipe/maya/scripts/abc_export/list_scenes.py to get list of scenes
Rem #################################################################################
"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe" "R:/pipeline/pipe/maya/scripts/abc_export/export_scenes_abc.py" ^
I:/battlestar_2206/shots/longform_shot060/anim/0263/longform_shot060_anim.0264.ma ^
pause