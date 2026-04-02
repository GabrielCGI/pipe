#from Plugins.clamp_texture import EXECUTE_DEPARTEMENT #type: ignore


def main(*args, **kwargs):
    # print('------------------ DEBUG ON SCENE OPEN ------------------')
    try:
        # PrismInit exists only in Houdini and Maya,
        # and will failed to import in Nuke
        import PrismInit
    except ImportError:
        return
    dcc = PrismInit.pcore.appPlugin.pluginName

    if dcc == "Maya":
        import maya.mel as mel
        import maya.cmds as cmds
        mel.eval("generateAllUvTilePreviews;")

    # print('------------------ DEBUG ON SCENE OPEN ------------------')