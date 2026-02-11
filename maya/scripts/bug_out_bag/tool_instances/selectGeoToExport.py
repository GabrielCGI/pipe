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

    def select_all_geo(self, parent):
        """cette fonction a pour but de seletctionner rapidement tous les dossier, qui s'appellent geo(en ignorant le namespace) et qui sont une reference"""
        hierarchy_nodes =cmds.listRelatives(parent, allDescendents=True, s=False, f=True)
        if hierarchy_nodes is None:
            return
        
        nodes_find = set()
        for node in hierarchy_nodes:
            if ":rig|" in node:
                continue
            elif node.endswith(":geo"):
                nodes_find.add(node)

        if nodes_find:
            cmds.select(nodes_find, add=True)

    def on_button_click(self,*args):
        cmds.select(clear=1)
        if cmds.checkBox('characters', query=True, value=True):
            self.select_all_geo('characters')
        if cmds.checkBox('props', query=True, value=True):
            self.select_all_geo('props')
        """if cmds.checkBox('world', query=True, value=True):
            self.select_all_geo('world')"""
        if cmds.checkBox('sets', query=True, value=True):
            self.select_all_geo('sets')

    def run(self):

        if cmds.window('selectGeoUI', exists=True):
            cmds.deleteUI('selectGeoUI')
        window = cmds.window('selectGeoUI', title='Select geo', widthHeight=(300, 150))
        cmds.columnLayout(adjustableColumn=True)

        cmds.text('result_label', label='Select checkboxes and click Select')
        cmds.text('gap',label='\n\n')
        # cmds.checkBox('world', label=f'all')
        cmds.checkBox('characters', label=f'Characters', value=True)
        cmds.checkBox('props', label=f'Props', value=True)
        cmds.checkBox('sets', label=f'Sets', value=False)

        cmds.button(label='Select', command=self.on_button_click)

        cmds.showWindow(window)
