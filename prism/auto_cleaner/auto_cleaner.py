import os
import glob
import shutil
from pathlib import Path
from enum import Enum

_PRODUCT_COUNT_DEFAULT = 10
_2D_RENDER_COUNT_DEFAULT = 5
_3D_RENDER_COUNT_DEFAULT = 3
_BACKUP_BASENAME = "old"

class EntityType(Enum):
    _PRODUCT = "AUTO_CLEANER_PRODUCT_TO_KEEP"
    _2D_RENDER = "AUTO_CLEANER_2DRENDER_TO_KEEP"
    _3D_RENDER = "AUTO_CLEANER_3DRENDER_TO_KEEP"


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
    else: # EntityType._3D_RENDER
        return "Renders/3dRender"


def getVersionToclean(entity_path: str, count_to_keep: int) -> dict:
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
    for layer_directory in layers_directories:
        version_pattern = os.path.join(layer_directory, "*")
        versions = [v for v in glob.glob(version_pattern) if not v.endswith(")")]
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
        for version in version_to_clean:
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
        print(f"Backup Directory : {backup_path}")
        for version in version_to_clean:
            print(f" - {version}")
            

def cleanEntity(scene_path: str, entity_type: str, print_only: bool=False):
    """Parse and move in backup directory 
    each version excending COUNT_TO_KEEP.

    Args:
        scene_path (str): scenepath, actually any path that contains the whole shot path.
    """    
    entity_segment = getEntitySegment(entity_type) 
    count_to_keep = getCountToKeep(entity_type)
    
    entity_path = getEntityPath(scene_path, entity_segment)
    versions_to_clean = getVersionToclean(entity_path, count_to_keep)

    if print_only:
        printVersions(versions_to_clean)
    else:
        cleanVersions(versions_to_clean)

    
if __name__ == "__main__":
    scene_path = "I:/Illogic_Training/03_Production/Shots/seq_01/sh_010"
    print("\n====================\n")
    cleanEntity(scene_path, EntityType._PRODUCT, True)
    print("\n====================\n")
    cleanEntity(scene_path, EntityType._2D_RENDER, True)
    print("\n====================\n")
    cleanEntity(scene_path, EntityType._3D_RENDER, True)