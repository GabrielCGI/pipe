
from . import check
from ..fixes import renameshader

class NamingShadingGroup(check.Check):
    def __init__(self):
        super().__init__(
            name='naming_shading_group',
            label='naming shading group',
            severity=check.Severity.WARNING,
            have_fix=True)
        
        self.documentation = 'in houdini, shader will be named like the maya shader group, so you need to name them well here. there name should be <materialName>+_mat '
        self.fixComment = 'the fix is to rename all the shader group , using their connected mat '

    def run(self, stateManager):
        core = stateManager.core
        if core.appPlugin.pluginName == 'Maya':
            return self.mayarun(stateManager)
        else:
            self.message = 'Check only on Maya, skipped.'
            return True
    
    def mayarun(self, stateManager):
        import maya.cmds as cmds
        
        shading_groups = cmds.ls(type="shadingEngine")
        wrongShaderGroup=[]
        for sg in shading_groups:
            connected_mat = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False)
            if connected_mat:
                mat_name = connected_mat[0]
                expected_sg_name = mat_name + "_mat"
                if sg == expected_sg_name or sg == "initialParticleSE" or sg == "initialShadingGroup" :
                    pass
                else:
                    wrongShaderGroup.append(sg)
        
        if wrongShaderGroup:
            mat_str = 'Some shader group have not the good name:\n'
            for mat in wrongShaderGroup:
                mat_str += f' - {mat} \n'
            
            self.message = mat_str.rstrip('\n')
            self.status = False
            return False
        else:
            self.message = f'all shader group are named correctly'
            self.status = True
            return True
    
    def fix(self, stateManager):
        import maya.cmds as cmds
        shading_groups = cmds.ls(type="shadingEngine")
        for sg in shading_groups:
            # Find the connected material
            connected_mat = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False)
            if connected_mat:
                mat_name = connected_mat[0]
                if "_mat" in mat_name:
                    new_name = mat_name.replace("_mat", "")
                    cmds.rename(mat_name, new_name)
                new_sg_name = mat_name + "_mat"
                # Rename the shading group
                try:
                    cmds.rename(sg, new_sg_name)
                    print(f"Renamed {sg} to {new_sg_name}")
                except RuntimeError as e:
                    print(f"Could not rename {sg}: {e}")