# region Imports

#Deadline
from Deadline.Events import *
from Deadline.Scripting import *

# Handle json files
import json

# System and path handlers
import os
from pathlib import Path
import sys
import socket
import re
import glob
import subprocess

# log
import logging 
import datetime

import time

# Import USD packages in the RANCH computers
# Needs updating for each new python version we use
ILL_PYTHON_SHARE_PATH = os.getenv("ILL_PYTHON_SHARE_PATH", r"R:\pipeline\networkInstall\python_shares")
UDIM_PATTERN = '\.(\d+|<UDIM>)\.'

if sys.version_info[0] == 3 :
    v = sys.version_info[1]
    if v == 11:
        venv_site_packages = os.path.join(ILL_PYTHON_SHARE_PATH, "python311_usd_pkgs", "Lib", "site-packages")
    elif v == 10:
        venv_site_packages = os.path.join(ILL_PYTHON_SHARE_PATH, "python310_usd_pkgs", "Lib", "site-packages")
    else:
        raise RuntimeError(f"Unsupported Python version: 3.{v}")
    
    if os.path.isdir(venv_site_packages):
        sys.path.insert(0, venv_site_packages)
    else:
        raise RuntimeError(f"venv site-packages not found: {venv_site_packages}")
else:
    raise RuntimeError(f"Unsupported Python version: {sys.version_info[0]}.x")

from pxr import Ar, Usd, Sdf, UsdUtils

# endregion

# region Global variables 
ROOT_CACHE_RANCH = '\\\\RANCH-SERVER\\ranch_cache'
RANCH_PC_PREFIX = "RANCH"
DEBUG = ["SPRINTER-04"]
RANCH_CPY_LOG_DIR = "C:/RANCH_CPY_log/"


USD_EXT = [".usdc" , ".usda" , ".usdnc" , ".usdna"] # The last two are for debug cuz im on apprentice. Wish i noticed the usd wasn't the same sooner LMAOOO.
 
# endregion

# region Helper functions

def setup_logs():
    os.makedirs(RANCH_CPY_LOG_DIR, exist_ok=True)
    log_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_copy_exr.log")
    log_path = os.path.join(RANCH_CPY_LOG_DIR, log_filename)

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def log_info(msg):
    logging.info(msg)
    print(msg)

def log_warning(msg):
    logging.warning
    print(msg)

def log_error(msg):
    logging.error(msg)
    print(msg)



def getJobName(deadlinePlugin):
    """
    Input : Deadline plugin
    Output : Job name (String)
    """
    job = deadlinePlugin.GetJob()
    jobName = job.JobName
    jobId = job.JobId

    json_name = jobName + "_" + jobId 
    return json_name

def getJsonPath(deadlinePlugin):
    """
    Input : Deadline plugin
    Output : Path to the newly created json from the job name in the ranch_cache (Pathlib Path)
    Ensures the dependencies_json folder exists.
    """
    json_name = getJobName(deadlinePlugin) + ".json"
    
    # Find folder in which the json should be created
    job = deadlinePlugin.GetJob()
    dir = Path(job.JobOutputDirectories[0]) / "_usd"
    splitdrive = os.path.splitdrive(dir)
    drive = splitdrive[0][0]
    relativepath = os.path.relpath(splitdrive[1], os.sep)
    json_dir = os.path.join(ROOT_CACHE_RANCH, drive, relativepath)

    json_path = Path(json_dir) / json_name
    log_info(f"Json path : {json_path}")
    return json_path

def getLockPath(deadlinePlugin):
    """
    Input : Deadline plugin
    Output : Path to the newly created lock path from the job name in the ranch_cache (Pathlib Path)
    Ensures the lock folder exists.
    """
    lock_name = getJobName(deadlinePlugin) + "_lock"
    
    # Create lock folder in case it doesnt exist in order to not overcrowd the thing.
    lock_folder = Path(ROOT_CACHE_RANCH) / "locks"
    lock_folder.mkdir(parents=True, exist_ok=True)
    
    lock_path = lock_folder / lock_name

    return lock_path

