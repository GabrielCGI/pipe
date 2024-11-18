"""Extracted From GF_AutoRig"""
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
import pymel.core.datatypes as dt
import maya.cmds as cmds
import math
import sys
import maya.api.OpenMaya as om


class CompactLabeledField(QtWidgets.QWidget):
    def __init__(self, name, suffix=None, parent=None):
        super(CompactLabeledField, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # Layout Setup
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Name label
        self.nameLabel = QtWidgets.QLabel('%s : ' % name)
        self.layout.addWidget(self.nameLabel)

        # Field
        self.field = None

        # Suffix
        self.suffix = None
        if suffix is not None:
            self.suffix = QtWidgets.QLabel(suffix)
            self.layout.addWidget(self.suffix)

        self.setFixedHeight(20)

    def setField(self, widget):
        if self.field is not None:
            self.field.setParent(None)
        self.field = widget
        self.layout.insertWidget(1, self.field)


class LabeledField(CompactLabeledField):
    def __init__(self, name, suffix=None, parent=None):
        super(LabeledField, self).__init__(name, suffix, parent)
        self.nameLabel.setAlignment(QtCore.Qt.AlignRight)
        self.setLabelWidth()

    def setLabelWidth(self, w=100):
        self.nameLabel.setFixedWidth(w)


class NodeField(QtWidgets.QLineEdit):
    nodeChanged = QtCore.Signal()

    def __init__(self, placeHolderText=''):
        super(NodeField, self).__init__()

        self.node = False

        self.setPlaceholderText(placeHolderText)

    def setPyNode(self, node=None):
        if node is None:
            sel = pm.ls(sl=True)
        else:
            sel = [node]
        if len(sel):
            self.node = sel[0]
            self.setText(self.node.name())
            self.nodeChanged.emit()
            return self.node

    def clearPyNode(self):
        self.node = None
        self.setText('')
        self.nodeChanged.emit()
        return None

    def PyNode(self):
        if self.node is not None:
            if not pm.objExists(self.node):
                self.clearPyNode()
        return self.node

    def setPyNodeFromText(self):
        text = self.text()
        if pm.objExists(text):
            return self.setPyNode(pm.PyNode(text))
        else:
            self.setText('')

    def __setPyNode(self, node):
        # if node is None:
        #     return
        # if not isinstance(node, pm.PyNode):
        #     raise TypeError('Expecting pm.PyNode type, got {} instead'.format(type(node)))
        # self.node = node
        if pm.objExists(node):
            self.node = pm.PyNode(node)
            self.setText(self.node.name())

    def __getPyNode(self):
        if isinstance(self.node, pm.PyNode):
            return self.node.name()
        return None

    pynode = QtCore.Property(str, __getPyNode, __setPyNode)


class NodeFieldType(NodeField):
    def __init__(self, placeHolderText='', checkShape=True, checkHistory=False, types=(pm.PyNode)):
        super(NodeFieldType, self).__init__(placeHolderText)

        self.checkShape = checkShape
        self.checkHistory = checkHistory
        self.types = types

    def setPyNode(self, node=None):
        if node is None:
            sel = pm.ls(sl=True)
        else:
            sel = [node]
        if len(sel):
            if isinstance(sel[0], self.types):
                self.node = sel[0]
                self.setText(self.node.name())
                self.nodeChanged.emit()
                return self.node
            elif self.checkShape:
                if isinstance(sel[0].getShape(), self.types):
                    self.node = sel[0].getShape()
                    self.setText(self.node.name())
                    self.nodeChanged.emit()
                    return self.node
            elif self.checkHistory:
                hist = [n for n in sel[0].history() if isinstance(n, self.types)]
                if len(hist):
                    self.node = hist[0]
                    self.setText(self.node.name())
                    self.nodeChanged.emit()
                    return self.node


class CheckBox(LabeledField):
    def __init__(self, name, parent=None):
        super(CheckBox, self).__init__(name, '', parent)
        cbx = QtWidgets.QCheckBox()
        self.stateChanged = cbx.stateChanged
        self.setField(cbx)

    def getValue(self):
        return self.field.isChecked()

    def setValue(self, value):
        self.field.setChecked(value)

    value = QtCore.Property(bool, getValue, setValue)


class ComboBox(LabeledField):
    def __init__(self, name, items, parent=None):
        super(ComboBox, self).__init__(name, '', parent)
        self.itemList = items
        cbx = QtWidgets.QComboBox()
        cbx.addItems(self.itemList)
        self.setField(cbx)

    def getValue(self):
        return self.field.currentText()

    def setValue(self, value):
        self.field.setCurrentText(value)

    value = QtCore.Property(bool, getValue, setValue)


class VectorField(QtWidgets.QWidget):
    def __init__(self, value=(0, 1, 0), parent=None, step=0.1):
        super(VectorField, self).__init__(parent=parent)
        # Layout Setup
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.xField = QtWidgets.QDoubleSpinBox()

        self.yField = QtWidgets.QDoubleSpinBox()

        self.zField = QtWidgets.QDoubleSpinBox()

        for field in (self.xField, self.yField, self.zField):
            field.setDecimals(3)
            self.layout.addWidget(field)
            field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            field.setRange(-1.0, 1.0)
            field.setSingleStep(step)

        self.setVector(value)

    def setVector(self, vector):
        self.xField.setValue(vector[0])
        self.yField.setValue(vector[1])
        self.zField.setValue(vector[2])

    def vector(self):
        return dt.Vector(self.xField.value(), self.yField.value(), self.zField.value())


class Vector2DField(QtWidgets.QWidget):
    def __init__(self, value=(50, 50), parent=None, asDouble=False):
        super(Vector2DField, self).__init__(parent=parent)
        # Layout Setup
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        if asDouble:
            self.xField = QtWidgets.QDoubleSpinBox()
            self.xField.setRange(0, 9999)

            self.yField = QtWidgets.QDoubleSpinBox()
            self.yField.setRange(0, 9999)
        else:
            self.xField = QtWidgets.QSpinBox()
            self.xField.setRange(0, 9999)

            self.yField = QtWidgets.QSpinBox()
            self.yField.setRange(0, 9999)

        for field in (self.xField, self.yField):
            self.layout.addWidget(field)
            field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            field.setMinimum(0)

        self.setVector(value)

    def setVector(self, vector):
        self.xField.setValue(vector[0])
        self.yField.setValue(vector[1])

    def vector(self):
        return self.xField.value(), self.yField.value()


class VectorRadioGroup(QtWidgets.QWidget):
    valueChanged = QtCore.Signal()

    def __init__(self, value='xPos', parent=None):
        super(VectorRadioGroup, self).__init__(parent=parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.radioGroup = QtWidgets.QButtonGroup()
        xRadio = QtWidgets.QRadioButton('X')
        self.layout.addWidget(xRadio)
        yRadio = QtWidgets.QRadioButton('Y')
        self.layout.addWidget(yRadio)
        zRadio = QtWidgets.QRadioButton('Z')
        self.layout.addWidget(zRadio)
        self.radioGroup.addButton(xRadio)
        self.radioGroup.setId(xRadio, 0)
        self.radioGroup.addButton(yRadio)
        self.radioGroup.setId(yRadio, 1)
        self.radioGroup.addButton(zRadio)
        self.radioGroup.setId(zRadio, 2)

        self.radioGroup.buttonClicked.connect(self.changedValueTrigger)

        self.directionCombo = QtWidgets.QComboBox()
        self.directionCombo.addItems(['+', '-'])
        self.layout.addWidget(self.directionCombo)

        self.directionCombo.currentTextChanged.connect(self.changedValueTrigger)

        self.setValue(value)

    def setValue(self, value):
        '''

        :param value: expecting strings like 'xPos', 'xNeg', 'yPos', etc... 
        :return: shit
        '''
        if not len(value):
            btn = self.radioGroup.checkedButton()
            if btn is not None:
                btn.setChecked(False)
            self.directionCombo.setCurrentText('+')
            return False
        a = value[0]
        if a == 'x':
            self.radioGroup.button(0).setChecked(True)
        elif a == 'y':
            self.radioGroup.button(1).setChecked(True)
        elif a == 'z':
            self.radioGroup.button(2).setChecked(True)
        else:
            raise ValueError('Invalid Value : {}'.format(value))

        if 'Pos' in value:
            self.directionCombo.setCurrentText('+')
        elif 'Neg' in value:
            self.directionCombo.setCurrentText('-')
        else:
            raise ValueError('Invalid Value : {}'.format(value))

        return True

    def getValue(self):
        checkedButton = self.radioGroup.checkedButton()
        if checkedButton is None:
            return ''
        axis = checkedButton.text().lower() + ('Neg' if self.directionCombo.currentText() == '-' else 'Pos')
        return axis

    def changedValueTrigger(self, *args, **kwargs):
        self.valueChanged.emit()

    value = QtCore.Property(str, getValue, setValue)


class NodeListModel(QtCore.QAbstractTableModel):
    VALID_NODE_TYPES = (pm.PyNode)

    def __init__(self, parent=None):
        # super(NodeListModel, self).__init__(parent)
        QtCore.QAbstractTableModel.__init__(self, parent)

        self.nodeList = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.nodeList)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if isinstance(index, int):
            row = index
        else:
            row = index.row()

        if role == QtCore.Qt.DisplayRole:
            if self.nodeList[row] is None:
                return "None"
            return self.nodeList[row].name()

        if role == QtCore.Qt.UserRole:
            return self.nodeList[row]

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole:
            return False

        row = index.row()
        self.nodeList[row] = value

        self.dataChanged.emit(index, index)
        return True

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)

        for i in range(position, position + rows):
            self.nodeList.insert(i, None)
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)

        del self.nodeList[position: position + rows]

        self.endRemoveRows()
        return True

    def _validateNodes(self, nodes):
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]

        ret = []
        for node in nodes:
            if isinstance(node, self.VALID_NODE_TYPES):
                ret.append(node)
        return ret

    def insertNode(self, node, row=None):
        node = self._validateNodes(node)

        if len(node):
            node = node[0]
        else:
            return

        if row is None:
            row = self.rowCount()

        self.insertRows(row, 1)
        index = self.index(row, 0)
        self.setData(index, node)

        return index

    def insertNodes(self, nodes, row=None):
        nodes = self._validateNodes(nodes)

        if row is None:
            row = self.rowCount()

        for n, node in enumerate(nodes):
            self.insertNode(node, row + n)

        return nodes

    def getIndexesFromValue(self, value, role=QtCore.Qt.DisplayRole, hits=1):
        result = []

        for r in range(self.rowCount()):
            index = self.index(r, 0)
            idValue = self.data(index, role=role)
            if value == idValue:
                result.append(index)
                if hits != -1:
                    if len(result) >= hits:
                        return result
        return result

    def removeNode(self, node):
        indexes = self.getIndexesFromValue(node, role=QtCore.Qt.UserRole)
        for idx in indexes:
            self.removeRows(idx.row(), 1)


