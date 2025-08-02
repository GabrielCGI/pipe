import maya.cmds as cmds
import uuid
import json


def show_save_reopen_popup():
    message = "Save the scene and reopen it."
    cmds.confirmDialog(
        title='Reminder',
        message=message,
        button=['OK'],
        defaultButton='OK',
        dismissString='OK'
    )


def run(*args):
    fileinfo = cmds.fileInfo("PrismStates", q=True)
    if not fileinfo:
        return

    clearInfo = fileinfo[0].encode().decode('unicode_escape')
    StateScene = json.loads(clearInfo)["states"]
    new_statScene = []
    for i, info in enumerate(StateScene):
        try:
            if info["stateclass"] == "ImportFile":
                continue
                
        except Exception as e: 
            print("error: note fonde", e, info)
        new_statScene.append(info)


    references = cmds.file(query=True, reference=True)
    new_import = []
    BIGDADA = StateScene
    for i in references:
        nameSplit = i.split("/")
        ref = nameSplit[-1].split(".")[0]
        taskName = nameSplit[-3]
        new_txt = i.replace("/", "\\")
        data = [new_txt, ref]
        UUID = uuid.uuid4()
        ref_node = cmds.referenceQuery(i, referenceNode=True)

        State = {"stateparent":"None", "stateclass":"ImportFile", 
        "uuid":f"{UUID.hex}", "statename":"{entity}_{product}_{version}", 
        "statemode":"ImportFile", 
        "filepath":f"{new_txt}","autoUpdate":"False", 
        "keepedits":"True", "autonamespaces":"False", 
        "updateabc":"False", "trackobjects":"True", 
        "connectednodes":[[ref_node, ref_node]], 
        "taskname":f"{taskName}", "nodenames":str([ref_node]), "setname":f"Import_{ref}_"}
        
        new_import.append(data)
        BIGDADA.append(State)

    final_data = {
        "states": BIGDADA
    }
    cmds.fileInfo("PrismStates", json.dumps(final_data, indent=4))
    cmds.fileInfo("PrismImports", str(new_import))

    show_save_reopen_popup()