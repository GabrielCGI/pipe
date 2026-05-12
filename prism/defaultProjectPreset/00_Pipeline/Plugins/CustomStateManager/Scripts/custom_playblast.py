

from qtpy import QtWidgets as Qt

class CustomPlayblast():
    STATUS = [
            'rev',
            'na' ,
            "bug",
            'q0' ,
            'app'
        ]
    
    def __init__(self, state):
        self.state = state
        
        if self.state.ui.className != "Playblast":
            return
        
        self.insertStatusCBB()
        
    def insertStatusCBB(self):
        prj_publish_layout: Qt.QHBoxLayout = self.state.ui.lo_prjMngPublish
        if prj_publish_layout.count() != 3:
            return

        status_cb = Qt.QComboBox()
        status_cb.addItems(self.STATUS)
        status_cb.setCurrentText(self.STATUS[0])
        
        prj_publish_layout.insertWidget(2, status_cb)
        