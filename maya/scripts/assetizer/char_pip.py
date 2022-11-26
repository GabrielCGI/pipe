


def shader_operator():
    counter=0
    #INIT DIC
    dic_sg={}
    #SELECT ALL SHADING ENGINE MINUS DEFAULT
    listShadingEngine = cmds.ls(type="shadingEngine")
    listShadingEngine.remove('initialParticleSE')
    listShadingEngine.remove('initialShadingGroup')

    #FIND ALL SHAPES OF A SHADING GROUP
    #Return a dictionary with key = sg name, value = list of shapes
    for sg in listShadingEngine:
        #GET THE SET
        set = cmds.sets(sg, query=True)
        print (sg)
        print(set)
        print("_____")
        #BUILD A LIST OF PATH WITH FORWARD SLASH
        if set:
            shapes_full_path_list = [cmds.ls(fp, long=True)[0].replace("|","/") for fp in set]
            if len(shapes_full_path_list)>0:
                dic_sg[sg]=shapes_full_path_list

    #Create operator and connect shaders
    for sg in dic_sg:
        #Build selection string
        selection = " or ".join(dic_sg[sg])
        setShader = cmds.createNode("aiSetParameter", n="setShader_"+sg)
        cmds.connectAttr(setShader+".out","aiStandInShape.operators[%s]"%(counter), f=True)
        counter+=1
        cmds.setAttr ( setShader +".selection", selection,type="string")

        list_input = cmds.ls(cmds.listConnections(sg),materials=1)
        shader = list_input[0]
        cmds.setAttr (setShader+".assignment[0]", "shader='%s'"%(shader),type="string")
        if len(list_input)>1:
            displace  = list_input[1]
            #Displace
            cmds.setAttr (setShader+".assignment[1]", "disp_map='%s'"%(displace),type="string")


def catclark_operator():
    counter = len(cmds.listConnections( 'aiStandInShape.operators'))
    sel = cmds.ls( long=True, type="mesh")
    i=0
    dic={}
    for i in range(5):
        shape_list = [s.replace("|","/") for s in sel if cmds.getAttr(s+".aiSubdivIterations") == i  ]
        dic[i]=shape_list
        i += 1
    print (dic)
    for key in dic:
        if dic[key]:

            selection = " or ".join(dic[key])
            set_param_subdiv = cmds.createNode("aiSetParameter", n="setSubdiv_"+str(key))
            cmds.setAttr ( set_param_subdiv +".selection", selection,type="string")
            cmds.setAttr (set_param_subdiv+".assignment[0]", "subdiv_type='catclark'",type="string")
            cmds.setAttr (set_param_subdiv+".assignment[1]", "subdiv_iterations=%s"%(key),type="string")
            cmds.connectAttr(set_param_subdiv+".out","aiStandInShape.operators[%s]"%(counter), f=True )
            counter+=1
shader_operator()
catclark_operator()
