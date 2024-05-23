from PySide2 import QtCore, QtGui, QtWidgets
import pymel.core as pm
import shiboken2
import maya.OpenMayaUI as omui

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class LineEditWithDrop(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super(LineEditWithDrop, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            self.setText(event.mimeData().text())
            event.acceptProposedAction()

class ColorTransferUI(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(ColorTransferUI, self).__init__(parent)

        self.setWindowTitle("Color Transfer Tool")
        self.setFixedSize(300, 150)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        layout = QtWidgets.QVBoxLayout(self)

        self.source_attr = LineEditWithDrop(self)
        self.source_attr.setPlaceholderText("Drag source attribute here")

        self.dest_attr = LineEditWithDrop(self)
        self.dest_attr.setPlaceholderText("Drag destination attribute here")

        self.transfer_button = QtWidgets.QPushButton("Transfer", self)
        self.transfer_button.clicked.connect(self.transfer_color)

        layout.addWidget(self.source_attr)
        layout.addWidget(self.dest_attr)
        layout.addWidget(self.transfer_button)

    def transfer_color(self):
        source_attr = self.source_attr.text()
        dest_attr = self.dest_attr.text()

        if source_attr and dest_attr:
            try:
                source_value = pm.getAttr(source_attr)
                pm.setAttr(dest_attr, source_value)
                pm.displayInfo(f"Color transferred from {source_attr} to {dest_attr}.")
            except pm.MayaAttributeError as e:
                pm.displayError(f"Error: {e}")
        else:
            pm.displayWarning("Please provide both source and destination attributes.")
