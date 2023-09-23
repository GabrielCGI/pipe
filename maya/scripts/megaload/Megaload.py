import os
import pymel.core as pm

directory = r"R:\megascan\Downloaded\3dplant\3dplant_garden plant_vgpochzia"

class MegascanAsset:
	def __init__(self, directory):
		self.directory = directory

	@property
	def name(self):
		self._name = directory.rsplit("_", 1)[-1]
		return self._name

	@property
	def path(self):
		self._path = self.directory
		return self._path

	@property
	def type(self):
		if "3d\\" in directory:
			self._type = "3dmodel"
		elif "3dplant\\" in directory:
			self._type = "3dplant"
		elif "surface\\" in directory:
			self._type = "surface"
		return self._type


def build_shader(asset, maps):
	shading_group = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=asset.name + "_SG")
	shader = pm.shadingNode("aiStandardSurface", asShader=True, name=asset.name+"_shader")
	place2dTexture = pm.shadingNode("place2dTexture", asUtility=True)

	shader.outColor >> shading_group.surfaceShader

	if "Color" in maps:
		color_node = pm.shadingNode("file", asUtility=True)
		aiColor_node = pm.shadingNode("aiColorCorrect", asUtility=True)
		color_node.fileTextureName.set(maps["Color"])

		place2dTexture.outUV >> color_node.uvCoord
		color_node.outColor >> aiColor_node.input
		aiColor_node.outColor >> shader.baseColor


	if "SpecRoughness" in maps:
		rough_node = pm.shadingNode("file", asUtility=True)
		remap_node = pm.shadingNode("remapValue", asUtility=True)
		rough_node.fileTextureName.set(maps["SpecRoughness"])

		place2dTexture.outUV >> rough_node.uvCoord
		rough_node.outColorR >> remap_node.inputValue
		remap_node.outValue >> shader.specularRoughness


	if "Metalness" in maps:
		metal_node = pm.shadingNode("file", asUtility=True)
		metal_node.fileTextureName.set(maps["Metalness"])

		place2dTexture.outUV >> metal_node.uvCoord
		metal_node.outColorR >> shader.metalness


	if "Normal" in maps:
		normal_node = pm.shadingNode("file", asUtility=True)
		aiNormal_node = pm.shadingNode("aiNormalMap", asUtility=True)
		normal_node.fileTextureName.set(maps["Normal"])

		place2dTexture.outUV >> normal_node.uvCoord
		normal_node.outColor >> aiNormal_node.input
		aiNormal_node.outValue >> shader.normalCamera


	if "Diplace" in maps:
		displace_node = pm.shadingNode("file", asUtility=True)
		dispShader_node = pm.shadingNode("displacementShader", asUtility=True)
		displace_node.fileTextureName.set(maps["Diplace"])

		place2dTexture.outUV >> displace_node.uvCoord
		displace_node.outColorR >> dispShader_node.displacement
		dispShader_node.displacement >> shading_group.displacementShader

	return shading_group


def scan_map(texture,asset_directory):
	for filename in os.listdir(asset_directory):
		if texture in filename and (filename.endswith('.exr') or filename.endswith('.jpg')):
			return asset_directory + "\\" + filename

def cleaned_maps(matching_files):
	# If a map value is empty, delete the map in dict
	for file in [texture for texture, file in matching_files.items() if not file]:
		del matching_files[file]
	return matching_files


def retrieve_maps_3dmodel(asset):
	
	asset_directory = asset.path

	matching_files = {}

	matching_files["Color"] = 			scan_map("_Albedo", asset_directory)
	matching_files["SpecRoughness"] = 	scan_map("_Roughness", asset_directory)
	matching_files["Metalness"] = 		scan_map("_Metalness", asset_directory)
	matching_files["Normal"] = 			scan_map("_Normal", asset_directory)
	matching_files["Diplace"] = 		scan_map("_Displacement", asset_directory)

	return cleaned_maps(matching_files)

def retrieve_maps_3dplant(asset):
	
	asset_directory = asset.path + "\\Textures\\Atlas"

	matching_files = {}

	matching_files["Color"] = 			scan_map("_Albedo", asset_directory)

	return cleaned_maps(matching_files)

def retrieve_maps_surface():
	pass


def retrive_maps(asset):
	if asset.type == "3dmodel":
		maps = retrieve_maps_3dmodel(asset)
		return maps

	if asset.type == "3dplant":
		maps = retrieve_maps_3dplant(asset)
		return maps

	if asset.type == "surface":
		maps = retrieve_maps_surface(asset)
		return maps


def load_object(name, direc, shading_group):
	#get objs in scene before import
	objs_before = set(pm.ls(dag=True, long=True))

	# .fbx files listing
	fbx_files = [f for f in os.listdir(direc) if f.startswith(name) and f.endswith('.fbx')]
	if fbx_files:

		# Import first matching file
		pm.importFile(os.path.join(direc, fbx_files[0]))
		# Get imported objs
		new_objs = set(pm.ls(dag=True, long=True)) - objs_before

		# Rename and assign shader
		for obj in new_objs:
			if pm.objectType(obj) == "transform":
				#pm.rename(obj, name)

				pm.select(obj)
				pm.hyperShade(assign=shading_group)



def run(directory):
	asset = MegascanAsset(directory)
	maps = retrive_maps(asset)
	shading_group = build_shader(asset, maps)

	if asset.type == "3dmodel":
		load_object(asset.name, asset.path, shading_group)

	elif asset.type == "3dplant":
		all_subdir = [d for d in os.listdir(asset.path) if os.path.isdir(os.path.join(asset.path, d))]

		for subdir in all_subdir:
			if subdir.startswith("Var"):
				folderpath = os.path.join(asset.path, subdir)
				load_object("Var",folderpath,shading_group)


run(directory)