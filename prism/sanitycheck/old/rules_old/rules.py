
# ONLY FOR TESTING PURPOSE
# Tu peux ignorer ces fonctions.

def testFalse(stateManager):
    print('Test False')
    
    return False, 'Test False'

def testTrue(stateManager):
    print('Test True')
    
    return True, 'Test True'
    
def have_shader_group_well_named(stateManager):
    core = stateManager.core
    
    if core.appPlugin.pluginName == 'Maya':
        from . import mayarules
        return mayarules.have_shader_group_well_named(stateManager)
        
def have_only_geo_at_root(stateManager):
    core = stateManager.core
    
    if core.appPlugin.pluginName == 'Maya':
        from . import mayarules
        return mayarules.have_only_geo_at_root(stateManager)

def have_all_render_node_set_to_xpu(stateManager):
    core = stateManager.core
    
    if core.appPlugin.pluginName == 'Houdini':
        from . import houdinirules
        return houdinirules.have_all_render_node_set_to_xpu(stateManager)
    
def have_material_preview(stateManager):
    core = stateManager.core
    if core.appPlugin.pluginName == 'Houdini':
        from . import houdinirules
        import importlib
        importlib.reload(houdinirules)
        return houdinirules.have_material_preview(stateManager)
    
    

