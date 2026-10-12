import logging 



logger = logging.getLogger("IllogicPlugin."+__name__)
IMPORT_PRISM = True
try:
    import PrismInit
except ImportError:
    IMPORT_PRISM = False



def setSolarisViewportsInDestop(renderer_name):
    import hou #type: ignore
    desktop = hou.ui.curDesktop()
    for pane_tab in desktop.paneTabs():
        try:
            if (pane_tab.type() != hou.paneTabType.SceneViewer) and not pane_tab.isViewingSceneGraph():
                continue
            if renderer_name not in pane_tab.hydraRenderers():
                print(f"'{renderer_name}' not available in {pane_tab.name()}")
            
            pane_tab.setHydraRenderer(renderer_name)
            pane_tab.restartRenderer()
        except Exception as e:
            logger.debug(str(e))


def main(*args, **kwargs):
    if IMPORT_PRISM is False:
        return
    
    logger.info("START: file Hook onSceneOpen")
    dcc = PrismInit.pcore.appPlugin.pluginName
    if dcc == "Maya":
        import maya.mel as mel #type: ignore
        logger.info("set LightIntensity and generate all previews udims")
        mel.eval("""setAttr "hardwareRenderingGlobals.defaultLightIntensity" 3;""")
        mel.eval("generateAllUvTilePreviews;")

    elif dcc == "Houdini":
        logger.info("force setup viewport to solaris")
        setSolarisViewportsInDestop("Houdini VK")
    
    logger.info("END: file Hook onSceneOpen")