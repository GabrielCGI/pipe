from . import check

class NamingCamera(check.Check):
    """
    TemplateCheck est un template de check, le nom de la classe 
    du check doit être égale au nom du fichier (peu importe la casse)
    Le nom du fichier doit être en miniscule (lowercase)
    """

    def __init__(self):
        super().__init__(
            name='naming_camera',
            label='naming camera',
            severity=check.Severity.WARNING,
            have_fix=False
            )
        self.documentation =    """you need to have a camera named like this:
        world
        └── camera
            └── camRig
                └── camera
                    └── shotCam
        also this camera should not have childrens"""

        self.fixComment = 'you need to rename, move , or create your camera, you can also import the camera rig, all the instruction should be in the wiki, on notion, that you can found with the illogic shelf, this is the notion button , a cube with a n on it'
        # severity est une enum qui indique le niveau de danger de l'erreur.
        # Il y a deux niveaux, Severity.WARNING et Severity.ERROR
        
        # Attribut propre au check (comme un objet classique)
        self.condition = True
        
        
    def run(self, stateManager):
        core = stateManager.core
        # Un check doit renvoyer True ou False.

        # Ce code ce lance peu importe le DCC
        print('This is a test running')

        # Ici on implemente notre check par DCC
        if core.appPlugin.pluginName == 'Maya':
            # Il est recommandé d'implémenter le check par DCC dans 
            # une méthode dédié afin d'éviter des conflits avec les imports
            return self.mayarun(stateManager)
        elif core.appPlugin.pluginName == 'Houdini':
            return self.houdinirun(stateManager)
        else:
            # Si le DCC n'est pas détecter
            return True

    def houdinirun(self, stateManager):
        """this is here where you will create a houdini check

        Args:
            stateManager (None): le statemanager de prism   

        Returns:
            bool: si le check est passé ou non
        """        

        import hou

        stage = hou.node('stage')
        print("executing a check in houdini")
        print(self.condition)
        if self.condition:
            self.message = 'The test has been passed.'
            self.status = True
            return True
        else:
            self.message = 'The test has not been passed.'
            # IMPORTANT TO UPDATE STATUS WHEN PASSING TEST
            self.status = False
            return False

    def mayarun(self, stateManager):
        """this is here where you will create a maya check

        Args:
            stateManager (None): le statemanager de prism   

        Returns:
            bool: si le check est passé ou non
        """
        import maya.cmds as cmds
        rootNodesList = cmds.ls(assemblies=True)
        errors = []
        def find_child_by_name(parent, name):
            def strip_namespace(obj_name):
                return obj_name.split(':')[-1]
            children = cmds.listRelatives(parent, children=True, fullPath=True) or []
            for child in children:
                if strip_namespace(child.split('|')[-1]) == name:
                    return child
            return None

        # Step 1: Check root object named "world"
        if not cmds.objExists('world'):
            self.message = 'Missing object: world'
            self.status = False
            return False

        # Step 2: Check for "camera" under "world"
        world_children = cmds.listRelatives('world', children=True, fullPath=True) or []
        camera = next((child for child in world_children if child.split('|')[-1] == 'camera'), None)
        if not camera:
            self.message = 'Missing object: camera under world'
            self.status = False
            return False

        # Step 3: Check for "camrig" under "camera"
        camrig = find_child_by_name(camera, 'camRig')
        if not camrig:
            self.message = 'Missing object: camRig under camera'
            self.status = False
            return False

        # Step 4: Check for "camera" under "camrig"
        camera_node = find_child_by_name(camrig, 'camera')
        if not camera_node:
            self.message = 'Missing object: camera under camRig'
            self.status = False
            return False

        # Step 5: Check for "camshape" under "camera"
        shotCam = find_child_by_name(camera_node, 'shotCam')
        if not shotCam:
            self.message = 'Missing object: shotCam under camera'
            self.status = False
            return False

        # Step 6: Check that "shotCam" is a camera shape node
        shapes = cmds.listRelatives(shotCam, shapes=True, fullPath=True)
        if not cmds.objectType(shapes[0]) == 'camera':
            self.message = f"{shotCam} is not a camera node its a : {cmds.objectType(shapes[0])}"
            self.status = False
            return False

        # Step 7: Check that "shotCam" has no children
        camera_children = cmds.listRelatives(shotCam, children=True, fullPath=True) or []
        #remove namesspace
        camera_children_clean=[]
        for child in camera_children:
            child=child.split(':')[-1]
            camera_children_clean.append(child)
        if any(child for child in camera_children_clean if child.split('|')[-1] != 'shotCamShape'):
            self.message = f"Object '{shotCam}' should not have children other than 'camshape' and it have:{camera_children}"
            self.status = False
            return False

        self.message = 'Hierarchy is valid!'
        self.status = True
        return True

        
    def fix(self, stateManager):
        print("Fix Check")
        self.condition = True
    