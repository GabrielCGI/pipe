name = "CopyToCloud"
classname = "CopyToCloud"

import os
import sys
import json
import tempfile
import subprocess
from qtpy.QtWidgets import QAction, QMessageBox
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
        self.core.registerCallback("openPBListContextMenu", self.mediaContextMenuRequested, plugin=self)



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
    
    @err_catcher(name=__name__)
    def mediaContextMenuRequested(self, mediaBrowser, menu, lw, item, path):
        if item is None:
            return
        
        if lw.objectName() == "tw_identifier":
            if item.childCount() >= 1:
                return
        
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

    def _ask(self, title, message):
        reply = QMessageBox.question(None, title, message, QMessageBox.Yes | QMessageBox.No)
        return reply == QMessageBox.Yes

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

        # Prompt if destination folder already exists
        if os.path.isdir(dst):
            if not self._ask("Destination exists", f"Destination folder already exists:\n{dst}\n\nContinue?"):
                return

        if os.path.isfile(src):
            if not self._collect_file_decision(dst):
                return
            decisions = {self.normalize_path(dst): self._file_overwrite_decision}
        elif os.path.isdir(src):
            decisions = {}
            if not self._collect_dir_decisions(src, dst, decisions):
                return
        else:
            self.core.popup("Invalid source type (not a file or folder)", severity="error")
            return

        # Write decisions to a temp file and launch the worker subprocess
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(decisions, tmp)
        tmp.close()

        worker = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_copy_worker.py")
        subprocess.Popen(
            [sys.executable, worker, src, dst, tmp.name],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )

        self.core.popup(f"Copy started in the background to:\n{dst}")

    def _collect_file_decision(self, dst):
        """Prompt once if destination file exists. Stores decision on self."""
        self._file_overwrite_decision = True
        if os.path.exists(dst):
            if not self._ask("File exists", f"File already exists:\n{dst}\n\nOverwrite?"):
                return False
        return True

    def _collect_dir_decisions(self, src_dir, dst_dir, decisions):
        """
        Walk src tree upfront, prompt once per folder that has conflicts.
        Populates decisions dict: { normpath(dst_folder): True/False }.
        Returns False if user cancelled at any point.
        """
        items = os.listdir(src_dir)
        files = [i for i in items if os.path.isfile(os.path.join(src_dir, i))]
        subdirs = [i for i in items if os.path.isdir(os.path.join(src_dir, i))]

        existing = [f for f in files if os.path.exists(os.path.join(dst_dir, f))]
        if existing:
            overwrite = self._ask(
                "Files exist",
                f"{len(existing)} file(s) already exist in:\n{dst_dir}\n\nOverwrite?"
            )
            decisions[self.normalize_path(dst_dir)] = overwrite

        for d in subdirs:
            src_sub = os.path.join(src_dir, d)
            dst_sub = os.path.join(dst_dir, d)
            if not self._collect_dir_decisions(src_sub, dst_sub, decisions):
                return False

        return True
