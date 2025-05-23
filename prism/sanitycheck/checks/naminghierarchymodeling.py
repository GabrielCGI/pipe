from . import check

class NamingHierarchyModeling(check.Check):
    """
    TemplateCheck est un template de check, le nom de la classe 
    du check doit être égale au nom du fichier (peu importe la casse)
    Le nom du fichier doit être en miniscule (lowercase)
    """

    def __init__(self):
        super().__init__(
            name='naming_hierarchy_modeling',
            label='naming hierarchy modeling',
            severity=check.Severity.WARNING,
            have_fix=False
            )
        self.documentation = """
there is 2 different naming rules, one for the characters and one for all the other assets

character:

<charName> (e.g: beaverDidier)
└──geo
    └──render
        ├── body
        ├── arms
        └── eyes


other:

geo
└── xform
    ├── pot
    └── stem

        """
        self.fixComment = "you need to respect the nomenctature on the documentation"

    def run(self, stateManager):
        print("running HaveOnlyGeoAtRoot check")
        core = stateManager.core
        if core.appPlugin.pluginName == 'Maya':
            return self.mayarun(stateManager)
        else:
            self.message = 'Check only on Maya, skipped.'
            return True

    def mayarun(self, stateManager):
        import maya.cmds as cmds
        from pathlib import Path

        def getErrorList(messagebefore,list,messageafter=''):
            messageStr= f"there should only have '{assetName}' nor 'sandbox' at the root of your hierarchy, there is nothing in the root or something else has been detected :\n"
            for item in list:
                messagebefore += f' - {item} \n'
            message = messagebefore.rstrip('\n')
            return message
        
        # first lets get whats in the root of your outliner
        rootNodesList = cmds.ls(assemblies=True)
        # lets remove all the camera at the root of our maya hierarchy
        cameraList=["persp","top","front","side","geo","left","back","bottom"]
        cameraDetectedList=[]
        for node in rootNodesList:
            if node in cameraList:
                shapes = cmds.listRelatives(node, shapes=True) or []
                shapeTypes = [cmds.nodeType(shape) for shape in shapes]
                if shapeTypes:
                    if shapeTypes[0]=="camera":
                        cameraDetectedList.append(node)
        cleanRootNodesList = list(set(rootNodesList)-set(cameraDetectedList))

        # now lets figure out the type of asset
        scene_path = cmds.file(query=True, sceneName=True)
        parts= Path(scene_path).parts
        type = parts[-6]
        otherList=["Environment","Props","sandbox","Sets"]

        if type == 'Characters':
            #check root
            assetName = parts[-5]
            if set(cleanRootNodesList) == set([assetName]) or set(cleanRootNodesList) == set([assetName,'sandbox']):
                pass
            else:
                messageStr= f"there should only have '{assetName}' nor 'sandbox' at the root of your hierarchy, there is nothing in the root or something else has been detected :\n"
                errorMessage=getErrorList(messageStr,cleanRootNodesList)
                self.message = errorMessage
                self.status = False
                return False
            
            #check children of the charaname
            children = cmds.listRelatives(assetName, children=True, fullPath=True) or []
            if set(children) == set([f'|{assetName}|geo']) :
                pass
            else:
                messageStr= f"there should only have '|{assetName}|geo' in '{assetName}' but there is nothing in the root or something else has been detected :\n"
                errorMessage=getErrorList(messageStr,children)
                self.message = errorMessage
                self.status = False
                return False
            
            #check children of the geo
            geoChildren = cmds.listRelatives(f'|{assetName}|geo', children=True, fullPath=True) or []
            if set(geoChildren) == set([f'|{assetName}|geo|render']) :
                pass
            else:
                messageStr= f"there should only have f'|{assetName}|geo|render'] in |{assetName}|geo but there is nothing in the root or something else has been detected :\n"
                errorMessage=getErrorList(messageStr,geoChildren)
                self.message = errorMessage
                self.status = False
                return False
            
            self.message = f"your hierarchy look well named!"
            self.status = True
            return True
        
        if type in otherList:
            #check root
            if set(cleanRootNodesList) == set(['geo']) or set(cleanRootNodesList) == set(['geo','sandbox']):
                pass
            else:
                messageStr= "there should only have 'geo' nor 'sandbox' at the root of your hierarchy, there is nothing in the root or something else has been detected :\n"
                errorMessage=getErrorList(messageStr,cleanRootNodesList)
                self.message = errorMessage
                self.status = False
                return False
            
            #check child of geo
            children = cmds.listRelatives(assetName, children=True, fullPath=True) or []
            if set(children) == set(['|geo|xform']):
                pass
            else:
                messageStr= "there should only have 'xform' in 'geo' at the root of your hierarchy, there is nothing in the root or something else has been detected :\n"
                errorMessage=getErrorList(messageStr,children)
                self.message = errorMessage
                self.status = False
                return False
            
            self.message = f"your hierarchy look well named!"
            self.status = True
            return True
        else:
            self.message = "the type is not detected, you are not in the pipeline? the sanity check dont undersand if you are in a character, a props ect"
            self.status = False
            return False
        
    
    def fix(self, stateManager):
        pass
    