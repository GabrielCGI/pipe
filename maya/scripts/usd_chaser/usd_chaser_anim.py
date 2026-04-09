from importlib import reload
from pxr import Usd, Sdf, Vt
import socket
import sys
import os



ALL_PRIM_PATH = []



# fonction pour parser tout les primitive dans le fichier usd
def feachAllPrim(path):
    if path.IsPrimPath():
        ALL_PRIM_PATH.append(path)

def main(file_path_usd):
    if not os.path.exists(file_path_usd):
        return False

    print("//------------USD CHASER: Start Script------------")
    print("---USD CHASER: parse find USD")
    #ouvrir et parcourir toute les prim pour récupéré leur path
    layer = Sdf.Layer.FindOrOpen(file_path_usd)
    layer.Traverse(layer.pseudoRoot.path, feachAllPrim)

    print("\n\n---USD CHASER: delete Primitive Attribute")
    deleteunUsedData(layer)

    if "I:/mikes_2511/03_Production" in file_path_usd.replace("\\", "/"):
        print("\n\n---USD CHASER: add Scale info")
        addScaleInfo(layer, ["*:Main*", "*:ctrl_world*", "*:World_Ctr*"], ["globalScale"], "primvars:globalScale")
        addScaleInfo(layer, ["*:Walk_Ctr*"], ["scaleY"], "primvars:WalkCtr")
        print("\n\n---USD CHASER: add Scale info")
    elif "I:/McDonald_2511/03_Production" in file_path_usd.replace("\\", "/"):
        addScaleInfo(layer, ["*:Rabbit_Root_Ctrl", "*:Bear_Root_Ctrl"], ["scaleY"], "primvars:globalScale")
    elif "I:/rivers_feature/03_Production" in file_path_usd.replace("\\", "/"):
        addScaleInfo(layer, ["*:Main*"], ["scaleY"], "primvars:globalScale")

    layer.Save()
    del layer
    print("\n\n---USD CHASER: layer saved")


# -------------------------------- ajouter les info du scale des ctrl dans le layer usd --------------------------------
def addScaleInfo(layer: Sdf.Layer, target_names, target_attrs, name_attr_USD):
    import maya.cmds as cmds
    all_node_maya_with_scale = {}
    for name in target_names:
        matches = cmds.ls(name, long=True, typ=["transform"])
        for node in matches:
            for attr in target_attrs:
                has_attr = cmds.attributeQuery(attr, node=node, exists=True)
                if has_attr:
                    print(node, 'found')
                    path_node = converteWithoutNameSpace(node)
                    data_frames = getKeyFrameValue(node, attr)
                    print("data maya", path_node, "\n", data_frames, "\n\n\n")
                    all_node_maya_with_scale[path_node] = data_frames

    if not all_node_maya_with_scale:
        print("-value not found")
        return False
    
    for prim_Path in ALL_PRIM_PATH:
        primSpec = layer.GetPrimAtPath(prim_Path)
        if not primSpec:
            continue
        if primSpec.kind != "component":
            continue            
        
        for node_path in all_node_maya_with_scale:
            if primSpec.path.pathString in node_path.replace("|", "/"):
                writeDataInPrimitive(layer, primSpec, name_attr_USD, all_node_maya_with_scale[node_path])

def converteWithoutNameSpace(node_name):
    name = ""
    for part in node_name.split("|")[1:]:
        name += "|" + part.split(":")[-1]
    
    return name

def getKeyFrameValue(node_name, attr):
    import maya.cmds as cmds
    
    result = {}
    curve = cmds.listConnections(node_name + "." + attr, type="animCurve")
    if curve:
        connections = cmds.listConnections(curve[0], plugs=True, destination=True)
        if not connections:
            return
        start = int(cmds.playbackOptions(q=True, min=True))
        end   = int(cmds.playbackOptions(q=True, max=True))
        
        for frame in range(start, end + 1):
            value = cmds.keyframe(curve[0], query=True, eval=True, time=(frame, frame))
            if value:
                result[frame] = value[0]
    else:
        result[1001] = cmds.getAttr(node_name + "." + attr)
    
    return result

