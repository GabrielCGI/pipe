from . import check

class ThereShouldBeLessThanXObject(check.Check):
    """
    TemplateCheck est un template de check, le nom de la classe 
    du check doit être égale au nom du fichier (peu importe la casse)
    Le nom du fichier doit être en miniscule (lowercase)
    """
    
    def __init__(self):
        super().__init__(
            name='thereshouldbelessthanxobject',
            label='there should be less than x objects',
            severity=check.Severity.ERROR,
            have_fix=False
            )
        self.limit=10000
        self.documentation = f'to be optimized you should have less than {self.limit} object in your scene'
        self.fixComment = ''
        self.condition = False

    def run(self, stateManager):
        core = stateManager.core
        if core.appPlugin.pluginName == 'Maya':
            return self.mayarun(stateManager)
        elif core.appPlugin.pluginName == 'Houdini':
            return self.houdinirun(stateManager)
        else:
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
        all_objects = cmds.ls(type='transform')
        object_count = len(all_objects)
        if object_count < self.limit:
            self.message = f'there is {object_count} transforms objects in your scene, its fine'
            self.status = True
            return True
        else:
            self.message = f'there is {object_count} transforms objects in your scene, its more than {self.limit}'
            self.status = False
            return False
        
    def fix(self, stateManager):
        print("Fix Check")
        self.condition = True
    