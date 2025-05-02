from . import check

class TemplateCheck(check.Check):
    """
    TemplateCheck est un template de check, le nom de la classe 
    du check doit être égale au nom du fichier (peu importe la casse)
    Le nom du fichier doit être en miniscule (lowercase)
    """

    def __init__(self):
        super().__init__(
            name='testCheck',
            label='Test Check',
            severity=check.Severity.WARNING,
            have_fix=True
            )
        self.documentation = 'This is the documentation that your check need to follow'
        self.fixComment = 'this is where you can explain what the fix script will do'
        # severity est une enum qui indique le niveau de danger de l'erreur.
        # Il y a deux niveaux, Severity.WARNING et Severity.ERROR
        
        # Attribut propre au check (comme un objet classique)
        self.condition = False
        
        
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
        print("executing a check in maya")
        if self.condition:
            self.message = 'The test has been passed.'
            self.status = True
            return True
        else:
            self.message = 'The test has not been passed.'
            self.status = False
            return False

    def fix(self, stateManager):
        print("Fix Check")
        self.condition = True
    