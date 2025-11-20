from importlib import reload
from pxr import Usd, Sdf
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
    print("USD CHASER: parse find USD")
    #ouvrir et parcourir toute les prim pour récupéré leur path
    layer = Sdf.Layer.FindOrOpen(file_path_usd)
    layer.Traverse(layer.pseudoRoot.path, feachAllPrim)

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
            
            # supprimer tout les attribute qui constitue le mesh pour tout les mesh qui non pas de time samplings uniquement eux
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
            
    
    # cette etape est la pour supprimer les primitives qui sont des geomSubnet pour enlver tout les bindmaterial qui sont efectuer par face et non pas a l'enssemble de l'objet
    if all_geomSubnet_to_delet:
        edit = Sdf.BatchNamespaceEdit()
        for p in all_geomSubnet_to_delet:
            edit.Add(p, Sdf.Path.emptyPath)
            print(p, '\nGeomSubset deleted\n')
        
        layer.Apply(edit)
    
                
    layer.Save()
    del layer
    print("USD CHASER: layer saved")
    #startInheriteClass(stateManager)
    print("//------------USD CHASER: finish Script------------")

def startInheriteClass(core):
    print("USD CHASER: create and inherte class")
    # en premier lieux récuperer la dernière version du container USD
    path_scene = core.getCurrentFileName()
    entity = core.getScenefileData(path_scene)
    last_usd_container = core.products.getLatestVersionFromProduct("USD", entity=entity)
    if not last_usd_container:
        return None

    file_usd = f'{str(last_usd_container["sequence"])}-{str(last_usd_container["shot"])}_{str(last_usd_container["product"])}_{str(last_usd_container["version"])}.usda'
    file_path_usd = f'{str(last_usd_container["path"])}/{file_usd}'
    if not os.path.exists(file_path_usd):
        return
    
    #ensuite on import l'outil inherite class qu'on run en lui donnant le path du dernier fichier usd du shot actuelle
    sys.path.append("R:\pipeline\pipe\houdini\scripts")
    import inheriteClassVariant as icv
    reload(icv)
    inClass = icv.inheriteClassAttr(file_path_usd, "Maya")

    #afficher un message suivant le type d'erreur que va nous retourner l'inherite class
    core.popup(inClass.message, severity=inClass.error_type)