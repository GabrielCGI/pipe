# RemoveSetShot.py

name = "RemoveSetShot"
classname = "RemoveSetShot"


class RemoveSetShot:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"

        # only in Houdini
        if self.core.appPlugin.pluginName == "Houdini":
            self.core.registerCallback("postInitialize", self.postInitialize, plugin=self)
            if self.core.status != "starting":
                self.postInitialize()

    def postInitialize(self):
        usdPlug = self.core.getPlugin("USD")
        if usdPlug:
            self.core.plugins.monkeyPatch(usdPlug.api.houdini_setShot, self.houdini_setShot, self, force=True)

    def houdini_setShot(self, origin):
        # do nothing
        pass