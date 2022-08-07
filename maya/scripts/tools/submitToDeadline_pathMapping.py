import importlib
import maya.cmds as cmds
import collectMayaScene
importlib.reload(collectMayaScene)
import replace_by_tx
import maya.mel as mel

def replace_abc_pipeline_script_node():
    counter_udpate=0
    counter_nodes=0
    script_list = cmds.ls(type = 'script')
    pipeline_script=[]
    for script in script_list:
        if script.startswith('scriptNode_ch'):
            pipeline_script.append(script)
            
    for abcScript in pipeline_script:
        counter_nodes+=1
        abcCommand = (cmds.scriptNode(abcScript, query=True, bs=True))
        abc_modif=abcCommand.replace("I:/","$DISK_I/")
        if abcCommand != abc_modif:
            cmds.scriptNode(abcScript , edit =True, bs=abc_modif)
            counter_udpate += 1
    print (str(counter_nodes)+" abc pipeline node found")        
    print (str(counter_udpate) +" abc pipeline node modified !")
    
def run():
    
    print ("Start replacing by tx !")
    replace_by_tx.replace_by_tx()
    
    print (" \nStart Abc pipeline script node path mapping")
    replace_abc_pipeline_script_node()
    
    #increment and save
    mel.eval('incrementAndSaveScene 0;')
    
    collectMayaScene.run()
    
    #Run modified submit to deadline
    mel.eval('source "R:/deadline/submission/Maya/Main/SubmitMayaToDeadlinePahtMappingOn.mel";SubmitMayaToDeadlinePahtMappingOn;')