import os
import re
import glob
import time
import shutil
import logging
import datetime
import traceback
from pathlib import Path

from .entitytype import EntityType
from . import loggingsetup

AC_MODULE_ROOT = os.path.dirname(__file__)
_DEFAULT_LOG_DIR = os.path.join(os.path.dirname(AC_MODULE_ROOT), "logs")
LOG_CONFIG = os.path.join(AC_MODULE_ROOT, "config/logconfig.json")
GLOBAL_LOG_DIR = os.environ.get("ILL_LOGS_PATH", False)
LOG_DIRECTORY = os.path.join(GLOBAL_LOG_DIR, "auto_cleaner_logs") if GLOBAL_LOG_DIR else _DEFAULT_LOG_DIR
logger = None

_PRODUCT_COUNT_DEFAULT = 10
_2D_RENDER_COUNT_DEFAULT = 5
_3D_RENDER_COUNT_DEFAULT = 3
_SCENEFILE_COUNT_DEFAULT = 50
_BACKUP_BASENAME = "old"

# Safety threshold
_MAX_SIZE_THRESHOLD = 0.3
_MIN_ELAPSED_DAY = 7

VERSION_PATTERN_RE = re.compile(r"v\d{3,9}")


def getLogger(log_name="unnamed"):
    loggingsetup.setup_log(
        logName=log_name,
        logConfigPath=LOG_CONFIG,
        logDirectory=LOG_DIRECTORY,
        with_time=True
    )
    return logging.getLogger(__package__)


def getAllFiles(directory: str):
    """Return all files in a given directory."""
    if os.path.isfile(directory):
        return [directory]
    
    files = []
    for entry in os.scandir(directory):
        if entry.is_dir(follow_symlinks=False):
            files += getAllFiles(entry.path)
        else:
            files += [entry.path]
    return files


def getSize(files):
    """Return total size of files in given path and subdirs."""
    return sum(list(map(lambda x: os.path.getsize(x), files)))


def getLastModificationTime(files):
    """Return last modification date in given path and subdirs."""
    files_sizes = list(map(lambda x: os.path.getmtime(x), files))
    if not len(files_sizes):
        return 0
    else:
        return min(files_sizes)


def getEntityPath(scene_path: str, type_path: str) -> str:
    """Get entity path from scene path

    Args:
        scene_path (str): scenepath, actually any path that contains the whole shot path.

    Returns:
        str: entity path, path ending with Export
    """    
    scene_path: Path = Path(scene_path)
    assert len(scene_path.parts) > 5, "Scene path is too short, no Export found."
    entity_path = Path(*scene_path.parts[:6])
    entity_path = (entity_path / type_path).as_posix()
    return entity_path


def getCountToKeep(entity_type: EntityType) -> int:
    """Number of version to keep when cleaning.

    Returns:
        int: number of version to keep. 
    """
    if entity_type == EntityType._PRODUCT:
        count_to_keep = os.getenv(entity_type.value, _PRODUCT_COUNT_DEFAULT)
        try:
            return int(count_to_keep)
        except ValueError:
            return _PRODUCT_COUNT_DEFAULT
    elif entity_type == EntityType._2D_RENDER:
        count_to_keep = os.getenv(entity_type.value, _2D_RENDER_COUNT_DEFAULT)
        try:
            return int(count_to_keep)
        except ValueError:
            return _2D_RENDER_COUNT_DEFAULT
    elif entity_type == EntityType._3D_RENDER:
        count_to_keep = os.getenv(entity_type.value, _3D_RENDER_COUNT_DEFAULT)
        try:
            return int(count_to_keep)
        except ValueError:
            return _3D_RENDER_COUNT_DEFAULT
    elif entity_type == EntityType._SCENEFILE:
        count_to_keep = os.getenv(entity_type.value, _SCENEFILE_COUNT_DEFAULT)
        try:
            return int(count_to_keep)
        except ValueError:
            return _SCENEFILE_COUNT_DEFAULT
    else:
        raise ValueError("Invalid entity type")


def getEntitySegment(entity_type: EntityType) -> str:
    """Get entity type path from entity path.

    Args:
        entity_type (EntityType): Entity type.

    Returns:
        str: Short path segment.
    """
    if entity_type == EntityType._PRODUCT:
        return "Export"
    elif entity_type == EntityType._2D_RENDER:
        return "Renders/2dRender"
    elif entity_type == EntityType._3D_RENDER:
        return "Renders/3dRender"
    elif entity_type == EntityType._SCENEFILE:
        return "Scenefiles/*"
    else:
        raise ValueError("Invalid entity type")


