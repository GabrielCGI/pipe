import os
import re
import glob
import shutil
import logging
from pathlib import Path

from .entitytype import EntityType
from . import loggingsetup

AC_MODULE_ROOT = os.path.dirname(__file__)
_DEFAULT_LOG_DIR = os.path.join(os.path.dirname(AC_MODULE_ROOT), "logs")
LOG_CONFIG = os.path.join(AC_MODULE_ROOT, "config/logconfig.json")
GLOBAL_LOG_DIR = os.environ.get("ILL_LOGS_PATH", False)
LOG_DIRECTORY = os.path.join(GLOBAL_LOG_DIR, "auto_cleaner_logs") if GLOBAL_LOG_DIR else _DEFAULT_LOG_DIR
logger = None
def getLogger():
    is_log_setup = loggingsetup.setup_log(
        logName='auto_cleaner',
        logConfigPath=LOG_CONFIG,
        logDirectory=LOG_DIRECTORY,
        with_time=True
    )
    if is_log_setup:
        print("Log is setup")
    else:
        print("Log failed to setup")
    print(__name__)
    return logging.getLogger(__name__)

_PRODUCT_COUNT_DEFAULT = 10
_2D_RENDER_COUNT_DEFAULT = 5
_3D_RENDER_COUNT_DEFAULT = 3
_BACKUP_BASENAME = "old"

VERSION_PATTERN_RE = re.compile(r"v\d{3,9}")

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
    assert os.path.exists(entity_path), "Entity path do not exists"
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
    else: # EntityType._3D_RENDER
        count_to_keep = os.getenv(entity_type.value, _3D_RENDER_COUNT_DEFAULT)
        try:
            return int(count_to_keep)
        except ValueError:
            return _3D_RENDER_COUNT_DEFAULT


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
    else:
        raise ValueError("Invalid entity type")


def getVersionToclean(
        entity_path: str,
        count_to_keep: int,
        exclude_list: list=[]) -> dict:
    """Get versions path to clean from entity path.
    Expected format: *:/03_production/*/*/*/Export

    Args:
        entity_path (str): entity path, path ending with Export
        count_to_keep (int): number of version to keep.
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
        versions.sort()
        layer_data = {}
        layer_data["versions"] = versions[:-count_to_keep]
        layer_data["backup"] = (Path(layer_directory) / _BACKUP_BASENAME)
        versions_datas[layer_directory] = layer_data
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
    each version excending COUNT_TO_KEEP.

    Args:
        scene_path (str): scenepath, actually any path that contains the whole shot path.
    """
    global logger
    logger = getLogger()
    logger.info(f"Start cleaning : {scene_path}")
    try:
        entity_segment = getEntitySegment(entity_type) 
    except ValueError as e:
        logger.error(e)
        return
    count_to_keep = getCountToKeep(entity_type)
    
    try:
        entity_path = getEntityPath(scene_path, entity_segment)
    except AssertionError as e:
        logger.error(e)
        return
    versions_to_clean = getVersionToclean(entity_path, count_to_keep, exclude_list)

    logger.info(f"Start moving {entity_type.name} files")
    if print_only:
        logger.info("Print only")
        printVersions(versions_to_clean)
    else:
        logger.info("Move")
        cleanVersions(versions_to_clean)
    logger.info(f"Move complete.\n")
