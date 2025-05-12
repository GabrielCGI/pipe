from . import check

class SMIsWellSetForModeling(check.Check):
    """
    TemplateCheck est un template de check, le nom de la classe 
    du check doit être égale au nom du fichier (peu importe la casse)
    Le nom du fichier doit être en miniscule (lowercase)
    """

    def __init__(self):
        
        super().__init__(
            name='state_manager_is_well_set_for_modeling',
            label='state manager is well set for modeling',
            severity=check.Severity.WARNING,
            have_fix=False
            )
        self.documentation = 'when you export your modeling you need to follow exactly the export settings described in the documentation on notion'
        self.fixComment = ''
        # severity est une enum qui indique le niveau de danger de l'erreur.
        # Il y a deux niveaux, Severity.WARNING et Severity.ERROR
        
        # Attribut propre au check (comme un objet classique)
        self.condition = True
        

    def run(self, stateManager):
        core = stateManager.core
        
        # Un check doit renvoyer True ou False.

        # Ce code ce lance peu importe le DCC

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
        import json

        smdict=stateManager.getStateSettings()
        data = json.loads(smdict)
        stateList=data["states"][1:]
        print(stateList)
        for obj in stateList:
            print(f"")
            print(f"")
            print(f"")
            for key, value in obj.items():
                print(f"{key}: {value}")
        # for state in stateList:
        #     if state 'stateclass': 'ImportFile':
        export_states = [state for state in stateList if state.get("stateclass") == "Export" or state.get("stateclass") == "USD Export"]
        maxState=2
        if len(export_states) > maxState:
            self.message = f'there should be max {maxState} state in the state manager, the usd one ,and the rigging one but {len(stateList)} have been detected'
            self.status = False
            return False
        print("hey")
        usdState=stateList[0]
        product=usdState.get("product")
        all_sets = cmds.ls(type='objectSet')
        

        for set in all_sets:
            print(set)
            print(product)
            if set ==product:
                members = cmds.sets(set, q=True)
                if members != ['geo']:
                    print("hey")
                    str = f'there is other stuff than geo selected in your product {product} :\n'
                    for member in members:
                        str += f' - {member} \n'
                    str += ' and there should only have geo'
                    self.message = str
                    self.status = False
                    return False
                else:
                    print("hey")
                    self.message = f'you only have {members} selected to export! nice'
                    self.status = True
                    return True

    def fix(self, stateManager):
        print("Fix Check")
        self.condition = True
