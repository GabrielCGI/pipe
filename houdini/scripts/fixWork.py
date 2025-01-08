

name = "FixWorklayer"
classname = "FixWorklayer"

import os

class FixWorklayer:
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
            self.core.plugins.monkeyPatch(usdPlug.api.setEditTargetToWorkLayer, self.setEditTargetToWorkLayer, self, force=True)

    def setEditTargetToWorkLayer(self, stage):
        api = self.core.getPlugin("USD").api
        sessionLayer = stage.GetSessionLayer()
        for layerpath in sessionLayer.subLayerPaths:
            layer = api.findLayerFromPath(layerpath)
            if layer.anonymous:
                idf = layer.identifier
            else:
                idf = os.path.splitext(os.path.basename(layer.realPath))[0]

            if idf == "work" or idf.endswith(":work"):
                workLayer = layer
                break
        else:
            workLayer = api.createAnonymousSublayer("work")
            result = api.addSubLayerToSubLayer(workLayer, sessionLayer)
            if result is not True:
                return

        target = api.getEditTarget(workLayer)
        stage.SetEditTarget(target)