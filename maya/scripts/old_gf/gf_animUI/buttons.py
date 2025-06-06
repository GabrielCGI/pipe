import math, json, sys
import maya.cmds as cmds
# Retrieve the version of Maya currently in use
maya_version = cmds.about(version=True)

if maya_version.startswith("2022"):
    # Using PySide2 for Maya 2022
    from PySide2 import QtCore, QtWidgets, QtGui
elif maya_version.startswith("2025"):
    # Using PySide6 for Maya 2025
    # Note: QAction and QShortcut have moved from QtWidgets to QtGui in PySide6
    from PySide6 import QtCore, QtWidgets, QtGui

import pymel.core as pm
from gf_animUI import ui_tools as uiUtils


def getPolygonPoints(n, r, sx=0, sy=0):
    x, y = (0.0, -r)
    points = [QtCore.QPoint(sx + x +r, sy + y +r)]
    step = 360.0/n
    for v in range(1, n):
        angle = math.radians(v * step)
        cs = math.cos(angle)
        sn = math.sin(angle)

        px = x * cs - y * sn
        py = x * sn + y * cs
        points.append(QtCore.QPoint(sx + px + r, sy + py + r))
    return points


class CustomButton(QtWidgets.QPushButton):
    _TYPE = 'default'
    _EDIT = False
    buttonEdited = QtCore.Signal(dict)
    shapeChangeRequested = QtCore.Signal(str)
    deleteRequested = QtCore.Signal()
    doubleClicked = QtCore.Signal()
    rbSelected = QtCore.Signal()

    def __init__(self, color=QtGui.QColor(240, 100, 100, 255), label='', border=1, x=5, y=5, width=50, height=50, parent=None, commandType='select', **kwargs):
        if isinstance(color, (tuple, list)):
            color = QtGui.QColor(*color)
        super(CustomButton, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.setFixedSize(width, height)
        self.setGeometry(x, y, width, height)
        self._label = label
        self._color = color
        self._border = border
        self._commandType = commandType
        self._internalData = {}

    def paintEvent(self, event):
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        paint = QtGui.QPainter()
        paint.begin(self)
        geom = option.rect
        paint.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_color = self._getBgColor()
        # Draw Shape
        paint.setBrush(bg_color)
        paint.setPen(self._getBorderPen())
        paint.drawRect(QtCore.QRect(2, 2, geom.width() - 4, geom.height() - 4))

        # Draw Text
        paint.setPen(self._getTextColor())
        paint.drawText(geom, self._label, QtGui.QTextOption(QtCore.Qt.AlignCenter))
        paint.end()

    def sizeHint(self, *args, **kwargs):
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)
        geom = option.rect

        return QtCore.QSize(geom.width(), geom.height())

    def setEditMode(self, value):
        self._EDIT = value
        if not value:
            self.setChecked(False)
        self.setCheckable(value)

    def _getBgColor(self):
        geom = self.geometry()
        if not self.isEnabled():
            return QtGui.QColor(125,125,125)
        rgb = [self._color.red(), self._color.green(), self._color.blue()]
        colorA = list([sorted([0, comp * 1.2, 255])[1] for comp in rgb])
        colorB = list([sorted([0, comp * 0.8, 255])[1] for comp in rgb])
        colorA = QtGui.QColor(colorA[0], colorA[1], colorA[2], self._color.alpha())
        colorB = QtGui.QColor(colorB[0], colorB[1], colorB[2], self._color.alpha())

        bg_gradient = QtGui.QLinearGradient(0, 0, geom.width(), geom.height())
        bg_gradient.setCoordinateMode(QtGui.QGradient.StretchToDeviceMode)
        bg_gradient.setStart(0.0,0.0)
        bg_gradient.setFinalStop(0.3, 1.0)
        if self.isDown():
            bg_gradient.setColorAt(.2, colorB)
            bg_gradient.setColorAt(.8, colorA)
        elif self.underMouse():
            bg_gradient.setColorAt(0, colorA)
            bg_gradient.setColorAt(1, colorA)
        else:
            bg_gradient.setColorAt(.2, colorA)
            bg_gradient.setColorAt(.8, colorB)

        return bg_gradient

    def _getBorderPen(self):
        if self.isEnabled():
            color = self.palette().color(QtGui.QPalette.Dark)
        else:
            color = self.palette().color(QtGui.QPalette.Light)

        if self.isChecked():
            pen = QtGui.QPen(QtCore.Qt.red, 2, s=QtCore.Qt.SolidLine)
            return pen

        if self._border == 0:
            pen = QtGui.QPen(QtCore.Qt.NoPen)
        elif self._border == 1:
            pen = QtGui.QPen(color, 1, s=QtCore.Qt.SolidLine)
        elif self._border == 2:
            pen = QtGui.QPen(color, 2, s=QtCore.Qt.SolidLine)
        elif self._border == 3:
            pen = QtGui.QPen(color, 2, s=QtCore.Qt.DashLine)
        else:
            pen = QtGui.QPen(color, 2, s=QtCore.Qt.DotLine)
        return pen

    def _getTextColor(self):
        colorAvg = sum(self._color.toTuple()[:3])/3
        if not self.isEnabled():
            return QtGui.QColor(80, 80, 80)
        if colorAvg < 128:
            return QtGui.QColor(220,220,220)
        else:
            return QtGui.QColor(20,20,20)

    def resizeEvent(self, event):
        super(CustomButton, self).resizeEvent(event)
        self.updateGeometry()

    def getData(self):
        data = {'type': self._TYPE,
                'color': (self._color.red(), self._color.green(), self._color.blue(), self._color.alpha()),
                'label': self._label,
                'border': self._border,
                'x': self.x(),
                'y': self.y(),
                'width': self.width(),
                'height': self.height(),
                'commandType': self._commandType}
        return data

    def setData(self, **kwargs):
        color = kwargs.get('color', None)
        label = kwargs.get('label', None)
        border = kwargs.get('border', None)
        x = kwargs.get('x', None)
        y = kwargs.get('y', None)
        width = kwargs.get('width', None)
        height = kwargs.get('height', None)

        if color is not None:
            self.setColor(QtGui.QColor(color))

        if label is not None:
            self.setLabel(label)

        if border is not None:
            self.setBorder(border)

        if width is not None:
            self.setWidth(width)

        if height is not None:
            self.setHeight(height)

        if x is not None:
            self.move(QtCore.QPoint(x, self.y()))

        if y is not None:
            self.move(QtCore.QPoint(self.x(), y))

    def setInternalData(self, **kwargs):
        self._internalData.update(kwargs)

    def getInternalData(self):
        return self._internalData

    def mousePressEvent(self, event):
        self.__mousePressPos = None
        self.__mouseMovePos = None
        if not self._EDIT:
            super(CustomButton, self).mousePressEvent(event)
            return

        if event.button() == QtCore.Qt.MidButton:
            self.__mousePressPos = event.globalPos()
            self.__mouseMovePos = event.globalPos()

        if event.button() == QtCore.Qt.LeftButton:
            self.toggle()

        if event.button() == QtCore.Qt.RightButton:
            self.openMenu(event.globalPos())

    def mouseMoveEvent(self, event):
        if not self._EDIT:
            super(CustomButton, self).mouseMoveEvent(event)
        else:
            if event.buttons() == QtCore.Qt.MidButton:


                globalPos = event.globalPos()
                diff = globalPos - self.__mouseMovePos
                self.moveBy(diff)

                self.__mouseMovePos = globalPos

    def moveBy(self, vector=QtCore.QPoint()):
        parent = self.parentWidget()
        globalPos = self.mapToGlobal(self.pos())
        newPos = self.mapFromGlobal(globalPos + vector)
        clampedPos = QtCore.QPoint(sorted((0, newPos.x(), parent.width() - 30))[1], sorted((0, newPos.y(), parent.height() - 30))[1])
        self.move(clampedPos)

    def mouseReleaseEvent(self, event):
        if not self._EDIT:
            super(CustomButton, self).mouseReleaseEvent(event)
        else:
            if self.__mousePressPos is not None:
                moved = event.globalPos() - self.__mousePressPos
                if moved.manhattanLength() > 3:
                    event.ignore()
                    self.buttonEdited.emit(self.getData())
                    return

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()

    def openMenu(self, pos):
        menu = QtWidgets.QMenu(self)
        if self._EDIT:
            execAction = menu.addAction('Execute')
            execAction.triggered.connect(self.clicked.emit)
            menu.addSeparator()
            shapeNames = [k for k in button_types.keys() if k != self._TYPE]
            shpMenu = menu.addMenu('Change Shape')
            for shp in shapeNames:
                action = shpMenu.addAction(shp)
                action.triggered.connect(lambda s=shp: self.shapeChangeRequested.emit(s))

            editAction = menu.addAction('Edit...')
            editAction.triggered.connect(self.openEditDialog)

            deleteAction = menu.addAction('Delete')
            deleteAction.triggered.connect(self.deleteRequested.emit)
            menu.exec_(pos)

    def openEditDialog(self):
        # initialData = self.getData()
        dialog = self.getOptionsWidget(asDialog=True, okButton=True)[0]
        dialog.setWindowTitle('Edit Button')
        dialog.show()
        dialog.accepted.connect(lambda: self.buttonEdited.emit(self.getData()))
        # dialog.rejected.connect(lambda: self.setData(**initialData))

    def getOptionsWidget(self, asDialog=False, okButton=False):
        if asDialog:
            widget = QtWidgets.QDialog(self.parentWidget())
        else:
            widget = QtWidgets.QFrame()
            widget.setFrameShape(QtWidgets.QFrame.StyledPanel)
            widget.setFrameShadow(QtWidgets.QFrame.Plain)
            widget.setLineWidth(1)
            widget.setMidLineWidth(0)
        layout = QtWidgets.QVBoxLayout(widget)

        layout.setContentsMargins(4, 4, 4, 4)

        # Label
        label = uiUtils.LabeledField('Label')
        labelField = QtWidgets.QLineEdit()
        labelField.setMaximumWidth(200)
        labelField.setText(self._label)
        label.setField(labelField)
        labelField.textChanged.connect(self.setLabel)

        # Border Type
        border = uiUtils.LabeledField('Border')
        borderField = QtWidgets.QSpinBox()
        border.setField(borderField)
        borderField.setMinimum(0)
        borderField.setMaximum(4)
        borderField.setValue(self._border)
        borderField.valueChanged.connect(self.setBorder)

        # Size
        size = uiUtils.LabeledField('Size')
        sizeField = uiUtils.Vector2DField((self.geometry().width(), self.geometry().height()))
        size.setField(sizeField)
        sizeField.xField.valueChanged.connect(self.setWidth)
        sizeField.yField.valueChanged.connect(self.setHeight)

        # Color
        color = uiUtils.LabeledField('Color')
        colorField = uiUtils.ColorPickerField(self._color)
        color.setField(colorField)
        colorField.colorChanged.connect(self.setColor)

        for field in (label, border, size, color):
            layout.addWidget(field)

        if okButton and asDialog:
            btn = QtWidgets.QPushButton('OK')
            btn.clicked.connect(widget.accept)
            layout.addWidget(btn)

        result = {'label': labelField,
                  'border': borderField,
                  'width': sizeField.xField,
                  'height': sizeField.yField,
                  'color': colorField}

        return widget, result

    # ---- Label ---- #
    def getLabel(self):
        return self._label

    def setLabel(self, value):
        self._label = value
        self.update()

    # ---- Color ---- #
    def getColor(self):
        return self._color

    def setColor(self, value):
        self._color = value
        self.update()

    # ---- Border ---- #
    def getBorder(self):
        return self._border

    def setBorder(self, value):
        self._border = value
        self.update()

    # ---- Size ---- #
    def getWidth(self):
        geom = self.geometry()
        return geom.width()

    def setWidth(self, value):
        geom = self.geometry()
        geom.setWidth(value)
        self.setGeometry(geom)
        self.update()

    def getHeight(self):
        geom = self.geometry()
        return geom.height()

    def setHeight(self, value):
        geom = self.geometry()
        geom.setHeight(value)
        self.setGeometry(geom)
        self.update()

    @classmethod
    def getEditMenu(cls, buttons, parent=None):
        menu = QtWidgets.QMenu(parent)

        if not len(buttons):
            return menu

        labelAction = menu.addAction('Label')
        colorAction = menu.addAction('Color')
        borderAction = menu.addAction('Border')
        sizeAction = menu.addAction('Size')

        # Label
        labelField = cls.getLabelField()
        labelField.setText(buttons[0].getLabel())
        labelField.textChanged.connect(lambda x: cls.setLabels(buttons, x))
        labelDialog = cls.getAttributeEditDialog('Label', labelField, parent)
        labelAction.triggered.connect(labelDialog.exec_)

        # Color
        colorField = cls.getColorField()
        colorField.setColor(buttons[0].getColor())
        colorField.colorChanged.connect(lambda x: cls.setColors(buttons, x))
        colorDialog = cls.getAttributeEditDialog('Color', colorField, parent)
        colorAction.triggered.connect(colorDialog.exec_)

        # Border
        borderField = cls.getBorderField()
        borderField.setValue(buttons[0].getBorder())
        borderField.valueChanged.connect(lambda x: cls.setBorders(buttons, x))
        borderDialog = cls.getAttributeEditDialog('Border', borderField, parent)
        borderAction.triggered.connect(borderDialog.exec_)

        # Border
        sizeField = cls.getSizeField()
        sizeField.xField.setValue(buttons[0].getWidth())
        sizeField.yField.setValue(buttons[0].getHeight())
        sizeField.xField.valueChanged.connect(lambda x: cls.setWidths(buttons, x))
        sizeField.yField.valueChanged.connect(lambda x: cls.setHeights(buttons, x))
        sizeDialog = cls.getAttributeEditDialog('Size', sizeField, parent)
        sizeAction.triggered.connect(sizeDialog.exec_)

        return menu

    @classmethod
    def getLabelField(cls):
        labelField = QtWidgets.QLineEdit()
        labelField.setMaximumWidth(200)
        return labelField

    @classmethod
    def getBorderField(cls):
        borderField = QtWidgets.QSpinBox()
        borderField.setMinimum(0)
        borderField.setMaximum(4)
        return borderField

    @classmethod
    def getColorField(cls):
        colorField = uiUtils.ColorPickerField()
        return colorField

    @classmethod
    def getSizeField(cls):
        sizeField = uiUtils.Vector2DField()
        return sizeField

    @classmethod
    def getAttributeEditDialog(cls, name, field, parent=None):
        dialog = QtWidgets.QDialog(parent)
        dialog.setWindowTitle('Edit Attribute')
        layout = QtWidgets.QVBoxLayout(dialog)
        labeledField = uiUtils.CompactLabeledField(name)
        labeledField.setField(field)
        layout.addWidget(labeledField)
        return dialog

    @classmethod
    def setLabels(cls, buttons, value):
        for btn in buttons:
            if isinstance(btn, cls):
                btn.setLabel(value)
                btn.buttonEdited.emit(btn.getData())

    @classmethod
    def setBorders(cls, buttons, value):
        for btn in buttons:
            if isinstance(btn, cls):
                btn.setBorder(value)
                btn.buttonEdited.emit(btn.getData())

    @classmethod
    def setColors(cls, buttons, value):
        for btn in buttons:
            if isinstance(btn, cls):
                btn.setColor(value)
                btn.buttonEdited.emit(btn.getData())

    @classmethod
    def setWidths(cls, buttons, value):
        for btn in buttons:
            if isinstance(btn, cls):
                btn.setWidth(value)
                btn.buttonEdited.emit(btn.getData())

    @classmethod
    def setHeights(cls, buttons, value):
        for btn in buttons:
            if isinstance(btn, cls):
                btn.setHeight(value)
                btn.buttonEdited.emit(btn.getData())


