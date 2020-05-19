#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*
#####################################################################################

MegascansLiveLinkAPI is the core component of the Megascans Plugin plugins.
This API relies on a QThread to monitor any incoming data from Bridge by communicating
via a socket port.

This module has a bunch of classes and functions that are standardized as much as possible
to make sure you don't have to modify them too much for them to work in any python-compatible
software.
If you're looking into extending the user interface then you can modify the MegascansLiveLinkUI
class to suit your needs.

#####################################################################################
#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*"""


import os, json, sys, socket, time, re

#BLOOM MODFI
#TO MAKE THE SCRIPT RELOAD YOU MUST MODIFY THE SHELF WITH reload(MSLiveLink.MS_API)
import maya.cmds as mc
import maya.mel as melc


class importerSetup():
    Identifier = None
    """set_Asset_Data takes the json data we received from the thread and converts it into
       a friendly structure for all the other functions to use. """

    def __init__(self):
        importerSetup.Identifier = self

    def set_Asset_Data(self, json_data):

        self.setRenderEngine()

        if(self.Renderer == "Not-Supported"):
            msg = 'Your current render engine is not supported by the Bridge Plugin so we are terminating the import process but the Plugin is still running!'
            mc.confirmDialog( title='MS Plugin Error', message=msg, button=['Ok'], defaultButton='Ok', cancelButton='Ok', dismissString='Ok')
            print (msg)
            return
        else:
            print("Your current render engine is " + self.Renderer)

        self.json_data = json_data
        self.TexturesList = []
        self.Type = self.json_data["type"]
        self.mesh_transforms = []
        self.imported_geo = []
        self.Path = self.json_data["path"]
        self.activeLOD = self.json_data["activeLOD"]

        self.minLOD = self.json_data["minLOD"]
        self.ID = self.json_data["id"]
        self.height = float(1.0)
        self.isScatterAsset = self.CheckScatterAsset()
        self.isBillboard = self.CheckIsBillboard()

        self.dictSetup = None

        self.All_textures_ = ["albedo", "displacement", "normal", "roughness", "specular", "normalbump",
                               "ao", "opacity", "translucency", "gloss", "metalness", "bump", "fuzz"]

        texturesListName = "components"
        if self.isBillboard:
            texturesListName = "components"

        self.TexturesList = [(obj["format"], obj["type"], obj["path"]) for obj in self.json_data[texturesListName] if obj["type"] in self.All_textures_]

        self.GeometryList = [(obj["format"], obj["path"]) for obj in self.json_data["meshList"]]

        if "name" in self.json_data.keys():
            self.Name = self.json_data["name"].replace(" ", "_")

        else:
            self.Name = os.path.basename(self.json_data["path"]).replace(" ", "_")

            if len(self.Name.split("_")) >= 2:
                self.Name = "_".join(self.Name.split("_")[:-1])

        self.materialName = self.Name + '_' + self.ID

        try:
            if 'meta' in self.json_data.keys():

                meta = self.json_data['meta']
                height_ = [item for item in meta if item["key"].lower() == "height"]
                if len(height_) >= 1:
                    self.height = float( height_[0]["value"].replace('m','') )
        except:
            pass

        self.initAssetImport()


    ########################################################################################
    """#############################    IMPORT FUNCTIONS    #############################"""
    ########################################################################################
    """#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*"""

    """initAssetImport initializes the main import chain process.
       Our geometry, materials and asset structure set up are all initialized within this
       function, which we call whenever the user imports a new asset
    """

    def initAssetImport(self):

        plugins_ = [item.lower() for item in mc.pluginInfo( query=True, listPlugins=True )]

        unit_ = mc.currentUnit(q=True)
        mc.currentUnit(l="centimeter")
        warnings = mc.scriptEditorInfo(q=True, suppressWarnings=True)
        mc.scriptEditorInfo(suppressWarnings=True)

        self.importGeometryData()
        self.importTextureData()

        if self.Renderer == "Redshift" and "redshift4maya" in plugins_:
            self.Redshift25_Setup()

        elif self.Renderer == "Vray" and "vrayformaya" in plugins_:
            self.Vray36_Setup()

        elif self.Renderer == "Arnold" and "mtoa" in plugins_:
            self.Arnold3_Setup()

        else:
            mc.warning(self.Renderer + " was not found, please make sure it's installed.")

        self.ScatterAssetSetup()

        mc.currentUnit(l=unit_)
        mc.scriptEditorInfo(suppressWarnings=warnings)

    def CheckScatterAsset(self):
        if(self.Type == "3d"):
            if('scatter' in self.json_data['categories'] or 'scatter' in self.json_data['tags']):
                # print("It is 3D scatter asset.")
                return True
        return False

    def CheckIsBillboard(self):
        # Use billboard textures if importing the Billboard LOD.
        if(self.Type == "3dplant"):
            if (self.activeLOD == self.minLOD):
                # print("It is billboard LOD.")
                return True
        return False


    def setRenderEngine(self):
        selectedRenderer = melc.eval("getAttr defaultRenderGlobals.currentRenderer;")
        selectedRenderer = selectedRenderer.lower()
        self.Renderer = "Not-Supported"

        if("redshift" in selectedRenderer):
            self.Renderer = "Redshift"
        elif("vray" in selectedRenderer):
            self.Renderer = "Vray"
        elif("arnold" in selectedRenderer):
            self.Renderer = "Arnold"

    #########################################################################################

    """ importTextureData creates a file node for each texture in self.TexturesList. """

    def importTextureData(self):

        self.tex_nodes = []

        cm_attrs = [("cme", "cme"), ("cfe", "cmcf"), ("cfp", "cmcp"), ("wsn", "ws")]
        colMgmtGlob = ('defaultColorMgtGlobals')
        self.coord_2d = mc.shadingNode('place2dTexture', asUtility=True, name=(self.ID + "_Coords"))

        maps_ = [item[1] for item in self.TexturesList]

        # tex = self.TexturesList[2]
        for tex in self.TexturesList:

            texture_ = tex[2]

            if tex[1] == "displacement":
                print("DISPLACEMENT SET TO EXR...")
                dirn_ = os.path.dirname(tex[2])
                filen_ = os.path.splitext(os.path.basename(tex[2]))[0]
                if os.path.exists(os.path.join(dirn_, filen_ + ".exr")):
                    texture_ = os.path.join(dirn_, filen_ + ".exr")

            newMap = mc.shadingNode('file', asTexture=True, name=(self.Name + "_" + tex[1].capitalize()) )

            mc.setAttr(newMap+".ftn", texture_, type="string")
            try:
                for attr in cm_attrs:
                    mc.connectAttr(colMgmtGlob +"."+attr[0], newMap+"."+attr[1])
            except:
                pass

            mc.setAttr(newMap+".ft", 2)
            mc.defaultNavigation(connectToExisting=True, source=self.coord_2d, destination=newMap)

            if tex[0] == "exr":
                #EDIT BLOOM
                melc.eval('setAttr "'+ newMap +'.cs" -type "string" "Utility - Raw";')
            else:
                if tex[1].lower() in ["albedo", "translucency"]:
                #EDIT BLOOM
                    melc.eval('setAttr "'+ newMap +'.cs" -type "string" "Utility - sRGB - Texture";')
                else:
                #EDIT BLOOM
                    melc.eval('setAttr "'+ newMap +'.cs" -type "string" "Utility - Raw";')


            self.tex_nodes.append((newMap, tex[1]))


    #########################################################################################

    """importGeometryData importes our geometry. """

    def importGeometryData(self):

        scene_a = mc.ls()

        if self.ApplyToSelection and self.Type.lower() not in ["3dplant", "3d"]:
            try:
                for m in mc.ls(sl=True,typ="transform"):
                    objectProps = mc.listRelatives(m, typ="mesh")
                    if objectProps is not None and len(objectProps) >= 1:
                        self.mesh_transforms.append(m)
                    else:
                        objectProps = mc.listRelatives(m, typ="nurbsSurface")
                        if objectProps is not None and len(objectProps) >= 1:
                            self.mesh_transforms.append(m)
            except:
                pass

        for mesh in self.GeometryList:
            if mesh[0] == "fbx":
                path_ = mesh[1]
                mc.file(path_, i=True, type="FBX", ignoreVersion=True, rpr=os.path.basename(self.Name), options="fbx")

            elif mesh[0] == "obj":
                path_ = mesh[1]
                mc.file(path_, i=True, type="OBJ", ignoreVersion=True, rpr=os.path.basename(self.Name), options="obj")

            elif mesh[0] == "abc":
                path_ = mesh[1]
                mc.file(path_, i=True, type="Alembic", ignoreVersion=True, rpr=os.path.basename(self.Name), importFrameRate = True, importTimeRange = "override")

        imported_ = list(set(mc.ls())-set(scene_a))

        for a in imported_:
            try:
                if mc.nodeType(a) == "transform":
                    melc.eval('assignSG lambert1 '+ a +';')

                    newMesh = mc.rename(a, self.createName(a) )
                    self.mesh_transforms.append(newMesh)
                    self.imported_geo.append(newMesh)

                if mc.nodeType(a) not in ["transform", "mesh"]:
                    try:
                        melc.eval('delete ' + a)
                    except:
                        pass
            except:
                pass

    def ScatterAssetSetup(self):
        if self.isScatterAsset and len(self.imported_geo) > 1:
            try:
                self.scatterParentName = self.ID + '_' + self.Name
                self.scatterParentName = mc.group( em=True, name=self.scatterParentName)

                for meshName in self.imported_geo:
                    try:
                        melc.eval('parent '+ meshName +' '+ self.scatterParentName +';')
                    except:
                        pass
            except:
                pass

    def createName(self, meshName):

        shortName = meshName

        try:
            if len(meshName.split("_") ) > 2:
                shortName = [meshName.split("_")[-2], meshName.split("_")[-1]]

                if shortName[0].lower() == self.ID.lower():
                    shortName.remove(shortName[0] )

                shortName = self.Name + '_' + self.ID + "_" + "_".join( shortName )
        except:
            shortName = meshName

        return shortName


    #MATERIAL SETUP FUNCTIONS

    #########################################################################################

    """Arnold3_Setup creates a Redshift material setup. """

    def Arnold3_Setup(self):

        nodes_ = mc.allNodeTypes()
        if len(self.tex_nodes) >= 1 and "aiStandardSurface" in nodes_:

            # Set the material and shading group

            arn_mat = mc.shadingNode('aiStandardSurface', asShader=True, name=(self.Name + "_Mat"))

            #EDIT BLOOM
            mc.setAttr(arn_mat+".specular", 1)
            mc.setAttr(arn_mat+".base", 1)
            mc.setAttr(arn_mat+".specularIOR", 1.4)
            mc.setAttr(arn_mat+".subsurfaceScale", 0.1)
            mc.setAttr(arn_mat+".subsurfaceRadius", 0.525634, 0.717933, 0.360343, type="double3")
            arn_sg = mc.sets(r=True, nss=True, name=(self.Name + "_SG"))
            mc.defaultNavigation(connectToExisting=True, source=arn_mat, destination=arn_sg)

            maps_ = [item[1] for item in self.tex_nodes]
            used_maps = []


            if "normal" in maps_:
                arn_normal = mc.shadingNode('bump2d', asUtility=True, name=(self.ID + "_bump2d"))
                mc.setAttr(arn_normal+".bumpInterp",1)
                mc.setAttr(arn_normal+".aiFlipR",0)
                mc.setAttr(arn_normal+".aiFlipG",0)
                normal_ = [item[0] for item in self.tex_nodes if item[1] == "normal"][0]
                mc.connectAttr((normal_+".outAlpha"), (arn_normal+".bumpValue"))
                if self.Type == "3dplant":
                    mc.connectAttr((arn_normal+".outNormal"), (arn_mat+".normalCamera"))
                    used_maps.append(arn_normal)


            if "albedo" in maps_:
                albedo_ = [item[0] for item in self.tex_nodes if item[1] == "albedo"][0]
                albedo_colorCorrect = mc.shadingNode("gammaCorrect", asUtility=True, name=(self.ID + "_gammaCorrect"))

                mc.setAttr(albedo_+".exposure", 0)
                mc.setAttr(albedo_colorCorrect+".gammaX",1)
                mc.setAttr(albedo_colorCorrect+".gammaY",1)
                mc.setAttr(albedo_colorCorrect+".gammaZ",1)
                mc.connectAttr((albedo_+".outColor"), (albedo_colorCorrect+".value"))
                mc.connectAttr((albedo_colorCorrect+".outValue"), (arn_mat+".baseColor"))
                mc.connectAttr((albedo_colorCorrect+".outValue"), (arn_mat+".subsurfaceColor."))


                used_maps.append(albedo_)


            if "roughness" in maps_:
                arn_rough_range = mc.shadingNode('remapColor', asUtility=True, name=(self.ID + "_Rough_Range"))
                mc.setAttr(arn_rough_range+".outputMax",0.6)
                mc.setAttr(arn_rough_range+".outputMin",0.4)
                roughness_ = [item[0] for item in self.tex_nodes if item[1] == "roughness"][0]
                mc.connectAttr((roughness_+".outColor"), (arn_rough_range+".color"))
                mc.connectAttr((arn_rough_range+".outColor.outColorR"), (arn_mat+".specularRoughness"))
                mc.setAttr(roughness_+".alphaIsLuminance", 1)

                used_maps.append(roughness_)


            if "displacement" in maps_:
                if self.activeLOD  != "high" and self.Type != "3dplant":
                    arn_disp_shr = mc.shadingNode('displacementShader', asTexture=True, name=(self.ID + "_Displacement_shr"))
                    subNode = mc.shadingNode('aiSubtract', asTexture=True, name=(self.ID + "_aiDispMid"))
                    mc.setAttr(subNode+'.input2',0.75, 0.75, 0.75, typ='double3' ) #MEGASCAN MID DISPLACE OFTEN AT 0,75... Why ? Idk.
                    displacement_ = [item[0] for item in self.tex_nodes if item[1] == "displacement"][0]
                    mc.connectAttr((displacement_+".outColorR"), (subNode+".input1.input1R"))
                    mc.connectAttr((subNode+".outColor.outColorR"), (arn_disp_shr+".displacement"))
                    mc.connectAttr((arn_disp_shr+".displacement"), (arn_sg+".displacementShader"))
                    mc.setAttr(displacement_+".alphaIsLuminance", 1)
                    mc.setAttr(arn_disp_shr+".scale", 1)
                    mc.setAttr(arn_disp_shr+".aiDisplacementZeroValue", 0)
                    used_maps.append(displacement_)


            if "metalness" in maps_:
                metalness_ = [item[0] for item in self.tex_nodes if item[1] == "metalness"][0]
                mc.connectAttr((metalness_+".outAlpha"), (arn_mat+".metalness"))
                mc.setAttr(metalness_+".alphaIsLuminance", 1)

                used_maps.append(metalness_)


            if "translucency" in maps_:
                translucency_ = [item[0] for item in self.tex_nodes if item[1] == "translucency"][0]
                addNode = mc.shadingNode('aiAdd', asTexture=True, name=(self.ID + "_aiAdd"))
                mc.connectAttr((translucency_+".outColor"), (addNode+".input1"))
                mc.connectAttr((albedo_colorCorrect+".outValue"), (addNode+".input2"))
                mc.connectAttr((addNode+".outColor"), (arn_mat+".subsurfaceColor"), f=True)
                mc.setAttr(arn_mat+".subsurface", 1)
                mc.setAttr(arn_mat+".thinWalled", 1)
                mc.setAttr(arn_mat+".subsurface", 0.35)

                used_maps.append(translucency_)


            if "fuzz" in maps_:
                #arn_fuzz_range = mc.shadingNode('aiRange', asShader=True, name=(self.ID + "_Fuzz_Range"))
                fuzz_ = [item[0] for item in self.tex_nodes if item[1] == "fuzz"][0]
                #mc.connectAttr((fuzz_+".outColor"), (arn_fuzz_range+".input"))
                #mc.connectAttr((arn_fuzz_range+".outColor.outColorR"), (arn_mat+".subsurface"))
                #mc.setAttr(fuzz_+".alphaIsLuminance", 1)
                #mc.setAttr(arn_fuzz_range+".outputMax", 0.85)
                used_maps.append(fuzz_)


            if "specular" in maps_ :
                if self.Type != "3dplant":
                    arn_spec_range= mc.shadingNode('remapColor', asUtility=True, name=(self.ID + "_specular_remapColor"))
                    #mc.setAttr(arn_spec_range+".outputMax",0)
                    #mc.setAttr(arn_spec_range+".outputMin",1)
                    spec_= [item[0] for item in self.tex_nodes if item[1] == "specular"][0]
                    mc.connectAttr((spec_+".outColor"), (arn_spec_range+".color"))
                    mc.connectAttr((arn_spec_range+".outColor"), (arn_mat+".specularColor"))
                    used_maps.append(spec_)
                else:
                    mc.setAttr(arn_mat+".specular", 0.6)

            if "opacity" in maps_:
                opacity_ = [item[0] for item in self.tex_nodes if item[1] == "opacity"][0]
                mc.connectAttr((opacity_+".outColor"), (arn_mat+".opacity"))
                mc.setAttr(opacity_+".alphaIsLuminance", 1)
                mc.setAttr(arn_mat+".thinWalled", 1)

                used_maps.append(opacity_)

            if len(self.mesh_transforms) >= 1:
                for mesh_ in self.mesh_transforms:
                    if self.activeLOD != "high":
                        mc.setAttr(mesh_+".aiSubdivType", 1)
                        if self.Type == '3dplant':
                            mc.setAttr(mesh_+".aiSubdivIterations", 1)
                        else:
                            mc.setAttr(mesh_+".aiSubdivIterations", 3)
                        mc.select(mesh_)
                        try:
                            melc.eval('polyCleanupArgList 4 { "0","1","1","0","0","0","0","0","0","1e-05","0","1e-05","0","1e-05","0","1","0","0" };')
                            mc.select(mesh_)
                            mc.polySetToFaceNormal()
                            mc.polySoftEdge()
                            mc.delete(mesh_, ch = 1)
                        except:
                            pass

                    if "displacement" in maps_:

                        if self.Type in ["3dplant", "3d"]:
                            mc.setAttr(mesh_+".aiDispHeight", 1)
                            mc.setAttr(mesh_+".aiDispZeroValue", 0)

                        else:
                            mc.setAttr(mesh_+".aiDispHeight",2)
                            mc.setAttr(mesh_+".aiDispZeroValue", 0)

                    if "opacity" in maps_:
                        mc.setAttr(mesh_+".aiOpaque", 0)

                    if "normal" not in maps_:
                        mc.setAttr(mesh_+".aiDispAutobump", 1)


                    mc.select(mesh_)
                    melc.eval('sets -e -forceElement '+arn_sg)

            self.RearrangeHyperShade()

        else:
            print("Please make sure you have the latest version of Arnold installed. Go to SolidAngle.com to get it.")

    # Reorganize the hypershade to clean the node layout. You can avoid using the
    # method if you don't want the plugin to change the position of your nodes.
    def RearrangeHyperShade(self):
        try:
            melc.eval('HypershadeWindow;')
            melc.eval('hyperShadePanelGraphCommand("hyperShadePanel1", "rearrangeGraph");')
        except:
            pass
    # This is not closing the hypershade window right now.
    def CloseHyperShader(self):
        try:
            melc.eval('closeNodeEditorEd hyperShadePrimaryNodeEditor;')
        except:
            pass

    # Returns the json structure sent by Bridge
    def getExportStructure(self):
        return self.json_data

    # Save preferences
    def loadApplyToSelection(self):
        if mc.optionVar( exists='QxlApplyToSelection') == 1:
            applyToSelectionFlag = mc.optionVar( q='QxlApplyToSelection')
            if applyToSelectionFlag == 1:
                self.ApplyToSelection = True
            else:
                self.ApplyToSelection = False
        else:
            self.setApplyToSelection(2)
            self.ApplyToSelection = False
        return self.ApplyToSelection

    def getApplyToSelection(self):
        return self.ApplyToSelection

    def updateApplyToSelection(self, flag = False):
        if flag:
            self.setApplyToSelection(1)
            self.ApplyToSelection = True
        else:
            self.setApplyToSelection(2)
            self.ApplyToSelection = False

    def setApplyToSelection(self, value):
        mc.optionVar( iv=('QxlApplyToSelection', value))


