from . import m_debug
import importlib 
import os

DEBUGPY = m_debug.debugpy
HOU_DEFAULT_VERSION = '20.5.591'

def debug():
    importlib.reload(m_debug)
    try:
        # try to get version of houdini if execute from houdini
        import hou
        version = hou.applicationVersionString()
    except Exception as e:
        # try to get version from env variable if it exists
        version = os.environ.get(
            'HOUDINI_ILL_VERSION',
            HOU_DEFAULT_VERSION
        )
    print(f'Start debug with hython {version}')
    m_debug.debug(version)
    
def breakpoint():
    DEBUGPY.breakpoint()