class RoundedButton(CustomButton):
    _TYPE = 'rounded'

    def __init__(self, color=QtGui.QColor(240, 100, 100, 255), label='', border=1, x=5, y=5, width=50, height=50, radius=10, parent=None, commandType='select', **kwargs):
        super(RoundedButton, self).__init__(color=color, label=label, border=border, x=x, y=y,
                                            width=width, height=height, parent=parent, commandType=commandType)
        self._radius = radius

    def paintEvent(self, event):
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        paint = QtGui.QPainter()
        paint.begin(self)
        geom = option.rect
        paint.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_color = self._getBgColor()
        # Draw Shape
        paint.setBrush(bg_color)
        paint.setPen(self._getBorderPen())
        paint.drawRoundedRect(QtCore.QRect(2, 2, geom.width() - 4, geom.height() - 4), self._radius, self._radius)

        # Draw Text
        paint.setPen(self._getTextColor())
        paint.drawText(geom, self._label, QtGui.QTextOption(QtCore.Qt.AlignCenter))
        paint.end()

    def getData(self):
        data = super(RoundedButton, self).getData()
        data['radius'] = self._radius
        return data

    def getOptionsWidget(self, asDialog=False, okButton=False):
        frame, result = super(RoundedButton, self).getOptionsWidget(asDialog, okButton)

        # Radius Type
        radius = uiUtils.LabeledField('Radius')
        radiusField = QtWidgets.QSpinBox()
        radius.setField(radiusField)
        radiusField.setMinimum(1)
        radiusField.setValue(self._radius)
        frame.layout().addWidget(radius)
        radiusField.valueChanged.connect(self.setRadius)

        result['radius'] = radiusField

        return frame, result

    def setRadius(self, value):
        self._radius = value
        self.update()


