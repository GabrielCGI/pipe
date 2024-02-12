from ..tool_models.ActionTool import *
from common.utils import *

class FaceFromShader(ActionTool):
    def __init__(self):
        # TODO Modify fields as you want (pref_name should be unique)
        super().__init__(name="Face From Shader",pref_name="face_from_shader",
                         description="Select the face of the object that has the shader", button_text="Run", tooltip="Select one object, select one shader, return the face of the object the belong to the shading group of the shader")

    def _action(self):
        print("START")
        # Get the currently selected objects
        selected_objects = pm.ls(selection=True,type="transform")
        first_shader =  pm.ls(selection=True, materials=True)

        # Ensure that there is at least one object selected
        if not selected_objects:
            raise ValueError("No object selected")

        # Get the shape of the first selected object
        selected_object = selected_objects[0].getShape()

        # Find the shading groups associated with the selected object
        shading_groups = pm.listConnections(first_shader, type='shadingEngine')[0]  # Corrected the typo here

        # Check if there is at least one shading group
        if not shading_groups:
            raise ValueError("No shading groups found for the selected object")

        first_shading_group = shading_groups

        # Get all faces of the object that are connected to the first shading group
        faces_in_first_group = pm.sets(first_shading_group, query=True)

        # Filter out only the faces of the selected object
        selected_object_faces = [face for face in faces_in_first_group if face.node() == selected_object]
        print("END")
        # Select the faces
        pm.select(selected_object_faces)
