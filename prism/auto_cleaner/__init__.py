import importlib
from . import auto_cleaner
from .entitytype import EntityType

def clean(scene_path: str,
          entity_type: EntityType,
          exclude_list: list=[],
          print_only: bool=False):
    importlib.reload(auto_cleaner)
    auto_cleaner.cleanEntity(
        scene_path=scene_path,
        entity_type=entity_type,
        exclude_list=exclude_list,
        print_only=print_only
    )


def getReadPathToVersion():
    from . import nukescan
    importlib.reload(nukescan)
    return nukescan.retrieve_read_files()