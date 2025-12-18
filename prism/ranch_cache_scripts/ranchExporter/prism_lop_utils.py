import os

def getUsdPath(kwargs: dict) -> str:
    """Get USD path from postRender context.

    Args:
        kwargs (dict): PostRender context.

    Returns:
        str: USD file path.
    """    
    
    exrpath = kwargs["outputpath"]
    
    # Dirty way to get usdc path
    basename = os.path.basename(exrpath)
    basename = os.path.splitext(os.path.splitext(basename)[0])[0]+".usdc"
    usdpath = os.path.join(os.path.dirname(exrpath), "_usd", basename)
    return os.path.abspath(usdpath)


def is_light_cache(kwargs) -> bool:
    try:
        node: hou.LopNode = kwargs["state"].node
        scenefile = kwargs["scenefile"]
    except:
        return False
    if not node:
        return False
    if not node.type().name() == 'prism::lop_filecache::1.0':
        return False
    save_mode = node.parm("saveMode")
    from_scenefile = node.parm("depFromScenefile")
    department = node.parm("department")
    if not save_mode or not from_scenefile or not department:
        return False
    if save_mode.eval() != 1:
        return False
    
    if from_scenefile.eval():
        return 'lighting' in scenefile.lower()
    else:
        dpt = department.menuLabels()[department.eval()].lower()
        return ('lighting' in dpt or 'lgt' in dpt)
