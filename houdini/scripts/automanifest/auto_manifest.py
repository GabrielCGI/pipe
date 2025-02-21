import re
import os
import sys
import hou 

def assetFinder(project, assetName, istr):
    assetFolder = project + '/03_Production/Assets/'
    istrnew = 'neverFound'
    for item in os.listdir(assetFolder):
        for sub in os.listdir(assetFolder + '/'+ item):
            if sub == assetName:
                print('Asset found at : '+item +'/'+ sub)
                istrnew = item +'/'+ assetName
                resolvedAsset = assetFolder + istrnew
                print(resolvedAsset)
                break
            if istrnew == 'neverFound':
                istrnew = istr
                resolvedAsset = assetFolder + istr
                print('resolved is '+resolvedAsset)
        print('Asset not found in subfolder : '+ item)
    return istrnew, resolvedAsset

def get_prims_at_path(stage, path):
    
    prims = []
    GRPprims = []
    
    
    def collect_prims(prim):
        
        #print('hello'+str(prim))
        
        for child in prim.GetAllChildren():
            print('roots are : '+str(child))
            for bb in child.GetAllChildren():
                print('sub prims are : '+str(bb))
                if bb.GetName().split('_')[-1] == 'GRP':
                    print('GRP detected')
                    for b in bb.GetAllChildren():
                        print('prims in _GRP are : '+ str(b))
                        GRPprims.append(b)

                else:
                    print('no GRP detected')
                    if bb.GetName() == 'geo':
                    
                        break
                    else:
                        prims.append(bb)
#                    for a in bb.GetAllChildren():
#                        print('sub_bb'+ str(a))
#                        prims.append(a)

    root_prim = stage.GetPrimAtPath(path)
    if root_prim:
        collect_prims(root_prim)
    else:
        hou.ui.displayMessage(f"Path '{path}' not found in stage.")
        
        
    return prims, GRPprims

def find_versions(directory):
    if not os.path.exists(directory):
        print(f"Error: The directory '{directory}' does not exist.")
        return None, 0
    versions = {}
    folder_count = 0  # Initialize the counter

    pattern = re.compile(r'^v(\d+)$')
    
    for item in os.listdir(directory):
        sub_dir = os.path.join(directory, item)
        if os.path.isdir(sub_dir):
            folder_count +=1
            current_folder = os.path.basename(os.path.normpath(sub_dir)).upper()
            versions[current_folder] = []
            iteration = 0
            for dir_name in os.listdir(sub_dir):              
                dir_path = os.path.join(sub_dir, dir_name)
                if os.path.isdir(dir_path):
                    match = pattern.match(dir_name)
                    if match:
                        version_number = int(match.group(1))
                        folder_path = dir_path.replace('\\', '/')
                        versions[current_folder].append((version_number, folder_path))
                        print('coucou'+versions)

                        

    for folder in versions:
        

        versions[folder].sort(reverse=True)
        # Sort by version number descending
    folder = folder.lower()


    return folder # Return both the versions dictionary and the folder count

def get_unique_asset(detected_prims):  

    prims = detected_prims
    uniprims = []
    dupli = []
    duplicount = []
    if len(prims) > 0:
        uniprims.append(prims[0])
        prims.remove(prims[0])
    else:
        print('out of range')
    realnums = []
    
    
    count = 1
    
    for child in prims:
        
        uniprimstest = uniprims[-1]

        uniprimstest = re.sub(r"\d+", "", uniprimstest)
        print(uniprimstest) 
        childtest = child
        childtest = re.sub(r"\d+", "", childtest)
        print(childtest)
    
        if childtest == uniprimstest:
            childint = re.findall(r'\d+', child)
            uniprimsint = re.findall(r'\d+', uniprims[-1])
            print(uniprimsint)
            realnum = int(childint[0])- count
            print(realnum)
    
#            print(childint, uniprimsint,realnum)

            try: 
                uniprimsint = uniprimsint[0]
                print('end of uniprims')
   
                if realnum == int(uniprimsint[0]):
                    count += 1
                    if count > 2:
                        dupli.remove(dupli[-1])
                        dupli.append(childtest.split('/')[-1])
                        duplicount.pop(-1)
                        duplicount.append(count)

                    else:
                        dupli.append(childtest.split('/')[-1])
                        duplicount.append(count)
    #                    print('new duplicount = '+str(duplicount))
            
                else:
                    
                    uniprims.append(child)
                    count = 1
    #                print('ahah')
            except:
                print('end of uniprims')
                
                
#            print('prims already in collection')
        else:
            count = 1 
            uniprims.append(child)
#            print('updated uniprims :'+str(uniprims))
    
    
#    
#    print(uniprims)
#    print(dupli)
#    print(duplicount)
#    print(realnums)
    return uniprims, dupli, duplicount, realnums
      

def autoManifest():
    
    path = "/world/assets"
    nodes = hou.selectedNodes()
