import pymel.core as pm
import os
def warning(txt):
    pm.error(txt)

def only_name(obj):
    only_name = obj.name().split("|")[-1].split(":")[-1]
    return only_name

def get_working_directory():
    working_directory = "D:/april/assets"
    return working_directory

def nameSpace_from_path(path):
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        nameSpace = name + "_00"
        nameSpace.replace(".","_")
        return nameSpace

def lock_all_transforms(obj, lock=True):

    if lock == True:
        if type(obj) == list:
            for o in obj:
                o.translate.lock()
                o.rotate.lock()
                o.scale.lock()
        else:
            obj.translate.lock()
            obj.rotate.lock()
            obj.scale.lock()
    if lock == False:
        if type(obj) == list:
            for o in obj:
                o.translate.unlock()
                o.rotate.unlock()
                o.scale.unlock()
        else:
            obj.translate.unlock()
            obj.rotate.unlock()
            obj.scale.unlock() 

def match_matrix(source, target):
    m = pm.xform(target, matrix=True, query=True)
    pm.xform(source, matrix=m)

