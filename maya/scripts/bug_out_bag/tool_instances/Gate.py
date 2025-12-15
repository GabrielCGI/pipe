from ..tool_models.MultipleActionTool import *


class Gate(MultipleActionTool):

    def __init__(self):
        actions = {
            "square": {
                "text": "square",
                "action": lambda: self.create_imageplane("square.png"),
                "row": 0
            },
            "hor": {
                "text": "16:9",
                "action": lambda: self.create_imageplane("hor.png"),
                "row": 0
            },
            "ver": {
                "text": "9:16",
                "action": lambda: self.create_imageplane("ver.png"),
                "row": 0
            },
            "fullB": {
                "text": "fb",
                "action": lambda: self.create_imageplane("fullBleed.jpg"),
                "row": 0
            },
            "__vca": {
                "text": "VCA",
                "action": lambda: self.create_imageplane("Guides_6000square2048_C.png"),
                "row": 0
            },
            "del": {
                "text": "Remove",
                "action": self.deleteImagePlane,
                "row": 0
            }
        }
        super().__init__(name="Gate tool", pref_name="gate_tool",
                         actions=actions, stretch=1)


    def deleteImagePlane(self):
        import maya.cmds as cmds
        panel = cmds.getPanel(withFocus=True)
        try:
            camera = cmds.modelEditor(panel, query=True, camera=True)
        except:
            return

        camShape = cmds.listRelatives(camera, c=True, ad=True)
        all_image_plane = cmds.listRelatives(camShape, c=True, ad=True)
        if not all_image_plane:
            return
        
        for shape in all_image_plane:
            cmds.delete(shape)


    def create_imageplane(self, ratio):
        import maya.cmds as cmds
        image_path = "R:/pipeline/pipe/maya/scripts/bug_out_bag/textures/" + ratio
        panel = cmds.getPanel(withFocus=True)
        try:
            camera = cmds.modelEditor(panel, query=True, camera=True)
        except:
            return
        if not camera:
            return
        
        self.deleteImagePlane()
        imageplane = cmds.imagePlane(camera= camera, fileName= image_path)[0]
        cmds.setAttr(imageplane + ".alphaGain", 0.5)
        cmds.setAttr(imageplane + ".fit", 2)
        cmds.setAttr(imageplane + ".depth", 1)