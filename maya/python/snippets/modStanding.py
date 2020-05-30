for s in cmds.ls(selection=True):
    try: 
        cmds.setAttr(s+".mode",0)
    except:
        pass
        