import maya.cmds as cmds
from pathlib import Path
import shutil

#DRIVES TO REPLACE
drive_sources = ["I:/","R:/"]
drive_archive = "D:/cache5/"

#LIST ALL ASSETS DIRECTORY USED IN SCENE
list_dir= cmds.filePathEditor(query=True, listDirectories="")

for dir in list_dir:
    #LIST ALL FILES IN DIR
    list_file= cmds.filePathEditor(query=True, listFiles=dir)

    for fil in list_file:
        fullpath = os.path.join(dir,fil)
        if fullpath.split("/")[0] == "I:":
            newdir = dir.replace("I:",drive_archive )
        if fullpath.split("/")[0] == "R:":
            newdir = dir.replace("R:",drive_archive )
        newfullpath = os.path.join(newdir,fil)
        path = Path(newdir)
        print(newfullpath)
        try:
            path.mkdir(parents=True)
            print("creating: "+ newdir)
        except OSError as e:
            print("File already exist: "+newdir)
        #shutil.copy(fullpath, newdir) #NE MARCHE PAS IL FAUT UTILISER AUTRE CHOSE QUE dir.replace
