import os

import re
import shutil
drive_dir = r"G:\Drive partagés\clarins_shared\clarins_2301\shots"


def listdir2(dir_path):
	result = [os.path.join(dir_path,item) for item in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path,item))]
	result.sort()
	return result

def listfile2(dir_path):
	result = [os.path.join(dir_path,item) for item in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,item))]
	return result

def find_last_maya(shot):
    path_m = os.path.join(shot,"Anim3D")

    maya_scenes = listfile2(path_m)
    maya_scenes.sort()
    last_maya_scene = maya_scenes[-1]

    return last_maya_scene

def find_destination(source):

	new_maya_scene = source.replace(r"G:\Drive partagés\clarins_shared\clarins_2301", r"I:\clarins_2301")

	return new_maya_scene

def copy_scene(scene):
	dest = find_destination(scene)
	try:
		dirName= os.path.dirname(dest)

		if not os.path.exists(dirName):
			os.makedirs(dirName)
		if not os.path.isfile(dest):
			if os.path.isdir(dest):
				print("IT'S A DIR !")
			print("Copy new scene: "+dest)
			shutil.copy2(scene, dest)
		else:
			print("Skipping: " + dest)
	except:
		print("ERROR: file already exist %s" %dest)

shots= listdir2(drive_dir)


for shot in shots:
    try:
        maya_scene = find_last_maya(shot)
        print("______________________")
        copy_scene(maya_scene)
    except:
        print("No maya scene: %s"%shot)
