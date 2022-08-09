import importlib
import maya.cmds as cmds
import collectMayaScene
import logging
import sys
import debug_reed #temporaire debug
importlib.reload(collectMayaScene)
import replace_by_tx
import maya.mel as mel
logger = logging.getLogger("submit")


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
    msg="Send To deadline ?"
    confirm = cmds.confirmDialog( title='Confirm',
                                    message=msg,
                                    button=['Continue','Stop'], defaultButton='Continue', cancelButton='Stop', dismissString='Stop' )
    if confirm == "Stop":
        msg = "Abort by user."

        sys.exit(msg)
    debug_reed.run()
    replace_by_tx.replace_by_tx()


    replace_abc_pipeline_script_node()
    msg = "Saving..."
    confirm = cmds.confirmDialog( title='Saving option',
                                    message=msg,
                                    button=['Save','Incremental Save',"Skip"], defaultButton='Save', cancelButton='Skip', dismissString='Skip'      )
    if confirm == "Save":
    #increment and save
        mel.eval('SaveScene 0;')
    if confirm == "Incremental Save":
        mel.eval('incrementAndSaveScene 0;')
    if confirm == "Skip":
        pass


    collectMayaScene.run()

    #Run modified submit to deadline
    mel.eval('source "R:/deadline/submission/Maya/Main/SubmitMayaToDeadlinePahtMappingOn.mel";SubmitMayaToDeadlinePahtMappingOn;')
