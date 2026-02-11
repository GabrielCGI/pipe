import qtpy.QtWidgets as qt



from PrismUtils.Decorators import err_catcher #type: ignore



class CustomExportAnim(qt.QWidget):
    className = "Export Animation"
    listType = "Export"

    def setup(self, state, core, stateManager, stateData=None):
        self.core = core
        self.state = state
        self.stateManager = stateManager
        self.canSetVersion = True
        self.setupUi()
        self.connectEvents()

        if stateData is not None:
            self.loadData(stateData)

    @err_catcher(name=__name__)
    def loadData(self, data):
        if "statename" in data:
            self.e_name.setText(data["statename"])
        if "option1" in data:
            self.chb_option1.setChecked(data["option1"])
        if "fileFormat" in data:
            idx = self.cb_format.find(data["fileFormat"])
            if idx != -1:
                self.cb_format.setCurrentIndex(idx)
        if "stateenabled" in data and self.listType == "Export":
            self.state.setCheckState(
                0,
                eval(
                    data["stateenabled"]
                    .replace("PySide.QtCore.", "")
                    .replace("PySide2.QtCore.", "")
                ),
            )

        self.core.callback("onStateSettingsLoaded", self, data)

    @err_catcher(name=__name__)
    def setupUi(self):
        self.lo_main = qt.QVBoxLayout(self)
        
        self.w_name = qt.QWidget()
        self.lo_main.addWidget(self.w_name)

        self.lo_name = qt.QVBoxLayout(self.w_name)

        self.l_name = qt.QLabel("Name:")
        self.lo_name.addWidget(self.l_name)

        self.editLine = qt.QTextEdit()
        self.lo_name.addWidget(self.editLine)



    @err_catcher(name=__name__)
    def connectEvents(self):
        pass

    @err_catcher(name=__name__)
    def nameChanged(self, text):
        self.state.setText(0, text)

    @err_catcher(name=__name__)
    def updateUi(self):
        return True

    @err_catcher(name=__name__)
    def preExecuteState(self):
        warnings = []

        return [self.state.text(0), warnings]

    @err_catcher(name=__name__)
    def executeState(self, parent, useVersion="next"):
        fileName = self.core.getCurrentFileName()
        entity = self.core.getScenefileData(fileName)
        plugin_usd = self.core.getPlugin("USD")
        layer_USD_path = plugin_usd.api.getNewEntityUsdPath(entity)

        print(layer_USD_path)
        result = {"result": "success"}
        if result["result"] == "success":
            return [self.state.text(0) + " - success"]
        else:
            return [
                self.state.text(0)
                + " - error - %s" % result["error"]
            ]

    @err_catcher(name=__name__)
    def getStateProps(self):
        stateProps = {}
        return stateProps