import socket
import time
import sys
import hou



def run(*args):
    hou.ui.displayMessage("I ran! I ran so far away!")
    if "FALCON-01" == socket.gethostname():
        return
    
    
    print("start customViewport")
    import ctypes
    ctypes.windll.kernel32.AllocConsole()
    sys.stdout = open('CONOUT$', 'w')
    sys.stderr = open('CONOUT$', 'w')
    sys.stdin = open('CONIN$', 'r')

    print(hou.hipFile.path())
    pane = hou.ui.desktop("Solaris").paneTabOfType(hou.paneTabType.SceneViewer)
    if not pane:
        raise RuntimeError("Pas de SceneViewer ouvert")

    viewport = pane.curViewport()
    settings = viewport.settings()


    #----------------------  |  Background  |  --------------------
    #-- colorScheme------------------
    settings.setColorScheme(hou.viewportColorScheme.DarkGrey)







    #------------------------  |  Texture  |  ---------------------
    #-- General ---------------------
    settings.setDisplayTextures(0)
    settings.setDisplayTextureLayers(0)
    settings.setDisplayProjectedTextures(0)
    settings.setTextureMipmapping(0)
    settings.setTextureAnisotropicFilter(1)


    # -- Texture 2D ------------------
    settings.setTextureResLimit2D(True)
    settings.setTextureMaxRes2D((16, 16))
    settings.setTextureBitDepthLimit2D(hou.viewportTextureDepth.Fixed8)
    settings.setTextureScale2D(0.1)


    # -- Texture Cache ---------------
    settings.setTextureCacheSize(2048)
    settings.setTextureMaxMemory(128)
    settings.setTextureAutoReduce2D(True)
    settings.setTextureAutoReduce3D(True)


    # -- Texture 3D (volumes) --------
    settings.setTextureResLimit3D(True)
    settings.setTextureMaxRes3D((16, 16, 16))
    settings.setTexture2DSettingsFor3D(True)

run()