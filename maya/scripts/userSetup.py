import maya.cmds as cmds

PLUGIN = "LookdevXMaya"

def force_autoload_off():
    try:
        all_plugins = cmds.pluginInfo(q=True, listPlugins=True) or []
        if PLUGIN not in all_plugins:
            return

        cmds.pluginInfo(PLUGIN, e=True, autoload=False)
        cmds.pluginInfo(savePluginPrefs=True)

        print(f"{PLUGIN}: AutoLoad forced OFF")

    except Exception as e:
        print(f"Error: {e}")

cmds.evalDeferred(force_autoload_off)
