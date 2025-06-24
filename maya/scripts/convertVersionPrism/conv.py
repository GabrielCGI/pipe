print("----------------------------------- import good version Prism -----------------------------------")

import os 
current_value = os.environ.get("MAYA_MODULE_PATH")
new_path = "R:/pipeline/pipe/maya/modules/2.0.16"
paths = current_value.split(os.pathsep) if current_value else []
paths.insert(0, new_path)
if False:
    os.environ["MAYA_MODULE_PATH"] = os.pathsep.join(paths)


print("new vales", os.environ["MAYA_MODULE_PATH"])