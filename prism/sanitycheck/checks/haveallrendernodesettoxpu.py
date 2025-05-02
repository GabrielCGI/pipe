
from . import check

class HaveAllRenderNodeSetToXpu(check.Check):
      
    def __init__(self):
        super().__init__(
            name='have_material_preview',
            label='Have Material Preview',
            severity=check.Severity.WARNING,
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
        
        # get all the prism lop render nodes
        prismLopRenderNodeList = []
        stage = hou.node("/stage")
        def recurse(node):
            if node.type().name() == "prism::LOP_Render::1.0":
                prismLopRenderNodeList.append(node)
            for child in node.children():
                recurse(child)
        recurse(stage)

        XPU_RENDERER = "BRAY_HdKarmaXPU"
        XPUprismLopRenderNodeList=[]
        CPUprismLopRenderNodeList=[]

        for node in prismLopRenderNodeList:
            current_value = node.parm("renderer").eval()
            if current_value != XPU_RENDERER:
                CPUprismLopRenderNodeList.append(node)
                # node.parm("renderer").set(XPU_RENDERER)
            else:
                XPUprismLopRenderNodeList.append(node)

        if CPUprismLopRenderNodeList:
            self.message = ('there should only be xpu render node'
                            ' in your scene, but it look like there'
                            f' is some node sets to cpu :{CPUprismLopRenderNodeList}')
            self.status = False
            return False 
        else:
            self.message = 'there is only xpu render node in your scene'
            self.status = True
            return True
    
    def fix(self, stateManager):
        pass