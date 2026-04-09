from PrismUtils.Decorators import err_catcher_plugin as err_catcher #type: ignore
import sys


MODULES_SEARCH_PATH = ["R:/pipeline/pipe/prism"]
for module_path in MODULES_SEARCH_PATH:
    if module_path not in sys.path:
        sys.path.insert(0, module_path)



name = "Clamp Textures"
classname = "ClampTextures"

EXECUTE_DEPARTEMENT = ["Lighting", "Setdress"]



class ClampTextures:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"
        
        if self.core.appPlugin.pluginName == 'Houdini':
            self.core.registerCallback("onSceneOpen", self.checkNeedClamping, plugin=self)

    @err_catcher(name=__name__)
    def checkNeedClamping(self, file_path):
        find = False
        for dep in EXECUTE_DEPARTEMENT:
            if f"\\{dep}\\" in file_path or f"/{dep}/" in file_path:
                find = True
                break
        
        if find:
            self.cropViewport()

    def cropViewport(self):
        import hou #type: ignore
        pane = hou.ui.desktop("Solaris").paneTabOfType(hou.paneTabType.SceneViewer)
        if not pane:
            raise RuntimeError("Pas de SceneViewer ouvert")

        viewport = pane.curViewport()
        settings = viewport.settings()
        value = [hou.viewportTextureDepth.Fixed8, 0.1, 1024]


        #------------------------  |  Texture  |  ---------------------
        # -- Texture 2D --
        settings.setTextureBitDepthLimit2D(value[0])
        settings.setTextureScale2D(value[1])

        # -- Texture Cache (volumes) --
        settings.setTextureCacheSize(value[2])

        # -- Texture 3D (volumes) --
        settings.setTexture2DSettingsFor3D(True)


        hou.hscript("glcache -c")
        print("texture Clamp in desktop 'solaris'")