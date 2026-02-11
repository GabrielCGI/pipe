import logging

try:
    _HAS_HOU = True
    import hou # type: ignore
except ImportError:
    _HAS_HOU = False

from . import usd_updater

logger = logging.getLogger(__name__)
PRISM_IMPORT_TYPE = 'prism::LOP_Import::1.0'

if _HAS_HOU: # pragma: no cover
    PRISM_BASE_COLOR = hou.Color(0.451, 0.369, 0.796)
    TO_UPDATE_COLOR = hou.Color(0.8, 0.1, 0.1)


    def getPrismImport() -> list[hou.OpNode]:
        stage: hou.LopNetwork = hou.node('/stage')
        prism_imports = []
        for node in stage.allNodes():
            if node.type().name() == PRISM_IMPORT_TYPE:
                prism_imports.append(node)
        return prism_imports
        
        
    def checkEveryNodes():
        selected_nodes = hou.selectedNodes()
        hou.clearAllSelected()

        prism_imports = getPrismImport()
        for node in prism_imports:
            path = node.parm('filepath').eval()
            instance = hou.qt.mainWindow()
            updater = usd_updater.MainInterface(
                openType='prism',
                pathPrism=path,
                ar_context=None,
                check_update_only=True,
                parent=instance
            )
            versions = updater.check_latest_container(path)
            if (not versions is None and (versions[0] != versions[1])
                or not updater.isUpdate()):
                node.setColor(TO_UPDATE_COLOR)
                logger.info(f"{node.name()} need to be updated")
            else:
                node.setColor(PRISM_BASE_COLOR)
                logger.info(f"{node.name()} is updated")

        if selected_nodes:
            for node in selected_nodes:
                node.setSelected(True)