import maya.cmds as cmds
import maya.standalone
import ctypes
import msvcrt
import socket
import sys
import re
import os


dataEnv = eval(sys.argv[1])
dataRef = eval(sys.argv[2])
departement = dataEnv["department"]
if dataEnv["DEBUG"] and True:
    ctypes.windll.kernel32.AllocConsole()
    sys.stdout = open('CONOUT$', 'w')
    sys.stdin = open('CONIN$', 'r')



def infoP(msg):
    print(str(msg), file=sys.stdout)

def error(msg):
    print("ILLOGIC ERROR : " + str(msg), file=sys.stdout)
    print("ILLOGIC ERROR : " + str(msg), file=sys.stderr)

def debugger():
    sys.path.append("R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages")
    from debug import debug
    debug.debug()
    debug.debugpy.breakpoint()

def catch_error(dataEnv):
    if not dataEnv or type(dataEnv) != dict:
        error("no data Environment")
        return True
    if not "Projet" in dataEnv:
        error("no Projet arguments")
        return True
    if not "Scene" in dataEnv:
        error("no Scene arguments")
        return True
    if not "Update" in dataEnv:
        error("no Update arguments")
        return True
     
    return False


def findLastScene(Projet, nameSpace, Type):
    dosAsset = rf"{Projet}03_Production/Assets/{Type}/{nameSpace}/Export/{departement}"
    last_file = None
    fileRef = None

    if not os.path.exists(dosAsset):
        return None

    last_Version, _ = findLastVersion(dosAsset)
    extention = None
    if departement == "Rigging":
        extention = "ma"
    elif departement == "toRig":
        extention = "usdc"
    
    last_file = f"{nameSpace}_{departement}_{last_Version}.{extention}"
    fileRef = rf"{Projet}03_Production/Assets/{Type}/{nameSpace}/Export/{departement}/{last_Version}/{last_file}"
    if not os.path.exists(fileRef):
        error("ERROR path not foud.........................")
        error(fileRef)
        fileRef = None
    
    return fileRef

def findLastVersion(path):
        max_version = -1
        latest_file = None
        version = 0
        for filename in os.listdir(path):
            if not filename or not filename.startswith("v"):
                continue

            v = re.findall(r'\d+', filename)[0]
            version = int(v)
            if version > max_version:
                max_version = version
                latest_file = filename

        return latest_file, version

def findRefInScene():
    refNodes = cmds.ls(type='reference')
    data_ref_in_scene = {}
    element_in_scene = []
    for refNode in refNodes:
        if refNode == "sharedReferenceNode":
            continue
        
        try:
            file_path = cmds.referenceQuery(refNode, f=True, wcn=True)
        except:
            continue
        
        try:
            asset = file_path.split("/")[-5]
            cat = file_path.split("/")[-6]
        except:
            error("impossible to find asset and asset Type for :" + refNode)
            continue
        
        if asset in element_in_scene:
            data_ref_in_scene[cat][asset].append(refNode)
        else:
            if cat in data_ref_in_scene:
                data_ref_in_scene[cat][asset] = [refNode]
                element_in_scene.append(asset)
            else:
                data_ref_in_scene[cat] = {asset:[refNode]}
                element_in_scene.append(asset)

    return data_ref_in_scene

def makeDifference(dataInScene, dataRef):
    for cat in dataInScene:
        for asset in dataInScene[cat]:
            if not cat in dataRef:
                continue
            if not asset in dataRef[cat]:
                continue

            new_nmb = dataRef[cat][asset] - len(dataInScene[cat][asset])
            if new_nmb <= 0:
                del dataRef[cat][asset]
            else:
                dataRef[cat][asset] = new_nmb

def createLastScene(PathScene):
    def findLastVersionScene(path, scene):
        max_version = -1
        latest_file = None
        version = 0
        for filename in os.listdir(path):
            if not filename:
                continue
            if not filename.startswith(scene) or not filename.endswith(".ma"):
                 continue

            v = re.findall(r'\d+', filename.split("_")[-1])[0]
            version = int(v)
            if version > max_version:
                max_version = version
                latest_file = filename
        
        name_scene = "_".join(latest_file.split("_")[:-1]) + "_v" + str(max_version + 1).zfill(3) + ".ma"
        return name_scene
    
    splitPath = PathScene.split("\\")[:-1]
    scene = "_".join(PathScene.split("\\")[-1].split("_")[:-1])
    folderPath = "\\".join(splitPath)
    new_scene = findLastVersionScene(folderPath, scene)

    return folderPath + "\\" + new_scene

