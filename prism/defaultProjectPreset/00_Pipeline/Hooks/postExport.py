# This script will be executed after the execution of an export state in the Prism State Manager.
# You can use this file to define project specific actions, like manipulating the outputfiles.

# Example:

# If the main function exists in this script, it will be called.
# The "kwargs" argument is a dictionary with usefull information about Prism and the current export.
#import usdApi

RANCH_EXPORTER_PATH = "R:/pipeline/pipe/prism/ranch_cache_scripts"
import sys
sys.path.append(RANCH_EXPORTER_PATH)

def main(*args, **kwargs):
    # print(args)
    # print(kwargs)
    # print(kwargs["core"])
    # print(kwargs["scenefile"])
    # print(kwargs["startframe"])
    # print(kwargs["endframe"])
    core = kwargs["core"]
    usdApi = core.getPlugin("USD").api
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
                            None
                            
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
#                            print(parent)
                            if prim.GetAttribute('points').ValueMightBeTimeVarying() is True:
                                print(str(prim) + ' is deformed geo')                        
                            else:
                                check = 0
                                path = str(parent).replace('>)', '')
                                path = path.split('/')

                                for i in path:

                                    if i == 'skinned' or i == "fxPlants" or i =="extraPublish":
                                        check = 1
                                        print(i + 'is in a folder')
       
                                if check == 0:
                                    prim.RemoveProperty('faceVertexCounts')
                                    prim.RemoveProperty('faceVertexIndices')
                                    prim.RemoveProperty('points')
                                    prim.RemoveProperty('normals')
                                    print('properties removed on : '+ i)
        
                    usdApi.saveStage(stage)
                    print(str(stage)+ 'successfully saved !')       
                else: 
                    None



    if core.appPlugin.pluginName == 'Houdini':
        import hou
        import importlib
        
        
        if not hou.isUIAvailable():
            print("Houdini is not in GUI mode. Skipping ranchExporter in postRender.")
            return
        else: 
            print("Houdini is  in GUI mode. Starting ranchExporter in post Render.")
            
            import threading
            import ranchExporter
            importlib.reload(ranchExporter)
            
            import socket
            hostname = socket.gethostname()
            if hostname in ['SPRINTER-04']:
                print(f'Currently debugging on {hostname}')
                usdpath = ranchExporter.getUsdPath(kwargs)
                ranchExporter.parseAndCopyToRanchDev(usdpath, kwargs,)
                # thread = threading.Thread(target=ranchExporter.parseAndCopyToRanchDev, args=(usdpath, kwargs,))
                # thread.start()
                return
        
            # usdpath = ranchExporter.getUsdPath(kwargs)
            # ranchExporter.parseAndCopyToRanchDev(usdpath, kwargs,)
            usdpath = ranchExporter.getUsdPath(kwargs)
            thread = threading.Thread(target=ranchExporter.parseAndCopyToRanch, args=(usdpath, kwargs,))
            thread.start()
