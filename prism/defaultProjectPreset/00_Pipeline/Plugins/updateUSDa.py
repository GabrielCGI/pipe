from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from qtpy.QtWidgets import QAction
import sys
import os
import socket
import importlib

DEV_LIST = ['SPRINTER-04']

try:
    if socket.gethostname() in DEV_LIST:
        sys.path.append("R:/devmaxime/dev/python/prism/update_assets_USD_dev")
        import updateAssetsUSD_dev as UD
    else:
        sys.path.append("R:/pipeline/pipe/prism/update_assets_USD")
        import updateAssetsUSD as UD
except:
    pass




LOCAL = r"I:/intermarche/"
CLOUD = r"I:/intermarche/04_Resources/googleCache"
name = "updateUSDa"
classname = "updateUSDa"



class updateUSDa:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"

        self.core.registerCallback("openPBFileContextMenu", self.contextMenu, plugin=self)
        self.core.registerCallback("productSelectorContextMenuRequested", self.productContextMenu, plugin=self)
        self.core.registerCallback("textureLibraryTextureContextMenuRequested", self.textureLibraryTextureContextMenuRequested, plugin=self)

    def normalize_path(self, path):
        return os.path.normpath(path)
    
    def is_valid_local_path(self, path):
        if not path or not os.path.exists(path):
            return False
        
        norm_path = self.normalize_path(path)
        if not "Export" in norm_path:
            return False
        
        return norm_path.startswith(self.normalize_path(LOCAL)) and not norm_path.startswith(self.normalize_path(CLOUD))

    def is_valid_cloud_path(self, path):
        return False
    


    @err_catcher(name=__name__)
    def contextMenu(self, origin, menu, path):
        self.add_copy_actions(menu, path)

    @err_catcher(name=__name__)
    def productContextMenu(self, productbrowser, lw, pos, menu):
        if lw != productbrowser.tw_versions:
            return

        data = productbrowser.getCurrentVersion()
        path = data.get("filename") or data.get("path") if data else None
        self.add_copy_actions(menu, path)

    @err_catcher(name=__name__)
    def textureLibraryTextureContextMenuRequested(self, origin, menu):
        if type(origin).__name__ != "TextureWidget" and type(origin).__name__ != "TextureStackWidget" :
            return

        path = getattr(origin, "path", None)
        self.add_copy_actions(menu, path)
    


    def add_copy_actions(self, menu, path):
        if self.is_valid_local_path(path):
            act_cloud = menu.addAction("update selected USDA file")
            act_cloud.triggered.connect(lambda: self.testbtm(path))
   
    def testbtm(self, path):
        files = os.listdir(path)

        for file in files:
            if ".usd" in file and not file.endswith(".bak"):
                THE_File = path + "\\"+ file
                break
        
        
        importlib.reload(UD)
        UD.startUpdateAssetsUSD("prism", THE_File)