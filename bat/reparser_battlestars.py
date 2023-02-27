import os

import re
import shutil
drive_dir = r"G:\Drive partagés\battlestar_partage\battlestar_2206\shots"

dic_replace_string ={"ch_roseknightsword":"ch_roseKnightSword",
					"ch_roseknightshield":"ch_roseKnightShield",
					"ch_roseknight":"ch_roseKnight",
					"ch_gingerbravecandycane":"ch_gingerBraveCandyCane",
					"ch_pandaweapon":"ch_pandaWeapon",
					"ch_googlepixelpro":"ch_googlePixelPro",

					"battlestar_2206/assets" : "I:/battlestar_2206/assets",
					"ch_deathknight":"ch_deathKnight",
					"ch_deathknightsword":"ch_deathKnightSword",
					"ch_oathkeeper":"ch_oathKeeper",
					"ch_oathkeepershield":"ch_oathKeeperShield",
					"ch_oathkeepersword":"ch_oathKeeperSword",
					"ch_archangel":"ch_archAngel",
					"ch_archangelweapon":"ch_archAngelWeapon"
					}
def listdir2(dir_path):
	result = [os.path.join(dir_path,item) for item in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path,item))]
	result.sort()
	return result

def listfile2(dir_path):
	result = [os.path.join(dir_path,item) for item in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,item))]
	return result

def multiple_replace(adict, text):
  # Create a regular expression from all of the dictionary keys
  regex = re.compile("|".join(map(re.escape, adict.keys(  ))))

  # For each match, look up the corresponding value in the dictionary
  return regex.sub(lambda match: adict[match.group(0)], text)

shots= listdir2(drive_dir)

def find_last_maya(shot):
	versions = listdir2(os.path.join(shot,"anim"))
	versions.sort()
	last_version=versions[-1]
	maya_scenes = listfile2(last_version)
	maya_scenes.sort()
	last_maya_scene = maya_scenes[-1]

	return last_maya_scene

def find_destination(source):

	new_maya_scene = source.replace(r"G:\Drive partagés\battlestar_partage\battlestar_2206", r"I:\battlestar_2206")

	return new_maya_scene

def copy_scene(scene):
	dest = find_destination(scene)
	print ("dest:%s"%dest)
	try:
		if not os.path.exists(dest):
			os.makedirs(dest)
		shutil.copy2(scene, dest)
	except:
		print("ERROR: file already exist %s" %dest)

def parse_maya_scene(maya_scene):
	filename, file_extension = os.path.splitext(maya_scene)
	new_maya_scene=filename+"_repathv1"+file_extension
	new_maya_scene = new_maya_scene.replace(r"G:\Drive partagés\battlestar_partage\battlestar_2206", r"I:\battlestar_2206")
	print (new_maya_scene)
	with open(maya_scene, 'r') as file :
		filedata = file.read()
		replaced_data = multiple_replace(dic_replace_string,filedata)

	with open(new_maya_scene, 'w') as file:
		file.write(replaced_data)
#shots=['G:\\Drive partagés\\battlestar_partage\\battlestar_2206\\shots\\longform_shot060']
for shot in shots:
	try:
		maya_scene = find_last_maya(shot)
		print("______________________")
		copy_scene(maya_scene)
	except:
		print("No maya scene: %s"%shot)

	pass
