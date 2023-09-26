import os
import pymel.core as pm
print("haaaa")
class MegascanAsset:
	def __init__(self, directory):
		self.directory = directory

	@property
	def name(self):
		self._name = self.directory.rsplit("_", 1)[-1]
		return self._name

	@property
	def path(self):
		self._path = self.directory
		return self._path

	@property
	def type(self):
		if "3d\\" in self.directory:
			self._type = "3dmodel"
		elif "3dplant\\" in self.directory:
			self._type = "3dplant"
		elif "surface\\" in self.directory:
			self._type = "surface"
		return self._type


def build_shader_3dmodel(asset, maps):
	shading_group = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=asset.name + "_SG")
	shader = pm.shadingNode("aiStandardSurface", asShader=True, name=asset.name+"_shader")
	place2dTexture = pm.shadingNode("place2dTexture", asUtility=True)

	shader.outColor >> shading_group.surfaceShader

	if "Color" in maps:
		color_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_Color")
		aiColor_node = pm.shadingNode("aiColorCorrect", asUtility=True, name=asset.name + "_aiColor")
		color_node.fileTextureName.set(maps["Color"])

		place2dTexture.outUV >> color_node.uvCoord
		color_node.outColor >> aiColor_node.input
		aiColor_node.outColor >> shader.baseColor

		pm.setAttr(aiColor_node + ".exposure", 0.5)


	if "Roughness" in maps:
		rough_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_rough")
		remap_node = pm.shadingNode("remapValue", asUtility=True, name=asset.name + "_remap")
		rough_node.fileTextureName.set(maps["Roughness"])

		place2dTexture.outUV >> rough_node.uvCoord
		rough_node.outColorR >> remap_node.inputValue
		remap_node.outValue >> shader.specularRoughness


	if "Metalness" in maps:
		metal_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_metal")
		metal_node.fileTextureName.set(maps["Metalness"])

		place2dTexture.outUV >> metal_node.uvCoord
		metal_node.outColorR >> shader.metalness


	if "Normal" in maps:
		normal_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_normal")
		aiNormal_node = pm.shadingNode("aiNormalMap", asUtility=True, name=asset.name + "_aiNormal")
		normal_node.fileTextureName.set(maps["Normal"])

		place2dTexture.outUV >> normal_node.uvCoord
		normal_node.outColor >> aiNormal_node.input
		aiNormal_node.outValue >> shader.normalCamera


	if "Diplace" in maps:
		displace_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_displace")
		dispShader_node = pm.shadingNode("displacementShader", asUtility=True, name=asset.name + "_dispShader")
		displace_node.fileTextureName.set(maps["Diplace"])

		pm.setAttr(dispShader_node + ".scale", 0.5)

		place2dTexture.outUV >> displace_node.uvCoord
		displace_node.outColorR >> dispShader_node.displacement
		dispShader_node.displacement >> shading_group.displacementShader

	return shading_group

def build_shader_3dplant(asset, maps):
	shading_group = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=asset.name + "_SG")
	shader = pm.shadingNode("standardSurface", asShader=True, name=asset.name+"_shader")
	place2dTexture = pm.shadingNode("place2dTexture", asUtility=True)

	pm.setAttr(shader + ".thinWalled", 1)
	pm.setAttr(shader + ".subsurface", 0.5)

	shader.outColor >> shading_group.surfaceShader

	if "Color" in maps:
		color_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_color")
		aiColor_node = pm.shadingNode("aiColorCorrect", asUtility=True, name=asset.name + "_aiColor")
		color_node.fileTextureName.set(maps["Color"])

		place2dTexture.outUV >> color_node.uvCoord
		color_node.outColor >> aiColor_node.input
		aiColor_node.outColor >> shader.baseColor
		
		pm.setAttr(aiColor_node + ".exposure", 0.5)
		

	if "Roughness" in maps:
		rough_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_rough")
		range_node = pm.shadingNode("aiRange", asUtility=True, name=asset.name + "_range")
		rough_node.fileTextureName.set(maps["Roughness"])

		place2dTexture.outUV >> rough_node.uvCoord
		rough_node.outColor >> range_node.input
		range_node.outColorR >> shader.specularRoughness


	if "Translucency" in maps:
		trans_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_trans")
		aiTrans_node = pm.shadingNode("aiAdd", asUtility=True, name=asset.name + "_aiTrans")
		trans_node.fileTextureName.set(maps["Translucency"])

		place2dTexture.outUV >> trans_node.uvCoord
		color_node.outColor >> aiTrans_node.input1
		trans_node.outColor >> aiTrans_node.input2
		aiTrans_node.outColor >> shader.subsurfaceColor


	if "Opacity" in maps:
		opac_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_opac")
		opac_node.fileTextureName.set(maps["Opacity"])

		place2dTexture.outUV >> opac_node.uvCoord
		opac_node.outColor >> shader.opacity


	if "Normal" in maps:
		normal_node = pm.shadingNode("file", asUtility=True, name=asset.name + "_normal")
		aiNormal_node = pm.shadingNode("aiNormalMap", asUtility=True, name=asset.name + "_aiNormal")
		normal_node.fileTextureName.set(maps["Normal"])

		place2dTexture.outUV >> normal_node.uvCoord
		normal_node.outColor >> aiNormal_node.input
		aiNormal_node.outValue >> shader.normalCamera

	return shading_group


