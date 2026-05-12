"""un outils pour permet d'exporter tout les variant un as un avec le bon variant et le bon rig 
pour faire en sorte que tu ai une scene
"""

from importlib import reload
import maya.cmds as cmds
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

    def passPrePublish(self, force=False, autoExport=True):
        if cmds.about(batch=True):
            return
        
        have_variant = True
        self.findNameCtrlVariant()
        if not force:
            if not self.name_variant or not self.name_ctrl:
                return 
        
        data = self.getDataInScene("IllogicVariantRIG")
        if data is None:
            data, have_variant = self.getAutoData()
        
        if not have_variant:
            cmds.warning("test " + str(have_variant)+ " " + str(data))
            return None


        self.UI_select_relationShip_export(data)
        if self.result and not self.windowRig.bypass and autoExport:
            self.ExportDataInScene()
            #self.saveDataInScene("IllogicVariantRIG", self.windowRig.data_to_Export)
            #self.saveDataInScene("IllogicPathRIG", data_path)

    def execAfterImportReference(self):
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
            return None

        if data:
            self.data = data
            self.ExportDataInScene()


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
        print(convert_data)
        if not convert_data:
            return None
        return convert_data

    def saveDataInScene(self, dataType, data_to_save):
        #save les datas dans la scene ouvert
        cmds.fileInfo(dataType, json.dumps(data_to_save))

    def ExportDataInScene(self):
        all_last_version_product = []
        data_path = {}

        import socket
        if socket.gethostname() == "FALCON-01":
            from . import debug
            debug.debug()
            debug.debugpy.breakpoint()
        
        #trouver la plus grande version possible de creer pour faire en sorte que tout les variants on la meme last_version possible
        #pour eviter aux moment de changer les variant qu'il y ai pas de soucis de mélange entre les ancienne version des variant  
        for export in self.data:
            pur_name = "Rigging_" + export.split("|")[-1]
            folder_product = self.core.products.createProduct(self.entity, pur_name).replace("\\", "/")
            data_next_version = self.core.products.getNextAvailableVersion(self.entity, pur_name)
            all_last_version_product.append(data_next_version)

        real_next_version = sorted(all_last_version_product)[-1]

        have_set, _list_geo, _list_rig = self.findSet() 
        for export in self.data:
            pur_name = "Rigging_" + export.split("|")[-1]
            # creation est gestion des fichier via prism pour garder le workflow de prism
            folder_product = self.core.products.createProduct(self.entity, pur_name).replace("\\", "/")
            os.makedirs(folder_product + "/" + real_next_version, exist_ok=True) 
            file_path = f"{folder_product}/{real_next_version}/{self.name_asset}_{pur_name}_{real_next_version}.mb"


            #passer le attribute Variant avec le variant qu'on veux exporter comme sa quand le variant sera importer il aura l'attriubte bien setup
            all_variant_value = cmds.attributeQuery(self.name_variant, node=self.name_ctrl, listEnum=True)[0].split(":")
            nmb_variant = None
            for i, variant in enumerate(all_variant_value):
                if variant == export.split("|")[-1]:
                    nmb_variant = i
                    break

            if nmb_variant is None:
                cmds.warning(f"variant name not found: {str(nmb_variant)}, {str(all_variant_value)}")
                continue
            
            cmds.setAttr(f"{self.name_ctrl}.{self.name_variant}", nmb_variant)


            #récupéré la selection et les data pour exporter le rig
            shapes_to_add = self.detecShape(self.data[export]["rig"])
            sel = self.data[export]["geo"] + self.data[export]["rig"] + shapes_to_add
            cmds.select(sel)
            
            #reconstruire tout les set suivant le variant pour avoir un bon export
            if have_set:
                cmds.delete("all_set")
                self.constructionSets(self.data[export]["geo"], "geometry_set")
                self.constructionSets(self.data[export]["rig"] + shapes_to_add, "control_set")
                cmds.sets(["geometry_set", "control_set"],n= "all_set")
                cmds.select("all_set", noExpand=True ,add=True)
            

            cmds.file(file_path, type="mayaAscii", exportSelected=True, exportAsReference=False)

            #make dict for the next tap  to merge all file exported for each variant
            data_path[f"{self.name_asset}_{pur_name}_{data_next_version}RN"] = file_path
        

        #reconstruire tout les set comme c'était à l'origine pour permetre à prism d'export l'assets correctement
        if have_set:
            cmds.delete("all_set")
            cmds.delete("geometry_set")
            cmds.delete("control_set")
            cmds.sets(_list_geo, n="geometry_set")
            cmds.sets(_list_rig, n="control_set")
            cmds.sets(["geometry_set", "control_set"],n= "all_set")
        
        return data_path
    
    def findSet(self) -> tuple:
        have_set = False
        _list_geo = None
        _list_rig = None
        if cmds.objExists("all_set") and cmds.nodeType("all_set") == "objectSet":
            have_set = True
            cmds.select("control_set")
            _list_rig = cmds.ls(sl=True, l=True)
            cmds.select("geometry_set")
            _list_geo = cmds.ls(sl=True, l=True)
        
        return have_set, _list_geo, _list_rig
    
    def constructionSets(self, geo_shape, set_name):
        if cmds.objExists(set_name) and cmds.nodeType(set_name) == "objectSet":
            cmds.delete(set_name)

        good_geo = []
        for i in geo_shape:
            for child in cmds.listRelatives(i, s=False, ad=True, f=True):
                if cmds.nodeType(child) in ["mesh", "nurbsCurve"]:
                    shape = cmds.listRelatives(child, s=False, p=True, f=True)[0]
                    good_geo.append(shape)

        cmds.sets(good_geo, n=set_name)
        #cmds.parent(set, "all_set")
            
    def detecShape(self, nodes):
        add_shape = []
        for node in nodes:
            fullPath_parent = cmds.ls(node, long=True)[0]
            Parent = ""
            for child in fullPath_parent.split("|")[1:]:
                Parent += "|" + child
                if not Parent:
                    continue

                shapes = cmds.listRelatives(Parent, s=True)
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

        self.data.clear()
        # interface pour choisir si oui ou non on veux exporter telle modé avec telle variant
        self.windowRig = UI.UISelectExport(self.core, self.name_asset, data, outliner_widget, self.name_variant, self.name_ctrl, main_window)
        self.windowRig.exec()

        self.data =  self.windowRig.data_to_Export
        self.result = self.windowRig.resulte