class PolygonButton(CustomButton):
    _TYPE = 'polygon'

    def __init__(self, color=QtGui.QColor(240, 100, 100, 255), label='', border=1, x=5, y=5, width=50, sides=5, parent=None, commandType='select', **kwargs):
        super(PolygonButton, self).__init__(color=color, label=label, border=border, x=x, y=y,
                                            width=width, height=width, parent=parent, commandType=commandType)
        self._sides = sides

    def paintEvent(self, event):
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        paint = QtGui.QPainter()
        paint.begin(self)
        geom = option.rect
        paint.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_color = self._getBgColor()
        # Draw Shape
        paint.setBrush(bg_color)
        paint.setPen(self._getBorderPen())
        polygon = QtGui.QPolygon(getPolygonPoints(self._sides, (geom.width()-3)/2, 2, 2))
        paint.drawPolygon(polygon)

        # Draw Text
        paint.setPen(self._getTextColor())
        paint.drawText(geom, self._label, QtGui.QTextOption(QtCore.Qt.AlignCenter))
        paint.end()

        polygon = QtGui.QPolygon(getPolygonPoints(self._sides, geom.width() / 2))
        mask = QtGui.QRegion(polygon)
        self.setMask(mask)

    def getData(self):
        data = super(PolygonButton, self).getData()
        data['sides'] = self._sides
        data.pop('height')
        return data

    def getOptionsWidget(self, asDialog=False, okButton=False):
        frame, result = super(PolygonButton, self).getOptionsWidget(asDialog, okButton)

        # Sides Type
        sides = uiUtils.LabeledField('sides')
        sidesField = QtWidgets.QSpinBox()
        sides.setField(sidesField)
        sidesField.setMinimum(3)
        sidesField.setValue(self._sides)
        frame.layout().addWidget(sides)
        sidesField.valueChanged.connect(self.setSides)


        result['height'].setDisabled(True)
        result['height'].hide()
        result.pop('height')
        result['sides'] = sidesField

        return frame, result

    def setSides(self, value):
        self._sides = value
        self.update()

    def setWidth(self, value):
        super(PolygonButton, self).setWidth(value)
        self.setHeight(value)