def hierarchie():
    refInScene = findRefInScene()
    #------------------WIP------------------
    for cat in refInScene:
        for asset in refInScene[cat]:
            for reference in refInScene[cat][asset]:
                all_ref = cmds.referenceQuery(reference, nodes=True, dp=True)
                if not all_ref:
                    continue
                    
                all_nodes = [n for n in all_ref if cmds.nodeType(n) == 'transform' and not n.count('|')>= 2]
                if not all_nodes:
                    continue
                
                nodes_root = [root for root in all_nodes if not cmds.listRelatives(root, parent=True, fullPath=True)]
                if not nodes_root:
                    continue

                for node in nodes_root:
                    try:
                        if departement == "Rigging":
                            parent = None
                            if "camRig" in reference or "camRig" in asset:
                                parent = "cameras"
                            else:
                                parent = f"assets|{cat.lower()}"

                            infoP(f'hierarchie of {node} in {parent}')
                            cmds.parent(node, parent)
                        
                        elif departement == "toRig":
                            infoP(f'hierarchie of rig in {node}')
                            cmds.parent("rig", node)
                        
                        else:
                            infoP("no department find to connect hierarchie")
                        
                    except:
                        error(f"impossible de parenter : {node}")



def ImportReference(Projet, dataRef):
    for cat in dataRef:
        for name in dataRef[cat]:
            nameSpace = name + "_" + departement
            if departement == "toRig":
                nameSpace = ":"
            
            ref_path = findLastScene(Projet, name, cat)
            if not ref_path:
                infoP(f"no path found for {cat}->{name}")
                continue

            for _ in range(dataRef[cat][name]):
                try:
                    cmds.file(ref_path, reference=True, namespace=nameSpace)
                    infoP(f"Référence importée avec le namespace '{nameSpace}': {ref_path}\n")
                except Exception as e:
                    error(f"\Erreur lors de l'import de la référence: {e}\n")

def UpdateReference(Projet, refInScene):
    for cat in refInScene:
        for asset in refInScene[cat]:
            for refNode in refInScene[cat][asset]:
                last_scene = findLastScene(Projet, asset, cat)
                if not last_scene:
                    continue
                scene_split = cmds.referenceQuery(refNode, f=True, wcn=True)
                if last_scene == scene_split:
                    continue
                try:
                    cmds.file(last_scene, loadReference=refNode)
                    infoP(f"Référence Update  new scene: {last_scene}\n")
                except Exception as e:
                    error(f"Erreur lors de l'import de la référence :{last_scene} {e}\n")


def CoreStandalone():
    if catch_error(dataEnv):
        return False
    
    scene = dataEnv["Scene"]
    if not os.path.isfile(scene):
        infoP("no scene find")
        return False

    infoP('\n\n\n\nSTART ------------------------------ILLOGIC REFERENCE UPDTE/IMPORT------------------------------------')
    if dataEnv["standalone"]:
        infoP("//ILLOGIC    Open scene...")
        cmds.file(scene, open=True, force=True, loadReferenceDepth="none")

    infoP("\n//ILLOGIC------------    find Reference in the scene...")
    refInScene = findRefInScene()

    infoP("assets en référence présent dans la scene:")
    MSG = ""
    for cat in refInScene:
        MSG += "\n" + cat
        for i in refInScene[cat]:
            MSG +=  "\n" + str(len(refInScene[cat][i])) + "x " + i
    MSG += "\n\n"
    infoP(MSG)
    

    if dataEnv["Update"]:
        infoP("\n//ILLOGIC------------    Update all reference...")
        UpdateReference(dataEnv["Projet"], refInScene)


    if dataRef:
        infoP("\n//ILLOGIC------------    import Reference...")
        if dataEnv["addition"]:
            makeDifference(refInScene, dataRef)
        ImportReference(dataEnv["Projet"], dataRef)

    infoP("\n//ILLOGIC------------    make hierarchie...")
    hierarchie()

    if dataEnv["standalone"]:
        infoP("\n//ILLOGIC------------    save scene...")
        try:
            new_file = createLastScene(scene)
            cmds.file(rename=new_file)
            cmds.file(save=True, type='mayaAscii')
        except Exception as e:
            error(e)
            pass
    

    infoP('\n\nEnd   ------------------------------ILLOGIC REFERENCE UPDTE/IMPORT------------------------------------\n\n')

    if dataEnv["DEBUG"]:
        infoP("\nAppuyez sur Entrée pour continuer..")
        msvcrt.getch()

    return True

if __name__ == "__main__":
    if dataEnv["standalone"]:
        import maya.cmds as cmds
        maya.standalone.initialize(name='python')
        import pymel.core as pm

    CoreStandalone()

    if dataEnv["standalone"]:
        maya.standalone.uninitialize()


