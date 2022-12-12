import pymel.core as pm
import utils_pymel as utils

def shader_operator():
    counter=0
    #INIT DIC
    dic_sg={}
    #SELECT ALL SHADING ENGINE MINUS DEFAULT
    listShadingEngine = pm.ls(type="shadingEngine")

    listShadingEngine.remove('initialParticleSE')
    listShadingEngine.remove('initialShadingGroup')

    #FIND ALL SHAPES OF A SHADING GROUP
    #Return a dictionary with key = sg name, value = list of shapes
    for sg in listShadingEngine:
        #GET THE SET
        member = sg.members()
        if member: 
            path_list = []
            for m in member:
                m = m.longName().replace(m.namespace(),"")
                m = m.replace("|","/")
                m = m.replace("ShapeDeformed","Shape*")
                path_list.append(m)

            if len(path_list)>0:
                dic_sg[sg]=path_list

    #Create operator and connect shaders
    for sg in dic_sg:
        #Build selection string
        selection = " or ".join(dic_sg[sg])
        setShader = pm.createNode("aiSetParameter", n="setShader_"+sg)
        pm.connectAttr(setShader+".out","aiStandInShape.operators[%s]"%(counter), f=True)
        counter+=1
        pm.setAttr ( setShader +".selection", selection,type="string")

        surf = pm.listConnections(sg+".surfaceShader")
        aiSurf = pm.listConnections(sg+".aiSurfaceShader")
        disp = pm.listConnections(sg+".displacementShader")

        if not aiSurf:
            shader = surf[0]
        else:
            shader = aiSurf[0]

        pm.setAttr (setShader+".assignment[0]", "shader='%s'"%(shader),type="string")
        if disp :

            #Displace
            pm.setAttr (setShader+".assignment[1]", "disp_map='%s'"%(disp[0]),type="string")


def catclark_operator():
    counter = len(pm.listConnections( 'aiStandInShape.operators'))
    sel = pm.ls( long=True, type="mesh")
    i=0
    dic={}
    for i in range(5):
        shape_list = []
        for s in sel:
            if pm.getAttr(s+".aiSubdivIterations") == i:
                s = s.longName().replace(s.namespace(),"")
                s = s.replace("|","/")
                s = s.replace("ShapeDeformed","Shape*")
                shape_list.append(s)
        dic[i]=shape_list
        i += 1

    for key in dic:
        if dic[key]:

            selection = " or ".join(dic[key])
            set_param_subdiv = pm.createNode("aiSetParameter", n="setSubdiv_"+str(key))
            pm.setAttr ( set_param_subdiv +".selection", selection,type="string")
            pm.setAttr (set_param_subdiv+".assignment[0]", "subdiv_type='catclark'",type="string")
            pm.setAttr (set_param_subdiv+".assignment[1]", "subdiv_iterations=%s"%(key),type="string")
            pm.connectAttr(set_param_subdiv+".out","aiStandInShape.operators[%s]"%(counter), f=True )
            counter+=1


def guess_dir():
    scene = pm.system.sceneName()
    split = scene.split("/")
    asset_dir=split[0]+"\\"
    split.pop(0)
    for i in range(len(split)):
        if split[i] == "assets":
            asset_dir = os.path.join(asset_dir,split[i],split[i+1])
            found = True
            asset_name = split[i+1]
            return asset_dir, asset_name

        asset_dir = os.path.join(asset_dir,split[i])
    return False

def abcExport(sel):
    if not sel:
        pm.error("No selection")
    asset_dir, asset_name= guess_dir()
    abc_dir = os.path.join(asset_dir,"abc")
    abc_name = asset_name+"_mod.abc"
    abc_path= os.path.join(abc_dir,abc_name)
    abc_path=abc_path.replace("\\","/")
    print(abc_path)
    utils.popUp("ABC export ready \n%s"%abc_path)
    os.makedirs(abc_dir, exist_ok=True)
    job = '-frameRange 1 1 -stripNamespaces -uvWrite -worldSpace -writeVisibility -dataFormat ogawa -root %s -file "%s"'%(sel[0].longName(),abc_path)
    print (job)
    pm.AbcExport(j= job)
    return abc_path, abc_name

def create_standIn(abc_path, abc_name):
    ass = pm.createNode("aiStandIn",n=abc_name.split(".")[0])
    ass.dso.set(abc_path)

sel = pm.ls(sl=True)
abc_path, abc_name= abcExport(sel)
create_standIn(abc_path, abc_name)
#shader_operator()
#catclark_operator()