def getVersionToclean(
        entity_path: str,
        entity_type: EntityType,
        count_to_keep: int,
        exclude_list: list=[]) -> dict:
    """Get versions path to clean from entity path.
    Expected format: *:/03_production/*/*/*/Export

    Args:
        entity_path (str): entity path, path ending with Export
        entity_type (EntityType): entity type.
        count_to_keep (int): number of version to keep.
        exclude_list (list[str]): list of files to keep.
    """
    if entity_type in [
            EntityType._PRODUCT,
            EntityType._2D_RENDER,
            EntityType._3D_RENDER
        ]:
        return getDirectoriesToClean(entity_path, count_to_keep, exclude_list)
    elif entity_type == EntityType._SCENEFILE:
        return getScenefilesToClean(entity_path, count_to_keep, exclude_list)


def deleteAllIndex(to_clear: list, indexes: list):
    indexes = list(set(indexes))
    indexes.sort()
    for i in indexes[::-1]:
        to_clear.pop(i)
    return to_clear


def isSafeVersionFile(file: str) -> bool:
    current_time = time.time()
    last_m = os.path.getmtime(file)
    elapsed_day = (current_time - last_m) / 86400
    return elapsed_day > _MIN_ELAPSED_DAY


def getSafeVersionsDirectories(versions: list) -> list:
    to_skip = []
    # check date
    for i, version_path in enumerate(versions):
        current_time = time.time()
        all_files = getAllFiles(version_path)
        # check date
        last_m = getLastModificationTime(all_files)
        elapsed_day = (current_time - last_m) / 86400
        if elapsed_day < _MIN_ELAPSED_DAY:
            to_skip.append(i)
            continue
    # clear versions
    versions = deleteAllIndex(versions, to_skip)
    to_skip = []
    if not len(versions):
        return versions
    # check size
    versions_sizes = []
    nb_files_per_version = []
    for version_path in versions:
        all_files = getAllFiles(version_path)
        nb_files_per_version.append(len(all_files))
        versions_sizes.append(getSize(all_files))
    nb_max_file = max(nb_files_per_version)
    max_size = max(versions_sizes)
    file_threshold = _MAX_SIZE_THRESHOLD*nb_max_file
    size_threshold = _MAX_SIZE_THRESHOLD*max_size
    for i, v_size in enumerate(versions_sizes):
        if v_size < size_threshold or nb_files_per_version[i] < file_threshold:
            to_skip.append(i)
    # clear versions
    versions = deleteAllIndex(versions, to_skip)
        
    return versions


def getDirectoriesToClean(
        entity_path: str,
        count_to_keep: int,
        exclude_list: list=[]) -> dict:
    """Get versions path to clean from entity path.
    Expected format: *:/03_production/*/*/*/Export

    Args:
        entity_path (str): entity path, path ending with Export
        count_to_keep (int): number of version to keep.
        exclude_list (list[str]): list of files to keep.
    """
    entity_path: Path = Path(entity_path)
    layer_pattern = (entity_path / "*").as_posix()
    layers_directories = glob.glob(layer_pattern)
    versions_datas = {}

    exclude_list_normpath = [
        os.path.normpath(exclude_path)
        for exclude_path in exclude_list
    ]

    version_pattern_compiled = re.compile(VERSION_PATTERN_RE)

    for layer_directory in layers_directories:
        version_pattern = os.path.join(layer_directory, "*")
        versions = []
        for version_path in glob.glob(version_pattern):
            version_basename = os.path.basename(version_path)
            version_path = os.path.normpath(version_path)
            if os.path.normpath(version_path) in exclude_list_normpath:
                continue
            if (version_pattern_compiled.fullmatch(version_basename)):
                versions.append(version_path)
        logger.info(f"Number of version before safety check: {len(versions)}")
        versions = getSafeVersionsDirectories(versions)
        logger.info(f"Number of version after safety check: {len(versions)}")
        versions.sort()
        layer_data = {}
        layer_data["versions"] = versions[:-count_to_keep]
        layer_data["backup"] = (Path(layer_directory) / _BACKUP_BASENAME)
        versions_datas[layer_directory] = layer_data
    return versions_datas