#    print(node)
    for node in nodes:
        stage = node.stage()  # Get the USD stage from the LOP node
    
        prims, GRPprims = get_prims_at_path(stage, path)
        
        if prims and GRPprims is None:
            sys.exit()
    
        primsname = []
        GRPprimsname = []
        print(prims, GRPprims)
        for i in prims:
            if prims is None:
                return
            else:
                asset_name = str(i).split('/')[-2]+'/'+ str(i).split('/')[-1].split('>')[0]
                print('PRIMSNAME is '+ asset_name)
                primsname.append(asset_name)
                
        uniprims, dupli, duplicount, realnums = get_unique_asset(primsname) 
        GRPuniprims = []
        for i in GRPprims:
            if GRPprims is None:
                return
            else: 
                print('base name is :' + str(i))
                asset_name = str(i).split('/')[-3]+'/'+ str(i).split('/')[-1].split('>')[0]

                asset_name = asset_name.replace('_', '')
                print('GRP name is : '+ asset_name)
                asset_name = re.sub(r'\d+', '', asset_name)+'_GRP'
                
                #GRPuniprims.append(asset_name)
                try: 
                    if asset_name == GRPuniprims[-1]:   
                        print('=')
                        #GRPuniprims.remove(GRPuniprims[0])
                    else:
                        print('!')
                        GRPuniprims.append(asset_name)
                except:

                    print('except')
                    print(str(i) + ' added to GRPprims')
                    GRPuniprims.append(asset_name)
                    

            
        print(GRPuniprims)

        for i in GRPuniprims:
            uniprims.append(i)
 
     
        if prims:
            print(f"Found {len(prims)} primitives at path '{path}', which are named {prims}.")
        else:
            print("No primitives found or path does not exist.")
    
        parent = node.parent()
        shot_name = node.name()
        parentPath = parent.path()
        print('parent path : '+parentPath)
        
        manifestPath = parentPath + '/MANIFEST_'+shot_name.replace('_IN','.00')
        
        if hou.node(manifestPath):
            print('Manifest already Exists')
            manifexist = 1
            sub = hou.node(manifestPath)
            merge = hou.node(manifestPath +'/merge')
            
        else:
            manifexist = 0
            sub = parent.createNode('subnet', 'MANIFEST_'+shot_name.replace('_IN','.00'))  
            print('manifest : '+manifestPath)
            sub.setColor(hou.Color((0.451, 0.369, 0.796)))
            sub.setPosition(node.position() + hou.Vector2(-4, 0))
            merge = sub.createNode('merge', 'merge')
            
            
        current = dupli
    #    print('dupli is'+str(dupli))
    #    print('current is'+ str(current))
        print(uniprims)
        unresolvedAssets = []
        unresolvedFiles = []
        pos = merge.position()

        for i in uniprims:
            print('uniprims = '+ str(i))
            istr = re.sub(r"\d+", "", i)
            print('istr is '+ istr)
            if istr.split('_')[-1] == 'GRP':
                    istrID = istr
                    istr = istr.replace('_GRP', '')
                    print(' new istr is : '+ istr)
            else:
                istrID = istr+('_noGRP')
            if i.split('_')[-1] == 'GRP':
                i = i.replace('_GRP', '')
            
            print('istr = '+istr)
            asset_path = '/world/assets/'+i
            print('asset_path = '+ asset_path)
            asset_name = istr.split('/')[-1]
            scene_path = hou.hipFile.path()
            root = scene_path.split('/')[0]+'/'+scene_path.split('/')[1]
