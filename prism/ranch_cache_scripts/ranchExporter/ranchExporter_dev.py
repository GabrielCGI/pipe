# Used for path parsing
import os
import re
import glob
import shutil
import tempfile
import subprocess
from pathlib import Path

# Used for logs
import logging

# Used to get timestamp
import datetime
import time

import threading
# Performance check
# Expect stresstest_utils.py to be in the same director
# Else delete this import and all occurence of @stu.timeElapsed
from . import stresstest_utils as stu

# Used to get USD dependencies
from pxr import Ar, Usd, Sdf, UsdUtils

DEBUG_SCENE = False
# Turn True if you want to see performance of decorate function
stu.SHOW_TIME = False

UDIM_PATTERN = '\.(\d+|<UDIM>)\.'
ROOT_CACHE_RANCH = os.path.join("I:", os.sep, "ranch_cache2")
PROD_DISK = 'i'

# This variable store globally deps found
CURRENT_LAYER_PATH = None
LAYER_DONE = []
DEPS = []

LOG_DIR = os.path.join(ROOT_CACHE_RANCH, "logs")
LOG = None
LOG_RECAP = []
LOG_COPY_RECAP = []
LOG_FILE = None
LOG_ENABLE_CONSOLE = False
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


class CopyFilter(logging.Filter):
    def __init__(self, buffer, formatter):
        super().__init__()
        self.buffer = buffer
        self.formatter = formatter
        
    def filter(self, record):
        if 'Copy created' in record.getMessage():
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
    
    logfilename = f"log_{timestamp}_{name}.log"
    LOG_FILE = os.path.join(LOG_DIR, logfilename)

    os.makedirs(LOG_DIR, exist_ok=True)
    
    LOG = logging.getLogger(f"PrismPostExport_{name}")
    LOG.setLevel(logging.INFO)

    LOG.propagate = LOG_ENABLE_CONSOLE

    if LOG.hasHandlers():
        LOG.handlers.clear()

    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s::%(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    LOG.addHandler(file_handler)
    LOG.addFilter(ReloggingFilter(logging.WARNING, LOG_RECAP, formatter))
    LOG.addFilter(CopyFilter(LOG_COPY_RECAP, formatter))


def logRecap():
    """Generate a shot summary of what happened during the copy to ranch.
    """    
    
    if LOG_FILE and os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'a') as log_file:
            log_file.write(
                '\n-----------------LOG RECAP-----------------\n')
            log_file.write(f'Already exists {COPY_ALREADY_EXISTS} files.\n')
            log_file.write(f'Failed to copy {COPY_FAILED} files.\n')
            log_file.write(f'Copy {COPY_SUCCESS} files.\n')
            for msg in LOG_COPY_RECAP:
                log_file.write(f" - {msg}\n")
            log_file.write(
                f'Found {len(LOG_RECAP)} warning level or above issues.\n')
            for msg in LOG_RECAP:
                log_file.write(f" - {msg}\n")
    

def is_light_cache(kwargs) -> bool:
    try:
        node: hou.LopNode = kwargs["state"].node
        scenefile = kwargs["scenefile"]
    except:
        return False
    if not node:
        return False
    if not node.type().name() == 'prism::lop_filecache::1.0':
        return False
    save_mode = node.parm("saveMode")
    from_scenefile = node.parm("depFromScenefile")
    department = node.parm("department")
    if not save_mode or not from_scenefile or not department:
        return False
    if save_mode.eval() != 1:
        return False
    
    if from_scenefile.eval():
        return True
        return 'lighting' in scenefile.lower()
    else:
        dpt = department.menuLabels()[department.eval()].lower()
        return ('lighting' in dpt or 'lgt' in dpt)


def filter_not_USD(assetPathProcessed):
    if 'bgeo' in assetPathProcessed:
        global DEPS
        resolver = Ar.GetResolver()
        if not CURRENT_LAYER_PATH:
            DEPS.append(os.path.normpath(assetPathProcessed))
            return ''
        abs_path = CURRENT_LAYER_PATH.ComputeAbsolutePath(assetPathProcessed)
        resolved_path = resolver.Resolve(abs_path)
        DEPS.append(resolved_path.GetPathString())
        # Return an empty string to remove the asset path
        return ''
    return assetPathProcessed
    
    
