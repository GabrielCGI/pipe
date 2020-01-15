#This tool is for batch exporting archive for XGen
#Select the object then run the script.
#Save your scene before execution.

# processDir(archiveName, destination, [scene filepath], [selectedObject],  1(active polyreduce), '80.0(lowpoly)', '30.0(midpoly)', 1.000000(animstart), 1.000000(anim end))
import xgenm.xmaya.xgmArchiveExport

#CHANGE THAT
destinationFolder = 'D:/arch/' #FORWARD SLASH !!!!

cmds.file(save=True)
sel = cmds.ls(selection = True) #The current selection
filepath = cmds.file(q=True, sn=True) #The file path of the current scene

for s in sel:
    hlp = xgenm.xmaya.xgmArchiveExport.xgmArchiveExport()
    hlp.processDir(s, destinationFolder, [filepath], [s],  1, '80.0', '30.0', 1.000000, 1.000000)
    #