try:
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
except:
    try:
        from PySide.QtGui import *
        from PySide.QtCore import *
    except:
        try:
            from PyQt5.QtGui import *
            from PyQ5.QtCore import *
            from PyQ5.QtWidgets import *
        except:
            try:
                from PyQt4.QtGui import *
                from PyQ4.QtCore import *
            except:
                pass


maya_plugin_version = "4.8"

""" GetHostApp returns the host application window as a parent for our widget """

def GetHostApp():
    try:
        mainWindow = QApplication.activeWindow()
        while True:
            lastWin = mainWindow.parent()
            if lastWin:
                mainWindow = lastWin
            else:
                break
        return mainWindow
    except:
        pass


""" QLiveLinkMonitor is a QThread-based thread that monitors a specific port for import.
Simply put, this class is responsible for communication between your software and Bridge."""

class QLiveLinkMonitor(QThread):

    Bridge_Call = Signal()
    Instance = []

    def __init__(self):
        QThread.__init__(self)
        self.TotalData = b""
        QLiveLinkMonitor.Instance.append(self)

    def __del__(self):
        self.quit()
        self.wait()

    def stop(self):
        self.terminate()

    def run(self):

        time.sleep(0.025)

        try:
            host, port = 'localhost', 13291

            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_.bind((host, port))

            while True:
                socket_.listen(5)
                client, address = socket_.accept()
                data = ""
                data = client.recv(4096*2)

                if data != "":
                    self.TotalData = b""
                    self.TotalData += data
                    while True:
                        data = client.recv(4096*2)
                        if data : self.TotalData += data
                        else : break

                    time.sleep(0.05)
                    self.Bridge_Call.emit()
                    time.sleep(0.05)
                    # break
        except:
            pass

    def InitializeImporter(self):
        print("Found import data, importing...")
        json_array = json.loads(self.TotalData)
        for asset_ in json_array:
            self = importerSetup.Identifier
            self.set_Asset_Data(asset_)


