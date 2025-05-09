from . import check

class AllGeoShouldHaveATRSof0(check.Check):
    """
    TemplateCheck est un template de check, le nom de la classe 
    du check doit être égale au nom du fichier (peu importe la casse)
    Le nom du fichier doit être en miniscule (lowercase)
    """

    def __init__(self):
        super().__init__(
            name='AllGeoShouldHaveATRSof0',
            label='all geo should have a trs of 0',
            severity=check.Severity.WARNING,
            have_fix=True
            )
        self.documentation = 'all your objects in the geo group should have a freezed transforms'
        self.fixComment = 'freeze the transform of all objets in the geo group'
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
        # List all transform nodes
        all_transforms = cmds.listRelatives('geo', allDescendents=True, type='transform', fullPath=True) or []
        all_transforms += ['|geo']
        print(f"all_transform={all_transforms}")

        if not all_transforms:
            cmds.warning("No transform nodes found.")
            return

        transformed = []

        for obj in all_transforms:
            if obj in ["persp","top","front","side","geo","left","back","bottom"]:
                continue  # skip cameras
            
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
            if shapes:
                shapetype=cmds.objectType(shapes[0])
                if shapetype =='imagePlane':
                    continue  # skip imageplane
            


            # Get transform attributes
            t = cmds.getAttr(obj + ".translate")[0]
            r = cmds.getAttr(obj + ".rotate")[0]
            s = cmds.getAttr(obj + ".scale")[0]

            # Check if they are different from default values
            if t != (0.0, 0.0, 0.0) or r != (0.0, 0.0, 0.0) or s != (1.0, 1.0, 1.0):
                transformed.append(obj)

        if transformed:
            self.message = 'Those object have transforms:\n'
            for obj in transformed:
                self.message += f' - {obj} \n'
            self.message = self.message.rstrip('\n')
            self.status = False
            return False
        else:
            print("No transformed objects found.")
            self.message = 'all the object have no transforms'
            self.status = True
            return True

    def fix(self, stateManager):
        print("Fix Check")
        import maya.cmds as cmds
        # List all transform nodes
        all_transforms = cmds.ls(type='transform')

        if not all_transforms:
            cmds.warning("No transform nodes found.")
            return

        # Freeze transforms on all
        for obj in all_transforms:
            # Skip default scene nodes like "persp", "top", etc.
            if obj in ['persp', 'top', 'front', 'side']:
                continue
            cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=True, normal=False)
            print(f"Transforms frozen for: {obj}")
        