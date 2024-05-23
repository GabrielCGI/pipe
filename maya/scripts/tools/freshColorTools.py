import maya.cmds as cmds
import pymel.core as pm
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class MyTool(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(MyTool, self).__init__(parent)
        self.setWindowTitle("My Tool")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(300, 100)  # re-size the window

        self.setup_ui()

    def setup_ui(self):
        # Main layout
        self.main_layout = QtWidgets.QVBoxLayout(self)

        # Buttons
        self.run_edge_button = QtWidgets.QPushButton("Add border")
        self.run_color_button = QtWidgets.QPushButton("Add colorSet \"Cd\"")
        self.run_color_from_shader_button = QtWidgets.QPushButton("Add colorSet \"Cd\" from Shader")
        self.run_color_blinn_button = QtWidgets.QPushButton("Viewport Shader Convert")

        # Add buttons to the layout
        self.main_layout.addWidget(self.run_edge_button)
        self.main_layout.addWidget(self.run_color_button)
        self.main_layout.addWidget(self.run_color_from_shader_button)
        self.main_layout.addWidget(self.run_color_blinn_button)

        # Connect buttons to their respective functions
        self.run_edge_button.clicked.connect(self.run_edge)
        self.run_color_button.clicked.connect(self.run_color)
        self.run_color_from_shader_button.clicked.connect(self.run_color_from_shader_clicked)
        self.run_color_blinn_button.clicked.connect(self.run_color_blinn)


    def run_edge(self):
        selection = cmds.ls(selection=True)
        print(selection)

        if selection:
            mesh = selection[0].split('.')[0]
            cmds.setAttr(mesh + '.aiExportColors', 1)

            existing_color_sets = cmds.polyColorSet(mesh, query=True, allColorSets=True) or []
            if 'border' not in existing_color_sets:
                cmds.polyColorSet(mesh, create=True, rpt="RGB", colorSet='border')
                cmds.polyColorSet(mesh, currentColorSet=True, colorSet='border')
                cmds.polyColorPerVertex(mesh + '.vtx[*]', rgb=(0, 0, 0), colorDisplayOption=True)

            cmds.polyColorSet(mesh, currentColorSet=True, colorSet='border')
            cmds.polyColorPerVertex(selection, rgb=(1, 1, 1), colorDisplayOption=True)
        else:
            print("Please select a polygon face to proceed.")

    def run_color_object(self, node, rgb):

        self.lamberificator(node)
        target = node
        cmds.setAttr(target.name() + '.aiExportColors', 1)
        existing_color_sets = cmds.polyColorSet(target.name(), query=True, allColorSets=True) or []
        if 'Cd' not in existing_color_sets:
            cmds.polyColorSet(target.name(), create=True, rpt="RGB", colorSet='Cd')

        cmds.polyColorSet(target.name(), currentColorSet=True, colorSet='Cd')
        cmds.polyColorPerVertex(target.name() + '.vtx[*]', rgb=rgb, colorDisplayOption=True)

    def run_color_faces(self, faces, rgb):
        self.lamberificator(faces[0])
        target = faces[0].split('.')[0]
        cmds.setAttr(target + '.aiExportColors', 1)

        existing_color_sets = cmds.polyColorSet(target, query=True, allColorSets=True) or []
        if 'Cd' not in existing_color_sets:
            cmds.polyColorSet(target, create=True, rpt="RGB", colorSet='Cd')

        cmds.polyColorSet(target, currentColorSet=True, colorSet='Cd')
        cmds.polyColorPerVertex(faces, rgb=rgb, colorDisplayOption=True)

    def run_color(self):

        selection = pm.ls(selection=True)
        color = cmds.colorEditor()
        if cmds.colorEditor(query=True, result=True):
            rgb = cmds.colorEditor(query=True, rgb=True)
        else:
            rgb=[0,1,0]
        color =  rgb

        if 'f' in selection[0].name():
            self.run_color_faces(selection, color )
        else:
            for obj in selection:
                self.run_color_object(obj, color )



    def run_color_blinn(self):
        for obj in pm.ls(selection=True):
            print("start vp shader on %s"%obj.name())
            color = self.get_first_aiUserDataColor_default_value(obj)
            if not color:
                pm.warning("No color found ! ")
                return
            print(color)

            if pm.nodeType(obj) == 'transform':
                shape = obj.getShape()
            else:
                shape = obj

            shading_groups = pm.listConnections(shape, type='shadingEngine')
            print(shading_groups)

            if not shading_groups:
                pm.warning("No shading groups found connected to the selected mesh.")
                return

            for sg in shading_groups:
                aiSurface = sg.aiSurfaceShader.connections()
                surface =sg.surfaceShader.connections()
                if aiSurface:
                    print("aiSurcaDetect")
                    print(aiSurface)

                    current_shader = aiSurface[0]
                else:
                    print(surface[0])
                    current_shader = surface[0]


                if current_shader:
                    shader_type = pm.nodeType(current_shader)
                    if shader_type not in ['blinn', 'lambert']:
                        pm.connectAttr(current_shader.outColor, sg.aiSurfaceShader, force=True)

                        # Create a new Lambert node
                        new_lambert = pm.shadingNode('lambert', asShader=True)

                        # Set its color to the retrieved color value
                        new_lambert.color.set(color)

                        # Connect the new Lambert node to the shading group's surfaceShader
                        pm.connectAttr(new_lambert.outColor, sg.surfaceShader, force=True)
                        allShapes = pm.listConnections(sg , type='shape', source=False)
                        for s in allShapes:
                            s.displayColors.set(0)

            shape.displayColors.set(0)
    def get_first_aiUserDataColor_default_value(self,node):
        default_color = None
        selected_object = node.getShape()

        shading_groups = pm.listConnections(selected_object, type='shadingEngine')
        print(shading_groups)

        if not shading_groups:
            pm.warning("No shading group connected to the selected object.")
            return None
    # Iterate over the shading groups to find aiUserDataColor nodes
        for sg in shading_groups:
            aiSurface = sg.aiSurfaceShader.connections()
            surface =sg.surfaceShader.connections()
            if aiSurface:
                print("aiSurcaDetect")
                shader = aiSurface[0]
            else:
                shader = surface[0]

            connected_nodes = pm.listHistory(shader)
            print(connected_nodes)
            for node in connected_nodes:
                if pm.nodeType(node) == 'aiUserDataColor':
                    if node.attribute.get() != "border":
                        # Get the default color value
                        default_color = pm.getAttr(node + ".default")
                        return default_color
                if pm.nodeType(node) == 'colorConstant':
                    if "MASTER" in node.name():
                        # Get the default color value
                        default_color = pm.getAttr(node + ".inColor")
                        return default_color
        pm.warning("No aiUserDataColor node found.")
        return None

    def run_color_from_shader_clicked(self):
        for obj in pm.ls(selection=True):
            print(obj)
            color = self.get_first_aiUserDataColor_default_value(obj)
            print(color)
            if not color:
                print("Skip color on %s"%obj)
                continue
            self.run_color_object(obj,color)


    def lamberificator(self, first_item):

        if "." in first_item:
            shape_name = first_item.split(".")[0]
            shape = pm.ls(shape_name)[0].getShape()
            print(shape)
        elif pm.nodeType(first_item) == 'transform':
            shape = pm.ls(first_item)[0].getShape()

        else:
            pm.warning("Selected item is neither a mesh component nor a transform.")
            return

        shading_groups = pm.listConnections(shape, type='shadingEngine')
        print(shading_groups)
        if not shading_groups:
            pm.warning("No shading groups found connected to the selected mesh.")
            return

        for sg in shading_groups:
            current_shader = pm.listConnections(sg.surfaceShader, source=True, destination=False)
            print(current_shader)
            if current_shader:
                shader_type = pm.nodeType(current_shader[0])
                if shader_type not in ['blinn', 'lambert']:
                    print("yeaj")
                    pm.connectAttr(current_shader[0].outColor, sg.aiSurfaceShader, force=True)
                    lambert1 = pm.PyNode('lambert1')
                    pm.connectAttr(lambert1.outColor, sg.surfaceShader, force=True)
