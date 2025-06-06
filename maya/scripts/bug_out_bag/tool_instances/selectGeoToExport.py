import maya.cmds as cmds

from ..tool_models.MultipleActionTool import *
from pxr import Usd, Sdf
import maya.cmds as cmds
import mayaUsd
import tempfile
import os

TMP_FILE_NAME = "USD_Maya_copy_paste_script_tmp.usda"

class GeoExport(MultipleActionTool):
    def __init__(self):
        actions = {
            "select_geo_to_export": {
                "text": "Select Geo To Export",
                "action": self.run,
                "row": 0
            }
        }
        tooltip = "this will select all the geo group in your props and chara"
        super().__init__(
            name="Select Geo To Export",
            pref_name="select_geo_to_export",
            actions=actions, stretch=1, tooltip=tooltip)

    def select_all_geo(self,parent):
        """cette fonction a pour but de seletctionner rapidement tous les dossier, qui s'appellent geo(en ignorant le namespace) et qui sont une reference"""
        geo_objects = []
        real_geoObject=[]
        dag_nodes = cmds.ls(dag=True)
        for node in dag_nodes:
            if 'geo' in node: geo_objects +=[node]

        for geo_object in geo_objects:
            parts=geo_object.split(":")
            for part in parts:
                if part == "geo":
                    real_geoObject.append(geo_object)
        print(real_geoObject)

        hierarchy_nodes =cmds.listRelatives(parent, allDescendents=True, )
        if hierarchy_nodes:
            hierarchy_nodes.append(parent)
            print(hierarchy_nodes)
            print(real_geoObject)
            filtered_nodes = [node for node in real_geoObject if node in hierarchy_nodes]
            # Sélectionner les objets filtrés
            if filtered_nodes:
                cmds.select(filtered_nodes, add=1)
                print(f"Les objets suivants ont été sélectionnés: {filtered_nodes}")
            else:
                print("Aucun objet contenant 'geo' dans le nom n'a été trouvé.")
        else : print(f"{parent} n'a pas d'enfants")

    def on_button_click(self,*args):
        cmds.select(clear=1)
        if cmds.checkBox('characters', query=True, value=True):
            self.select_all_geo('characters')
        if cmds.checkBox('props', query=True, value=True):
            self.select_all_geo('props')
        if cmds.checkBox('world', query=True, value=True):
            self.select_all_geo('world')
        if cmds.checkBox('Sets', query=True, value=True):
            self.select_all_geo('Sets')

    def run(self):

        if cmds.window('selectGeoUI', exists=True):
            cmds.deleteUI('selectGeoUI')
        window = cmds.window('selectGeoUI', title='select geo', widthHeight=(300, 150))
        cmds.columnLayout(adjustableColumn=True)

        cmds.text('result_label', label='Select checkboxes and click Submit')
        cmds.text('gap',label='')
        cmds.checkBox('world', label=f'all')
        cmds.text('gap2',label='')
        cmds.checkBox('characters', label=f'Characters', value=True)
        cmds.checkBox('props', label=f'Props', value=True)
        cmds.checkBox('Sets', label=f'Sets', value=False)

        cmds.button(label='select', command=self.on_button_click)

        cmds.showWindow(window)
