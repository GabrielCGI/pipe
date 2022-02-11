from PySide2 import QtCore
from PySide2 import QtWidgets
import maya.cmds as cmds
import os
import glob
import os.path
import re
import pymel.core as pm
import sys


PLUGIN_NAME         = 'Substance to Arnold'
PLUGIN_VERSION      = '1.0'
## Orignal Coder   Mostafa Samir mostafastormgfx@gmail.com
##update by Slacker TED
##modified by Gabriel.G


class SubstanceImporter():
    def __init__(self):
        print(PLUGIN_NAME +' ver '+ PLUGIN_VERSION + '\n')
        self.initUI()

    def initUI(self):
        #Create our main window
        self.dlgMain = QtWidgets.QDialog()
        self.dlgMain.setWindowTitle(PLUGIN_NAME +'ver'+ PLUGIN_VERSION)
        self.dlgMain.setFixedSize(500,450)
        self.dlgMain.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        #Create vertical layout
        self.layVDlgMain = QtWidgets.QVBoxLayout()
        self.dlgMain.setLayout(self.layVDlgMain)
        ##self.dlgMain.setStyleSheet ("""QWidget {background-color:#1c2122;border-width: 2px;border-color: #0d5666;border-style: solid;border-radius: 4; }QPushButton {color: white;background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #056, stop: 1 #99e, stop: 1.49 #027, stop: 0.5 #66b, stop: 1 #77c);border-width: 2px;border-color: #22d8ff;border-style: solid;border-radius: 4;padding: 3px;font-size: 12px;padding-left: 5px;padding-right: 5px;min-width: 50px;max-width: 175px;min-height: 13px;max-height: 23px;}QGroupBox { background-color: #141c58; border-radius: 4;border:2px solid #0d5666;}""");

        #Create Dirctory Group box
        self.grpBrowseForDirectory = QtWidgets.QGroupBox('Texture Directory')
        self.layVDlgMain.addWidget(self.grpBrowseForDirectory)

        #Create H layout in Dirctory Group box
        self.layHBrowseForDirectory = QtWidgets.QVBoxLayout()
        self.grpBrowseForDirectory.setLayout(self.layHBrowseForDirectory)

        #Create Push btn for browse Dirctory  in Group box
        self.btnBrowseForDir = QtWidgets.QPushButton('Select Texture Directory')
        self.layHBrowseForDirectory.addWidget(self.btnBrowseForDir)
        self.btnBrowseForDir.clicked.connect(self.btnBrowseForDirClicked)
        self.texFoundLabel = QtWidgets.QLabel("")
        self.layHBrowseForDirectory.addWidget(self.texFoundLabel)

        self.btnBrowseForDispDir = QtWidgets.QPushButton('Select Displace Directory')
        self.layHBrowseForDirectory.addWidget(self.btnBrowseForDispDir)
        self.dispTexFoundLabel = QtWidgets.QLabel("")
        self.btnBrowseForDispDir.clicked.connect(self.btnBrowseForDispDirClicked)
        self.layHBrowseForDirectory.addWidget(self.dispTexFoundLabel)

        #Create Import Group box
        self.grpImport = QtWidgets.QGroupBox('Material')
        self.layVDlgMain.addWidget(self.grpImport)

        #Create H Layout
        self.layHImport = QtWidgets.QVBoxLayout()
        self.grpImport.setLayout(self.layHImport)

        #self.subdivLayout = QtWidgets.QHBoxLayout()
        #self.subdivType = QtWidgets.QComboBox()
        #self.subdivLevel = QtWidgets.QSpinBox(1)
        #self.subdivLayout.addWidget(self.subdivType)
        #self.subdivLayout.addWidget(self.subdivLevel)
        #self.layHImport.addLayout(self.subdivLayout)

        #Create label obj selected
        sel = cmds.ls(sl=True)
        if len(sel)==0:
            msg= "Please select on object first"
            cmds.confirmDialog(title="Error",message=msg)
            sys.exit(msg)
        label = "Selected objects: "
        for s in sel:
            label += s+","

        self.objList = QtWidgets.QLabel(label)
        self.layHImport.addWidget(self.objList)
        #Shader Name
        self.shaderHImport = QtWidgets.QHBoxLayout()
        self.shaderNameLabel = QtWidgets.QLabel()
        self.shaderNameLabel.setText('Shader Name:')
        self.shaderName = QtWidgets.QLineEdit(sel[0]+"_shader")

        self.shaderHImport.addWidget(self.shaderNameLabel)
        self.shaderHImport.addWidget(self.shaderName)

        self.layHImport.addLayout(self.shaderHImport)
        #Create Import Button
        self.btnImportTex = QtWidgets.QPushButton('Create materials')
        self.layHImport.addWidget(self.btnImportTex)
        self.btnImportTex.setEnabled(0)
        self.btnImportTex.clicked.connect(self.btnImportTexClicked)

        self.dlgMain.show()

    def btnBrowseForDirClicked(self):
        self.ImportTexDir = QtWidgets.QFileDialog.getExistingDirectory()
        self.btnBrowseForDir.setText(self.ImportTexDir)
        self.btnImportTex.setEnabled(1)
        self.listFoundTex()

    def btnBrowseForDispDirClicked(self):
        self.ImportTexDispDir = QtWidgets.QFileDialog.getExistingDirectory()
        self.btnBrowseForDispDir.setText(self.ImportTexDispDir)
        self.listFoundDispTex()

    def btnImportTexClicked(self):
        self.arnoldImport()

    def listFoundTex(self):
        texPath= self.ImportTexDir
        format = ".exr"
        colorTexAll = glob.glob(texPath+"\\*BaseColor*"+format)
        roughnessTexAll = glob.glob(texPath+"\\*Roughness*"+format)
        metalnessTexAll = glob.glob(texPath+"\\*Metalness*"+format)
        normalTexAll = glob.glob(texPath+"\\*Normal*"+format)

        # Keep only the first occurence (if more than one it's mean there is UDIM)
        #Check if texture exist
        listTex = ""
        if len(colorTexAll) > 0: listTex+=str(os.path.basename(colorTexAll[0]))+"\n"
        if len(roughnessTexAll) >0:listTex+=str(os.path.basename(roughnessTexAll[0]))+"\n"
        if len(metalnessTexAll) >0: listTex+=str(os.path.basename(metalnessTexAll[0]))+"\n"
        if len(normalTexAll) >0: listTex+=str(os.path.basename(normalTexAll[0]))+"\n"

        if len(listTex)==0:
            self.texFoundLabel.setText("No textures found ! \nPlease check the path \nPlease check texture's format is EXR ")
        else:
            self.texFoundLabel.setText(listTex)

    def listFoundDispTex(self):
        dispPath= self.ImportTexDispDir
        format = ".exr"
        displacePattern = ["displace","Height"]
        displaceTexAll=[]
        for pattern in displacePattern:
            displaceTexAll += glob.glob(dispPath+"\\*"+pattern+"*"+format)

        # Keep only the first occurence (if more than one it's mean there is UDIM)
        #Check if texture exist
        listTex = ""
        if len(displaceTexAll) > 0: listTex+=str(os.path.basename(displaceTexAll[0]))+"\n"

        if len(listTex)==0:
            self.dispTexFoundLabel.setText("No textures found ! \nPlease check the path \nPlease check texture's format is EXR \nPlease check the texture name contain \"Height\" or \"displace\"")
        else:
            self.dispTexFoundLabel.setText(listTex)

    def arnoldImport(self):
        #Get selection
        selection = cmds.ls(sl=True)

        texPath= self.ImportTexDir
        if hasattr(self, 'ImportTexDispDir'):
            dispPath = self.ImportTexDispDir
        else:
            dispPath = None

        print(texPath)
        templateShader = {
        "color" : "BaseColor",
        "specRoughness" : "Roughness",
        "specular" : 0.7,
        "metalness" : "Metalness",
        "displace" : "Height",
        "aiDisplacementZeroValue" : 0,
        "aiSubdivIterations" : 2,
        "Normal" : "Normal",
        }
        format = ".exr"
        #Init variable
        colorTexPath= None
        colorTexPath= None
        metalnessTexPath= None
        normalTexPath = None
        specRoughTexPath= None
        displaceTexPath = None

        # Scan for all textures by matching pattern
        colorTexAll = glob.glob(texPath+"\\*BaseColor*"+format)
        roughnessTexAll = glob.glob(texPath+"\\*Roughness*"+format)
        metalnessTexAll = glob.glob(texPath+"\\*Metalness*"+format)
        normalTexAll = glob.glob(texPath+"\\*Normal*"+format)

        # Keep only the first occurence (if more than one it's mean there is UDIM)
        #Check if texture exist
        if len(colorTexAll) > 0: colorTexPath = colorTexAll[0]
        if len(roughnessTexAll) >0: specRoughTexPath = roughnessTexAll[0]
        if len(metalnessTexAll) >0: metalnessTexPath =metalnessTexAll[0]
        if len(normalTexAll) >0: normalTexPath = normalTexAll[0]


        #BUILD SHADER
        s = self.shaderName.text()
        shader = cmds.shadingNode ("aiStandardSurface", asShader=True, name="%sShader"%s)
        shadingGroup = cmds.sets(name="%sSG" % shader, empty=True, renderable=True, noSurfaceShader=True)
        #Set shaders properties
        cmds.setAttr("%s.specular" % shader, templateShader["specular"] )
        cmds.setAttr("%s.base" % shader, 1)
        #Assign Shader to Shading Group
        cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % shadingGroup)

        #### Displace ####
        if dispPath:
            #Scan for disp with wild card and pattern matching
            displaceTexAll = []
            displacePattern = ["displace","Height"]
            for pattern in displacePattern:
                displaceTexAll += glob.glob(dispPath+"\\*"+pattern+"*"+format)
            #Check if a displace texture is found
            if len(displaceTexAll) > 0: displaceTexPath = displaceTexAll[0]
            if displaceTexPath:
                #Create displacement shader node and configure
                dispShader = cmds.shadingNode("displacementShader", asShader=True, name="%sDisplace"%s)
                cmds.setAttr("%s.aiDisplacementZeroValue" % dispShader, templateShader["aiDisplacementZeroValue"] )
                cmds.setAttr("%s.aiDisplacementAutoBump" % dispShader, 1)
                #Create texture node for displacment
                dispTex = cmds.shadingNode("file", asTexture=True, name="%s_disp" %s)
                cmds.setAttr("%s.fileTextureName" % dispTex, displaceTexPath, type="string")
                if len(displaceTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % dispTex , 3) #to duim
                #Connect displacement
                cmds.connectAttr("%s.outColor.outColorR" %dispTex, "%s.displacement" % dispShader)
                cmds.connectAttr("%s.displacement" % dispShader, "%s.displacementShader" % shadingGroup)   #displacement

        #### Color ####
        if colorTexPath:
            colorTex = cmds.shadingNode("file", asTexture=True, name="%s_color" % s)
            cmds.setAttr("%s.fileTextureName" % colorTex , colorTexPath, type="string")
            if len(colorTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % colorTex , 3) #set to udim
            #Connect
            cmds.connectAttr("%s.outColor" %colorTex, "%s.baseColor" %shader)

        #### Specular Roughness ####
        if specRoughTexPath:
            specRoughnessTex = cmds.shadingNode("file", asTexture=True, name="%s_specRoughness" % s)
            cmds.setAttr("%s.alphaIsLuminance" % specRoughnessTex, 0) #Tick Alpah is Luminance
            cmds.setAttr("%s.fileTextureName" % specRoughnessTex, specRoughTexPath, type="string")
            if len(roughnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % specRoughnessTex , 3) #set to udim
            #Connect
            cmds.connectAttr("%s.outColor.outColorR" % specRoughnessTex, "%s.specularRoughness" %shader)

        #Metalness
        if metalnessTexPath:
            metalTex = cmds.shadingNode("file", asTexture=True, name="%s_metalness" % s)
            cmds.setAttr("%s.fileTextureName" % metalTex, metalnessTexPath, type="string")
            if len(metalnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % metalTex , 3) #set to udim
            cmds.connectAttr("%s.outColor.outColorR" %metalTex, "%s.metalness" %shader)

        #Normal
        if normalTexPath:
            NormalTex = cmds.shadingNode("file", asTexture=True, name="%s_Normal" % s)
            aiNormalMap = cmds.shadingNode("aiNormalMap", asTexture=True, name="%s_aiNormalMap" % s)
            cmds.setAttr("%s.fileTextureName" % NormalTex, normalTexPath, type="string")
            if len(normalTexAll) >= 2:cmds.setAttr("%s.uvTilingMode" % NormalTex , 3)  #set to udim
            cmds.connectAttr("%s.outColor" %NormalTex, "%s.input" %aiNormalMap)
            cmds.connectAttr("%s.outValue" %aiNormalMap, "%s.normalCamera" %shader)

        for obj in selection:
            #Arnold Subdivision attribut object
            cmds.setAttr("%s.aiSubdivType" % obj, 1)
            cmds.setAttr("%s.aiSubdivIterations" % obj, templateShader["aiSubdivIterations"])
            cmds.sets(obj, e=True, forceElement= shadingGroup)
plugin = SubstanceImporter()
