from . import auto_cleaner

def clean(scene_path: str, entity_type: auto_cleaner.EntityType, ):
    auto_cleaner.cleanEntity(scene_path, entity_type)