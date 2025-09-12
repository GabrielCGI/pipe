import maya.cmds as cmds
import maya.standalone
import msvcrt
import sys
import re
import os



def infoP(msg):
    print(msg, file=sys.stdout)

def error(msg):
    print(msg)
    print("ILLOGIC ERROR : " + msg, file=sys.stderr)

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
    dosAsset = rf"{Projet}/03_Production/Assets/{Type}/{nameSpace}/Export/Rigging"
    versionUSD = None
    fileRef = None
    if not os.path.exists(dosAsset):
        return None

    lastVersion, _ = findLastVersion(dosAsset)
    for filename in os.listdir(dosAsset + "/" + lastVersion):
        if filename.startswith(f"{nameSpace}_Rigging_{lastVersion}.ma"):
            versionUSD = filename
    
    fileRef = rf"{Projet}/03_Production/Assets/{Type}/{nameSpace}/Export/Rigging/{lastVersion}/{versionUSD}"
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
    dataRefInscene = {}
    elementInScene = []
    for refNode in refNodes:
        try:
            file_path = cmds.referenceQuery(refNode, filename=True).split(".ma")[0] + ".ma"
        except:
            continue
        asset = file_path.split("/")[-5]
        cat = file_path.split("/")[-6]
        
        if asset in elementInScene:
            dataRefInscene[cat][asset].append(refNode)
        else:
            if cat in dataRefInscene:
                dataRefInscene[cat][asset] = [refNode]
                elementInScene.append(asset)
            else:
                dataRefInscene[cat] = {asset:[refNode]}
                elementInScene.append(asset)

    return dataRefInscene

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

def hierarchie():
    refInScene = findRefInScene()
    if not cmds.objExists("|assets"):
        cmds.createNode("transform", n="assets", ss=True)
    if not cmds.objExists("|assets|characters"):
        cmds.createNode("transform", n="characters", ss=True, p="|assets")
    if not cmds.objExists("|assets|props"):
        cmds.createNode("transform", n="props", ss=True, p="|assets")

    #------------------WIP------------------
    for cat in refInScene:
        for asset in refInScene[cat]:
            for reference in refInScene[cat][asset]:
                Nodes = cmds.referenceQuery(reference, nodes=True, dp=True)
                if not Nodes:
                    continue

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


def ImportReference(Projet, dataRef):
    for cat in dataRef:
        for name in dataRef[cat]:
            nameSpace = name + "_Rigging"
            ref_path = findLastScene(Projet, name, cat)
            if not ref_path:
                continue

            for i in range(dataRef[cat][name]):
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

                if last_scene == cmds.referenceQuery(refNode, filename=True).split(".ma")[0] + ".ma":
                    continue
                try:
                    cmds.file(last_scene, loadReference=refNode)
                    infoP(f"Référence Update  new scene: {last_scene}\n")
                except Exception as e:
                    error(f"\Erreur lors de l'import de la référence: {e}\n")





def CoreStandalone():
    dataEnv = eval(sys.argv[1])
    dataRef = eval(sys.argv[2])
    sys.stdout = open('CONOUT$', 'w')
    sys.stderr = open('CONOUT$', 'w')
    sys.stdin = open('CONIN$', 'r')

    if catch_error(dataEnv):
        return False
    
    scene = dataEnv["Scene"]
    if not os.path.isfile(scene):
        return False

    infoP('\n\n\n\nSTART ------------------------------ILLOGIC REFERENCE UPDTE/IMPORT------------------------------------')
    infoP("//ILLOGIC    open the scene without loading reference...")
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

    infoP("\n//ILLOGIC------------    organise hierarchie...")
    hierarchie()

    infoP("\n//ILLOGIC------------    save scene...")
    try:
        new_file = createLastScene(scene)
        print("scene save :", new_file)
        cmds.file(rename=new_file)
        cmds.file(save=True, type='mayaAscii')
    except Exception as e:
        pass

    infoP('\n\nEnd   ------------------------------ILLOGIC REFERENCE UPDTE/IMPORT------------------------------------\n\n')

    if dataEnv["DEBUG"]:
        infoP("\nAppuyez sur Entrée pour continuer..")
        msvcrt.getch()

    return True




maya.standalone.initialize(name='python')
result = CoreStandalone()
if not result:
    sys.exit(1)
maya.standalone.uninitialize()