"""
#################################################################################################
#################################################################################################
"""

stylesheet_ = ("""

QCheckBox { background: transparent; color: #E6E6E6; font-family: Source Sans Pro; font-size: 14px; }
QCheckBox::indicator:hover { border: 2px solid #2B98F0; background-color: transparent; }
QCheckBox::indicator:checked:hover { background-color: #2B98F0; border: 2px solid #73a5ce; }
QCheckBox:indicator{ color: #67696a; background-color: transparent; border: 2px solid #67696a;
width: 14px; height: 14px; border-radius: 2px; }
QCheckBox::indicator:checked { border: 2px solid #18191b;
background-color: #2B98F0; color: #ffffff; }
QCheckBox::hover { spacing: 12px; background: transparent; color: #ffffff; }
QCheckBox::checked { color: #ffffff; }
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { border: 1px solid #444; }
QCheckBox:disabled { background: transparent; color: #414141; font-family: Source Sans Pro;
font-size: 14px; margin: 0px; text-align: center; }

QComboBox { color: #FFFFFF; font-size: 14px; padding: 2px 2px 2px 8px; font-family: Source Sans Pro;
selection-background-color: #1d1e1f; background-color: #1d1e1f; }
QComboBox:hover { color: #c9c9c9; font-size: 14px; padding: 2px 2px 2px 8px; font-family: Source Sans Pro;
selection-background-color: #232426; background-color: #232426; } """)


