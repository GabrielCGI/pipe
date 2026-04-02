from pathlib import Path
import maya.cmds as cmds
import json
import sys
import re
import os 



DATA_PARSE = os.path.join(Path(os.path.dirname(__file__)).parent, "configs", "parser_data.json")


class RefUpdaterCore():
    def __init__(self, standalone, projet_path, file_path: str=None):
        self.standalone = standalone
        self.file_path = self.findScenePath(file_path)
        self.reference_in_scene = {}
        self.projet_path = projet_path.replace("\\", "/")
        self.Data_in_scene = None

    def ExecutionProcedure(self, data_update: dict, compare=False):
        if self.standalone:
            self.startStandalone()
        
        #Récuéré tout les info des références dans la scene
        self.Data_in_scene = self.findAssetsInScene()[0]

        # start process to import and update reference.
        if "import" in data_update:
            self.ImportNewReference(data_update["import"], compare)
        else:
            self.emitdata("no import found")
        if "update" in data_update:
            self.UpdateReference(data_update["update"])
        else:
            self.emitdata("no update found")

        # organise the herarchie in the scene
        self.makeHerarchie()

        if self.standalone:
            self.EndStandalone()
        

    def findAssetsInScene(self) -> list[dict, str]:
        refNodes = cmds.ls(type='reference')
        data_ref_in_scene = {"Shots":{}, "Assets":{}}

        nmb_ref = 0
        for refNode in refNodes:
            if refNode == "sharedReferenceNode":
                continue
            try:
                reference_path = cmds.referenceQuery(refNode, f=True, wcn=True)
            except Exception as e:
                self.emitdata(str(e))
                continue

            if not reference_path:
                continue
            
            reference_path = reference_path.replace("\\", "/")
            if "/03_Production/" not in reference_path:
                continue

            entity = reference_path.split(f"{self.projet_path}03_Production/")[-1].split("/")
            Type = data_ref_in_scene.setdefault(entity[0], {})
            cat = Type.setdefault(entity[1], {})
            item = cat.setdefault(entity[2], {})

            if entity[4] not in item:
                item[entity[4]] = {"ref":[refNode], "version":[entity[5]]}
            else:
                item[entity[4]]["ref"].append(refNode)
                item[entity[4]]["version"].append(entity[5])

            nmb_ref +=1

        return data_ref_in_scene, nmb_ref
    
    def makeHerarchie(self):
        self.Data_in_scene = self.findAssetsInScene()[0]
        for info in self.iteration_Data(self.Data_in_scene):
            if info["Type"] == "Shots":
                continue
            data_hide = self.dataHide("procedure", "no_hiearchie")
            if data_hide:
                if info["item"] in data_hide[info["Type"]]:
                    continue
            
            if info["entity"] == "toRig" and cmds.objExists(info["item"]):
                cmds.parent("rig", "|" + info["item"])
            elif info["item"] == "camRig" and cmds.objExists(info["item"]):
                cmds.parent(info["item"], "cameras")
                
            else:
                # creer le grp root de la scene 
                grp_type = info["Type"].lower()
                if not cmds.objExists(grp_type):
                    grp_type = self.createNodeAtttr(grp_type, "Scope", True, "")
                
                # creer le grp de la quategorie de l'asset 
                grp_cat = info["cat"].lower()
                if not cmds.objExists(grp_cat):
                    grp_cat = self.createNodeAtttr(grp_cat, "Scope", False)
                    if grp_cat not in data_hide["cat"]:
                        cmds.parent(grp_cat, grp_type)
                

                # récupéré tout les node d'une reference 
                all_ref = cmds.referenceQuery(info["reference"], nodes=True, dp=True)
                if not all_ref:
                    continue
                all_nodes = [n for n in all_ref if cmds.nodeType(n) == 'transform' and not n.count('|')>= 2]
                if not all_nodes:
                    continue
                
                # parmie tout les node des references reccuperer tout les node qui sont aux root pour les ranger apres
                nodes_root = [root for root in all_nodes if not cmds.listRelatives(root, parent=True, fullPath=True)]
                if not nodes_root:
                    continue
                
                for node in nodes_root:
                    grp_item = self.createNodeAtttr(info["item"], "Scope", False)
                    location = cmds.parent(grp_item, grp_cat)
                    cmds.parent(node, location)

    def makeDifference(self):
        if not self.Data_in_scene:
            self.Data_in_scene = self.findAssetsInScene()[0]
        
        datacompare = {}
        for info in self.iteration_Data(self.Data_in_scene):
            if info["item"] not in datacompare:
                datacompare[info["item"]] = 1
            else:
                datacompare[info["item"]] += 1

        return datacompare
    
    def cantImport(self, info, datacompare):
        if info["item"] in datacompare:
            if datacompare[info["item"]] > 0:
                datacompare[info["item"]] - 1
                return True

        return False


    # ---------------------- update et import reference in the scene ----------------------
    def ImportNewReference(self, data: dict, compare: bool) -> None:
        if not data:
            return
        
        datacompare = {}
        if compare:
            datacompare = self.makeDifference()

        for info in self.iteration_Data(data):
            if self.cantImport(info, datacompare):
                continue

            # ---------------- get file product -------------------
            file_path, showPath = self.findFile(info)
            if file_path is None:
                self.emitdata(f"--- path not Found: {showPath[0]}/{showPath[1]}/<file>")
                continue
            
            try:
                cmds.file(file_path, reference=True, namespace=info["reference"])
                self.emitdata(f"Référence importée avec le namespace: {info['reference']}, file: {file_path}\n")
            except Exception as e:
                self.emitdata(f"\Erreur lors de l'import de la référence: {e}\n")

    def UpdateReference(self, data: dict) -> None:
        if not data:
            return
        
        refNodes = cmds.ls(type='reference')
        for info in self.iteration_Data(data):
            if info["reference"] not in refNodes:
                continue

            # ---------------- get file product -------------------
            file_path, showPath = self.findFile(info)
            if file_path is None:
                self.emitdata(f"--- path not Found: {showPath[0]}/{showPath[1]}/<file>")
                continue
            
            # --------------- Recuperer le path de la reference pour la comparer avec le file_path trouver ---------------
            reference_path = cmds.referenceQuery(info["reference"], f=True, wcn=True)
            if not reference_path:
                continue
            reference_path = reference_path.replace("\\", "/")
            if file_path == reference_path:
                continue

            try:
                cmds.file(file_path, loadReference=info["reference"])
                self.emitdata(f"Référence Update  new scene: {file_path}\n")
            except Exception as e:
                self.emitdata(f"Erreur lors de l'import de la référence :{file_path} {e}\n")


    # ---------------------------------- METHODE COMMUN ----------------------------------
    def findFile(self, info):
        path = f'{self.projet_path}03_Production/{info["Type"]}/{info["cat"]}/{info["item"]}/Export/{info["entity"]}'
        if not os.path.exists(path):
            return None, [path, None]
        
        version = info['version']
        if version == "latest":
            version = self.findElement(path, info["Type"], "", True)
            if version is not None:
                version = version[-1]


        file = None
        if info["Type"] == "Assets":
            file = f'{info["item"]}_{info["entity"]}_{version}'
        elif  info["Type"] == "Shots":
            file = f'{info["cat"]}-{info["item"]}_{info["entity"]}_{version}'

        folder_path = f'{path}/{version}'
        for f in os.listdir(folder_path):
            if not f.startswith(file):
                continue
            for extention in self.dataHide("procedure", "extention_valide"):
                if f.endswith(extention):
                    return f'{path}/{version}/{f}', [path, version] 
        
        return None, [path, version] 
    
    def findScenePath(self, file_path):
        if file_path is None:        
            file_path = cmds.file(q=True, sn=True)
            if not file_path:
                return None

        elif not os.path.exists(file_path):
            return None
        
        return file_path

    def iteration_Data(self, data_in_scene: dict[dict]):
        for Type in data_in_scene:
            for cat in data_in_scene[Type]:
                for item in data_in_scene[Type][cat]:
                    for entity in data_in_scene[Type][cat][item]:
                        for i, reference in enumerate(data_in_scene[Type][cat][item][entity]["ref"]):
                            yield {
                            "Type": Type,
                            "cat": cat,
                            "item": item,
                            "entity": entity,
                            "reference": reference,
                            "version": data_in_scene[Type][cat][item][entity]["version"][i]
                            }

    def dataHide(self, Type: str, data_find:str) -> list[str]:
        if not DATA_PARSE:
            return []
        
        json_data = None
        with open(DATA_PARSE, "r") as f:
            json_data:dict = json.loads(f.read())
        
        if not json_data:
            return []
        
        return json_data[Type].get(data_find, [])
    
    def findElement(self, path: str, Type: str, data_find: str, only_folder=False) -> list[str]:
        if not os.path.exists(path):
            self.emitdata(f"le chemin: {path} n'est pas trouvable")
            return None
        
        good_product = []
        for product in os.listdir(path):
            if only_folder and not os.path.isdir(f"{path}/{product}"):
                continue
            if product in self.dataHide(Type, data_find):
                continue
            good_product.append(product)
        
        if not good_product:
            return None
        
        return good_product

    def createNodeAtttr(self, name: str, typeName: str, create_kine: bool, kind=None) -> str:
        grp = cmds.createNode("transform", n=name, ss=True)
        cmds.addAttr(grp, longName="USD_typeName", niceName="typeName", dataType="string")
        cmds.setAttr(grp + ".USD_typeName", typeName, type="string")
        if kind:
            cmds.addAttr(grp, longName="USD_kind", niceName="kind", dataType="string")
            cmds.setAttr(grp + ".USD_kind", kind, type="string")

        return grp
    


    # ----------------------- methode pour les execution en standalone ------------------
    def startStandalone(self):
        self.emitdata("--------------------------- START EXECUTION ----------------------------------")
        import maya.standalone
        maya.standalone.initialize(name='python')
        try:
            import pymel.core as pm
        except ImportError:
            sys.path.append(r"R:/pipeline/networkInstall/python_shares/python311_pymel_pkgs/Lib/site-packages/pymel")
            import pymel.core as pm

        if not os.path.exists(self.file_path):
            self.emitdata("la scene est n'existe pas")
            raise Exception("la scene est n'existe pas")

        self.emitdata("---- open scene:" + self.file_path)
        cmds.file(self.file_path, open=True, force=True, loadReferenceDepth="none")

    def EndStandalone(self):
        import maya.standalone
        new_file = self.createLastScene(self.file_path)

        self.emitdata("---- save scene here:" + new_file)
        cmds.file(rename=new_file)
        cmds.file(save=True, type='mayaAscii')

        maya.standalone.uninitialize()
        self.emitdata("--------------------------- END EXECUTION ----------------------------------")

    def createLastScene(self, PathScene):
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

        splitPath = PathScene.split("/")[:-1]
        scene = "_".join(PathScene.split("/")[-1].split("_")[:-1])
        folderPath = "/".join(splitPath)
        new_scene = findLastVersionScene(folderPath, scene)
        return folderPath + "/" + new_scene
    

    def emitdata(self, msg):
        print(f"SIGNAL:{msg}", flush=sys.stdout)