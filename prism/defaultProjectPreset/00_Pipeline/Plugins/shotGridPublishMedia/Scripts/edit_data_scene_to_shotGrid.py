

def findStatusFromCurrentState(core)-> str:
    if core.appPlugin.pluginName != 'Maya':
        return "rev"
    
    state = core.getStateManager().curExecutedState
    if state is None:
        return "rev"
    return state.lo_prjMngPublish.itemAt(2).wid.currentText()

def _findToExport(core):
        import maya.cmds as cmds
        import json
        import re

        #--------------    import la data du state manager de la scene et la comparer avec les presets
        fileinfo = cmds.fileInfo("PrismStates", q=True)
        clearInfo = fileinfo[0].encode().decode('unicode_escape')
        State_scene = json.loads(clearInfo)["states"]
        if not State_scene:
            return []
        del State_scene[0]



        #--------------    read la data du projet pour trouver les presets du state manager pour l'export
        good_state = []
        for i, state in enumerate(State_scene):
            if state["stateclass"] in["Playblast", "ImportFile"]:
                continue
            if not state["stateenabled"]:
                continue
            
            good_state.append(state)

        
        data_Export = ""
        path_scene = core.getCurrentFileName()
        entity = core.getScenefileData(path_scene)
        # get geo to export and all shading engine------------------------------------------
        for state in good_state:
            export = None
            if state["stateclass"] == "USD Export":
                export = findGoodSetsUSD(state)
            elif state["stateclass"] == "Export":
                export = state["productname"]
            
            if export is None:
                continue
            
            data_version = core.products.getLatestVersionpathFromProduct(export, entity=entity)
            next_version = core.products.getNextAvailableVersion(entity, export)
            if data_version:
                next_export = re.sub(r'v\d+', next_version, data_version)
            else:
                root_path = core.products.getProductPathFromEntity(entity)
                
                next_export = f"{root_path}\\{export}\\{next_version}\\{export}_{next_version}..."

            data_Export += f"- file exported: {next_export}\n"


        return data_Export

def findGoodSetsUSD(State: dict) -> str:
        if State["saveMode"] == "Custom":
            return State["product"]
        
        elif State["saveMode"] == "Layer":
            dep = State["departmentLayer"]
            sublayer = State["sublayer"]
            if State["useSublayer"]:
                return f"_layer_{dep}_{sublayer}"
            else:
                return f"_layer_{dep}_master"
        else:
            return "USD"

# Custom par illogic pouvoir retrouver tout les data exporter durant le publish  pour pourvoir les faire remonté dans shotGrid
def addPathGeometryCustom(core) -> str:
    name_scene = "Unknow"
    data_export = "Unknow"
    if core.appPlugin.pluginName == 'Maya':
        import maya.cmds as cmds
        name_scene = cmds.file(q=True, sn=True)
        export = _findToExport(core)
        if export:
            data_export = export
        else:
            data_export = "Nothing has been exported"
    
    elif core.appPlugin.pluginName == 'Nuke':
        name_scene = "Nuke "
    
    elif core.appPlugin.pluginName == 'Standalone':
        name_scene = "Panel Media of Prism"


    data_path = f"This version come from :{name_scene}\n{data_export}"
    return data_path



# main execution
def mainCustom(data, core)-> dict:
    data["sg_path_to_geometry"] = addPathGeometryCustom(core)
    status = findStatusFromCurrentState(core)
    if status:
        data["sg_status_list"] = status
    
    return data