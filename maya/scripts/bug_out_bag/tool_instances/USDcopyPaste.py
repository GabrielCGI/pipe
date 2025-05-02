from ..tool_models.MultipleActionTool import *
from pxr import Usd, Sdf
import maya.cmds as cmds
import mayaUsd
import tempfile
import os

TMP_FILE_NAME = "USD_Maya_copy_paste_script_tmp.usda"

class USDCopyPaste(MultipleActionTool):
    def __init__(self):
        actions = {
            "Copy": {
                "text": "Copy",
                "action": self.__copy_USD_layer,
                "row": 0
            },
            "Paste": {
                "text": "Paste",
                "action": self.__paste_USD_layer,
                "row": 0
            }
        }
        tooltip = "Copy paste USD layer"
        super().__init__(
            name="USD Copy Paste",
            pref_name="usd_copy_paste",
            actions=actions, stretch=1, tooltip=tooltip)


    def __get_selected_stage(self):
        """
        Return the selected stage.
        """

        maya_stage_node = cmds.ls(selection=True, l=True)
        if not len(maya_stage_node):
            cmds.confirmDialog(
                title='No layer selected',
                message='Please select a layer',
                button=['OK'],
                defaultButton='OK'
            )
            cmds.warning('Please select a layer')
            print("Please select a layer")
            return None
        maya_stage_node = maya_stage_node[0]

        asset_stage = mayaUsd.ufe.getStage(maya_stage_node)
        if asset_stage is None:
            cmds.confirmDialog(
                title='No stage selected',
                message='Please select a correct stage',
                button=['OK'],
                defaultButton='OK'
            )
            cmds.warning('Please select a layer')
            print("Please select a correct stage")
            return None
        
        return asset_stage


    """
    Here we are not using Import and Export function 
    because it do not recognize layers some times.
    """
    def __copy_USD_layer(self):
        """
        Copy the selected layer in USD Layer Editor to a tempfile.usda.
        Replace #sdf 1.4.32 with #usda 1.0 if the first line starts with #usda 1.0.
        """

        asset_stage = self.__get_selected_stage()
        if asset_stage is None:
            return

        tmp_dir = tempfile.gettempdir()
        tmp_file_path = os.path.join(tmp_dir, TMP_FILE_NAME)
        
        session_layer = asset_stage.GetEditTarget().GetLayer()
        tmp_file_raw = session_layer.ExportToString()

        # Check if the first line starts with #usda 1.0 and replace #sdf 1.4.32
        lines = tmp_file_raw.splitlines()
        if lines and lines[0].startswith("#usda 1.0"):
            print("replace usda 1.0 to #sdf 1.4.32 ")
            lines[0] = lines[0].replace( "#usda 1.0","#sdf 1.4.32")

        # Rejoin the lines and write to the temporary file
        tmp_file_modified = "\n".join(lines)

        with open(tmp_file_path, 'w') as tmp_file:
            tmp_file.write(tmp_file_modified)
            
        cmds.confirmDialog(
            title='USD successfully exported',
            message=f'Exported USD Edits in:\n {tmp_file_path}',
            button=['OK'],
            defaultButton='OK'
        )
        print("Exported USD Edits in:\n", tmp_file_path)
        os.startfile(tmp_file_path)
            
    def __paste_USD_layer(self):
        """
        Paste to the selected layer in USD Layer Editor the currently copied
        layer from a tempfile.usda.
        """

        tmp_dir = tempfile.gettempdir()
        tmp_file_path = os.path.join(tmp_dir, TMP_FILE_NAME)
        
        if not os.path.exists(tmp_file_path):
            cmds.confirmDialog(
                title='Could not find tmp file',
                message=f'Could not find tmp file: \n {tmp_file_path}',
                button=['OK'],
                defaultButton='OK'
            )
            raise FileNotFoundError(
                f"Temporary file does not exist: {tmp_file_path}")
            
        asset_stage = self.__get_selected_stage()
        if asset_stage is None:
            return
        
        with open(tmp_file_path, 'r') as tmp_file:
            tmp_file_raw = tmp_file.read()

        session_layer = asset_stage.GetEditTarget().GetLayer()
        session_layer.ImportFromString(tmp_file_raw)
        
        cmds.confirmDialog(
            title='USD successfully import',
            message='USD Edits successfully imported to the target stage.',
            button=['OK'],
            defaultButton='OK'
        )
        print("USD Edits successfully imported to the target stage.")