# TODO : Add some security check or find out if there are ever more than one 
def findUSDPath(deadlinePlugin):
    """
    Input : Deadline plugin 
    Output : Path to the export usd file (Pathlib path type) 
    """
    job = deadlinePlugin.GetJob()
    dir = Path(job.JobOutputDirectories[0]) / "_usd"
    exr = job.JobOutputFileNames[0]

    for file in os.scandir(dir):
        filename = file.name
        for ext in USD_EXT :
            if filename.endswith(ext):
                log_info(f"USD found at : {filename}")
                return Path(file)

    log_error(f"USD file not found in folder : {dir}")
    raise Exception(f"USD File not found at {dir}")

def getAssetPathFromUSD(usd_file: str) -> Sdf.AssetPath:
    """Get Sdf.AssetPath from given USD file. 

    Args:
        stage (Usd.Stage): USD stage.

    Returns:
        Sdf.AssetPath: SDF Asset path.
    """    
    
    return Sdf.AssetPath(usd_file)

def getDependencies(asset_path: Sdf.AssetPath) -> list[str]:
    """Get every dependencies of an USD files as str path.

    Args:
        asset_path (Sdf.AssetPath): Asset path to parse.

    Returns:
        list[str]: List of every dependencies as absolute path.
    """

    log_info(f'Compute dependencies from {asset_path}')
    
    ctx = os.environ.get('PXR_AR_DEFAULT_SEARCH_PATH', False)
    if not ctx:
        ctx = ["I:/", "R:/"]
        log_info(f'Did not found context in env and fallback to {ctx}')
    else:
        ctx = ctx.split(';')
        log_info(f'Found context in {ctx} in env: PXR_AR_DEFAULT_SEARCH_PATH')
    ar_ctx = Ar.DefaultResolverContext(ctx)
    with Ar.ResolverContextBinder(ar_ctx):
        dependencies = UsdUtils.ComputeAllDependencies(asset_path)
    
    layers, assets, unresolved_paths = dependencies
    
    layers_path = []
    log_info(f'Get layer resolved path from {len(layers)} layers')
    for layer in layers:
        layer_path = str(layer.resolvedPath)
        if layer_path != '':
            layers_path.append(str(layer.resolvedPath))
    
    paths: list = layers_path + assets + unresolved_paths
    log_info("Remove duplicates")
    paths = list(set(paths))
    
    log_info(f"Got {len(paths)} dependencies")        
    
    return paths

def getDependenciesFromJSON(json_path) : 
    paths = []

    json_path_str = str(json_path)

    if not json_path_str.endswith(".json") : 
        return paths

    with open(json_path_str , "r") as f:

        data = json.load(f)
        for item in data : 
            paths.append(item)

    return paths

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

def parseRobocopyOutput(src, dst, output):
    # global COPY_SUCCESS, COPY_ALREADY_EXISTS, COPY_FAILED
    log_info(f'Copy from {src} to {dst}:')
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
            log_info(f" - Copied: {copied}")
            # COPY_SUCCESS += copied
        if ignored:
            log_info(f" - Already copied: {ignored}"
            )
            # COPY_ALREADY_EXISTS += ignored
        if failed:
            log_warning(f" - Failed: {failed}")
            # COPY_FAILED += failed
    else:
        log_info(f"! Could not parse precise result")
        if output.returncode > 1:
            # COPY_FAILED += 1
            log_info(f" - Copy failed {src}")
        else:
            # COPY_SUCCESS += 1
            log_info(f" - Copy created")


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
            # log_info(f"Copying : {result.stdout}")
            parseRobocopyOutput(directory, destination_dir, result)
        except Exception as e:
            log_error(e)
            raise Exception(e) 
        