"""
#################################################################################################
#################################################################################################
"""


class LiveLinkUI(QWidget):

    Instance = []
    Settings = [0, 0, 0]


    # USER INTERFACE WIDGETS

    def __init__(self, _importerSetup_, parent=GetHostApp()):
        super(LiveLinkUI, self).__init__(parent)

        LiveLinkUI.Instance = self
        self.Importer = _importerSetup_
        self.Importer.loadApplyToSelection()

        self._path_ = os.path.dirname(__file__).replace("\\", "/")

        self.setObjectName("LiveLinkUI")
        img_ = QPixmap( os.path.join(self._path_, "MS_Logo.png") )
        self.setWindowIcon(QIcon(img_))
        self.setMinimumWidth(275)
        self.setWindowTitle("MS Plugin " + maya_plugin_version + " - Maya")
        self.setWindowFlags(Qt.Window)

        self.style_ = ("""  QWidget#LiveLinkUI { background-color: #262729; } """)
        self.setStyleSheet(self.style_)

        # Set the main layout
        self.MainLayout = QVBoxLayout()
        self.setLayout(self.MainLayout)
        self.MainLayout.setSpacing(5)
        self.MainLayout.setContentsMargins(5, 2, 5, 2)


        #Set the checkbox options

        self.checks_l = QVBoxLayout()
        self.checks_l.setSpacing(2)
        self.MainLayout.addLayout(self.checks_l)

        self.applytoSel = QCheckBox("Apply Material to Selection")
        self.applytoSel.setToolTip("Applies the imported material(s) to your selection\?n prior to the import.")
        self.applytoSel.setChecked( self.Importer.getApplyToSelection())
        self.applytoSel.setFixedHeight(30)
        self.applytoSel.setStyleSheet(stylesheet_)

        self.checks_l.addWidget(self.applytoSel)

        self.applytoSel.stateChanged.connect(self.settingsChanged)


    # USER INTERFACE FUNCTIONS

    def settingsChanged(self):
        self.Importer.updateApplyToSelection(self.applytoSel.isChecked())


