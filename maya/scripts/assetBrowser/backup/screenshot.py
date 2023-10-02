import sys
from PySide2.QtWidgets import QApplication, QRubberBand, QLabel, QVBoxLayout, QWidget
from PySide2.QtCore import Qt, QRect
from PySide2.QtGui import QPixmap, QPainter
#from PIL import ImageGrab


class ScreenCaptureTool(QWidget):
    def __init__(self):
        super().__init__()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = None
        self.layout = QVBoxLayout()
        self.label = QLabel("Drag the mouse to capture a region")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setWindowOpacity(0.5)
        self.showMaximized()

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        self.rubberBand.hide()
        rect = self.rubberBand.geometry()
        self.close()
        self.captureScreen(rect)

    def captureScreen(self, rect):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
        screenshot.save('D:\\screenshot.png', 'png')


try:

    ui.deleteLater()
except:
    pass
ui = ScreenCaptureTool()
ui.create()
ui.show()