class EditableNodeView(QtWidgets.QWidget):
    MODEL = NodeListModel
    VIEW = QtWidgets.QListView
    nodesAdded = QtCore.Signal(list)

    def __init__(self, parent=None, filterField=True, buttonText='Add Node'):
        # super(EditableNodeView, self).__init__(parent)
        QtWidgets.QWidget.__init__(self, parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setSpacing(0)
        self.listView = self.VIEW()
        self.layout.addWidget(self.listView)

        self.model = self.MODEL()
        if filterField:
            self.filterField = QtWidgets.QLineEdit()
            self.layout.addWidget(self.filterField)
            self.proxyModel = QtCore.QSortFilterProxyModel()
            # Assuming filterField and proxyModel are already defined
            if int(maya_version) >= 2025:
                # For Maya 2025 or newer, using PySide6
                self.filterField.textChanged.connect(self.proxyModel.setFilterRegularExpression)
            else:
                # For Maya versions older than 2025, using PySide2
                self.filterField.textChanged.connect(self.proxyModel.setFilterRegExp)
            self.proxyModel.setSourceModel(self.model)
            self.listView.setModel(self.proxyModel)

        else:
            self.listView.setModel(self.model)
        self.listView.doubleClicked.connect(self.onDoubleClicked)

        addBtn = QtWidgets.QPushButton(buttonText)
        addBtn.clicked.connect(self.addSelected)
        self.layout.addWidget(addBtn)

    def addSelected(self):
        nodes = self.model.insertNodes(pm.ls(sl=True))
        self.nodesAdded.emit(nodes)

    def onDoubleClicked(self, index):
        if self.model.flags(index) & 2:
            self.listView.edit(index)
        else:
            self.model.removeRows(index.row(), 1)


class SplitterFrame(QtWidgets.QSplitter):
    def __init__(self, parent=None, orientation=QtCore.Qt.Horizontal):
        QtWidgets.QSplitter.__init__(self, orientation, parent)

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setLineWidth(1)
        self.setMidLineWidth(0)

        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        #
        # self.layout = QtWidgets.QHBoxLayout(self)
        # self.layout.setContentsMargins(4, 4, 4, 4)
        # self.layout.setSpacing(2)
        #
        # self.addWidget = self.layout.addWidget


class ModelWidgetMapper(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        # Layout Setup
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(3)

        self._dataMapper = QtWidgets.QDataWidgetMapper()

    def setModel(self, model):
        self._dataMapper.setModel(model)
        self._doMapping()
        self._dataMapper.toFirst()

    def _doMapping(self):
        '''Reimplement this to map the widget to the proper columns'''
        # self._dataMapper.addMapping(widget, int, ("PropertyName"))
        pass

    def setSelection(self, current, old):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)


class StandardTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(StandardTreeView, self).__init__(parent)

    def mousePressEvent(self, event):
        self.clearSelection()
        self.setCurrentIndex(QtCore.QModelIndex())
        super(StandardTreeView, self).mousePressEvent(event)


class WrapWidget(QtWidgets.QFrame):
    buttonClickedId = QtCore.Signal(int)

    def __init__(self, parent=None):
        QtWidgets.QFrame.__init__(self, parent)

        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setLineWidth(1)
        self.setMidLineWidth(0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.buttonGroup = QtWidgets.QButtonGroup(self)
        self.buttonGroup.buttonClicked.connect(self.onClicked)
        self.columnMin = 1

        # self.setMinimumSize(QtCore.QSize(300,300))
        # self.setMaximumSize(QtCore.QSize(10000,10000))

        self.cellSize = QtCore.QSize(40, 40)
        self.setMinimumWidth(40)

        self.buttons = []

    def resizeEvent(self, event):
        super(WrapWidget, self).resizeEvent(event)
        self.updateGrid()

    def columnCount(self):
        x = float(self.cellSize.width())
        w = float(self.geometry().width())
        count = w / x
        return math.trunc(count)

    def rowCount(self):
        x = float(self.cellSize.height())
        h = float(self.geometry().height())
        count = h / x
        return math.trunc(count)

    def addToolButton(self, icon=None, idx=None):
        if idx is None:
            idx = len(self.buttons)
        btn = QtWidgets.QPushButton(self)
        btn.setFlat(True)
        btn.setFixedSize(self.cellSize)
        self.layout.addWidget(btn)
        if icon is not None:
            btn.setIcon(icon)
            btn.setIconSize(self.cellSize)
        btn.setCheckable(False)
        self.buttons.append(btn)
        self.buttonGroup.addButton(btn, idx)
        self.updateGrid()
        return btn

    def onClicked(self, btn):
        self.buttonClickedId.emit(self.buttonGroup.id(btn))

    def updateGrid(self):
        btnCount = len(self.buttons)
        colCount = self.columnCount()
        curCol = -1
        curRow = 0
        for x in range(0, btnCount):
            if x < colCount + (colCount * curRow):
                curCol += 1
            else:
                curCol = 0
                curRow += 1
            btn = self.buttons[x]
            pX = curCol * self.cellSize.width()
            pY = curRow * self.cellSize.height()
            geom = QtCore.QRect(pX, pY, self.cellSize.width(), self.cellSize.height())
            btn.setGeometry(geom)
        self.setFixedHeight(self.cellSize.height() * (curRow + 1))

    def setCellSize(self, w, h):
        self.cellSize = QtCore.QSize(w, h)
        self.setMinColumns(self.columnMin)
        self.updateGrid()

    def setMinColumns(self, n):
        self.columnMin = n
        self.setMinimumWidth(self.cellSize.width() * max([n, 1]))
        self.updateGrid()


class ColorSlider(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ColorSlider, self).__init__(parent)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.spinBox = QtWidgets.QSpinBox()
        self.spinBox.setMinimum(0)
        self.spinBox.setMaximum(31)
        self.spinBox.setFixedWidth(60)
        self.spinBox.setMaximumHeight(20)

        # self.label = QtGui.QLabel()
        self.label = Circle()
        self.label.setMinimumWidth(30)
        self.label.setMaximumHeight(20)

        self.colors = [(.5, .5, .5), (0, 0, 0), (.5, .5, .5),
                       (.75, .75, .75), (.8, 0, .2), (0, 0, .4),
                       (0, 0, 1), (0, .3, 0), (.2, 0, .3), (.8, 0, .8),
                       (.6, .3, .2), (.25, .13, .13), (.7, .2, 0),
                       (1, 0, 0), (0, 1, 0), (0, 0.3, 0.6),
                       (1, 1, 1), (1, 1, 0), (0, 1, 1), (0, 1, .8),
                       (1, .7, .7), (.9, .7, .5), (1, 1, .4), (0, .7, .4),
                       (.6, .4, .2), (.63, .63, .17), (.4, .6, .2), (.2, .63, .35),
                       (.18, .63, .63), (.18, .4, .63), (.43, .18, .63), (.63, .18, .4)]

        self.spinBox.valueChanged.connect(self.label.updateColor)

        self.layout.addWidget(self.spinBox)
        self.layout.addWidget(self.label)
        self.label.updateColor(0)

    def updateColor(self, id=0):
        color = self.colors[id]
        self.label.setStyleSheet('background:rgb(%s,%s,%s);' % (color[0] * 256, color[1] * 256, color[2] * 256))

    def getValue(self):
        return self.spinBox.value()

    def setValue(self, n):
        self.spinBox.setValue(n)


class Circle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Circle, self).__init__(parent)
        self.color = [0, 0, 0]

        self.colors = [(.5, .5, .5), (0, 0, 0), (.5, .5, .5),
                       (.75, .75, .75), (.8, 0, .2), (0, 0, .4),
                       (0, 0, 1), (0, .3, 0), (.2, 0, .3), (.8, 0, .8),
                       (.6, .3, .2), (.25, .13, .13), (.7, .2, 0),
                       (1, 0, 0), (0, 1, 0), (0, 0.3, 0.6),
                       (1, 1, 1), (1, 1, 0), (0, 1, 1), (0, 1, .8),
                       (1, .7, .7), (.9, .7, .5), (1, 1, .4), (0, .7, .4),
                       (.6, .4, .2), (.63, .63, .17), (.4, .6, .2), (.2, .63, .35),
                       (.18, .63, .63), (.18, .4, .63), (.43, .18, .63), (.63, .18, .4)]

    def paintEvent(self, event):
        paint = QtGui.QPainter()
        paint.begin(self)
        geom = event.rect()
        paint.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor(self.color[0], self.color[1], self.color[2])
        paint.setPen(self.palette().color(QtGui.QPalette.Dark))
        paint.drawEllipse(2, 2, geom.height() - 2, geom.height() - 2)
        paint.setBrush(color)
        paint.drawEllipse(2, 2, geom.height() - 2, geom.height() - 2)
        paint.end()

    def updateColor(self, id=0):
        self.color = [x * 255 for x in self.colors[id]]
        self.update()


class ColorPicker(QtWidgets.QWidget):
    colorChanged = QtCore.Signal(QtGui.QColor)

    def __init__(self, parent=None, alpha=True):
        super(ColorPicker, self).__init__(parent)
        self.color = QtGui.QColor(100,100,100,255)
        self.colorDialog = ColorDialog(self, alpha)

    def mouseReleaseEvent(self, event):
        super(ColorPicker, self).mouseReleaseEvent(event)

        # color = QtWidgets.QColorDialog.getColor(options=QtWidgets.QColorDialog.ShowAlphaChannel|QtWidgets.QColorDialog.DontUseNativeDialog)
        self.colorDialog.open()
        self.colorDialog.setCurrentColor(self.color)
        self.colorDialog.addToCustom()
        self.colorDialog.accepted.connect(lambda :self.setColor(self.colorDialog.currentColor(), True))
        # if color.isValid():
        #     self.setColor(color, True)

    def paintEvent(self, event):
        paint = QtGui.QPainter()
        paint.begin(self)
        geom = event.rect()
        paint.setRenderHint(QtGui.QPainter.Antialiasing)
        paint.setPen(self.palette().color(QtGui.QPalette.Dark))
        paint.setBrush(self.color)
        paint.drawEllipse(2, 2, geom.height() - 2, geom.height() - 2)
        paint.end()

    def setColor(self, color=QtGui.QColor(), emit=False):
        self.color = color
        if emit:
            self.colorChanged.emit(color)
        self.update()


class ColorDialog(QtWidgets.QColorDialog):
    def __init__(self, parent=None, alpha=True):
        super(ColorDialog, self).__init__(parent)
        if alpha:
            self.setOptions(QtWidgets.QColorDialog.ShowAlphaChannel|QtWidgets.QColorDialog.DontUseNativeDialog)
        else:
            self.setOptions(QtWidgets.QColorDialog.DontUseNativeDialog)
        self._customColors = [self.customColor(x) for x in range(self.customCount())]
        self.accepted.connect(self.addToCustom)

    def addToCustom(self, color=None):
        if color is None:
            color = self.currentColor()

        if color in self._customColors:
            return

        count = self.customCount()
        if len(self._customColors) >= count:
            del self._customColors[-1:]

        self._customColors.insert(0, color)
        for x, c in enumerate(self._customColors):
            self.setCustomColor(x, c)


class ColorPickerField(QtWidgets.QWidget):
    colorChanged = QtCore.Signal(QtGui.QColor)

    def __init__(self, value=QtGui.QColor(), parent=None, alpha=True):
        super(ColorPickerField, self).__init__(parent=parent)
        # Layout Setup
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignLeft)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)

        self.rField = QtWidgets.QSpinBox()

        self.gField = QtWidgets.QSpinBox()

        self.bField = QtWidgets.QSpinBox()

        self.aField = QtWidgets.QSpinBox()
        self.aField.setEnabled(alpha)

        self.colorPicker = ColorPicker()
        self.colorPicker.setFixedSize(30, 30)

        for field in (self.rField, self.gField, self.bField, self.aField):
            self.layout.addWidget(field)
            field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            field.setRange(0, 255)
            field.valueChanged.connect(lambda: self.colorPicker.setColor(self.color(), True))

        self.layout.addWidget(self.colorPicker)
        self.colorPicker.colorChanged.connect(self.setColor)

        self.setColor(value)

    def setColor(self, color=QtGui.QColor()):
        self.rField.setValue(color.red())
        self.gField.setValue(color.green())
        self.bField.setValue(color.blue())
        self.aField.setValue(color.alpha())
        self.colorPicker.setColor(color)
        self.colorChanged.emit(color)

    def setVector(self, vector):
        self.rField.setValue(vector[0])
        self.gField.setValue(vector[1])
        self.bField.setValue(vector[2])

    def color(self):
        return QtGui.QColor(self.rField.value(), self.gField.value(), self.bField.value(), self.aField.value())

    def asVector(self):
        color = dt.Vector(self.color().toTuple()[:3])
        return color

    def asNormalizedVector(self):
        color = self.asVector()
        color.normalize()
        return color