def apply_filter(layer, dependencyInfo):
    global CURRENT_LAYER_PATH, LAYER_DONE
    layer.Reload(force=True)
    if not layer.identifier in LAYER_DONE:
        CURRENT_LAYER_PATH = layer
        LAYER_DONE.append(layer.identifier)
        UsdUtils.ModifyAssetPaths(layer, filter_not_USD)
    return dependencyInfo


@stu.timeElapsed
def getDependencies(asset_path: Sdf.AssetPath) -> list[str]:
    """Get every dependencies of an USD files as str path.

    Args:
        asset_path (Sdf.AssetPath): Asset path to parse.

    Returns:
        list[str]: List of every dependencies as absolute path.
    """
    layer = Sdf.Layer.FindOrOpen(asset_path.path)
    if not layer:
        LOG.error(f"Failed to open layer: {asset_path.path}")
        return []
    layer.Reload(force=True)

    global DEPS
    DEPS = []
    ctx = os.environ.get('PXR_AR_DEFAULT_SEARCH_PATH', False)
    if not ctx:
        ctx = ["I:/", "R:/"]
        LOG.info(f'Did not found context in env and fallback to {ctx}')
    else:
        ctx = ctx.split(';')
        LOG.info(f'Found context in {ctx} in env: PXR_AR_DEFAULT_SEARCH_PATH')
    ar_ctx = Ar.DefaultResolverContext(ctx)
    with Ar.ResolverContextBinder(ar_ctx):
        UsdUtils.ModifyAssetPaths(layer, filter_not_USD)
        
        dependencies = UsdUtils.ComputeAllDependencies(layer.identifier, apply_filter)
    layers, assets, unresolved_paths = dependencies
    
    layers_path = []
    for layer in layers:
        layer_path = str(layer.resolvedPath)
        if layer_path != '':
            layers_path.append(layer_path)
            
    abs_deps = resolveExternalDependencies(asset_path.path)      
    
    paths = layers_path + assets + unresolved_paths + abs_deps
    paths = list(set(paths))
    LOG.info(f'Found {len(paths)} dependencies')
       
    DEPS = []     
    return paths


# LOUIS MET L'ANCIENNE VERSION DE getDependencies ICI POUR LE MOMENT
# @stu.timeElapsed     
# def getDependencies(asset_path: Sdf.AssetPath) -> list[str]:
#     """Get every dependencies of an USD files as str path.

#     Args:
#         asset_path (Sdf.AssetPath): Asset path to parse.

#     Returns:
#         list[str]: List of every dependencies as absolute path.
#     """
    
#     LOG.info(f'Compute dependencies from {asset_path}')
#     dependencies = UsdUtils.ComputeAllDependencies(asset_path)
    
#     layers, assets, unresolved_paths = dependencies
    
#     layers_path = []
#     LOG.info(f'Get layer resolved path from {len(layers)} layers')
#     for layer in layers:
#         layer_path = str(layer.resolvedPath)
#         if layer_path != '':
#             layers_path.append(str(layer.resolvedPath))
    
#     paths: list = layers_path + assets + unresolved_paths
#     LOG.info('Remove duplicates')
#     paths = list(set(paths))
    
#     LOG.info(f'Got {len(paths)} dependencies')
            
#     return paths

    
def resolveExternalDependencies(usd_path: str) -> list[str]:
    """Resolve dependencies by looking at usd path
    and PXR_AR_DEFAULT_SEARCH_PATH.

    Args:
        usd_path (str): usd path in disk.

    Returns:
        list[str]: list of absolute path for dependencies that really exists.
    """    
    # Resolve externals dependencies
    usd_dir = os.path.dirname(usd_path)
    drives = getDriveList()
    abs_deps = []
    unresolved_deps = []
    for path in DEPS:
        
        if os.path.isabs(path):
            abs_deps.append(path)
            continue
            
        abs_path = os.path.join(usd_dir, path)
        if os.path.exists(abs_path):
            abs_deps.append(os.path.normpath(abs_path))
            continue
        
        found_in_drive = False
        for drive in drives:
            abs_path = os.path.join(f"{drive}:", os.sep, path)
            if os.path.exists(abs_path):
                abs_deps.append(os.path.normpath(abs_path))
                found_in_drive = True
                break
        if not found_in_drive:       
            unresolved_deps.append(path)
    
    LOG.info('Unresolved dependencies:')
    for path in unresolved_deps:
        LOG.info(f" - {path}")
            
    return abs_deps


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


