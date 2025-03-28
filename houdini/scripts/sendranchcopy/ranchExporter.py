# Used for path parsing
import os
import re
import glob
import shutil

# Used for logs
import logging

# Used to get timestamp
import datetime
import time

# Used to get USD dependencies
from pxr import Usd, Sdf, UsdUtils

import hou

UDIM_PATTERN = '\.(\d+|<UDIM>)\.'
ROOT_CACHE_RANCH = os.path.join("I:", os.sep, "ranch_cache2")
LOG_DIR = os.path.join(ROOT_CACHE_RANCH, "logs")
LOG = None
LOG_RECAP = []
LOG_FILE = None
COPY_SUCCESS = 0
COPY_FAILED = 0
COPY_ALREADY_EXISTS = 0

class ReloggingFilter(logging.Filter):
    def __init__(self, level, buffer, formatter):
        super().__init__()
        self.level = level
        self.buffer = buffer
        self.formatter = formatter
        
    def filter(self, record):
        if record.levelno >= self.level:
            log_entry = self.formatter.format(record)
            self.buffer.append(log_entry)
        return True

    
def setupLog(usdfile: str):
    """Setup LOG basic config.

    Args:
        usdfile (str): USD path.
    """
    global LOG
    global LOG_FILE
    
    basename = os.path.basename(usdfile)
    name = os.path.splitext(basename)[0]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    logfilename = f"log_{timestamp}_{name}.txt"
    LOG_FILE = os.path.join(LOG_DIR, logfilename)

    os.makedirs(LOG_DIR, exist_ok=True)
    
    LOG = logging.getLogger(f"PrismPostExport_{name}")
    LOG.setLevel(logging.INFO)

    LOG.propagate = False

    if LOG.hasHandlers():
        LOG.handlers.clear()

    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s::%(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    LOG.addHandler(file_handler)
    LOG.addFilter(ReloggingFilter(logging.WARNING, LOG_RECAP, formatter))


def logRecap():
    """Generate a shot summary of what happened during the copy to ranch.
    """
    
    recap = ''  
    recap += '\n-----------------LOG RECAP-----------------\n'
    recap += f'Copy {COPY_SUCCESS} files.\n'
    recap += f'Failed to copy {COPY_FAILED} files.\n'
    recap += f'Already exists {COPY_ALREADY_EXISTS} files.\n'
    recap += f'Found {len(LOG_RECAP)} warning level or above issues.\n'
    
    if LOG_FILE and os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(recap)
            for msg in LOG_RECAP:
                recap_entry = f" - {msg}\n"
                recap += recap_entry
                log_file.write(recap_entry)
                
    return recap
    

def getDependencies(asset_path: Sdf.AssetPath) -> list[str]:
    """Get every dependencies of an USD files as str path.

    Args:
        asset_path (Sdf.AssetPath): Asset path to parse.

    Returns:
        list[str]: List of every dependencies as absolute path.
    """
    
    dependencies = UsdUtils.ComputeAllDependencies(asset_path)
    
    layers, assets, unresolved_paths = dependencies
    
    layers_path = []
    for layer in layers:
        layer_path = str(layer.resolvedPath)
        if layer_path != '':
            layers_path.append(str(layer.resolvedPath))
    
    paths: list = layers_path + assets + unresolved_paths
    paths = list(set(paths))
            
    return paths


def getPathFamily(path: str):
    """Get every udim and rat files related to the path file,
    if it exits.

    Args:
        path (str): USD dependencies path.

    Returns:
        list[str]: Every path found and path if it exists.
    """    
    
    to_copy = []
    udim_match = re.search(UDIM_PATTERN, path)
    if udim_match:
        udim_span = udim_match.span()
        glob_path_pattern = path[:udim_span[0]]+".*."+path[udim_span[1]:]
        path_list = glob.glob(glob_path_pattern)
        path_list = [os.path.abspath(path) for path in path_list]
        path_list = list(set(path_list))
        to_copy = path_list
    else:
        # if os.path.exists(path):
        # TODO Use a blacklist system instead of hardcoded specific file to avoid
        if os.path.basename(path) != 'thumbnail.png':
            to_copy = [path]

    for path in to_copy:
        rat_path = path+".rat"
        if os.path.exists(rat_path):
            to_copy.append(os.path.abspath(rat_path))
    
    return to_copy

 
def getPathToCopy(abs_paths: list[str]):
    """Get a set of absolute filepath to copy from dependency list.

    Args:
        abs_paths (list[str]): Every dependencies paths found.

    Returns:
        list[str]: Set of existing dependencies files and related files.
    """    
    
    to_copy = []
    for path in abs_paths:
        to_copy += getPathFamily(path)
    
    list(set(to_copy))
    return to_copy


def getAssetPathFromStage(stage: Usd.Stage) -> Sdf.AssetPath:
    """Get Sdf.AssetPath from given USD stage. 

    Args:
        stage (Usd.Stage): USD stage.

    Returns:
        Sdf.AssetPath: SDF Asset path.
    """    
    
    return Sdf.AssetPath(stage.GetRootLayer().identifier)


def getAssetPathFromUSD(usd_file: str) -> Sdf.AssetPath:
    """Get Sdf.AssetPath from given USD file. 

    Args:
        stage (Usd.Stage): USD stage.

    Returns:
        Sdf.AssetPath: SDF Asset path.
    """    
    
    return Sdf.AssetPath(usd_file)


def copyToCacheranch(abs_paths: list[str]):
    """Copy every files found to cache ranch.

    Args:
        abs_paths (list[str]): Set of existing file to copy.
    """    
    
    for src in abs_paths:
        try:
            splitdrive = os.path.splitdrive(src)
            drive = splitdrive[0][0]
            relativepath = os.path.relpath(splitdrive[1], os.sep)
            dst = os.path.join(ROOT_CACHE_RANCH, drive, relativepath)
            copy(src, dst)
        except:
            LOG.warning(f"Failed to copy {src}")


def copy(src: str, dst: str):
    """Copy src to dst and create directory tree in needed.

    Args:
        src (str): Path to source file.
        dst (str): Path to destination.
    """    
    global COPY_SUCCESS
    global COPY_FAILED
    global COPY_ALREADY_EXISTS
    
    if not os.path.isfile(src):
        LOG.warning(f"File do not exists '{src}'")
        COPY_FAILED += 1
        return    
    updated = False
    if os.path.isfile(dst):
        dst_stat = os.stat(dst)
        dst_mtime = dst_stat.st_mtime_ns
        dst_size = dst_stat.st_size
        
        src_stat = os.stat(src)
        src_mtime = src_stat.st_mtime_ns
        src_size = src_stat.st_size
        
        if src_mtime <= dst_mtime and src_size == dst_size:
            updated = True
            LOG.info(f"Already updated '{dst}'")
            COPY_ALREADY_EXISTS += 1
    if not updated:
        # TODO Find a faster copyfile
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        COPY_SUCCESS += 1
        LOG.info(f"Copy created '{dst}'")

def parseAndCopyToRanch(stage: Usd.Stage, scene_path: str):
    """
    Parse every dependencies and copy them to ROOT_CACHE_RANCH.
    
    Args:
        stage (Usd.Stage): USD stage.
        dst (str): Path to destination.
    """
    
    if not stage or not scene_path:
        return
    
    setupLog(scene_path)

    LOG.info("Started a copy. Please wait...")
    
    start = time.monotonic_ns()
    
    LOG.info("Getting dependencies from USD stage...")
    
    asset_path = getAssetPathFromStage(stage)
    abs_paths = getDependencies(asset_path)
    to_copy = getPathToCopy(abs_paths)
    copyToCacheranch(to_copy)
    
    time_ns = time.monotonic_ns() - start
    time_sec = time_ns / 1000000000
        
    recap = logRecap()
    
    log_complete = f"Copy completed in: {time_sec} s"
    LOG.info(log_complete)
    hou.ui.displayMessage(text=log_complete, details=recap,
                          severity=hou.severityType.Message)