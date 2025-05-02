import hou

# ------------------------------HOUDINI RULES-------------------------------------------

def have_all_render_node_set_to_xpu(stateManager):
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
        return False , f'there should only be xpu render node in your scene, but it look like there is some node sets to cpu :{CPUprismLopRenderNodeList}'
    else:
        return True, 'there is only xpu render node in your scene'
    
def have_material_preview(stateManager):
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
        mat_str = 'Those material do not have preview:\n'
        for mat in no_preview_mat:
            mat_str += f'{mat.name()} \n'
        
        return False, mat_str.rstrip('\n')
    else:
        return True, 'Every material have a preview.'