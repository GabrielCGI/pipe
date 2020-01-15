import maya.cmds as cmds
import os
import sys
#Load Abc Plugins
cmds.loadPlugin("AbcImport.mll", quiet=True)
cmds.loadPlugin("AbcExport.mll", quiet=True)



import projects as projects
reload(projects)


currentProject = projects.getCurrentProject()
projectsData = projects.getProjectData(currentProject)
assetsDir = projectsData.get("assetsDir")
assetsDic = projects.buildAssetDb()   #Get dictionnary of all asset for th current project


def nameFromCharRef(charRef):
    "Parse the references name to get the character name"
    name = "not a character"                # hack to avoid an error from empty string
    charRefUnique = charRef.split("RN")[0]              # Get only the reference name without number suffix


    if len(charRefUnique.split("_")) >= 2:
        name = "%s_%s"%(charRefUnique.split("_")[0],charRefUnique.split("_")[1])  #assetame = ch_x_rig_lib1.abc => ch_x
    return name


def listCharRef():
    "Return a list of all references wich is a Character"
    listCharRef = []
    #List all references
    listAllRef = cmds.ls(type="reference")

    for ref in listAllRef:
        name = nameFromCharRef(ref)  #Ch_gros
        if any(name in nameFromDic for nameFromDic in assetsDic.keys()):
            if len(ref.split(":")) <= 1:            # filter through the child node of the rig reference
                listCharRef.append(ref)
    print "list char ref:%s"%(listCharRef)
    return listCharRef


def listSelectedCharRef():
    "Return a list of references, parent from current selection, wich is a Character"
    print "listSelectedCharRef"
    listSelectedRef = []
    selection = cmds.ls(selection=True)

    for shape in selection:
        shapeNameSpace = shape.split(":")[0]  # Delete ":" (ch_x_rig_lib1:GEO_x . . . => ch_x_rig_lib1)
        print "shape name space: %s"%(shapeNameSpace)
        listAllRef = cmds.ls(type="reference")
        for ref in listAllRef:
            print "ref: %s" % (ref)
            refSplit = ref.split("RN")
            if len(refSplit) >= 2:              # make sure the list is > 2 element to avoid "list index out of range"
                if shapeNameSpace == "%s%s" % (refSplit[0], refSplit[1]):               #(ch_xRN1 => ch_x1)
                    if ref not in listSelectedRef:
                        listSelectedRef.append(ref)
    return listSelectedRef


def listGeoByCharRef(charRef):
    "Return a list of all Geo needed to be exported in the Alembic"
    listGeo= []
    name = nameFromCharRef(charRef)

    # Get from a database a list of the character's shapes to be exported
    listGeoDic = assetsDic.get(name).get("geo")
    version = charRef.split("RN")[-1]
    baseName = charRef.split("RN")[0]

    for geoDic in listGeoDic:
        if version: #Si il y a des version ['ch_rat_rig_lib', '1']
            split = geoDic.split(baseName) #["ch_rat_rig_lib",":GEO"]
            geoVersion = baseName+version+split[1] #["ch_rat_rig_lib1:GEO"]
            listGeo.append(geoVersion)
        if not version: #Si il n'y a pas de version ['ch_rat_rig_lib', '']
            listGeo.append(geoDic)

    #Return list
    return listGeo


def buildCommand (start, end, path, geoList, attrList, subframe, frameSample):
   "Build Command for abc export job"
   command = ""
   command += "-frameRange %s %s"%(start, end) #Frame Range
   command += " -uvWrite -writeUVSets -dataFormat ogawa "
   if subframe == True:
       if len(frameSample.split(" ")==3):
           for f in frameSample.split(" "):
               command += "-frameRelativeSample %s "%(f)
   if attrList[0]:
       for attr in attrList:
           command += " -attr %s"%(attr)           #Attributs

   for geo in geoList:
       geoRootName = cmds.ls(geo, l=True)[0]     #Geo List
       command += " -root %s"%geoRootName

   command += " -file %s"%(path)                #File Path
   return command


def exportAbcByChar(charRef, start, end, dirPath, subframe, frameSample):
    "Export an Abc for a given character"
    name = nameFromCharRef(charRef)
    print "MM_NAME:"
    print name
    geoList = listGeoByCharRef(charRef)
    print "GEOLIST:"
    print geoList
    attrList = assetsDic.get(name).get("attr")
    if not charRef.split("RN")[1]:   #if list empty
        num = "00"
    else:
        num = "%02d"%(int(charRef.split("RN")[1]))
    abcName = "%s_%s.abc"%(name,num)
    path = os.path.join(dirPath[0],abcName)
    command = buildCommand(start,end,path,geoList,attrList,subframe,frameSample)
    print "------------------------\n------------ BEGGINING EXPORT %s ------------ \n %s"%(charRef, command)
    cmds.refresh(suspend=True)
    cmds.AbcExport (j= command )
    cmds.refresh(suspend=False)
    print "------------ SUCCESS EXPORT %s  ! ------------"%(charRef)


def exportAnim(start=0, end=100, subframe=False, frameSample="0 0 0", charList=[]):
    basicFilter = "*.abc"
    dirPath = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=2,)
    for char in charList:
        exportAbcByChar(char, start, end, dirPath, subframe, frameSample)

def updateList():
    return

#GUI
class exportAnimGuiCls(object):
    def __init__(self):

        pass

    def show(self):
        self.exportAnimGui()

    def exportAnimGui(self):
        if cmds.window("Export Alembic", exists=True):
            cmds.deleteUi("Export Alembic")

        self.window = cmds.window(title="Export Alembic", iconName="Export Abc")
        cmds.columnLayout(columnWidth=400)

        self.charList = cmds.textScrollList( numberOfRows=8, allowMultiSelection=True,
                        append=[],
                        showIndexedItem=4 )

        mainLayout = cmds.gridLayout(numberOfColumns=2, cellWidthHeight=(90, 20))
        cmds.text(label="Start Range:")
        startField = cmds.intField('start', v=cmds.playbackOptions(min=True, query=True))
        cmds.text(label="End Range:")
        endField = cmds.intField('end', v=cmds.playbackOptions(max=True, query=True))
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=2)
        frameSample = cmds.textField(text = "-0.25 0 0.25")
        subFrameCheckBox = cmds.checkBox(label="Subframes", value = False)

        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=1)
        btnExport = cmds.button(label="Export", width=180, c=lambda *_: self.exportClicked(
            start=cmds.intField(startField, q=1, v=1),end=cmds.intField(endField, q=1, v=1),
            charList= cmds.textScrollList(self.charList,q=True,selectItem=True),
            subframe=cmds.checkBox(subFrameCheckBox,q=1,v=1),
            frameSample= cmds.textField(frameSample, q=1, text=1)
            ))
        cmds.setParent("..")

        cmds.showWindow(self.window)

    def updateCharList(self, charList):
        print cmds.textScrollList(self.charList, e=True, append=charList)


    def exportClicked(self, start=0, end=100,subframe=False,frameSample="0 0 0", charList=[]):
        if charList:
            exportAnim(start=start, end=end, subframe=subframe,frameSample="0 0 0", charList=charList)
        else:
            cmds.confirmDialog(title="Nothing selected",message="Nothing selected !")