#           print(root)
            istrcheck = 'None'
            wrongFilepath = 0
            
            filepath = root+'/03_Production/Assets/'+istr+'/Export/USD/'

                
            if not os.path.exists(filepath):
                
                
                istrcheck = istr
                print(istr)
                istr, filepath = assetFinder(root, asset_name, istr)
                print(istr, filepath)
            
                filepath = filepath + '/Export/USD/'
                wrongFilepath = 1
            print('filepath = '+ filepath)
            if istr == istrcheck:
                print("Asset "+ asset_name+" couldn't be found")
                
                unresolvedAssets.append(asset_path + asset_name)
            else:

                latest_version = str(find_versions(filepath))
                final_path = filepath + latest_version + '/'+ asset_name +'_USD_'+ latest_version + '.usdc'
                if os.path.isfile(final_path):
                    final_path = final_path
                else:
                    if os.path.isfile(final_path.replace((final_path.split('.')[-1]), 'usd')):
                        final_path = final_path.replace((final_path.split('.')[-1]), 'usd')
                    else:
                        final_path = final_path.replace((final_path.split('.')[-1]), 'usda')
                
                if not os.path.isfile(final_path):
                    unresolvedFiles.append(asset_name)

                else:
                
                    if hou.node(sub.path()+'/'+asset_name):
                        asset_import = hou.node(sub.path()+'/'+asset_name)
                        exist = 1
                        pos = asset_import.position()
                    else:
                        
                        asset_import = sub.createNode("prism::LOP_Import::1.0", asset_name)
                        
                        exist = 0
                        asset_import.setPosition(pos + hou.Vector2(3, 0))
                        pos = asset_import.position()

                        if istrID.split('_')[-1] == 'GRP':
                                    
                            duplicate = sub.createNode('duplicate', asset_name +'_duplicates')
                            duplicate.setPosition(pos + hou.Vector2(0, -1))
                            duplicate.parm('sourceprims').set('`chs("../'+i.split('/')[-1]+'/parent")`')
                            duplicate.parm('ncy').set(1) 
                            duplicate.parm('separatesource').set(1)
                            duplicate.parm('destinationprims').set('/world/assets/Sets/`@srcname`_GRP')
                            duplicate.parm('modifysource').set('hide')
                            duplicate.parm('makeinstances').set(1)
                            duplicate.setInput(0, asset_import)


                        

                    final_path = final_path.replace(root, '$PRISM_JOB')
                
                    asset_import.parm('filepath').set(final_path)
                    asset_import.parm('filepath').pressButton()
                    asset_import.parm('importAs').set('reference')
                    if wrongFilepath == 0:
                        print('OLA1'+str(istr))
                        if istrID.split('_')[-1] == 'GRP':
                            asset_import.parm('parent').set(asset_path.replace(istr.split('/')[-1], 'source/')+istr.split('/')[-1])
                            
                        else:

                            asset_import.parm('parent').set(asset_path.replace(istr,'`chs("entity")`'))
                    else:

                        assetFolder = root + '/03_Production/Assets/'
                        checkfolder = 0
                        print(istr)
                        for item in os.listdir(assetFolder):
                            if asset_path.split('/')[3] == item:
                                checkfolder = 1
                                print('match' + str(item)+str(asset_path.split('/')[3] ))
                            else:
                                print('no match')
                        if checkfolder == 1:       
                            print('no change')                     
                            asset_path = asset_path
                            if istrID.split('_')[-1] == 'GRP':
                                asset_path = asset_path.replace(asset_path.split('/')[-1], 'source/')+istr.split('/')[-1]
                        else:    
                            print('changed')
                            
                            asset_path = '/'.join(asset_path.split('/')[:3])+'/'+istr.split('/')[0]+'/'+'/'.join(asset_path.split('/')[-2:])
                        

                        asset_import.parm('parent').set(asset_path)
                        print('OLA2'+str(istr))
                        print('asset path is : '+asset_path)
        #           print(asset_path.replace(istr,'`chs("entity")`'))    
                    
            #        print(asset_name)
                    
            #        print('current is at'+str(current))
                    
                    if str(current) == '[]':
            #            print('current is at'+str(current))
                        if exist == 0:
                            if istrID.split('_')[-1] == 'GRP':
                                    
                                merge.setNextInput(duplicate)
                            else:
               
                                merge.setNextInput(asset_import)
                        
                    else:
                        if asset_name == current[0]:
                            if wrongFilepath == 0:
                                print('OLA3'+str(istr))
                                asse    t_import.parm('parent').set(asset_path.replace(('/'.join(asset_path.split('/')[-2:])), '`chs("entity")`1')+'/'+asset_name)
                            else:    
                                print('OLA4'+str(istr))
                                asset_import.parm('parent').set('/world/assets/'+istr+'1/'+asset_name)
                            
                            if exist == 1 and hou.node(manifestPath + '/'+asset_name +'_duplicates'):
                                duplicate = hou.node(manifestPath + '/'+asset_name +'_duplicates')
                            
                            else:
                                
                                
                                duplicate = sub.createNode('duplicate', asset_name +'_duplicates')
                                duplicate.setPosition(pos + hou.Vector2(0, -1))
                                duplicate.parm('sourceprims').set('/world/assets/'+i)
                                duplicate.parm('duplicatename').set(asset_name+'`@copy+1`')
                                duplicate.parm('modifysource').set('')

                                if exist == 1:
                                    
                                    for outConnection in asset_import.outputConnections():
                                        outNode = outConnection.outputNode()
                                        outIndex = outConnection.inputIndex()
                                        if outNode == merge:  
                                            outNode.setInput(outIndex, None, 0)
                                        else:
                                            outNode.setInput(outIndex, duplicate, 0)
                                    
                                duplicate.setInput(0, asset_import)
                                
                                merge.setNextInput(duplicate)
                                
                               

                            duplicate.parm('ncy').set(duplicount[0]) 
                            
                            current.remove(current[0])
                            duplicount.remove(duplicount[0])
                        
                        else:
                            if istrID.split('_')[-1] == 'GRP':
                                    
                                merge.setNextInput(duplicate)
                            else:
               
                                merge.setNextInput(asset_import)
                    
        output = hou.node(sub.path()+'/output0')
        output.setInput(0, merge)

        if manifexist != 1:
            print('Manifest Created Successfully !')
            sub.layoutChildren()
        else:
            print('Manifest Updated Successfully !')

        if unresolvedAssets:    
            hou.ui.displayMessage("Assets unresolved are : "+ ' '.join(unresolvedAssets))
        if unresolvedFiles:
            hou.ui.displayMessage('USD not found for assets at : ' + ' '. join(unresolvedFiles))