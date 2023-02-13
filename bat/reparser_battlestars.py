import os
drive_dir = r"G:\Drive partagés\battlestar_partage\battlestar_2206\shots"

def listdir2(dir_path):
	result = [os.path.join(dir_path,item) for item in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path,item))]
	return result

def listfile2(dir_path):
	result = [os.path.join(dir_path,item) for item in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,item))]
	return result

shots= listdir2(drive_dir)


for shot in shots:
	versions = listdir2(os.path.join(shot,"layout"))
	versions.sort()
	last_version=versions[-1]
	maya_scene = listfile2(last_version)
	print(maya_scene)