class CurrentSelectionLabel(QtWidgets.QLabel):
    validSelection = QtCore.Signal(bool)
    def __init__(self, parent=None):
        super(CurrentSelectionLabel, self).__init__(parent=parent)

        self._selChangedCallback = MEventCallbackHandler('SelectionChanged', self._selectionChanged)
        self._selChangedCallback.install()

    def activate(self):
        self._selChangedCallback.install()
        self._selectionChanged()

    def deactivate(self):
        self._selChangedCallback.uninstall()
        self.setText('')

    def _selectionChanged(self, *args, **kwargs):
        sel = cmds.ls(sl=True)
        if len(sel):
            text = sel[0]
            if len(sel) > 1:
                text += '...'
            self.validSelection.emit(True)
        else:
            text = 'None'
            self.validSelection.emit(False)

        self.setText(text)

    def showEvent(self, event):
        super(CurrentSelectionLabel, self).showEvent(event)
        self.activate()

    def hideEvent(self, event):
        super(CurrentSelectionLabel, self).hideEvent(event)
        self.deactivate()


class MEventCallbackHandler(object):
    def __init__(self, cb, fn):
        self._callback = cb
        self._function = fn
        self._id = None

    def install(self):
        if self._id:
            return False

        self._id = om.MEventMessage.addEventCallback(self._callback, self._function)
        return True

    def uninstall(self):
        if self._id:
            om.MEventMessage.removeCallback(self._id)
            self._id = None
            return True

        return False

    def __del__(self):
        self.uninstall()