# PLUGIN UI INITIALIZER
def initLiveLink(openUI = True):

    _importerSetup_ = importerSetup()

    if LiveLinkUI.Instance != None:
        try: LiveLinkUI.Instance.close()
        except: pass

    LiveLinkUI.Instance = LiveLinkUI(_importerSetup_)
    LiveLinkUI.Instance.show()
    pref_geo = QRect(500, 300, 460, 30)
    LiveLinkUI.Instance.setGeometry(pref_geo)
    StartSocketServer()

    return LiveLinkUI.Instance

def createMSshelf():

    import maya.cmds as cmds
    import maya.mel as mel

    path_ = os.path.dirname(__file__).replace("\\", "/")

    shelfName_ = "MSPlugin"
    imgPath = os.path.join( path_, "MS_Logo.png" ).replace("\\", "/")
    cmd_ = ("""import sys
path_ = 'PATH'
if path_ not in sys.path:
    sys.path.append( path_ )
import MSLiveLink.MS_API as msAPI
msAPI.initLiveLink()""").replace("PATH", os.path.dirname(path_).replace("\\", "/") )

    shelftoplevel = mel.eval("$gShelfTopLevel = $gShelfTopLevel;")

    shelfList_ = cmds.tabLayout(shelftoplevel, query=True, childArray=True)

    try:
        DeleteMayaOldShelf()
    except:
        pass

    if shelftoplevel != None:
        if shelfName_ in shelfList_:
            try:
                for element in cmds.shelfLayout(shelfName_, q=1, ca=1):
                    cmds.deleteUI(element)
            except:
                pass
        else:
            mel.eval("addNewShelfTab " + shelfName_ + ";")

        cmds.shelfButton( label="MS", command=cmd_, parent=shelfName_, image=imgPath)
        cmds.saveAllShelves(shelftoplevel)

    initLiveLink()

def DeleteMayaOldShelf(shelfName = "MSLiveLink"):
    import maya.cmds as cmds
    import maya.mel as mel

    try:
        shelfExists = cmds.shelfLayout(shelfName, ex=True)
        if shelfExists:
            mel.eval('deleteShelfTab %s' % shelfName)
            gShelfTopLevel = mel.eval('$tmpVar=$gShelfTopLevel')
            cmds.saveAllShelves(gShelfTopLevel)
        else:
            return
    except:
        pass

# Start the Plugin server here.
def StartSocketServer():
    try:
        if len(QLiveLinkMonitor.Instance) == 0:
            bridge_monitor = QLiveLinkMonitor()
            bridge_monitor.Bridge_Call.connect(bridge_monitor.InitializeImporter)
            bridge_monitor.start()
        print("Quixel Bridge Plugin started successfully.")
    except:
        print("Quixel Bridge Plugin failed to start.")
        pass