@stu.timeElapsed  
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


def getUsdPath(kwargs: dict) -> str:
    """Get USD path from postRender context.

    Args:
        kwargs (dict): PostRender context.

    Returns:
        str: USD file path.
    """    
    
    exrpath = kwargs["outputpath"]
    
    # Dirty way to get usdc path
    basename = os.path.basename(exrpath)
    basename = os.path.splitext(os.path.splitext(basename)[0])[0]+".usdc"
    usdpath = os.path.join(os.path.dirname(exrpath), "_usd", basename)
    return os.path.abspath(usdpath)


def getUsdStage(kwargs: dict) -> Usd.Stage:
    """Get USD stage from state node in current context.

    Args:
        kwargs (dict): Current context.

    Returns:
        Usd.Stage: USD stage.
    """  
    try:
        print(f"DEBUG: Looking at {kwargs['state'].node} ")
        node = kwargs["state"].node.input(0)
        print(f"DEBUG: Looking at input {node} ")
    except:
        print("FAILED TO GET NODE FOR STAGE")
    print (f"Debug: Stage found: {node.stage()}")
    return node.stage()


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


def getDriveList():
    try:
        drives_str = os.environ['PXR_AR_DEFAULT_SEARCH_PATH']
        # expect a str with this format "C:/;D:/" each drive separated by a ;
        return [i[0].lower() for i in drives_str.split(';') if i]
    except:
        # default value to change later if ressource and prod2 change
        return ['i', 'r'] 

def getGroupedPath(abs_paths): 
    paths: list[Path] = []
    for path in abs_paths:
        paths.append(Path(path))
        
    grouped_path = {}
    for path in paths:
        norm_path = path.parent.as_posix()
        if not norm_path in grouped_path:
            grouped_path[norm_path] = [path.name]
        else:
            grouped_path[norm_path].append(path.name)

        
    for dir in grouped_path:
        grouped_path[dir] = list(set(grouped_path[dir]))
    return grouped_path


def copyToCacheranch(copy_list: list[str]):
    """Copy every files found to cache ranch.

    Args:
        copy_list (list[str]): Set of existing file to copy.
    """
            
    drive_list = getDriveList()
    for src in copy_list:
        try:
            # Try to find src disk and if the path is relative set it to i
            splitdrive = os.path.splitdrive(src)
            drive = splitdrive[0]
            if not drive:
                for allowed_drive in drive_list:
                    abs_path = os.path.join(
                        f"{allowed_drive}:",
                        os.sep, splitdrive[1]
                    )
                    os.path.exists(abs_path)
                    if os.path.exists(abs_path):
                        drive = allowed_drive
                        src = abs_path
                        break
            else:
                drive = drive[0]
                
            relativepath = os.path.relpath(splitdrive[1], os.sep)
            dst = os.path.join(ROOT_CACHE_RANCH, drive, relativepath)
            copy(src, dst)
        except Exception as e:
            LOG.warning(f"Failed to copy {src}")
            LOG.warning(e)

@stu.timeElapsed
def copyToCacheranchV2(copy_list: list[str]):
    """Copy every files found to cache ranch.

    Args:
        copy_list (list[str]): Set of existing file to copy.
    """
    
    drive_list = getDriveList()
    abs_paths = []
    for file_path in copy_list:
        splitdrive = os.path.splitdrive(file_path)
        drive = splitdrive[0]
        if not drive:
            for allowed_drive in drive_list:
                abs_path = os.path.join(
                    f"{allowed_drive}:",
                    os.sep, splitdrive[1]
                )
                os.path.exists(abs_path)
                if os.path.exists(abs_path):
                    abs_paths.append(abs_path)
                    break
        else:
            abs_paths.append(file_path)
            
    copy_list = getGroupedPath(abs_paths)

    for directory in copy_list:
        file_list = copy_list[directory]
        
        splitdrive = os.path.splitdrive(directory)
        drive = splitdrive[0][0]
        relativepath = os.path.relpath(splitdrive[1], os.sep)
        destination_dir = os.path.join(ROOT_CACHE_RANCH, drive, relativepath)
        
        command = ['robocopy', directory, destination_dir, *file_list]
        try:
            result = subprocess.run(
                command,
                creationflags=subprocess.CREATE_NO_WINDOW,
                capture_output=True
            )
            parseRobocopyOutput(directory, destination_dir, result)
        except Exception as e:
            LOG.error(e)


