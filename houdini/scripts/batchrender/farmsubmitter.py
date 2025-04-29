import sys
import PrismInit

USD_PLUGIN = PrismInit.pcore.getPlugin('USD')
LOP_RENDER = USD_PLUGIN.api.lopRender

loprender_module = sys.modules[LOP_RENDER.__module__]

class Farm_Submitter(loprender_module.Farm_Submitter):
    
    def __init__(self, origin, states, kwargs):
        super().__init__(origin, states[0], kwargs)
        self.states = states
    
    def submit(self):
        self.hide()
        self.state.ui.gb_submit.setCheckable(True)
        self.state.ui.gb_submit.setChecked(True)

        sanityChecks = bool(self.kwargs["node"].parm("sanityChecks").eval())
        version = 'next'
        saveScene = bool(self.kwargs["node"].parm("saveScene").eval())
        incrementScene = saveScene and bool(
            self.kwargs["node"].parm("incrementScene").eval()
        )

        sm = self.core.getStateManager()
        result = sm.publish(
            successPopup=False,
            executeState=True,
            states=self.states,
            useVersion=version,
            saveScene=saveScene,
            incrementScene=incrementScene,
            sanityChecks=sanityChecks,
            versionWarning=False,
        )
        if result:
            msg = "Job submitted successfully."
            self.core.popup(msg, severity="info")

        self.close()