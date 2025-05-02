import sys

import hou
import PrismInit

DEBUG_MODE = True
try:
    sys.path.append(r'R:\devmaxime\virtualvens\sanitycheck\Lib\site-packages')
    import debugpy
except:
    DEBUG_MODE = False


def debug():
    if not DEBUG_MODE:
        return
    
    hython = r"C:\Program Files\Side Effects Software\Houdini 20.5.548\bin\hython3.11.exe"
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        print("Already attached")
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()

debug()

def main():
    core = PrismInit.pcore

    usdplg = core.getPlugin('USD')
    loprender = usdplg.api.lopRender

    node = hou.node('stage/shot10')

    state = loprender.getStateFromNode({'node': node})
    parents = state.ui.__class__.__bases__

    parent_method = []
    for p in parents:
        parent_method += dir(p)

    for i in dir(state.ui):
        if not i in parent_method:
            print(i)
            
    debugpy.breakpoint()
    
    pass