def writeDataInPrimitive(layer: Sdf.Layer, primSpec: Sdf.PrimSpec, name_attr_USD: str, data_ctrl):
    attr_spec = layer.GetAttributeAtPath(primSpec.path.__str__() + "." + name_attr_USD)
    if attr_spec is None:
        attr_spec = Sdf.AttributeSpec(primSpec, name_attr_USD, Sdf.ValueTypeNames.Double)
        attr_spec.custom = True
    #print("time sampling")
    for frame, value in data_ctrl.items():
        #print("frame:", frame, "value: ", value)
        layer.SetTimeSample(attr_spec.path, float(frame), float(value))



# -------------------------------- delete tout les attribute qui ne sont pas utile dans le layer --------------------------------
def deleteunUsedData(layer: Sdf.Layer):
    all_geomSubnet_to_delet = []
    for prim_Path in ALL_PRIM_PATH:
        primSpec = layer.GetPrimAtPath(prim_Path)
        if not primSpec:
            continue
        
        #enlever le kink component que maya met par defaut pour tout les premier qui se trouve aux root du fichier usd
        if prim_Path == "/assets":
            primSpec.ClearKind()

        if primSpec.typeName == 'Mesh':
            # enlever la 'properties' subdivisionScheme pour absolument tout le smesh
            if "subdivisionScheme" in primSpec.properties:
                del primSpec.properties["subdivisionScheme"]
            
            # verifier si il y a une "klé" / du time sampling dans le mesh si il n'y en a pas on continue
            keyTime = layer.ListTimeSamplesForPath(str(prim_Path) + ".points")
            if keyTime:
                print(prim_Path, '\nis deformed keep geo\n')
                continue
            
            # supprimer tout les attribute qui constitue le mesh pour tout les mesh qui non pas de time samplings uniquement eux (donc les objet non skinner)
            if "faceVertexCounts" in primSpec.properties:
                del primSpec.properties["faceVertexCounts"]
            if "faceVertexIndices" in primSpec.properties:
                del primSpec.properties["faceVertexIndices"]
            if "points" in primSpec.properties:
                del primSpec.properties["points"]
            if "normals" in primSpec.properties:
                del primSpec.properties["normals"]

        elif primSpec.typeName == 'GeomSubset':
            all_geomSubnet_to_delet.append(prim_Path)
            
    
    # cette etape est la pour supprimer les primitives qui sont des geomSubnet pour enlver tout les bindmaterial qui sont effectuer par face et non pas a l'enssemble de l'objet
    if all_geomSubnet_to_delet:
        edit = Sdf.BatchNamespaceEdit()
        for p in all_geomSubnet_to_delet:
            edit.Add(p, Sdf.Path.emptyPath)
            print(p, '\nGeomSubset deleted\n')
        
        layer.Apply(edit)



# ----------------------------------------- démmarrer le script pour le inherite class -----------------------------------------
def startInheriteClass(core):
    print("USD CHASER: create and inherte class")
    # en premier lieux récuperer la dernière version du container USD
    path_scene = core.getCurrentFileName()
    entity = core.getScenefileData(path_scene)
    last_usd_container = core.products.getLatestVersionFromProduct("USD", entity=entity)
    if not last_usd_container:
        return None
    
    
    force_asset = False
    if last_usd_container["type"] == "asset":
        force_asset = True
        file_usd = f'{str(last_usd_container["asset"])}_{str(last_usd_container["product"])}_{str(last_usd_container["version"])}.usda'
    else:
        file_usd = f'{str(last_usd_container["sequence"])}-{str(last_usd_container["shot"])}_{str(last_usd_container["product"])}_{str(last_usd_container["version"])}.usda'
    
    file_path_usd = f'{str(last_usd_container["path"])}/{file_usd}'
    if not os.path.exists(file_path_usd):
        return
    
    #ensuite on import l'outil inherite class qu'on run en lui donnant le path du dernier fichier usd du shot actuelle
    sys.path.append("R:\pipeline\pipe\houdini\scripts")
    import inheriteClassVariant as icv
    reload(icv)
    inClass = icv.inheriteClassAttr(file_path_usd, "Maya", forceAsset = force_asset)

    #afficher un message suivant le type d'erreur que va nous retourner l'inherite class
    core.popup(inClass.message, severity=inClass.error_type)