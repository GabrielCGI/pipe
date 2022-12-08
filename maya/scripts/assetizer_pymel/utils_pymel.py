import pymel.core as pm
def warning(txt):
    pm.error(txt)
    
def only_name(obj):
    only_name = obj.name().split("|")[-1]
    return only_name