name = "ChangeHuskRenderCommand"
classname = "ChangeHuskRenderCommand"


class ChangeHuskRenderCommand:
    def __init__(self, core):
        self.core = core
        self.version = "v1.1.0"
        
        if self.core.appPlugin.pluginName not in ["Houdini", "Maya"]:
              return
          
        # check if USD plugin is loaded
        dlPlugin = self.core.getPlugin("USD")
        if dlPlugin:
            # if yes, patch the function
            self.applyPatch(dlPlugin)

        # register callback in case the USD plugin will be loaded later on
        # this is important if the plugin gets loaded later on during the startup or manually by the user
        self.core.registerCallback(
            "pluginLoaded", self.onPluginLoaded, plugin=self
        )

    def onPluginLoaded(self, plugin):
        # check if the loaded plugin is the USD plugin and if yes apply the patch
        if plugin.pluginName == "USD":
            self.applyPatch(plugin)

    def applyPatch(self, plugin):
        print("Patching HUSK Render Command - V003")
        # apply the monkeypatch to the "getHuskRenderScript" function of the USD plugin
        self.core.plugins.monkeyPatch(plugin.getHuskRenderScript, self.getHuskRenderScript, self, force=True)

    def getHuskRenderScript(self):
        script_path = r"R:/pipeline/pipe/prism/ranch_cache_scripts/husk_render_v3.py"
        with open(script_path, "r", encoding="utf-8") as f:
            script = f.read()
        return script