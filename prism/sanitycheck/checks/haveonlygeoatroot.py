
from . import check

class HaveOnlyGeoAtRoot(check.Check):
      
    def __init__(self):
        super().__init__(
            name='have_only_geo_at_root',
            label='Have Only Geo At Root',
            severity=check.Severity.WARNING,
            have_fix=False)
        self.documentation = "in this scene you should only have the geo group at the root, you can also have a 'sandbox' group to put some temp stuff , but nothing else"
        self.fixComment = "you need to delete the other nodes, or rename your main group , you can put all the node temp in a group named, 'sandbox'"

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

        if set(cleanRootNodesList) == set(['geo']) or set(cleanRootNodesList) == set(['geo','sandbox']):
            self.message = "there is only 'geo' nor 'sandbox' in the root of your hierarchy"
            self.status = True
            return True
        else:
            messageStr= "there should only have 'geo' nor 'sandbox' at the root of your hierarchy, there is nothing in the root or something else has been detected :\n"
            for nodes in cleanRootNodesList:
                messageStr += f' - {nodes} \n'
            
            self.message = messageStr.rstrip('\n')

            self.status = False
            return False
    
    def fix(self, stateManager):
        pass