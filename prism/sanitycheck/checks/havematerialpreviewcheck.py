
from . import check

class HaveMaterialPreviewCheck(check.Check):
      
    def __init__(self):
        super().__init__(
            name='have_material_preview',
            label='Have Material Preview',
            severity=check.Severity.ERROR,
            have_fix=False)

    def run(self, stateManager):
        core = stateManager.core
        if core.appPlugin.pluginName == 'Houdini':
            return self.houdinirun(stateManager)
        else:
            self.message = 'Check only on Houdini, skipped.'
            return True
        
    def houdinirun(self, stateManager):
        import hou
        
        stage = hou.node('stage')
        mat_libs = []
        for node in stage.children():
            if node.type().name() == 'materiallibrary':
                mat_libs.append(node)

        no_preview_mat = []

        for mat_lib in mat_libs:
            for mat in mat_lib.children():
                has_usd_preview = False
                for node in mat.children():
                    if node.type().name() == 'usdpreviewsurface':
                        has_usd_preview = True
                        if node.outputs():
                            not_connected = True
                            for preview_output in node.outputs():
                                if preview_output.type().name() == 'suboutput':
                                    not_connected = False
                            if not_connected:
                                no_preview_mat.append(mat)
                        
                        else:
                            no_preview_mat.append(mat)
                            
                if not has_usd_preview:
                    no_preview_mat.append(mat)
                    
        if no_preview_mat:
            mat_str = 'Those material do not have preview for:\n'
            for mat in no_preview_mat:
                mat_str += f' - {mat.name()} \n'
            
            self.message = mat_str.rstrip('\n')
            self.status = False
            return False
        else:
            self.message = 'Every material have a preview.'
            self.status = True
            return True
            
    
    def fix(self, stateManager):
        pass