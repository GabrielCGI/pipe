import pymel.core as pm

def get_objects_without_aiStandardShader():
    all_objects = pm.ls(geometry=True)
    objects_without_aiStandard = []

    for obj in all_objects:
        shading_grps = pm.listConnections(obj, type='shadingEngine')
        if shading_grps:
            for sg in shading_grps:
                surface_shader = pm.listConnections(sg.surfaceShader)
                ai_surface_shader = pm.listConnections(sg.aiSurfaceShader)

                has_aiStandardShader = False
                
                if surface_shader:
                    if 'aiStandardSurface' in surface_shader[0].nodeType(i=True):
                        has_aiStandardShader = True
                
                if ai_surface_shader:
                    if 'aiStandardSurface' in ai_surface_shader[0].nodeType(i=True):
                        has_aiStandardShader = True
                
                if not has_aiStandardShader:
                    objects_without_aiStandard.append(obj)
                    break

    return objects_without_aiStandard

# Select objects without aiStandardSurface shader
objects_to_select = get_objects_without_aiStandardShader()
pm.select(objects_to_select, replace=True)