def scan_map(texture,asset_directory):
	for filename in os.listdir(asset_directory):
		if texture in filename and (filename.endswith('.exr') or filename.endswith('.jpg')):
			return asset_directory + "\\" + filename

def clean_empty_value(matching_files):
	# If a map value is empty, delete the map in dict
	for file in [texture for texture, file in matching_files.items() if not file]:
		del matching_files[file]
	return matching_files


def retrieve_maps(asset):
	
	asset_directory = asset.path

	matching_files = {}

	matching_files["Color"] = 			scan_map("_Albedo", asset_directory)
	matching_files["Roughness"] = 		scan_map("_Roughness", asset_directory)
	matching_files["Metalness"] = 		scan_map("_Metalness", asset_directory)
	matching_files["Normal"] = 			scan_map("_Normal", asset_directory)
	matching_files["Diplace"] = 		scan_map("_Displacement", asset_directory)

	return clean_empty_value(matching_files)

def retrieve_maps_3dplant(asset):
	
	asset_directory = asset.path + "\\Textures\\Atlas"

	matching_files = {}

	matching_files["Color"] = 			scan_map("_Albedo", asset_directory)
	matching_files["Roughness"] = 		scan_map("_Roughness", asset_directory)
	matching_files["Translucency"] = 	scan_map("_Translucency", asset_directory)
	matching_files["Opacity"] = 		scan_map("_Opacity", asset_directory)
	matching_files["Normal"] = 			scan_map("_Normal", asset_directory)

	return clean_empty_value(matching_files)


def load_object(pattern, direc, shading_group, new_name=None):
	objs_before = set(pm.ls(dag=True, long=True))
	fbx_files = [f for f in os.listdir(direc) if f.startswith(pattern) and f.endswith('.fbx')]

	if fbx_files:
		pm.importFile(os.path.join(direc, fbx_files[0]))
	new_objs = set(pm.ls(dag=True, long=True)) - objs_before

	for obj in new_objs:
		if pm.objectType(obj) == "transform":
			pm.rename(obj, new_name if new_name else pattern+"1")
			pm.select(obj)
			pm.hyperShade(assign=shading_group)

			shape = pm.listRelatives(obj, shapes=True)[0]
			pm.setAttr(shape + ".aiSubdivType", 1)
			pm.setAttr(shape + ".aiSubdivIterations", 2)



def shading_process(asset):
	if asset.type == "3dmodel":
		maps = retrieve_maps(asset)
		shading_group = build_shader_3dmodel(asset, maps)

		load_object(asset.name, asset.path, shading_group, new_name=asset.name)

	if asset.type == "3dplant":
		maps = retrieve_maps_3dplant(asset)
		shading_group = build_shader_3dplant(asset, maps)

		all_subdir = os.listdir(asset.path)
		for subdir in all_subdir:
			if subdir.startswith("Var"):
				folderpath = os.path.join(asset.path, subdir)
				load_object("Var",folderpath,shading_group, new_name=asset.name)

	if asset.type == "surface":
		maps = retrieve_maps(asset)
		shading_group = build_shader_3dmodel(asset, maps)



def run_loader(directory):
	directory = directory.replace("/", "\\")
	print(directory)
	asset = MegascanAsset(directory)
	shading_process(asset)