class EllipseButton(CustomButton):
    _TYPE = 'ellipse'

    def __init__(self, color=QtGui.QColor(240, 100, 100, 255), label='', border=1, x=5, y=5, width=50, height=50, parent=None, commandType='select', **kwargs):
        super(EllipseButton, self).__init__(color=color, label=label, border=border, x=x, y=y,
                                            width=width, height=height, parent=parent, commandType=commandType)

    def paintEvent(self, event):
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        paint = QtGui.QPainter()
        paint.begin(self)
        geom = option.rect
        paint.setRenderHint(QtGui.QPainter.Antialiasing)

        bg_color = self._getBgColor()
        # Draw Shape
        paint.setBrush(bg_color)
        paint.setPen(self._getBorderPen())
        paint.drawEllipse(2, 2, geom.width() - 4, geom.height() - 4)

        # Draw Text
        paint.setPen(self._getTextColor())
        paint.drawText(geom, self._label, QtGui.QTextOption(QtCore.Qt.AlignCenter))
        paint.end()

    def resizeEvent(self, event):
        super(EllipseButton, self).resizeEvent(event)
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)
        geom = option.rect
        mask = QtGui.QRegion(geom, QtGui.QRegion.Ellipse)
        self.setMask(mask)
        self.updateGeometry()


