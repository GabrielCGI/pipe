# This script will be executed after the execution of an export state in the Prism State Manager.
# You can use this file to define project specific actions, like manipulating the outputfiles.

# Example:
print ("Prism has exported objects.")

# If the main function exists in this script, it will be called.
# The "kwargs" argument is a dictionary with usefull information about Prism and the current export.
#import usdApi

def main(*args, **kwargs):
#     print(args)
#     print(kwargs)
#    print(kwargs["core"])
    core = kwargs["core"]
    usdApi = core.getPlugin("USD").api
#    print('coucou '+str(kwargs))
#    print(kwargs["scenefile"])
#     print(kwargs["startframe"])
#     print(kwargs["endframe"])
    comment = core.getStateManager().publishComment
    if comment == 'noHook':
        print('Hook deactivated')
        return

    else:
        print('Hook started')
        if core.appPlugin.pluginName == "Maya":
            for i in kwargs["scenefile"].split('\\'):
                if i == 'Anim':
                    print('In Maya Anim task.')
                    path = kwargs["outputpath"]

                    fileext = ['usd', 'usdc', 'usda']
                    check = 0
                    for i in fileext:
                        
                        if path.split('.')[-1] != i:
                            print('not usd')
                            
                        else:
                            check = 1
                    if check == 0:
                        print('not usd export')
                        break
                    print('in usd export')
                    stage = usdApi.getStageFromFile(path)
                    prims = stage.TraverseAll()

                    for prim in prims:
                        if prim.GetTypeName() == 'Mesh':
                            prim.RemoveProperty("subdivisionScheme")
                            parent = prim.GetParent()
                            print(parent)
                            if prim.GetAttribute('points').ValueMightBeTimeVarying() is True:
                                print('deformed geo')                        
                            else:
                                check = 0
                                path = str(parent).replace('>)', '')
                                path = path.split('/')
                                print(path)
                                for i in path:
                                    if i == 'skinned' or "fxPlants" or "extraPublish" in i:
                                        check = 1
                                if check == 0:
                                    prim.RemoveProperty('faceVertexCounts')
                                    prim.RemoveProperty('faceVertexIndices')
                                    prim.RemoveProperty('points')
                                    prim.RemoveProperty('normals')
        
                    usdApi.saveStage(stage)       
                else: 
                    None



    if core.appPlugin.pluginName == 'Houdini':
        print('hello Houdini')