def getScenefilesToClean(
        entity_path: str,
        count_to_keep: int,
        exclude_list: list=[]) -> dict:
    """Get versions scenefiles path to clean from entity path.
    Expected format: *:/03_production/*/*/*/Export

    Args:
        entity_path (str): entity path, path ending with Export
        count_to_keep (int): number of version to keep.
        exclude_list (list[str]): list of files to keep.
    """
    entity_path: Path = Path(entity_path)
    layer_pattern = (entity_path / "*").as_posix()
    task_directories = glob.glob(layer_pattern)
    versions_datas = {}

    exclude_list_normpath = [
        os.path.normpath(exclude_path)
        for exclude_path in exclude_list
    ]

    version_pattern_compiled = re.compile(VERSION_PATTERN_RE)

    for task_directory in task_directories:
        scenefiles = os.listdir(task_directory)
        sf_versions = {}
        for sf_basename in scenefiles:
            sf_fullpath = os.path.join(task_directory, sf_basename)
            if not isSafeVersionFile(sf_fullpath):
                continue
            if os.path.normpath(sf_fullpath) in exclude_list_normpath:
                continue
            version_match = version_pattern_compiled.search(sf_basename)
            if not version_match:
                continue
            version_span = version_match.span()
            version = sf_basename[version_span[0]:version_span[1]]
            sf_versions.setdefault(version, []).append(sf_fullpath)
        task_datas = {}
        sorted_versions = sorted(sf_versions.keys())[:-count_to_keep]
        task_datas['versions'] =  [x for v in sorted_versions for x in sf_versions[v]]
        task_datas['backup'] = (Path(task_directory) / "old")
        versions_datas[task_directory] = task_datas
    return versions_datas


def cleanVersions(versions_datas: dict):
    """Move every version in their backup/old directory.

    Args:
        versions_datas (dict): List of version and backup dir for each layers.
    """    
    for layer in versions_datas.keys():
        backup_path: str = versions_datas[layer]['backup']
        version_to_clean: list = versions_datas[layer]['versions']
        logger.info(f"Backup Directory : {backup_path}")
        if len(version_to_clean):
            os.makedirs(backup_path, exist_ok=True)
        for version in version_to_clean:
            logger.info(f" - {version}")
            try:
                shutil.move(version, backup_path)
            except shutil.Error:
                continue


def printVersions(versions_datas: dict):
    """Print every version and their backup directory.

    Args:
        versions_data (dict): List of version and backup dir for each layers.
    """
    for layer in versions_datas.keys():
        backup_path: str = versions_datas[layer]['backup']
        version_to_clean: list = versions_datas[layer]['versions']
        logger.info(f"Backup Directory : {backup_path}")
        for version in version_to_clean:
            logger.info(f" - {version}")
            

def cleanEntity(
        scene_path: str,
        entity_type: EntityType,
        exclude_list: list=[],
        print_only: bool=False):
    """Parse and move in backup directory 
    each version exceeding COUNT_TO_KEEP.

    Args:
        scene_path (str): scenepath, actually any path that contains the whole shot path.
    """
    try:
        global logger
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]
        logger = getLogger(f"{scene_name}_{entity_type.name}")
        logger.info(f"Start cleaning : {scene_path}")
        try:
            entity_segment = getEntitySegment(entity_type) 
            count_to_keep = getCountToKeep(entity_type)
        except ValueError as e:
            logger.error(e)
            return
        
        try:
            entity_path = getEntityPath(scene_path, entity_segment)
        except AssertionError as e:
            logger.error(e)
            return
        versions_to_clean = getVersionToclean(
            entity_path,
            entity_type,
            count_to_keep,
            exclude_list
        )

        logger.info(f"Start moving {entity_type.name} files")
        if print_only:
            logger.info("Print only")
            printVersions(versions_to_clean)
        else:
            logger.info("Move")
            cleanVersions(versions_to_clean)
        logger.info(f"Move complete.\n")
    except Exception as e:
        try:
            sanitized_name = loggingsetup.sanitize_filename(f"{scene_name}_{entity_type.name}")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            error_log_name = os.path.join(LOG_DIRECTORY, f"ERROR_LOG_{timestamp}_{sanitized_name}.log")
            with open(error_log_name, "a+") as error_file:
                error_file.write(str(e)+"\n")
                error_file.write(str(traceback.format_exc()))
        except:
            pass