class LayerButton(QtWidgets.QPushButton):
    _EDIT = False
    toggleAllRequested = QtCore.Signal()
    deleteRequested = QtCore.Signal()
    editRequested = QtCore.Signal()
    def __init__(self, x, y, size, color=QtGui.QColor(100,255,100), parent=None):
        super(LayerButton, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.setGeometry(x, y, size, size)
        self.setCheckable(True)
        self._color = color
        self._deletable = True

    @property
    def deletable(self):
        return self._deletable

    @deletable.setter
    def deletable(self, value):
        self._deletable = value

    def setEditMode(self, value):
        self._EDIT = value

    def paintEvent(self, *args, **kwargs):
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)

        paint = QtGui.QPainter()
        paint.begin(self)
        geom = option.rect
        paint.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.isChecked():
            bg_color = QtGui.QRadialGradient(geom.width()/2, geom.height()/2, geom.width()/2, geom.width()/2, geom.height()/2)
            bg_color.setColorAt(0.0, QtCore.Qt.white)
            bg_color.setColorAt(0.5, self._color)
            bg_color.setColorAt(.8, QtCore.Qt.black)
        else:
            bg_color = QtGui.QRadialGradient(geom.width() / 2, geom.height() / 2, geom.width() / 2, geom.width() / 2,
                                             geom.height() / 2)
            bg_color.setColorAt(0.5, self._color.darker(300))
            bg_color.setColorAt(.8, QtCore.Qt.black)
        # Draw Shape
        paint.setBrush(bg_color)
        paint.setPen(QtGui.QPen(QtCore.Qt.black, 2))
        paint.drawEllipse(2, 2, geom.width() - 4, geom.height() - 4)

    def resizeEvent(self, event):
        super(LayerButton, self).resizeEvent(event)
        option = QtWidgets.QStyleOptionButton()
        option.initFrom(self)
        geom = option.rect
        mask = QtGui.QRegion(geom, QtGui.QRegion.Ellipse)
        self.setMask(mask)
        self.updateGeometry()

    def openMenu(self, pos):
        menu = QtWidgets.QMenu(self)
        if self._EDIT:
            selectBtnAction = menu.addAction('Toggle All')
            selectBtnAction.triggered.connect(self.toggleAllRequested.emit)

            editAction = menu.addAction('Edit')
            editAction.triggered.connect(self.editRequested.emit)

            if self._deletable:
                deleteAction = menu.addAction('Delete')
                deleteAction.triggered.connect(self.deleteRequested.emit)
            menu.exec_(pos)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.openMenu(event.globalPos())
            return

        super(LayerButton, self).mousePressEvent(event)


button_types = {'default': CustomButton,
                'rounded': RoundedButton,
                'polygon': PolygonButton,
                'ellipse': EllipseButton}


def generateButtonCommand(attr):
    data = json.loads(attr.get())
    commandType = data.get('commandType')
    cmd = None
    if commandType == 'select':
        node = attr.node()
        cmd = lambda: pm.select(node,
                                tgl=True if QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier else False,
                                d=True if QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.ControlModifier else False,
                                r=True if QtGui.QGuiApplication.keyboardModifiers() == QtCore.Qt.NoModifier else False,
                                add=True if QtGui.QGuiApplication.keyboardModifiers() == (QtCore.Qt.ControlModifier|QtCore.Qt.ShiftModifier) else False)

    return cmd


def generateToolTip(attr):
    data = json.loads(attr.get())
    commandType = data.get('commandType')
    cmd = None
    if commandType == 'select':
        node = attr.node()
        if isinstance(node, pm.nodetypes.ObjectSet):
            toolTip = 'SELECT SET : {}'.format(node)
        else:
            toolTip = 'SELECT : {}'.format(node)

    return toolTip