class MSceneCallbackHandler(object):
    _eventNames = {'beforeNew': om.MSceneMessage.kBeforeNew,
                   'afterNew': om.MSceneMessage.kAfterNew,
                   'beforeOpen': om.MSceneMessage.kBeforeOpen,
                   'afterOpen': om.MSceneMessage.kAfterOpen}

    def __init__(self, cb, fn):
        if not cb in self._eventNames:
            raise ValueError('{} event is not supported'.format(cb))
        self._callback = self._eventNames[cb]
        self._function = fn
        self._id = None

    def install(self):
        if self._id:
            return False

        self._id = om.MSceneMessage.addCallback(self._callback, self._function)
        return True

    def uninstall(self):
        if self._id:
            om.MSceneMessage.removeCallback(self._id)
            self._id = None
            return True

        return False

    def __del__(self):
        self.uninstall()


class StandardNodeListModel(QtCore.QAbstractListModel):
    def __init__(self, nodes, parent=None):
        super(StandardNodeListModel, self).__init__(parent)
        self.nodes = nodes

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.nodes)

    def data(self, index, role):
        if isinstance(index, int):
            row = index
        else:
            row = index.row()

        if role == QtCore.Qt.DisplayRole:
            if self.nodes[row] is None:
                return "None"
            return self.nodes[row].name()

        if role == QtCore.Qt.UserRole:
            return self.nodes[row]

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class StandardNodeListWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(StandardNodeListWidget, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)
        self.filterField = QtWidgets.QLineEdit()
        self.listView = QtWidgets.QListView()
        self.layout.addWidget(self.filterField)
        self.layout.addWidget(self.listView)

        self.proxyModel = QtCore.QSortFilterProxyModel()
        # Assuming filterField and proxyModel are already defined
        if int(maya_version) >= 2025:
            # For Maya 2025 or newer, using PySide6
            self.filterField.textChanged.connect(self.proxyModel.setFilterRegularExpression)
        else:
            # For Maya versions older than 2025, using PySide2
            self.filterField.textChanged.connect(self.proxyModel.setFilterRegExp)
        self.listView.setModel(self.proxyModel)

        self.listView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.listView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.setMinimumWidth(250)

    def setModel(self, model):
        self.proxyModel.setSourceModel(model)

    def selectObjects(self, *args):
        sel = self.selectedNodes()
        pm.select(sel)

    def selectedNodes(self):
        sel = []
        for idx in self.listView.selectedIndexes():
            idx = self.proxyModel.mapToSource(idx)
            sourceModel = idx.model()
            sel.append(sourceModel.nodes[idx.row()])
        return sel

    def selectNext(self):
        if self.proxyModel.rowCount() == 0:
            return

        selIds = self.listView.selectedIndexes()
        row = 0
        if len(selIds):
            row = selIds[-1].row()
            if row < self.proxyModel.rowCount():
                row +=1

        mIndex = self.proxyModel.index(row, 0)
        self.listView.setCurrentIndex(mIndex)
        self.selectObjects()


class FilterAttributesListWidget(StandardNodeListWidget):
    _ATTYPE = ['enum']

    def __init__(self, parent=None):
        super(FilterAttributesListWidget, self).__init__(parent=parent)

        self._selChangedCallback = MEventCallbackHandler('SelectionChanged', self._selectionChanged)
        self._selChangedCallback.install()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def activate(self):
        self._selChangedCallback.install()
        self._selectionChanged()

    def deactivate(self):
        self._selChangedCallback.uninstall()

    def setAttributeType(self, attrTypes):
        self._ATTYPE = attrTypes

    def filterFromList(self, nodes):
        attributes = []
        for obj in nodes:
            attributes.extend([obj.attr(at) for at in pm.listAttr(obj, ud=True, k=True) if obj.attr(at).get(type=True) in self._ATTYPE])
        return attributes

    def _selectionChanged(self, *args):
        sel = pm.ls(sl=True)
        filtered = self.filterFromList(sel)
        model = StandardNodeListModel(filtered)
        self.setModel(model)

    def showEvent(self, event):
        super(FilterAttributesListWidget, self).showEvent(event)
        self.activate()

    def hideEvent(self, event):
        super(FilterAttributesListWidget, self).hideEvent(event)
        self.deactivate()