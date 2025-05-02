
from . import check

class HaveOnlyGeoAtRoot(check.Check):
      
    def __init__(self):
        super().__init__(
            name='have_only_geo_at_root',
            label='Have Only Geo At Root',
            severity=check.Severity.ERROR,
            have_fix=False)
        self.documentation = 'in this scene you should only have the geo group at the root, nothing else'
        self.fixComment = 'you need to delete the other nodes, or rename your main group'

    def run(self, stateManager):
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

        if cleanRootNodesList != ['geo']:
            self.message = ('there should only have geo at the root of your hierarchy,'
                            ' there is nothing in the root or something'
                            f' else has been detected :{cleanRootNodesList}')
            self.status = False
            return False
        else:
            self.message = 'there is only geo in the root of your hierarchy'
            self.status = True
            return True
    
    def fix(self, stateManager):
        pass