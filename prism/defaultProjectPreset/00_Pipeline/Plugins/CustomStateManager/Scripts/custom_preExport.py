import maya.cmds as cmds




class CustomPreExport():
    def __init__(self, kwargs):
        self.all_kargs = kwargs
        self.state = kwargs["state"]
        
        if self.state.className != "Export" and self.state.className != "USD Export":
            return
        