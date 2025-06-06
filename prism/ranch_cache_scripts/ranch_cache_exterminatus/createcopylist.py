import os
import sys
import glob
import json
import time
import re
from pathlib import Path
import logging
import shutil
import datetime
import threading
import subprocess

FORMATTER = logging.Formatter(fmt="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(FORMATTER)
logger.addHandler(stream_handler)

CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_NAME = os.path.join(r"R:\logs\ranch_cache_exterminatus", f"{CURRENT_DATE}")

VSCODE_PATH = r"C:\Program Files\Microsoft VS Code\Code.exe"

DEBUG_MODE = False

INCLUDE_MODE = False
NOT_EMPTY = False

RCLONE_DIR = r'\\Il-mpl-fs-01\RESSOURCES\it\backups\rclone'
FILTER_DIR = os.path.join(RCLONE_DIR, 'filters_files')
PROD_TO_BACKUP_FILE = os.path.join(RCLONE_DIR, "prod2_to_backup.txt")

TARGET_SHOT = True
TARGET_ASSET = True
    
def parseLatestVersions(
        prodRoot: str,
        nbVersion: dict,
        notEmpty: bool=False,
        includeMode: bool=False) -> list[str]:
    """
    Create an exclude list with old assets and shots in a production.

    includeMode define if we returns an inclusion or an exclusion list.

    Args:
        prodRoot (str): Production root.
        nbVersion (dict): How many version to save per category.
        notEmpty (bool, optional): Return only not empty folders. Defaults to False.
        includeMode (bool, optional): Enable inclusion mode. Defaults to False.        
        
    Returns:
        list[str]: Olds versions paths list to exclude.
    """
    
    global INCLUDE_MODE, NOT_EMPTY
    INCLUDE_MODE = includeMode
    NOT_EMPTY = notEmpty

    asset_path = os.path.join(prodRoot, '03_Production', 'Assets')
    shot_path = os.path.join(prodRoot, '03_Production', 'Shots')
    
    # Assets paths
    asset_pattern = os.path.join(asset_path, '*', '*')
    assets_paths = glob.glob(asset_pattern)
    
    # Assets paths with no type
    asset_no_type_pattern = os.path.join(asset_path, '*')
    assets_no_type_paths = glob.glob(asset_no_type_pattern)
    
    # Shots paths
    shot_pattern = os.path.join(shot_path, '*', '*')
    shots_paths = glob.glob(shot_pattern)
    
    assets_exclude_paths = []
    assets_no_type_exclude_paths = []
    shots_exclude_paths = []
    if TARGET_ASSET:
        assets_exclude_paths = getExcludeCopyList(assets_paths, nbVersion)
        assets_no_type_exclude_paths = getExcludeCopyList(assets_no_type_paths, nbVersion)
    if TARGET_SHOT:
        shots_exclude_paths = getExcludeCopyList(shots_paths, nbVersion)
    
    scenefiles_exclude_paths = []
    if TARGET_ASSET:
        # Scene files asset no type : 
        scenefiles_exclude_paths = getExcludeListScenefile(assets_paths, nbVersion["scenefiles"])
        # Scene files asset : 
        scenefiles_exclude_paths += getExcludeListScenefile(assets_no_type_paths, nbVersion["scenefiles"])
    if TARGET_SHOT:
        # Scene files shots : 
        scenefiles_exclude_paths += getExcludeListScenefile(shots_paths, nbVersion["scenefiles"])
    
    exclude_list = (assets_exclude_paths
                    + assets_no_type_exclude_paths
                    + shots_exclude_paths
                    + scenefiles_exclude_paths)
    
    return list(set(exclude_list))
    

def getExcludeCopyList(entity_list: list[str], nbVersion: dict) -> list[str]:
    """Get version to exclude from entity renders, exports and playblasts.

    Args:
        entity_list (list[str]): List of entities paths.
        nbVersion (dict): How many version to save per category.

    Returns:
        list[str]: Olds versions path to exclude.
    """   
     
    exclude_list = []
    
    for i, entity in enumerate(entity_list):
        if DEBUG_MODE and i > 3:
            return exclude_list
        # Export versions
        exclude_list += getExcludeListFromExport(entity, nbVersion["export"])
        # Render versions
        exclude_list += getExcludeListFromRenders(entity, nbVersion["renders"])
        # Playblast versions
        exclude_list += getExcludeListFromPlayBlasts(entity, nbVersion["playblasts"])

    return exclude_list


def getExcludeFromIdentifier(identifiers_list: str, nbVersion: int) -> list[str]:
    """Get every version except the nbVersion latest ones.

    Args:
        identifiers_list (list[str]): Paths list to identifiers.
        nbVersion (int): How many version to save.

    Returns:
        list[str]: Olds versions path to exclude.
    """    
    
    exclude_list = []
    for identifier in identifiers_list:
        version_pattern = os.path.join(identifier, 'v*[0-9]')
        version_list = glob.glob(version_pattern)
        
        if NOT_EMPTY:
            for version in version_list:
                file_list = [str(f) for f in Path(version).glob('*')]
                if len(file_list) < 2:
                    file_list += [str(f) for f in Path(version).glob('*/*')]
                    if len(file_list) < 2:
                        version_list.remove(version)
                
        version_list.sort()
        if nbVersion > 0:
            if INCLUDE_MODE:
                version_list = version_list[-nbVersion:]            
            else:
                version_list = version_list[:-nbVersion]
                
        exclude_list += version_list

    return exclude_list


def getExcludeListFromExport(entity: str, nbVersion: int) -> list[str]:
    """Get exports paths to exclude.

    Args:
        entity (str): Entity path.
        nbVersion (int): How many version to save.

    Returns:
        list[str]: Olds versions path to exclude.
    """
    
    export_pattern = os.path.join(entity, 'Export', '*')
    export_list = glob.glob(export_pattern)  
    return getExcludeFromIdentifier(export_list, nbVersion)


def getExcludeListFromRenders(entity: str, nbVersion: int) -> list[str]:
    """Get renders paths to exclude.

    Args:
        entity (str): Entity path.
        nbVersion (int): How many version to save.

    Returns:
        list[str]: Olds versions path to exclude.
    """
    
    exclude_list = []
    render2d_pattern = os.path.join(entity, 'Renders', '2dRender', '*')
    render2d_list = glob.glob(render2d_pattern)  
    
    render3d_pattern = os.path.join(entity, 'Renders', '3dRender', '*')
    render3d_list = glob.glob(render3d_pattern)  
    
    exclude_list += getExcludeFromIdentifier(render2d_list, nbVersion)
    exclude_list += getExcludeFromIdentifier(render3d_list, nbVersion)
    
    return exclude_list
    
    
def getExcludeListFromPlayBlasts(entity, nbVersion):
    """Get playblasts paths to exclude.

    Args:
        entity (str): Entity path.
        nbVersion (int): How many version to save.

    Returns:
        list[str]: Olds versions path to exclude.
    """
    
    export_pattern = os.path.join(entity, 'Playblasts', '*')
    export_list = glob.glob(export_pattern)
    return getExcludeFromIdentifier(export_list, nbVersion)


def getFilesFromSceneFiles(
        file_list: list[str],
        nbVersion: int,
        version_pattern: str=r'_v(\d+)') -> list[str]:
    """Get files for versions that are not the nbVersion latest.

    Args:
        file_list (list[str]): Scenefile files.
        nbVersion (int): How many version to save.
        version_pattern (str, optional): Regex version pattern. Defaults to r'_v(\d+)'.

    Returns:
        list[str]: Files to exclude.
    """    
    
    version_map = {}

    # collecter les fichiers par version
    for file in file_list:
        match = re.search(version_pattern, file)
        if match:
            version = int(match.group(1))
            version_map.setdefault(version, []).append(file)

    # trier les versions et virer les nbVersion derniers
    # show exclude paths to not copy :
    latest_versions = sorted(version_map.keys())
    if nbVersion > 0:
        if INCLUDE_MODE:
            latest_versions = latest_versions[-nbVersion:]
        else:
            latest_versions = latest_versions[:-nbVersion]

    # collecter les fichiers de ces versions
    result_file_list = []
    for version in latest_versions:
        result_file_list.extend(version_map[version])

    return result_file_list


def getExcludeListScenefile(entity_list: list[str], nbVersion: int) -> list[str]:
    """Get scenefiles for versions that are not the nbVersion latest. 

    Args:
        entity_list (list[str]): Entities paths.
        nbVersion (int): How many version to save.

    Returns:
        list[str]: Scenefiles to exclude.
    """    
    
    # Pour du debug : 
    # print(f'working on partial entity list : {entity_list[50:51]}')

    exclude_path_list = []

    # entity can be either a shot or an asset root
    for i, entity in enumerate(entity_list): 
        if DEBUG_MODE and i > 3:
            return exclude_path_list
        
        task_paths = []
        
        # Get all tasks paths
        dept_pattern = os.path.join(entity, 'Scenefiles', '*')
        dept_paths = glob.glob(dept_pattern)  
        for dept_path in dept_paths:
            tasks_pattern = os.path.join(dept_path, '*')
            task_paths += glob.glob(tasks_pattern)  

        #print(f"found task paths : ")

        # In each task path, found last versions
        for task_path in task_paths:
            file_version_pattern = os.path.join(task_path, '*')
            file_version_list = glob.glob(file_version_pattern)
            
            #print("file_version_list:")
            
            files_toExclude = getFilesFromSceneFiles(file_version_list, nbVersion)
            #print("files to exclude:")
            exclude_path_list+=files_toExclude
        
    return exclude_path_list
    

def parseArgsFromJSON(filepath: str):
    """Parse arguments from JSON

    Args:
        filepath (str): JSON file.

    Returns:
        dict: dict of arguments.
    """    

    if not os.path.exists(filepath):
        logger.error(f'Preset do not exists: {filepath}')
        return {}
    
    if not os.path.splitext(filepath)[1] == '.json':
        logger.error(f'Preset is not a json: {filepath}')
        return {}
    
    with open(filepath) as file:
        data = json.load(file)
        
    return data


def argsCheck():
    """
    Quick check of arguments validity.
    """
    
    if len(sys.argv) != 2:
        logger.error("Usage: <preset_config>", file=sys.stderr)
        sys.exit()
        
    preset_filepath = sys.argv[1]

    if not os.path.exists(preset_filepath):
        logger.error(f'{preset_filepath} do not exists.', file=sys.stderr)
        sys.exit()
        
    return preset_filepath


def findProdToBackupPath(prod_root_path: str) -> list[str]:
    """Find every prism prod in a given directory.

    Args:
        prod_root_path (str): Directory to parse.

    Returns:
        list[str]: list of productions found.
    """
    
    root_path = Path(prod_root_path)
    prod_to_backup_paths = []

    # Utilisation de glob pour parcourir les sous-dossiers
    for subfolder in root_path.glob('*'):
        if subfolder.is_dir():
            prod_to_backup_paths.append(str(subfolder))

    return prod_to_backup_paths


def getExcludeList(prodRoot: str, data: dict) -> list[str]:
    """Get list of file to not backup.

    Args:
        prodRoot (str): Prism prod root.
        data (dict): Filters context.

    Returns:
        list[str]: List of files or directories to exclude.
    """    
    
    version_to_save = data.get('version_to_save')
    filters = data.get('filters', {})

    exclude_preset = filters.get('exclude', [])
    
    exclude_list = parseLatestVersions(prodRoot, version_to_save, notEmpty=False, includeMode=False)
    exclude_list += exclude_preset
    exclude_list.sort()
        
    return exclude_list     


def open_log(log_file):
    command = [VSCODE_PATH, log_file]
    subprocess.run(command)


def delete_file(file_list):
    
    logger.info(f'Deleting {len(file_list)} directories...')
    delete_count = 0
    skip_count = 0
    for file in file_list:
        try:
            shutil.rmtree(file)
            delete_count += 1
        except Exception as e:
            logger.warning(e)
            logger.warning(f"Could not delete {file}")
            skip_count += 1
            continue
        
    return delete_count, skip_count
    
                       
if __name__ == '__main__':
    preset_filepath = argsCheck()
    
    start = time.monotonic_ns()
    
    data = parseArgsFromJSON(preset_filepath)
    
    productions_root = data.get("productions_root")
    prod_root_list = findProdToBackupPath(productions_root)
    
    targetasset = data.get("target_asset", True)
    targetshot = data.get("target_shot", True)
    TARGET_ASSET = targetasset
    TARGET_SHOT = targetshot
        
    to_delete_list = {}
    
    logger.info('Start parsing file to delete...')
    for i, prod_root in enumerate(prod_root_list):
        prod_root_name = Path(prod_root).parts[-1]
        to_delete_list[prod_root_name] = getExcludeList(prod_root, data)
        
    for prod_root in to_delete_list:
        prod_log = LOG_NAME + f"_{prod_root}.log"
        fileHandler = logging.FileHandler(filename=prod_log)
        fileHandler.setLevel(logging.DEBUG)
        fileHandler.setFormatter(FORMATTER)
        logger.addHandler(fileHandler)
        prod_list = to_delete_list.get(prod_root, False)
        if prod_list:
            for file in prod_list:
                logger.debug(file)
            thread = threading.Thread(target=open_log, args=(prod_log,))
            thread.start()
            res = input(
                f"Do you want to delete {len(prod_list)}"
                f" directories in {prod_root} cache ? (y/n)\n"
            )
            if res.lower() == 'y':
                del_res = delete_file(prod_list)
                logger.info('Rapport:')
                logger.info(f' - Deleted: {del_res[0]}')
                logger.info(f' - Skipped {del_res[1]}')
        else:
            logger.info(f'No files found for {prod_root} - skipped')
        logger.removeHandler(fileHandler)
            
    time_ns = time.monotonic_ns() - start
    logger.info(f'Exterminatus completed in {time_ns / 1e9}')