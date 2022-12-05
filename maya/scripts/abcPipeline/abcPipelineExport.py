import maya.cmds as cmds
import os
import sys
import importlib
#Load Abc Plugins
cmds.loadPlugin("AbcImport.mll", quiet=True)
cmds.loadPlugin("AbcExport.mll", quiet=True)



import projects as projects



currentProject = projects.getCurrentProject()
projectsData = projects.getProjectData(currentProject)
assetsDir = projectsData.get("assetsDir")
assetsDic = projects.buildAssetDb()   #Get dictionnary of all asset for th current project

def nameFromCharRef(charRef):
    "Parse the references name to get the character name"
    name = "not a character"                # hack to avoid an error from empty string
    charRefUnique = charRef.split("RN")[0]              # Get only the reference name without number suffix

    split = charRefUnique.split("_")
    try:
        name = split[0]+"_"+split[1]
    except:
        pass


    return name

def listCharRef():
    "Return a list of all references wich is a Character"
    listCharRef = []
    #List all references
    listAllRef = cmds.ls(type="reference")

    for ref in listAllRef:
        name = nameFromCharRef(ref)  #Ch_gros

        try: #Obligatory try because referenceQuery raise error: sharedReferenceNode' is not associated with a reference file. #
            if cmds.referenceQuery(ref, isLoaded=True): #Check if the reference is loaded
                if any(name in nameFromDic for nameFromDic in list(assetsDic.keys())):
                    if len(ref.split(":")) <= 1:            # filter through the child node of the rig reference
                            listCharRef.append(ref)
        except:
            pass
    return listCharRef

def listSelectedCharRef():
    "Return a list of references, parent from current selection, wich is a Character"
    listSelectedRef = []
    selection = cmds.ls(selection=True)

    for shape in selection:
        shapeNameSpace = shape.split(":")[0]  # Delete ":" (ch_x_rig_lib1:GEO_x . . . => ch_x_rig_lib1)
        listAllRef = cmds.ls(type="reference")
        for ref in listAllRef:
            print("ref: %s" % (ref))
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
    baseName = charRef.split("RN")[0] #ch_gingerbreadCandy_rigging_lib

    for geoDic in listGeoDic:
        print(geoDic)
        geoOnly = geoDic.split(":")
        if len(geoOnly)>1:
            del geoOnly[0]
            geo_stich = (":").join(geoOnly)
            geoOnly=[]
            geoOnly.append(geo_stich)

        geoWithNamespace = cmds.referenceQuery(charRef, namespace=True ) + ":" + geoOnly[-1]
        print(geoWithNamespace)
        listGeo.append(geoWithNamespace)

    #Return list
    print(listGeo)
    return listGeo

def buildCommand (start, end, path, geoList, attrList, subframe, frameSample,filterEuler,v2):
   "Build Command for abc export job"
   command = ""
   command += "-frameRange %s %s"%(start, end) #Frame Range
   if v2:
       command += " -writeVisibility  -stripNamespaces  -worldSpace -dataFormat ogawa "
   else:
       command += " -writeVisibility -uvWrite -writeColorSets -stripNamespaces -writeUVSets -worldSpace -dataFormat ogawa "
   if subframe == True:
       for f in frameSample.split(" "):
           command += "-frameRelativeSample %s "%(f)
   if filterEuler == True:
       command += "-eulerFilter"
   if attrList[0]:
       for attr in attrList:
           command += " -attr %s"%(attr)           #Attributs

   for geo in geoList:
       geoRootName = cmds.ls(geo, l=True)[0]     #Geo List
       command += " -root %s"%geoRootName

   command += " -file \"%s\""%(path)                #File Path
   return command

def exportAbcByChar(charRef, start, end, dirPath, subframe, frameSample, filterEuler):
    "Export an Abc for a given character"
    name = nameFromCharRef(charRef)
    geoList = listGeoByCharRef(charRef)
    v2 = False
    if os.path.isdir(os.path.join(assetsDir,name,"publish")):
        v2=True

    attrList = assetsDic.get(name).get("attr")
    intRiggingNumber = 0

    riggingNumber = charRef.split("RN")[0].split("_")[-1]
    if riggingNumber.isdigit():
        intRiggingNumber = int(riggingNumber)

    if not charRef.split("RN")[1]:   #if list empty
        num = f'{intRiggingNumber:02d}'

    else:
        num = intRiggingNumber + (int(charRef.split("RN")[1])*10)
        num =  f'{num:02d}'

#chekc if the reference is like ch_bee_rigging_lib2RN (and not ch_bee_rigging_libRN1)
    if riggingNumber.split("lib")[-1].isdigit():
        num  = int(num) + int(riggingNumber.split("lib")[-1])

        num = f'{num:02d}'


    abcName = "%s_%s.abc"%(name,num)
    path = os.path.join(dirPath[0],abcName)
    path = path.replace("/",'\\')
    path = path.replace("\\",'\\\\')


    command = buildCommand(start,end,path,geoList,attrList,subframe,frameSample,filterEuler,v2)
    print("------------------------\n------------ BEGGINING EXPORT %s ------------ \n %s"%(charRef, command))
    cmds.refresh(suspend=True)
    cmds.AbcExport (j= command )
    cmds.refresh(suspend=False)
    print("------------ SUCCESS EXPORT %s  ! ------------"%(charRef))

def exportAnim(start=0, end=100, subframe=False, frameSample="0", charList=[],filterEuler=False):
    basicFilter = "*.abc"
    dirPath = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=2,)
    for char in charList:
        exportAbcByChar(char, start, end, dirPath, subframe, frameSample, filterEuler)

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

        self.charList = cmds.textScrollList( numberOfRows=20, allowMultiSelection=True,
                        append=[],
                        showIndexedItem=4 )

        mainLayout = cmds.gridLayout(numberOfColumns=2, cellWidthHeight=(90, 20))
        cmds.text(label="Start Range:")
        startField = cmds.intField('start', v=cmds.playbackOptions(min=True, query=True))
        cmds.text(label="End Range:")
        endField = cmds.intField('end', v=cmds.playbackOptions(max=True, query=True))
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=3)
        frameSample = cmds.textField(text = "-0.25 0 0.25")
        subFrameCheckBox = cmds.checkBox(label="Subframes", value = False)
        filterEurlerCheckBox = cmds.checkBox(label="Filter Euler Rotation", value = True)

        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=1)
        btnExport = cmds.button(label="Export", width=180, c=lambda *_: self.exportClicked(
            start=cmds.intField(startField, q=1, v=1),end=cmds.intField(endField, q=1, v=1),
            charList= cmds.textScrollList(self.charList,q=True,selectItem=True),
            subframe=cmds.checkBox(subFrameCheckBox,q=1,v=1),
            frameSample= cmds.textField(frameSample, q=1, text=1),
            filterEuler = cmds.checkBox(filterEurlerCheckBox,q=1,v=1)
            ))
        cmds.setParent("..")

        cmds.showWindow(self.window)

    def updateCharList(self, charList):
        print(cmds.textScrollList(self.charList, e=True, append=charList))


    def exportClicked(self, start=0, end=100,subframe=False,frameSample="0 0 0", charList=[],filterEuler=False):
        if charList:
            exportAnim(start=start, end=end, subframe=subframe,frameSample=frameSample, charList=charList,filterEuler=filterEuler)
        else:
            cmds.confirmDialog(title="Nothing selected",message="Nothing selected !")