def blacklist_other_ranch(deadlinePlugin, blacklist : bool):
    """
    This function blacklists or whitelists all other ranch workers to this job.
    setting blacklist to true will blacklist, and false will whitelist

    Input : 
        deadline plugin : DeadlinePlugin, blacklist : bool
    
    """
    job = deadlinePlugin.GetJob()
    jobId = job.JobId
    slave_name = deadlinePlugin.GetSlaveName() # Store our name to not be blacklisted

    # 
    ranch_workers = []

    for name in RepositoryUtils.GetSlaveNames(True) :
        if "RANCH" in name and (name != slave_name) :
            ranch_workers.append(name)

    if blacklist : 
        RepositoryUtils.AddSlavesToMachineLimitList(jobId, ranch_workers)
        log_info(f"Blacklisted ranch workers : {ranch_workers}")
    else : 
        RepositoryUtils.RemoveSlavesFromMachineLimitList(jobId, ranch_workers)
        log_info(f"Whitelisted workers : {ranch_workers}")

# endregion

# region Main

# Test main to check if the deadlinePlugin is properly found. 
def __main__(*args):

    """
    Pre-task script for RANCH jobs, gets dependencies, and copies all necessary files into ranch computer by accessing the network files.
    Input : 
        Deadline arguments, most importantly a Deadline Plugin (args[0])
    """

    deadlinePlugin = args[0]
    setup_logs()

    log_info("Launched pretask script")

    # Ranch pc
    if not (socket.gethostname().startswith(RANCH_PC_PREFIX)) : 
        log_info("Not ranch pc")
        return

    usdpath = findUSDPath(deadlinePlugin)
    json_path = getJsonPath(deadlinePlugin) 
    lock_path = getLockPath(deadlinePlugin)

    log_info("Checking json")
    if(os.path.isfile(json_path)):
        log_info("JSON file found, dependencies computed, skipping pretask script")
        return

    # If lock exists requeue 
    log_info("Checking lock")
    if(os.path.isfile(lock_path)):
        log_info("Lock file found, checking if worker interrupted")

        # Interruption check, if a worker isn't working on it, delete the lock
        ranch_wokring = False
        job = deadlinePlugin.GetJob()
        tasks = RepositoryUtils.GetJobTasks(job , True).TaskCollectionTasks
        slave_name = deadlinePlugin.GetSlaveName()
        for task in tasks : 
            if "RANCH" in task.TaskSlaveName and task.TaskSlaveName != slave_name : 
                ranch_wokring = True
        
        if ranch_wokring :
            log_info("RANCH still computing dependencies, failing job")

            # in theory should requeue with no error, but for some reason it still causes an error...   
            # https://docs.thinkboxsoftware.com/products/deadline/10.2/2_Scripting%20Reference/class_frantic_x_1_1_processes_1_1_managed_process.html#ae096dfdfdd769549a2dabf5b63f85422
            deadlinePlugin.AbortRender("Minor abort : Dependencies not yet computed", deadlinePlugin.AbortLevel.Minor) 
            return
        
        else :
            log_info("No ranch computing dependencies, but lock was found. Removing lock...")
            os.remove(lock_path)
            log_info("Lock file removed")
            blacklist_other_ranch(deadlinePlugin, blacklist=False)

        

    # Create lock
    open(lock_path , "a").close() 
    log_info("Created lock")
    # After the lock is created, blacklist the rest and copy
    blacklist_other_ranch(deadlinePlugin , blacklist=True)
    log_info("Blacklisted other files")

    # Get dependencies
    log_info("Getting dependencies from USD")
    start = time.time()
    asset_path = getAssetPathFromUSD(str(usdpath))
    paths = getDependencies(asset_path)
    end = time.time()
    log_info(f"Done getting dependencies from USD in {end-start} seconds")

    log_info("Start copy")
    start = time.time()
    to_copy = getPathToCopy(paths)
    copyToCacheranchV2(to_copy)
    end = time.time()
    log_info(f"Copy Done in : {end - start} seconds")

    blacklist_other_ranch(deadlinePlugin, blacklist=False)

    # Write json file (added security)
    json_str = json.dumps(paths, indent=4)  
    with open(json_path, "w") as f:
        f.write(json_str)
    log_info("JSON file written")

    # Delete lock file
    if os.path.exists(lock_path):
        os.remove(lock_path)
    log_info("Lock file removed")

    return 0

# endregion