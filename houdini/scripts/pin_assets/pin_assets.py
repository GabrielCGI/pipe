
import os
import logging

import hou
import PrismInit
from pxr import Ar, Usd, Vt
from usdAssetResolver import CachedResolver

ASSETS_FOLDER_NAME = "Assets"
AR_PREFIX_IDENTIFIER = "@"

# Init logger
logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y/%m/%d %I:%M:%S%p")
LOG = logging.getLogger("Python | {file_name}".format(file_name=__name__))
LOG.setLevel(level=logging.DEBUG)


def findStage():
    """
    Return current active houdini stage.
    
    :returns: The node corresponding to the current active stage or None
    """
    stage = hou.node("/stage/")
    if not stage:
        return None
    else:
        return hou.node("/stage/")

def getFilePath():
    """
    Return every filepath for every LOP prism import in 
    the current stage.
    
    :returns: A list with every filepath found
    """
    stage = findStage()
    
    lop_import_type = hou\
                      .lopNodeTypeCategory()\
                      .nodeType("prism::LOP_Import::1.0")
    
    ## Get every LOP import (prism)
    lop_import = []
    for i in stage.children():
        if (i.type() == lop_import_type):
            lop_import.append(i)

    # Get every file path (later add a way to ensure it is an absolute path)
    # Probably need to specify a prefix (maybe a suffix too)
    # for identifier (@identifier@)
    assets_path = []
    for i in lop_import:
        assets_path.append(i.parm("filepath").eval())
        
    return assets_path

def buildMappingPairs(assetsPath):
    """
    Return the dictionary associating each asset path with
    an identifier.
    
    :param assetsPath: A list of asset filepath
    :returns: A dictionary with identifier as key and path as value
    """
    assets_id_path = {}
    for asset_path in assetsPath:
        # Format the path to */*/*/* then split when there is a /
        split_path = os.path.normpath(asset_path).replace("\\", "/").split("/")
        assets_index = None
        
        # If the filepath is recognized as an identifer try to resolver him
        # Else find identifer in the filepath
        if asset_path.startswith(AR_PREFIX_IDENTIFIER):
            # Find ID
            id = asset_path.split(AR_PREFIX_IDENTIFIER)
            id = "".join(id[1:])
            
            # Resolve absolute path
            resolver = Ar.GetResolver()
            file_path = resolver.Resolve(asset_path).GetPathString()
            
            if id and file_path:
                assets_id_path[id] = file_path
        else:
            # Determine if the path is an asset path
            for dir_index in range(len(split_path)):
                if split_path[dir_index] == ASSETS_FOLDER_NAME:
                    assets_index = dir_index

            ## Determine entity type and entity name to build an identifier
            # Expect the entity type and entity name 
            # to follow immediately the assets folder
            if assets_index and len(split_path) > assets_index + 2:
                entity_type = split_path[assets_index+1]
                entity_name = split_path[assets_index+2]
                entity_identifier = entity_type + "/" + entity_name
                
                assets_id_path[entity_identifier] = asset_path
    
    return assets_id_path

def saveMappingPairs(mappingPairs):
    """ Create an USD file which store mapping pairs
    provided.
    
    :param mappingPairs: A set of mapping pairs
    """
    
    # Update info to show to the user
    update_info = ""
    for identifier, file_path in mappingPairs.items():
        base_name = os.path.basename(file_path)
        update_info += identifier + " -> " + base_name + "\n"
        
    # Ask for confirmation
    if mappingPairs:
        confirmation_message = ("The following assets will be pinned:\n\n"
                               + update_info)
        
        user_choice = hou.ui.displayMessage(
            confirmation_message, ('Confirm', 'Cancel'),
            close_choice=1)
        
        if user_choice != 0:
                LOG.info("Update cancel by user")
                return 
    else:
        LOG.info("No asset to pin found")
        return
            
    ## Build USD file with mapping pair
    
    # Build Mapping pair filepath base on scene filepath
    current_location = PrismInit.pcore.getCurrentFileName()
    current_location_dir = os.path.dirname(current_location)
    current_location_name = os.path.basename(current_location)
    current_location_name = os.path.splitext(current_location_name)[0]
    mapping_pair_filepath = os.path.join(current_location_dir,\
                            f"{current_location_name}_pinninginfo.usda")
    
    
    # Create an USD file with a layer customLayerData
    # to store mapping pair.
    mapping_pair_stage = Usd.Stage.CreateNew(mapping_pair_filepath)
    mapping_array = []
    for identity, filepath in mappingPairs.items():
        mapping_array.extend([identity, filepath])
    mapping_pair_stage.SetMetadata('customLayerData',\
        {CachedResolver.Tokens.mappingPairs: Vt.StringArray(mapping_array)})

    # Save USD file
    mapping_pair_stage.Save()

def run():
    """ Build a pinning file corresponding 
    to the current state of the stage.
    
    1 - Find current stage
    2 - Find each LOP prism import in the stage
    3 - For each import, get their filepath
    4 - For each filepath, find a corresponding identifier "type/name"
    5 - Prompt user to confirm the mapping pair
    6 - Save mapping pair
    
    """
    
    filepaths = getFilePath()
    mapping_pairs = buildMappingPairs(filepaths)
    saveMappingPairs(mapping_pairs)