from pathlib import Path
import traceback
import time
import sys
import os



# recuperer l'emplacement du module pour l'importer si il n'est pas present dans les sys path
MODULE_PATH = Path(os.path.dirname(__file__)).parent.parent
timer = 5


def startProcess():
    if MODULE_PATH not in sys.path:
        sys.path.append(str(MODULE_PATH))
    import reference_updater #type: ignore

    scene_path = str(sys.argv[1])
    data = eval(sys.argv[2])
    projet_path = scene_path.replace("\\", "/").split("03_Production/")[0]

    referencer = reference_updater.noUI(True, projet_path, scene_path)
    referencer.ExecutionProcedure(data)



try:
    startProcess()

except Exception as e:
    print("--------------------------- ERROR EXECUTION ----------------------------------\n"*3)
    print(e)
    print(traceback.format_exc())
    timer = 20

#permet juste de voir la fin de la console cmd pour les utilisateur quand il affiche la console pour s'avoir si tout c'est bien passer ou pas
time.sleep(timer)
