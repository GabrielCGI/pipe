from pxr import Usd, Sdf
import maya.cmds as cmds
import mayaUsd

# Function to export USD edits as a string
def export_usd_edits(maya_stage_node):
    asset_stage = mayaUsd.ufe.getStage(maya_stage_node)
    session_layer = asset_stage.GetSessionLayer()
    return session_layer.ExportToString()

# Function to import USD edits into a session layer
def import_usd_edits(maya_stage_node, usd_data):
    asset_stage = mayaUsd.ufe.getStage(maya_stage_node)
    session_layer = asset_stage.GetSessionLayer()
    session_layer.ImportFromString(usd_data)

# Select the source stage and export the session layer edits
source_node = cmds.ls(selection=True, l=True)[0]
usd_data = export_usd_edits(source_node)
print("Exported USD Edits:\n", usd_data)

# Select the target stage to paste the edits
# Ensure you select the target node before running the next part
target_node = cmds.ls(selection=True, l=True)[0]
import_usd_edits(target_node, usd_data)
print("USD Edits successfully imported to the target stage.")