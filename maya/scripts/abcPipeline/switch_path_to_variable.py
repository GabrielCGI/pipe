script_list = cmds.ls(type = 'script')
pipeline_script=[]
for script in script_list:
    if script.startswith('scriptNode_ch'):
        pipeline_script.append(script)
        
for abcScript in pipeline_script:
    abcCommand = (cmds.scriptNode(abcScript, query=True, bs=True))
    abc_modif=abcCommand.replace("I:","$DISK_I")
    print(abc_modif)
    cmds.scriptNode(abcScript , edit =True, bs=abc_modif)    