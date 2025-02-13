import hou

# Nodes identifiers
LIGHT_MAKER_ID = 'illogic::Light_maker'
MAPPING_ID = 'KEY'
COPNET_ID = 'copnet'

# Parameters identifiers
TOGGLELIGHT_PARM = 'toggle_light'
X_PARM = "light_positionx"
Y_PARM = "light_positiony"
Z_PARM = "light_positionz"

def clean():
    """
    Delete every fake light and untoggle
    togglelight checkbox in every light makers.
    """
    
    stage = hou.node("stage/")

    canDelete = hou.ui.displayConfirmation(
        "Do you want to delete every fake light?")

    if not canDelete:
        return
    
    copnets = []

    # Get every copnet nodes in stage
    for node in stage.children():
        if node.type().name() == COPNET_ID:
            copnets.append(node)

    # Get every light makers in every copnet nodes
    light_makers = []
    for copnet in copnets:
        for node in copnet.children():
            if LIGHT_MAKER_ID in node.type().name():
                light_makers.append(node)

    # For each light maker disable their fake light
    for lm in light_makers:
        mapping_tuple = lm.glob(MAPPING_ID)
        if not mapping_tuple:
            continue
        mapping = mapping_tuple[0]
        if not mapping:
            continue
        togglelight = mapping.parm(TOGGLELIGHT_PARM)
        if not togglelight:
            continue
        
        # Check if the fake light is toggle
        if not togglelight.eval():
            continue
        
        # Disable any references to fake light position
        x = mapping.parm(X_PARM)
        y = mapping.parm(Y_PARM)
        z = mapping.parm(Z_PARM)
        if not x or not y or not z:
            continue
        x.deleteAllKeyframes()
        y.deleteAllKeyframes()
        z.deleteAllKeyframes()
        
        togglelight.set(False)
        
        # Get linked light node from parameter expression
        lightposx = mapping.parm(X_PARM)
        if not lightposx:
            continue
        exp = lightposx.expression()
        if not exp:
            continue
        light = hou.node(exp[4:-4])
        
        # Destroy fake light linked to light maker
        if not light:
            continue
        light.destroy()