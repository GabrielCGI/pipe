from ..tool_models.MultipleActionTool import *


class Gate(MultipleActionTool):

    def __init__(self):
        actions = {
            "square": {
                "text": "square",
                "action": self.__square,
                "row": 0
            },
            "hor": {
                "text": "16:9",
                "action": self.__hor,
                "row": 0
            },
            "ver": {
                "text": "9:16",
                "action": self.__ver,
                "row": 0
            }
        }
        super().__init__(name="Gate tool", pref_name="gate_tool",
                         actions=actions, stretch=1)



    def __square(self):
        # TODO Enter the code you want the tool to execute on action 1
        print("Action 1")
        # Usage
        image_path = "R:/pipeline/pipe/maya/scripts/bug_out_bag/textures/square.png"
        self.create_imageplane(image_path)
    def __hor(self):
        print("Action 2")
        # Usage
        image_path = "R:/pipeline/pipe/maya/scripts/bug_out_bag/textures/hor.png"
        self.create_imageplane(image_path)
    def __ver(self):
        print("Action 3")
        # Usage
        image_path = "R:/pipeline/pipe/maya/scripts/bug_out_bag/textures/ver.png"
        self.create_imageplane(image_path)

    def create_imageplane(self, image_path):

                # Get the active viewport
        viewport = pm.playblast(activeEditor=True)

        # Get the camera that is active in the viewport
        cameraVP = pm.modelEditor(viewport, query=True, camera=True)



        if not cameraVP :
            raise Exception("Please select a camera.")

        camera = cameraVP.getShape()
        camera.filmFit.set(0)
        # Check for existing image planes attached to the camera
        image_planes = pm.listConnections(camera, type='imagePlane')

        if image_planes:
            # If an image plane exists, update the image path
            image_plane = image_planes[0].getShape()
            print(image_plane)
            pm.select(image_plane)
            image_plane.imageName.set(image_path)
            image_plane.fit.set(1)
            print(f"Updated image path for existing image plane on {camera}.")
        else:
            # If no image plane exists, create one and set attributes
            image_plane = pm.imagePlane(camera=camera, fileName=image_path, lookThrough=camera)[0]
            image_plane.depth.set(1)
            image_plane.alphaGain.set(0.5)
            image_plane.fit.set(1)
            print(f"Image plane created for {camera} with image {image_path}. Depth set to 1 and alphaGain set to 0.5.")
        current_mode = pm.evaluationManager(query=True, mode=True)[0]
        if current_mode == 'parallel':
            pm.evaluationManager(mode="off")
            pm.refresh()
            pm.evaluationManager(mode="parallel")
        pm.refresh()
