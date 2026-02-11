from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from qtpy.QtWidgets import QAction, QMenu
import sys
import os
import subprocess
from pathlib import Path

MODULES_SEARCH_PATH = [
    "R:/pipeline/pipe/prism",
]
try:
    for module_path in MODULES_SEARCH_PATH:
        if not module_path in sys.path:
            sys.path.insert(0, module_path)
    
    import USDToolBox_pck
except Exception as e:
    print(f"Import failed: {e}")


#va trouver le chemin de ou ce situe ce fichier python pour pouvoir setup dans les variable local et global le projet
script_path = Path(__file__)
project_path = Path(*script_path.parts[:-3]).as_posix()
LOCAL = os.path.normpath(f"{project_path}")
CLOUD = os.path.normpath(f"{project_path}/04_Resources/googleCache")
name = "USDToolBox"
classname = "USDToolBox"


class USDToolBox:
    def __init__(self, core):
        self.core = core
        self.version = "v2.0.0"
        self.core.registerCallback("productSelectorContextMenuRequested", self.productContextMenu, plugin=self)
        self.create_usd_toolbox_menu()
    
    
    def create_usd_toolbox_menu(self):
        """
        Create a submenu named USD Tool Box,
        this submenu will be added to the right context menu in prism.
        """        
        
        self.action_path = ""
        
        self.toolbox_menu = QMenu("USD Tool Box")
        self.toolbox_menu.setObjectName('USD_tool_box')
        
        self.add_menu_action(
            "Update selected USD file",
            self.updateDependencies
        )
        self.add_menu_action(
            "Update selected USD file (NEW)",
            self.updateDependenciesNew
        )
        self.add_menu_action(
            "Clean preview material",
            self.cleanMaterialAttributes
        )
        self.add_menu_action(
            "Open With CST",
            self.openWithCST
        )
        
        
    def add_menu_action(self, name: str, method, menu: QMenu=None):
        """
        Add action to menu by specifying name and method.
        
        Note: self.action_path is provided to action, so every method
        should have a path parameter (even if not used).

        Args:
            name (str): action name displayed.
            method (function): method with path parameters.
            menu (QMenu, optional): menu to add action, 
                default to USD Tool Box. Defaults to None.
        """        
        
        if not menu:
            menu = self.toolbox_menu
        action: QAction = menu.addAction(name)
        action.triggered.connect(lambda: method(self.action_path))
        
        
    def is_valid_local_path(self, path: str):
        """Check if a path is local to production and is
        located in Export folder.

        Args:
            path (str): Path to check.

        Returns:
            bool: True if the path respect both condition, false otherwise 
        """
             
        if not path or not os.path.exists(path):
            return False
        
        norm_path = os.path.normpath(path)
        if not "Export" in norm_path:
            return False
        
        return norm_path.startswith(LOCAL) and not norm_path.startswith(CLOUD)


    @err_catcher(name=__name__)
    def productContextMenu(self, productbrowser, lw, pos, menu):
        """
        Callback whenever a context menu is open in product window.
        """        
        
        if lw != productbrowser.tw_versions:
            return

        data = productbrowser.getCurrentVersion()
        path = data.get("filename") or data.get("path") if data else None
        self.add_actions(menu, path)


    def add_actions(self, menu: QMenu, path: str):
        """Add an action to the contexte menu if path provided is valid.

        Args:
            menu (QMenu): Menu to fill.
            path (str): Product path.
        """     
           
        if self.is_valid_local_path(path):
            self.action_path = path            
            menu.addMenu(self.toolbox_menu)
   
   
    def updateDependenciesNew(self, product_directory: str):
        """
        Entry point of USD updater, a tool that simplify
        updates of dependencies of an USD File.
        
        Args:
            product_directory (str): USD Product directory.
        """
        
        files = os.listdir(product_directory)
        usd_path = None
        for file in files:
            # avoid backup usd file
            if ".usd" in file and not file.endswith(".bak"):
                usd_path = os.path.join(product_directory, file)
                break
        if usd_path is None:
            return
        
        USDToolBox_pck.updateAssetsUSD_new.startUpdateAssetsUSD(
            openType="prism",
            tmpfile=usd_path,
            prism_core=self.core
        )

    
    def updateDependencies(self, product_directory: str):
        """
        Entry point of USD updater, a tool that simplify
        updates of dependencies of an USD File.
        
        Args:
            product_directory (str): USD Product directory.
        """
        
        files = os.listdir(product_directory)
        usd_path = None
        for file in files:
            # avoid backup usd file
            if ".usd" in file and not file.endswith(".bak"):
                usd_path = os.path.join(product_directory, file)
                break
        if usd_path is None:
            return
            
        USDToolBox_pck.updateAssetsUSD.startUpdateAssetsUSD("prism", usd_path)
        
    
    def cleanMaterialAttributes(self, product_directory: str):
        """
        Clean USD connections.

        Args:
            product_directory (str): USD Product directory.
        """
        
        result = self.core.popupQuestion(text='Do you want to clean preview material ?')
        if result == "Yes":
            USDToolBox_pck.editpreviewUSD.edit_preview_USD(product_directory, self.core)


    def openWithCST(self, product_directory: str):
        
        
        files = os.listdir(product_directory)
        usd_path = None
        for file in files:
            # avoid backup usd file
            if ".usd" in file and not file.endswith(".bak"):
                usd_path = os.path.join(product_directory, file)
                break
        if usd_path is None:
            return
        
        cst_dir = "C:/ILLOGIC_APP/cst_3dinfo-v0.3.9/bin"
        cst_app = "cst_3dinfo.exe"

        command = [os.path.join(cst_dir, cst_app), usd_path]
        
        subprocess.Popen(command, cwd=cst_dir)
