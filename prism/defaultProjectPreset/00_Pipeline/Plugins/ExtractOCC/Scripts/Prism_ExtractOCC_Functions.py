from PrismUtils.Decorators import err_catcher_plugin as err_catcher #type: ignore
import os
import subprocess
import tempfile
import re


VENV_ACTIVATE = r"R:\devQuentin\quentin\work\resources\pipeline\scripts\.venv\Scripts\activate.bat"
EXTRACT_SCRIPT = r"R:\devQuentin\quentin\work\resources\pipeline\scripts\sandbox\extract_ao_pass_v5.py"


class Prism_ExtractOCC_Functions(object):

    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        # self.core.registerCallback(
        #     "openPBListContextMenu", self.mediaVersionContextMenu, plugin=self
        # )
        self.core.registerCallback("openPBListContextMenu", self.mediaContextMenuRequested, plugin=self)

    # @err_catcher(name=__name__)
    # def mediaVersionContextMenu(self, mediaBrowser, menu, lw, item, path):
    #     if item is None or lw.objectName() != "tw_versions":
    #         return

    #     action = menu.addAction("extractOCC")
    #     action.triggered.connect(lambda: self.runExtractOCC(path))

    def _ends_with_version(self, path: str) -> bool:
        return bool(re.search(r'\\v\d{3}$', path))

    @err_catcher(name=__name__)
    def runExtractOCC(self, path):

        if self._ends_with_version(path):
            path = path + "/beauty"

        bat = tempfile.NamedTemporaryFile(
            mode="w", suffix=".bat", delete=False, newline="\r\n"
        )
        bat.write(
            "@echo on\r\n"
            f'call "{VENV_ACTIVATE}"\r\n'
            f'python "{EXTRACT_SCRIPT}" "{path}"\r\n'
            "pause\r\n"
        )
        bat.close()
        subprocess.Popen(
            ["cmd.exe", "/c", bat.name],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

    @err_catcher(name=__name__)
    def mediaContextMenuRequested(self, mediaBrowser, menu, lw, item, path):
        if item is None:
            return
        
        if lw.objectName() == "tw_identifier":
            if item.childCount() >= 1:
                return
        
        self.add_copy_actions(menu, path)

    def add_copy_actions(self, menu, path):
        act_cloud = menu.addAction("Extract OCC")
        act_cloud.triggered.connect(lambda: self.runExtractOCC(path))
