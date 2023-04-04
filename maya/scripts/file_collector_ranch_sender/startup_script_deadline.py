import re
import os
import maya.mel as mel
from pymel.core import *

DISK_PATHS = {
    "I:": r'\\RANCH-126\ranch_cache\I',
    "R:": r'\\RANCH-126\ranch_cache\R',
    "B:": r'\\RANCH-126\ranch_cache\B',
    "P:": r'\\RANCH-126\ranch_cache\P',
}


# Repath all the References to the RANCH path
def __repath_references():
    list_refs = ls(references=True)
    for ref in list_refs:
        # Take only the ref loaded
        if not ref.isLoaded():
            continue
        # Repath only the ref having a path that exists locally
        path = referenceQuery(ref, filename=True)
        if not os.path.exists(path):
            continue
        # The path must match
        match = re.match(r"^(.:)[\\\/](.*\w)$", path)
        if not match:
            continue
        # The path must have a DISK known
        disk = match.group(1)
        if disk not in DISK_PATHS:
            continue
        # The new path should exists on the RANCH to be repath
        relative_path = match.group(2)
        new_path = os.path.join(DISK_PATHS[disk], relative_path)
        if not os.path.exists(new_path):
            continue
        # Repath the reference
        file_ref = FileReference(ref)
        file_ref.replaceWith(new_path)
        mel.eval(r'print "| Repath ref ' + path + ' by ' + new_path.replace("\\", "/") + '\\n";')


# # Get the path data from a File, an AiImage or a StandIn
# def __get_path_file(elem):
#     if objectType(elem, isType='file'):
#         return elem.fileTextureName.get()
#     elif objectType(elem, isType='aiImage'):
#         return elem.filename.get()
#     elif objectType(elem, isType='aiStandIn'):
#         return elem.dso.get()
#     else:
#         return None
#
#
# # Set the path of a File, an AiImage or a StandIn
# def __set_path_file(elem, path):
#     if objectType(elem, isType='file'):
#         mel.eval('print "| Repath File '+elem.fileTextureName.get()+' by '+path+'\\n";')
#         elem.fileTextureName.set(path)
#     elif objectType(elem, isType='aiImage'):
#         mel.eval('print "| Repath Image '+elem.filename.get()+' by '+path+'\\n";')
#         elem.filename.set(path)
#     elif objectType(elem, isType='aiStandIn'):
#         mel.eval('print "| Repath StandIn '+elem.dso.get()+' by '+path+'\\n";')
#         elem.dso.set(path)
#
# # Set all path to relative (remove the disks from paths)
# def __repath_files_to_relative():
#     list_file = ls(type="file")
#     list_images = ls(type="aiImage")
#     list_standin = ls(type="aiStandIn")
#     list_elem = list_file + list_images + list_standin
#     for elem in list_elem:
#         path = __get_path_file(elem)
#         if path is not None and os.path.exists(path):
#             match = re.match(r"^([\w:]*)[\\\/](.*\w)$", path)
#             if match:
#                 disk = match.group(1)
#                 if disk in DISK_PATHS:
#                     relative_path = match.group(2)
#                     __set_path_file(elem, relative_path)


def run():
    pass
    # # If on a RANCH we repath reference to the RANCH path and change all path of Files, Images and StandIns to relative
    # if os.environ['COMPUTERNAME'].startswith('RANCH'):
    #     mel.eval('print "+-- Illogic path mapping Reference because computer is RANCH\\n";')
    #     #__repath_references() #il y a tjr un pb avec le repath des references. Si il y a des nested references, Les references enfants se reload quand même.
    # else:
    #     # If on LOCAL the repath are not run
    #     mel.eval('print "--- Illogic no path mapping because computer is LOCAL\\n";')
