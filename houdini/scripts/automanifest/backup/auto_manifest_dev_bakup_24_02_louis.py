import os
import glob
import time
import math

import hou
import PrismInit

SHOW_TIME = False

FILEPATH_PARM = 'filepath'
PARENT_PARM = 'parent'
IMPORTAS_PARM = 'importAs'
IMPORTAS_REFERENCE_ID = 2
USD_PLUGIN = PrismInit.pcore.getPlugin("USD")


def timeElapsed(func):
    def inner(*args, **kwargs):
        if not SHOW_TIME:
            return func(*args, **kwargs)
        
        start = time.process_time_ns()
        result = func(*args, **kwargs)
        time_ns = time.process_time_ns() - start
        time_sec = time_ns / 1000000000
        
        print(f"Function: {func.__name__}")
        print(f"as taken: {time_sec} s | {time_ns} ns")
        return result
    return inner


@timeElapsed
def getPrims(selectedNode: hou.Node) -> list[str]:
    """Get all prims in the scene graph of a selected node.

    Args:
        selectedNode (hou.Node): Selected node.

    Returns:
        list[str]: USD paths of every prims.
    """
    
    search_root = "/world/assets/"
    
    lop_node = selectedNode  # Assume the first selected node
    stage = lop_node.stage()  # Get the USD stage

    if not stage:
        hou.ui.displayMessage("No USD stage found in the selected node.",
                              severity=hou.severityType.Error)
        return
        
    rule = hou.LopSelectionRule()
    rule.setTraversalDemands(hou.lopTraversalDemands.Default)
    rule.setPathPattern(
        f"%kind:component {search_root}*/* {search_root}*/*/*  {search_root}*/*/*/*")
    prim_paths = rule.expandedPaths(lopnode=None, stage=stage)

    prims = []
    for prim in prim_paths:
        prims.append(str(prim))
        print(str(prim))
            
    return prims


@timeElapsed
def getAssets() -> list[str]:
    core = PrismInit.pcore
    path = core.getAssetPath()
    globpath = os.path.join(path, "*", "*")
    return glob.glob(globpath)
 
 
@timeElapsed
def getCommonAssets(assets: list[str], prims: list[str]) -> list[str]:
    commonAssets = []
    for prim in prims:
        for asset in assets:
            if os.path.basename(prim) == os.path.basename(asset):
                commonAssets.append(asset)
                
    commonAssets = list(set(commonAssets))
    return commonAssets
 
 
@timeElapsed
def createSubnet(
        selectedNode: hou.Node,
        commonAssets: list[str]) -> list[hou.LopNode]:
    
    currentPosition = selectedNode.position()
    offset = hou.Vector2(2, 0)
    
    stage = selectedNode.parent()
    subnet = stage.createNode(
        node_type_name='subnet',
        node_name='import_prism_manifest')
    
    subnet.setPosition(currentPosition + offset)
    
    with hou.undos.disabler():
        asset_imports: list[hou.LopNode] = []
        for asset in commonAssets:
            asset_import = createImport(subnet, asset)
            if not asset_import:
                continue
            asset_imports.append(asset_import)
        
    return subnet, asset_imports


@timeElapsed
def createImport(subnet: hou.Node, assetPath: str) -> hou.LopNode:
    
    asset_name = getAssetName(assetPath)
    entity = {'type': 'asset', 'asset_path': asset_name}
    filepath = USD_PLUGIN.api.getLatestEntityUsdPath(entity=entity)
    if not filepath:
        return 
    
    expression = 'node = hou.pwd()\n'\
                 'parm = node.parm("entity").eval()\n'\
                 'asset_name = parm.split("/")[-1]\n'\
                 'classprim =  "__class__/"+asset_name\n'\
                 'return classprim'
    
    asset_import: hou.LopNode = subnet.createNode(
        node_type_name='prism::LOP_Import::1.0',
        node_name=f'IMPORT_{os.path.basename(assetPath)}')

    asset_import.parm(FILEPATH_PARM).set(filepath)
    asset_import.parm(FILEPATH_PARM).pressButton()
    asset_import.parm(IMPORTAS_PARM).set(IMPORTAS_REFERENCE_ID)
    asset_import.parm(PARENT_PARM).setExpression(
        expression=expression, language=hou.exprLanguage.Python)
    
    return asset_import 

def getAssetName(assetPath: str) -> str:
    parent = os.path.basename(os.path.dirname(assetPath))
    base = os.path.basename(assetPath)
    return f'{parent}/{base}'


@timeElapsed
def setupSubnet(subnet: hou.Node, assetImports: list[hou.LopNode]):
    
    with hou.undos.disabler():
        merge = subnet.createNode('merge')
        configureprimitive = subnet.createNode('configureprimitive')
        
        output = subnet.subnetOutputs()
        if not output:
            hou.ui.displayMessage("No output in created subnetwork",
                                severity=hou.severityType.Error)
            return
        output = output[0]
        
        # Setup configureprimitive parameters
        configureprimitive.parm('primpattern').set('/__class__/*')
        configureprimitive.parm('setkind').set(1)
        configureprimitive.parm('kind').set('component')
        configureprimitive.parm('Schema').set(1)
        configureprimitive.parm('settype').set(1)
        configureprimitive.parm('setspecifier').set(1)
        configureprimitive.parm('specifier').set('class')
        
        # Link every nodes
        output.setInput(0, configureprimitive)
        configureprimitive.setInput(0, merge)
        for i, node in enumerate(assetImports):
            merge.setInput(i, node)
        
        layoutNodes(assetImports, [output, configureprimitive, merge])

def layoutNodes(assetImport: list[hou.OpNode], outputtree: list[hou.OpNode]):
    
    start = outputtree.pop(0)
    start.move(hou.Vector2(-3, 1.5))
    for i in range(len(outputtree)):
        offset = hou.Vector2(0, 1)
        outputtree[i].setPosition(start.position() + (i+1)*offset)
        
    # Arrange every lop import node in a 3/4 aspect rectangle
    # slightly above the highest node of the tree
    
    n = len(assetImport)
    if not n:
        return
    
    lastleafpos = outputtree[-1].position()
    spacing_x = 2
    spacing_y = spacing_x/2
    height = round(math.sqrt(n*4/3))
    width = math.ceil(n/height)
    start_offset = hou.Vector2(-((width-1)*spacing_x)/2.0, 5)
    startingPoint = lastleafpos + start_offset
    
    for x in range(width):
        for y in range(height):
            offset = hou.Vector2(spacing_x * x, spacing_y * y)
            if x%2==0:
                offset[1] += spacing_y/2
            if not assetImport:
                break
            node = assetImport.pop(0)
            node.setPosition(startingPoint + offset)
    
@timeElapsed
def run():
    
    selectedNodes: list[hou.Node] = hou.selectedNodes()
    if not selectedNodes:
        hou.ui.displayMessage(text="Please select a shot node",
                              severity=hou.severityType.Message)
        return
       
    selectedNodes = selectedNodes[0]
    all_assets = getAssets()
    all_prims = getPrims(selectedNodes)
    if all_prims is None:
        return
    
    commonAssets = getCommonAssets(all_assets, all_prims)
    
    isCancelled = hou.ui.displayMessage(
        f"Do you want to import {len(commonAssets)} assets?", buttons=('Confirm', 'Cancel'),
        default_choice=0, close_choice=1)

    
    if not isCancelled:
        subnet, asset_imports = createSubnet(selectedNodes, commonAssets)
        setupSubnet(subnet, asset_imports)


