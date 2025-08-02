name = "CopyToCloud"
classname = "CopyToCloud"

import os
import sys
import shutil
from pathlib import Path
from qtpy.QtWidgets import QAction
import qtpy.QtWidgets as qt 
from PrismUtils.Decorators import err_catcher_plugin as err_catcher


file_path = os.path.abspath(__file__)
porjet = file_path.split("\\")[1]
LOCAL = rf"I:/{porjet}"
CLOUD = rf"I:/{porjet}/04_Resources/googleCache"

class CopyToCloud:
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
        return norm_path.startswith(self.normalize_path(LOCAL)) and not norm_path.startswith(self.normalize_path(CLOUD))

    def is_valid_cloud_path(self, path):
        if not path or not os.path.exists(path):
            return False

        norm_path = self.normalize_path(path)
        return norm_path.startswith(self.normalize_path(CLOUD))

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
            act_cloud = menu.addAction("Copy to cloud")
            act_cloud.triggered.connect(lambda: self.copy_to_cloud(path))
        elif self.is_valid_cloud_path(path):
            act_local = menu.addAction("Copy to local")
            act_local.triggered.connect(lambda: self.copy_to_local(path))

    def copy_to_cloud(self, src):
        self.copy_to(src, LOCAL, CLOUD)

    def copy_to_local(self, src):
        self.copy_to(src, CLOUD, LOCAL)

    def copy_to(self, src, src_root, dest_root):
        norm_src = self.normalize_path(src)
        norm_src_root = self.normalize_path(src_root)

        if not norm_src.startswith(norm_src_root):
            self.core.popup(
                f"Source path doesn't match expected prefix.\n"
                f"Path:   {src}\n"
                f"Prefix: {src_root}",
                severity="error"
            )
            return

        relative_path = norm_src[len(norm_src_root):].lstrip("\\/")
        dst = os.path.join(dest_root, relative_path)

        try:
            self.copiePaste(src, dst)
            explorer_target = os.path.dirname(dst)
            self.core.popup(f"Copied successfully to:\n{dst}", severity="info")
            os.startfile(explorer_target)

        except Exception as e:
            self.core.popup(f"Copy failed:\n{e}", severity="error")
    

    def copiePaste(self, src, dest):
        src = Path(src)
        dest = Path(dest)
        forAll = None
        forNo = None
        for root, dirs, files in os.walk(src):
            rel_path = Path(root).relative_to(src)
            dest_dir = dest / rel_path
            dest_dir.mkdir(parents=True, exist_ok=True)
            for file in files:
                src_file = Path(root) / file
                dest_file = dest_dir / file
                
                if dest_file.exists() and not forAll:
                    if forNo:
                        continue
                    choix = show_custom_question(dest_file)
                    if choix == "Yes":
                        self.replaceFIle(src_file, dest_file)
                    elif choix == "No":
                        continue
                    elif choix == "yes for All":
                        self.replaceFIle(src_file, dest_file)
                        forAll = True
                    elif choix == "No for All":
                        forNo = True
                        continue
                else:
                    self.replaceFIle(src_file, dest_file)

    def replaceFIle(self, src, dst):
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            self.core.popup(f"Copy failed:\n{e}", severity="error")




#petit interface pour choisir si on veux tout remplacer ou uniquement le fichier en question
def show_custom_question(path):
    msg_box = qt.QMessageBox()
    msg_box.setWindowTitle("Conflit de fichier")
    msg_box.setText(f"The file already exists. What would you like to do ?\n{path}")

    bouton_oui = msg_box.addButton("Replace", qt.QMessageBox.YesRole)
    bouton_tout = msg_box.addButton("Replace all", qt.QMessageBox.AcceptRole)
    bouton_non = msg_box.addButton("Ignore", qt.QMessageBox.NoRole)
    bouton_aucun = msg_box.addButton("Ignore all", qt.QMessageBox.RejectRole)

    msg_box.exec_()
    if msg_box.clickedButton() == bouton_oui:       return "Yes"
    elif msg_box.clickedButton() == bouton_non:     return "No"
    elif msg_box.clickedButton() == bouton_tout:    return "yes for All"
    elif msg_box.clickedButton() == bouton_aucun:   return "No for All"