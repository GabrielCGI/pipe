"""un outils pour permet d'exporter tout les variant un as un avec le bon variant et le bon rig 
pour faire en sorte que tu ai une scene
"""

from importlib import reload
import maya.cmds as cmds
from pathlib import Path
import json
import os



class splitVariantsRig():
    def __init__(self, core, path_scene):
        self.entity = core.getScenefileData(path_scene)
        self.name_asset = self.entity['asset']
        self.path_scene = path_scene
        self.name_variant = None
        self.name_ctrl = None
        self.result = True
        self.core = core
        self.data = {}

    def passPrePublish(self):
        if cmds.about(batch=True):
            return
        
        have_variant = True
        self.findNameCtrlVariant()
        if not self.name_variant or not self.name_ctrl:
            return 
        
        data = self.getDataInScene("IllogicVariantRIG")
        if data is None:
            data, have_variant = self.getAutoData()
        
        if not have_variant:
            cmds.warning("test " + str(have_variant)+ " " + str(data))
            return None
        
        self.UI_select_relationShip_export(data)
        if self.result and not self.windowRig.bypass:
            data_path = self.ExportDataInScene()
            #self.saveDataInScene("IllogicVariantRIG", self.windowRig.data_to_Export)
            #self.saveDataInScene("IllogicPathRIG", data_path)

    #--------------------------------- methode pass PostExport ---------------------------------
    def passPostExport(self):
        data = self.getDataInScene("IllogicPathRIG")
        if not data:
            return
        
        # reccuper le dernirer export de rigging pour re ecrire le products
        data_last_version = self.core.products.getLatestVersionFromProduct("Rigging", self.entity)
        product = data_last_version["product"]
        version = data_last_version["version"]
        asset = data_last_version["asset"]
        path = data_last_version["path"]

        path_packages = str(Path(os.path.abspath(__file__)).parent)
        new_scene_name = f"{asset}_{product}_{version}.ma"
        path_scene = f"{path}/{new_scene_name}"


        with open(f"{path_packages}/template_scene_rigging.ma", "r") as f:
            file_texte =f.read()
        
        # convertie les donner en mel script
        all_import_Reference = ""
        for i, reference in enumerate(data):
            if i == 0:
                all_import_Reference += f'file -rdi 1 -ns ":" -rfn "{reference}" -op "v=0;"\n'
                all_import_Reference += f'		 -typ "mayaAscii" "{data[reference]}";\n'
            else:
                all_import_Reference += f'file -rdi 1 -ns ":" -dr 1 -rfn "{reference}" -op "v=0;"\n'
                all_import_Reference += f'		  -typ "mayaAscii" "{data[reference]}";\n'
        
        for reference in data:
            all_import_Reference += f'file -r -ns ":" -dr 1 -rfn "{reference}" -op "v=0;" -typ "mayaAscii"\n'
            all_import_Reference += f'		 "{data[reference]}";\n'


        #edite le template pour correcpondre a l'assets
        file_texte = file_texte.replace("__nameScene__.ma", new_scene_name)
        file_texte = file_texte.replace("__insert__information__all_data__here__", all_import_Reference)

        #save le fichier aux bon endroits dans la pipe
        with open(path_scene, "w") as f:
            f.write(file_texte)





    #--------------------------------- methode pass PrePublish ---------------------------------
    def findNameCtrlVariant(self):
        #permet de trouver le bon controller world et de trouver le bon attribute qui à le bon nom
        self.name_variant = None
        self.name_ctrl = None
        for ctrl in  ["ctrl_world", "c_world", "World_Ctr", "world_Ctr"]:
            if cmds.objExists(ctrl):
                self.name_ctrl = ctrl
                break
        
        for attr in  ["Variant", "variant", "var"]:
            if cmds.objExists(f"{self.name_ctrl}.{attr}"):
                self.name_variant = attr
                break
    
    def getAutoData(self):
        if cmds.objExists(f'{self.name_asset}|rig'):
            rig = f'{self.name_asset}|rig'
        else:
            rig = None

        all_vairant = cmds.attributeQuery(self.name_variant, node=self.name_ctrl, listEnum=True)
        if all_vairant is None:
            return None, True
        

        data = {}
        for variant in all_vairant[0].split(":"):
            if cmds.objExists(variant):
                name_variant = cmds.ls(variant, long=True)
                data[variant] = {"rig": [rig], "geo": name_variant}
        
        return data, True

    def getDataInScene(self, dataType) -> dict[str]:
        # trouver les data save dans la scene pour les donner a l'UI
        data = cmds.fileInfo(dataType, q=True)
        if not data:
            return None

        convert_data = json.loads(data[0].encode().decode('unicode_escape'))
        if not convert_data:
            return None
        return convert_data

    def saveDataInScene(self, dataType, data_to_save):
        #save les datas dans la scene ouvert
        cmds.fileInfo(dataType, json.dumps(data_to_save))

    def ExportDataInScene(self):
        all_last_version_product = []
        data_path = {}

        #trouver la plus grande version possible de creer pour faire en sorte que tout les variants on la meme last_version possible
        #pour eviter aux moment de changer les variant qu'il y ai pas de soucis de mélange entre les ancienne version des variant  
        for export in self.data:
            pur_name = "Rigging_" + export.split("|")[-1]
            folder_product = self.core.products.createProduct(self.entity, pur_name).replace("\\", "/")
            data_next_version = self.core.products.getNextAvailableVersion(self.entity, pur_name)
            all_last_version_product.append(data_next_version)
            print(folder_product, data_next_version)

        real_next_version = sorted(all_last_version_product)[-1]


        for export in self.data:
            pur_name = "Rigging_" + export.split("|")[-1]
            # creation est gestion des fichier via prism pour garder le workflow de prism
            folder_product = self.core.products.createProduct(self.entity, pur_name).replace("\\", "/")
            os.makedirs(folder_product + "/" + real_next_version, exist_ok=True) 
            file_path = f"{folder_product}/{real_next_version}/{self.name_asset}_{pur_name}_{real_next_version}.ma"


            #passer le attribute Variant avec le variant qu'on veux exporter comme sa quand le variant sera importer il aura l'attriubte bien setup
            all_variant_value = cmds.attributeQuery(self.name_variant, node=self.name_ctrl, listEnum=True)[0].split(":")
            nmb_variant = None
            for i, variant in enumerate(all_variant_value):
                if variant == export.split("|")[-1]:
                    nmb_variant = i
                    break

            cmds.setAttr(f"{self.name_ctrl}.{self.name_variant}", nmb_variant)


            #récupéré la selection et les data pour exporter le rig
            shapes_to_add = self.detecShape(self.data[export]["rig"])
            sel = self.data[export]["geo"] + self.data[export]["rig"] + shapes_to_add
            cmds.select(sel)
            cmds.file(file_path, type="mayaAscii", exportSelected=True, exportAsReference=False)

            #make dict for the next tap  to merge all file exported for each variant
            data_path[f"{self.name_asset}_{pur_name}_{data_next_version}RN"] = file_path

        return data_path
            
    def detecShape(self, node):
        add_shape = []
        all_parent = reversed(cmds.ls(node, long=True)[0].split("|"))
        for parent in all_parent:
            parent_path = cmds.listRelatives(parent, parent=True, fullPath=True)
            if not parent_path:
                break

            shapes = cmds.listRelatives(parent_path, s=True)
            if not shapes:
                continue

            for i in shapes:
                add_shape.append(i)
        
        return add_shape

    def UI_select_relationShip_export(self, data: dict[str]):
        from . import ui_split_variant_selection as UI
        from PySide6.QtWidgets import QWidget
        from shiboken6 import wrapInstance
        from maya import OpenMayaUI
        reload(UI)

        # trouver la fenètre principale pour ratacher l'UI
        main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
        main_window = wrapInstance(int(main_window_ptr), QWidget)


        # récupéré tout les dag node de l'outliner pour le reconstruire dans mon UI et écupérer l’éditeur Outliner associé
        ptr = OpenMayaUI.MQtUtil.findControl(cmds.outlinerPanel())
        outliner_widget = wrapInstance(int(ptr), QWidget)
        cmds.refresh()


        # interface pour choirisir si oui ou non on veux exporter telle modé avec telle variant
        self.windowRig = UI.UISelectExport(self.core, self.name_asset, data, outliner_widget, self.name_variant, self.name_ctrl, main_window)
        self.windowRig.exec()

        self.data =  self.windowRig.data_to_Export
        self.result = self.windowRig.resulte