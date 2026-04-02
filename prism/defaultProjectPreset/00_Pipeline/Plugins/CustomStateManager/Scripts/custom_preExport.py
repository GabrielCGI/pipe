



class CustomPreExport():
    def __init__(self, kwargs):
        self.all_kargs = kwargs
        self.state = kwargs["state"]
        
        if self.state.className != "Export" and self.state.className != "USD Export":
            return
        if self.state.cb_rangeType.currentIndex() != 2:
            return
        
        #recuperer la frame n+ quelque chose pour la mettre dans l'export
        # value = self.state.Illo_spin_frame_plus_10.value()-1
        # kwargs["startframe"] = kwargs["startframe"] - value
        # kwargs["endframe"] = kwargs["endframe"] + value 