def parseRobocopyOutput(src, dst, output):
    global COPY_SUCCESS, COPY_ALREADY_EXISTS, COPY_FAILED
    LOG.info(f'Copy from {src} to {dst}:')
    stdout = output.stdout.decode(errors='replace')
    regex_pattern = (
        r'\s*(?:Fichiers|Files).*?'
        r':\s*(\d+)\s+(\d+)\s+(\d+)'
    )
    match = re.search(regex_pattern, stdout)
    if match and len(match.groups()) == 3:
        total = int(match.group(1))
        copied = int(match.group(2))
        ignored = int(match.group(3))
        failed = total - (copied + ignored)
        if copied:
            LOG.info(f" - Copied: {copied}")
            COPY_SUCCESS += copied
        if ignored:
            LOG.info(f" - Already copied: {ignored}"
            )
            COPY_ALREADY_EXISTS += ignored
        if failed:
            LOG.warning(f" - Failed: {failed}")
            COPY_FAILED += failed
    else:
        LOG.warning(f"Could not parse precise result")
        if output.returncode > 1:
            COPY_FAILED += 1
            LOG.error(f" - Copy failed")
        else:
            COPY_SUCCESS += 1
            LOG.warning(f" - Copy created")


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

def copyToRanch(deps_path, start_time=0.0):
    start = time.monotonic_ns()
    LOG.info('Getting paths to copy ...')
    
    to_copy = getPathToCopy(deps_path)
    
    LOG.info('Path to copy:')
    for path in to_copy:
        LOG.info(f" - {path}")
        
    time_ns = time.monotonic_ns() - start
    time_sec = time_ns / 1000000000
    LOG.info(f"Path parsing completed in: {time_sec} s | {time_ns} ns\n")
    
    start = time.monotonic_ns()
    LOG.info('Start copy ...')
    copyToCacheranchV2(to_copy)
    
    time_ns = time.monotonic_ns() - start
    time_sec = time_ns / 1000000000
        
    LOG.info(f"Copy completed in: {time_sec} s | {time_ns} ns")
    
    logRecap()
    full_time = time.monotonic() - start_time
    print(f'INFO: Ranch export ended in {full_time} s.')
    

def parseAndCopyToRanch(usdpath, kwargs):
    """
    Parse every dependencies and copy them to ROOT_CACHE_RANCH.
    """    
    
    start_full = time.monotonic()

    setupLog(usdpath)

    LOG.info("Started a copy. Please wait...")
    
    lop_node = kwargs['state'].node
    
    LOG.info('Check if the node is a light cache...')    
    if is_light_cache(kwargs):
        LOG.info('Node is a light filecache')
        usdPath = lop_node.parm('importPath').eval()
        if usdpath.endswith('.json'):
            LOG.warning('Could not find USD path')
            
            print('INFO: Ranch export ended.')
            return
        asset_path = getAssetPathFromUSD(usdPath)
    elif lop_node.type().name() == 'prism::LOP_Render::1.0':
        LOG.info("Skipped because the node is a LOP RENDER")
        print('INFO: Ranch export ended.')
        return # TO_UNCOMMENT
        writeToNode = lop_node.parm('writeToDisk')
        if writeToNode and writeToNode.eval():
            LOG.info("Getting dependencies from USD file...")
            asset_path = getAssetPathFromUSD(usdpath)
        else:
            LOG.info("Getting dependencies from USD stage...")
            asset_path = getAssetPathFromStage(stage)
    else:
        LOG.info('Render node is not LOP render or LOP File Cache')
        print('INFO: Ranch export ended.')
        return
    
    start = time.monotonic_ns()
    LOG.info('Start parsing dependencies ...')
    abs_paths = getDependencies(asset_path)
    
    time_ns = time.monotonic_ns() - start
    time_sec = time_ns / 1000000000
    LOG.info(f"Parsing completed in: {time_sec} s | {time_ns} ns\n")
    
    thread_copy = threading.Thread(target=copyToRanch, args=(abs_paths, start_full))
    thread_copy.start()