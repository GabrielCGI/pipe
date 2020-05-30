################################################################
# SpeedTreeImporter.py
#
# *** INTERACTIVE DATA VISUALIZATION (IDV) PROPRIETARY INFORMATION ***
#
# This software is supplied under the terms of a license agreement or
# nondisclosure agreement with Interactive Data Visualization and may
# not be copied or disclosed except in accordance with the terms of
# that agreement.
#
# Copyright (c) 2003-2017 IDV, Inc.
# All Rights Reserved.
# IDV, Inc.
# Web: http://www.speedtree.com


################################################################
# Imports

import maya.cmds as mc
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import xml.dom.minidom as xmldom
import os.path as path
import sys


################################################################
# class SpeedTreeMaterial

class SpeedTreeMap:
	def __init__(self, red = 1.0, green = 1.0, blue = 1.0, file = ""):
		self.red = red
		self.green = green
		self.blue = blue
		self.file = file

class SpeedTreeMaterial:
	def __init__(self, name, twoSided = False, vertexOpacity = False, userData = ""):
		self.shader = None
		self.name = name
		self.twoSided = twoSided
		self.vertexOpacity = vertexOpacity
		self.userData = userData
		self.maps = { }


################################################################
# SpeedTreeImporterTranslatorBase

class SpeedTreeImporterTranslatorBase(OpenMayaMPx.MPxFileTranslator):
	def __init__(self):
		OpenMayaMPx.MPxFileTranslator.__init__(self)
	def haveWriteMethod(self):
		return False
	def haveReadMethod(self):
		return True
	def haveNamespaceSupport(self):
		return True
	def filter(self):
		return "*.stmat"
	def defaultExtension(self):
		return "stmat"
	def writer(self, fileObject, optionString, accessMode):
		pass

	def CreateFileTexture(self, filename, colorManagement = True):
		texFile = mc.shadingNode("file", asTexture = True, isColorManaged = colorManagement)
		if (filename.find("<UDIM>") > -1):
			mc.setAttr(texFile + ".uvTilingMode", 3)
			filename = filename.replace("<UDIM>", "1001")
		mc.setAttr(texFile + ".fileTextureName", filename, type = "string")
		tex2dPlacement = mc.shadingNode("place2dTexture", asUtility = True)
		mc.connectAttr(tex2dPlacement + ".outUV", texFile + ".uvCoord")
		mc.connectAttr(tex2dPlacement + ".outUvFilterSize", texFile + ".uvFilterSize")
		mc.connectAttr(tex2dPlacement + ".vertexCameraOne", texFile + ".vertexCameraOne")
		mc.connectAttr(tex2dPlacement + ".vertexUvThree", texFile + ".vertexUvThree")
		mc.connectAttr(tex2dPlacement + ".vertexUvTwo", texFile + ".vertexUvTwo")
		mc.connectAttr(tex2dPlacement + ".vertexUvOne", texFile + ".vertexUvOne")
		mc.connectAttr(tex2dPlacement + ".repeatV", texFile + ".repeatV")
		mc.connectAttr(tex2dPlacement + ".repeatU", texFile + ".repeatU")
		mc.connectAttr(tex2dPlacement + ".rotateFrame", texFile + ".rotateFrame")
		mc.connectAttr(tex2dPlacement + ".offsetV", texFile + ".offsetV")
		mc.connectAttr(tex2dPlacement + ".offsetU", texFile + ".offsetU")
		mc.setAttr(tex2dPlacement + ".ihi", 0)
		return texFile

	def ConnectMaterial(self, mat, sg):
		if (mc.attributeQuery("outColor", node = mat, exists = True)):
			mc.connectAttr(mat + ".outColor", sg + ".surfaceShader", force = True)
		else:
			mc.connectAttr(mat + '.message', sg + '.miMaterialShader', force = True)
			mc.connectAttr(mat + '.message', sg + '.miShadowShader', force = True)
			mc.connectAttr(mat + '.message', sg + '.miPhotonShader', force = True)

	def reader(self, fileObject, optionString, accessMode):
		try:
			doc = xmldom.parse(fileObject.expandedFullName())
			root = doc.getElementsByTagName('Materials');
			if len(root) > 0:
				# remember materials and shading groups that existed before import
				aBeforeMaterials = mc.ls(mat = True)
				aBeforeSets = mc.ls(sets = True)
				aBeforeObjects = mc.ls(tr = True)

				# load mesh
				meshFile = fileObject.expandedPath() + root[0].attributes["Mesh"].value
				extension = path.splitext(meshFile)[1]
				fileTypes = []
				OpenMaya.MFileIO.getFileTypes(fileTypes)
				blendInTexcoord = 1
				try:
					if (extension == ".abc" and "Alembic" not in fileTypes):
						print "SpeedTree ERROR: Alembic plugin is not loaded"
						raise
					if (extension == ".fbx" and "FBX" not in fileTypes):
						print "SpeedTree ERROR: FBX plugin is not loaded"
						raise

					if (extension == ".abc"):
						mel.eval("AbcImport -mode import -fitTimeRange -rcs \"" + meshFile + "\"")
						blendInTexcoord = 0
					else:
						OpenMaya.MFileIO.importFile(meshFile)

				except:
					print "SpeedTree ERROR: Failed to load mesh file [" + meshFile + "]"
					#print sys.exc_info()
					return None

				try:
					aAfterMaterials = mc.ls(mat = True)
					aAfterSets = mc.ls(sets = True)
					aAfterObjects = mc.ls(tr = True)

					# turn off vertex color display
					for newobj in aAfterObjects:
						if (newobj not in aBeforeObjects):
							mc.select(newobj)
							mc.polyOptions(colorShadedDisplay = False)

					# load speedtree materials
					aNewMaterials = { }
					materials = root[0].getElementsByTagName('Material')
					for material in materials:
						stMaterial = SpeedTreeMaterial(material.attributes["Name"].value,
														material.attributes["TwoSided"].value == "1",
														material.attributes["VertexOpacity"].value == "1",
														material.attributes["UserData"].value)
						maps = material.getElementsByTagName('Map')
						for stmap in maps:
							newmap = SpeedTreeMap()
							if (stmap.attributes.has_key("File")):
								newmap.file = stmap.attributes["File"].value
							elif (stmap.attributes.has_key("Value")):
								newmap.red = newmap.green = newmap.blue = float(stmap.attributes["Value"].value)
							else:
								newmap.red = float(stmap.attributes["ColorR"].value)
								newmap.green = float(stmap.attributes["ColorG"].value)
								newmap.blue = float(stmap.attributes["ColorB"].value)

							stMaterial.maps[stmap.attributes["Name"].value] = newmap
						aNewMaterials[stMaterial.name] = stMaterial

					# hook new materials to the shading engines on the mesh
					for newset in aAfterSets:
						if (newset not in aBeforeSets):
							stMaterialName = None
							# first try shading group name (with or without SG at the end)
							if (aNewMaterials.has_key(newset)):
								stMaterialName = newset
							elif (aNewMaterials.has_key(newset[:-2])):
								stMaterialName = newset[:-2]
							else:
								# if not, try to find a similar material name
								shaderName = newset + ".surfaceShader"
								if (mc.objExists(shaderName)):
									matName = mc.connectionInfo(shaderName, sfd = True).split('.')[0]
									if (aNewMaterials.has_key(matName)):
										stMaterialName = matName

							# make new material and hook it up
							if (stMaterialName != None):
								aShapes = mc.listConnections(newset + ".dagSetMembers")
								newmat = self.CreateMaterial(aNewMaterials[stMaterialName], aShapes, blendInTexcoord)
								aNewMaterials[stMaterialName].shader = newmat
								self.ConnectMaterial(newmat, newset)

					# delete all the new materials since we replaced them
					for mat in aAfterMaterials:
						if (mat not in 	aBeforeMaterials):
							aHistory = mc.listHistory(mat, pruneDagObjects = True)
							mc.delete(aHistory)

					# go back through and attempt to rename the materials
					for mat in aNewMaterials.itervalues():
						if (mat.shader != None):
							mc.rename(mat.shader, mat.name)

				except:
					print "SpeedTree ERROR: Failed to update material connections"
					#print sys.exc_info()

		except:
			print "SpeedTree ERROR: Failed to read SpeedTree stmat file"
			#print sys.exc_info()


################################################################
# SpeedTreeImporterTranslator

class SpeedTreeImporterTranslator(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree"
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		shader = mc.shadingNode("phong", asShader = True)
		mc.setAttr(shader + ".diffuse", 1.0)
		mc.setAttr(shader + ".ambientColor", 0.05, 0.05, 0.05)

		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".color")
			else:
				mc.setAttr(shader + ".color", stmap.red, stmap.green, stmap.blue)

		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				bump2dNode = mc.shadingNode("bump2d", asUtility = True)
				mc.setAttr(bump2dNode + ".bumpInterp", 1)
				mc.connectAttr(textureNode + ".outAlpha", bump2dNode + ".bumpValue")
				mc.connectAttr(bump2dNode + ".outNormal", shader + ".normalCamera")

		# standard maya shader doesn't have a vertex color node! so no branch seam blending
		opacityTexture = None
		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				opacityTexture = self.CreateFileTexture(stmap.file)
				mc.setAttr(opacityTexture + ".colorSpace", "Raw", type="string")
				opacityReverse = mc.shadingNode("reverse", asUtility = True)
				mc.connectAttr(opacityTexture + ".outColor", opacityReverse + ".input")
				mc.connectAttr(opacityReverse + ".output", shader + ".transparency")

		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColorR", shader + ".reflectivity")
				mulNode = mc.shadingNode("multiplyDivide", asUtility = True)
				mc.connectAttr(textureNode + ".outColor", mulNode + ".input1")
				mc.setAttr(mulNode + ".input2", stmap.red * 100, stmap.red * 100, stmap.red * 100)
				mc.connectAttr(mulNode + ".outputX", shader + ".cosinePower")
				if (opacityTexture == None):
					mc.connectAttr(textureNode + ".outColor", shader + ".specularColor")
				else:
					mulNode = mc.shadingNode("multiplyDivide", asUtility = True)
					mc.connectAttr(textureNode + ".outColor", mulNode + ".input1")
					mc.connectAttr(opacityTexture + ".outColor", mulNode + ".input2")
					mc.connectAttr(mulNode + ".output", shader + ".specularColor")
			else:
				mc.setAttr(shader + ".cosinePower", stmap.red * 100)
				mc.setAttr(shader + ".reflectivity", stmap.red)
				if (opacityTexture == None):
					mc.setAttr(shader + ".specularColor", stmap.red, stmap.red, stmap.red)
				else:
					mc.connectAttr(opacityTexture + ".outColor", shader + ".specularColor")
					mulNode = mc.shadingNode("multiplyDivide", asUtility = True)
					mc.connectAttr(opacityTexture + ".outColor", mulNode + ".input1")
					mc.setAttr(mulNode + ".input2", stmap.red, stmap.red, stmap.red)
					mc.connectAttr(mulNode + ".output", shader + ".specularColor")

		return shader


################################################################
# SpeedTreeImporterVRayTranslator

class SpeedTreeImporterVRayTranslator(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree for V-Ray"
	def haveReadMethod(self):
		return mc.pluginInfo("vrayformaya", q = True, l = True) # check to see if vray plugin is available
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		hasSSS = stMaterial.maps.has_key("SubsurfaceAmount")
		shader = mc.shadingNode("VRayMtl", asShader = hasSSS==0, asUtility = hasSSS==1)

		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".color")
			else:
				mc.setAttr(shader + ".color", stmap.red, stmap.green, stmap.blue)

		normalTexture = None;
		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				mc.setAttr(shader + ".bumpMapType", 1)
				normalTexture = self.CreateFileTexture(stmap.file)
				mc.setAttr(normalTexture + ".colorSpace", "Raw", type="string")
				mc.connectAttr(normalTexture + ".outColor", shader + ".bumpMap")

		mc.setAttr(shader + ".opacityMode", 2)
		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColor", shader + ".opacityMap")
		elif (stMaterial.vertexOpacity):
			# use vertex color for branch seam blending
			vertexColor = mc.shadingNode("VRayVertexColors", asTexture = True)
			mc.setAttr(vertexColor + ".type", 1)
			mc.setAttr(vertexColor + ".name", "blend_ao", type = "string")
			mc.setAttr(vertexColor + ".defaultColor", 1.0, 1.0, 1.0)
			mc.setAttr(vertexColor + ".useUVSets", blendInTexcoord)
			mc.connectAttr(vertexColor + ".outColor.outColorR", shader + ".opacityMap.opacityMapR")
			mc.connectAttr(vertexColor + ".outColor.outColorR", shader + ".opacityMap.opacityMapG")
			mc.connectAttr(vertexColor + ".outColor.outColorR", shader + ".opacityMap.opacityMapB")

		mc.setAttr(shader + ".brdfType", 3)
		mc.setAttr(shader + ".reflectionColor", 0.5, 0.5, 0.5)
		mc.setAttr(shader + ".useFresnel", 1)
		mc.setAttr(shader + ".ggxTailFalloff", 5.0)
		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColorR", shader + ".reflectionGlossiness")
				mc.connectAttr(textureNode + ".outColorR", shader + ".refractionGlossiness")
				glossReverse = mc.shadingNode("reverse", asUtility = True)
				mc.connectAttr(textureNode + ".outColor", glossReverse + ".input")
				mc.connectAttr(glossReverse + ".outputX", shader + ".roughnessAmount")
			else:
				mc.setAttr(shader + ".reflectionGlossiness", stmap.red)
				mc.setAttr(shader + ".refractionGlossiness", stmap.red)
				mc.setAttr(shader + ".roughnessAmount", 1.0 - stmap.red)

		if (hasSSS):
			frontShader = shader
			backShader = mc.duplicate(frontShader, ic = True)[0]
			shader = mc.shadingNode("VRayMtl2Sided", asShader = True)
			mc.connectAttr(frontShader + ".outColor", shader + ".frontMaterial")
			mc.connectAttr(backShader + ".outColor", shader + ".backMaterial")

			# flip the normalmap on the back
			if (normalTexture != None):
				normalReverse = mc.shadingNode("reverse", asUtility = True)
				mc.connectAttr(normalTexture + ".outColor", normalReverse + ".input")
				mc.disconnectAttr(normalTexture + ".outColor", backShader + ".bumpMap")
				mc.connectAttr(normalReverse + ".outputX", backShader + ".bumpMapR")
				mc.connectAttr(normalReverse + ".outputY", backShader + ".bumpMapG")
				mc.connectAttr(normalTexture + ".outColorB", backShader + ".bumpMapB")

			stmap1 = stMaterial.maps["SubsurfaceAmount"]
			stmap2 = stMaterial.maps["SubsurfaceColor"]
			if (not stmap1.file and not stmap2.file):
				mc.setAttr(shader + ".translucencyTex", stmap1.red * stmap2.red, stmap1.green * stmap2.green, stmap1.blue * stmap2.blue)
			else:
				mulNode = mc.shadingNode("multiplyDivide", asUtility = True)
				mc.connectAttr(mulNode + ".output", shader + ".translucencyTex")

				if (stmap1.file):
					textureNode = self.CreateFileTexture(stmap1.file)
					mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
					mc.connectAttr(textureNode + '.outColor', mulNode + '.input1')
				else:
					mc.setAttr(mulNode + '.input1', stmap1.red, stmap1.green, stmap1.blue)

				if (stmap2.file):
					textureNode = self.CreateFileTexture(stmap2.file)
					mc.connectAttr(textureNode + '.outColor', mulNode + '.input2')
				else:
					mc.setAttr(mulNode + '.input2', stmap2.red, stmap2.green, stmap2.blue)

		return shader


################################################################
# SpeedTreeImporterMentalRayTranslator

class SpeedTreeImporterMentalRayTranslator(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree for Mental Ray"
	def haveReadMethod(self):
		return mc.pluginInfo("Mayatomr", q = True, l = True) # check to see if mental ray plugin is available
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		shader = mc.shadingNode("mia_material_x", asShader = True)

		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".diffuse")
			else:
				mc.setAttr(shader + ".diffuse", stmap.red, stmap.green, stmap.blue)

		mc.setAttr(shader + ".bump_mode", 3)
		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				bump2dNode = mc.shadingNode("bump2d", asUtility = True)
				mc.setAttr(bump2dNode + ".bumpInterp", 1)
				mc.connectAttr(textureNode + ".outAlpha", bump2dNode + ".bumpValue")
				misSetNormalNode = mc.shadingNode("misss_set_normal", asUtility = True)
				mc.connectAttr(bump2dNode + ".outNormal", misSetNormalNode + ".normal")
				mc.connectAttr(misSetNormalNode + ".outValue", shader + ".overall_bump")

		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				# try to alleviate mental ray blurring the opacity map on glancing angles
				mc.setAttr(textureNode + ".filterType", 0)
				mc.connectAttr(textureNode + ".outColorR", shader + ".cutout_opacity")
		elif (stMaterial.vertexOpacity):
			# use vertex color for branch seam blending
			if (blendInTexcoord):
				uvChooser = mc.shadingNode('uvChooser', n='blend_ao', asUtility = True)
				mc.connectAttr(uvChooser + ".outUv.outU", shader + ".cutout_opacity")
				index = 0
				for shape in aShapes:
					mc.connectAttr(shape + ".uvSet[1].uvSetName", uvChooser + ".uvSets[" + str(index) + "]")
					index += 1
			else:
				vertexColor = mc.shadingNode("mentalrayVertexColors", asUtility = True)
				mc.setAttr(vertexColor + ".defaultColor", 1.0, 1.0, 1.0)
				mc.connectAttr(vertexColor + ".outColorR", shader + ".cutout_opacity")
				index = 0
				for shape in aShapes:
					mc.connectAttr(shape + ".colorSet[0].colorName", vertexColor + ".cpvSets[" + str(index) + "]")
					index += 1

		mc.setAttr(shader + ".brdf_fresnel", 1)
		mc.setAttr(shader + ".refl_color", 1.0, 1.0, 1.0)
		mc.setAttr(shader + ".reflectivity", 0.25)
		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColorR", shader + ".refl_gloss")
				mc.connectAttr(textureNode + ".outColorR", shader + ".refr_gloss")
				glossReverse = mc.shadingNode("reverse", asUtility = True)
				mc.connectAttr(textureNode + ".outColor", glossReverse + ".input")
				mc.connectAttr(glossReverse + ".outputX", shader + ".diffuse_roughness")
			else:
				mc.setAttr(shader + ".diffuse_roughness", 1.0 - stmap.red)
				mc.setAttr(shader + ".refl_gloss", stmap.red)
				mc.setAttr(shader + ".refr_gloss", stmap.red)

		if (stMaterial.maps.has_key("SubsurfaceAmount")):
			stmap = stMaterial.maps["SubsurfaceAmount"]
			mc.setAttr(shader + '.thin_walled', 1)
			mc.setAttr(shader + '.refr_translucency', 1)
			mc.setAttr(shader + '.refr_trans_weight', 1.0)
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + '.outColorR', shader + '.transparency')
			else:
				mc.setAttr(shader + '.transparency', stmap.red)

			stmap = stMaterial.maps["SubsurfaceColor"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + '.outColor', shader + '.refr_color')
				mc.connectAttr(textureNode + '.outColor', shader + '.refr_trans_color')
			else:
				mc.setAttr(shader + '.refr_color', stmap.red, stmap.green, stmap.blue)
				mc.setAttr(shader + '.refr_trans_color', stmap.red, stmap.green, stmap.blue)

		return shader


################################################################
# SpeedTreeImporterRedshiftTranslator

class SpeedTreeImporterRedshiftTranslator(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree for Redshift"
	def haveReadMethod(self):
		return mc.pluginInfo("redshift4maya", q = True, l = True) # check to see if redshift plugin is available
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		shader = mc.shadingNode("RedshiftMaterial", asShader = True)

		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".diffuse_color")
			else:
				mc.setAttr(shader + ".diffuse_color", stmap.red, stmap.green, stmap.blue)

		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				normalNode = mc.shadingNode("RedshiftNormalMap", asTexture = True)
				mc.setAttr(normalNode + ".tex0", stmap.file, type="string")
				mc.connectAttr(normalNode + ".outDisplacementVector", shader + ".bump_input")

		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColor", shader + ".opacity_color")
		elif (stMaterial.vertexOpacity):
			# use vertex color for branch seam blending
			vertexColor = mc.shadingNode("RedshiftVertexColor", asTexture = True)
			mc.setAttr(vertexColor + ".vertexSet", "blend_ao", type = "string")
			mc.setAttr(vertexColor + ".defaultColor", 1.0, 1.0, 1.0)
			mc.connectAttr(vertexColor + ".outColor.outColorR", shader + ".opacity_colorR")
			mc.connectAttr(vertexColor + ".outColor.outColorR", shader + ".opacity_colorG")
			mc.connectAttr(vertexColor + ".outColor.outColorR", shader + ".opacity_colorB")

		mc.setAttr(shader + ".refl_brdf", 1)
		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				roughness = mc.shadingNode("reverse", asUtility = True)
				mc.connectAttr(textureNode + ".outColor", roughness + ".input")
				mc.connectAttr(roughness + ".outputX", shader + ".diffuse_roughness")
				mc.connectAttr(roughness + ".outputX", shader + ".refl_roughness")
				mc.connectAttr(roughness + ".outputX", shader + ".refr_roughness")
			else:
				mc.setAttr(shader + ".diffuse_roughness", 1.0 - stmap.red)
				mc.setAttr(shader + ".refl_roughness", 1.0 - stmap.red)
				mc.setAttr(shader + ".refr_roughness", 1.0 - stmap.red)

		if (stMaterial.maps.has_key("SubsurfaceAmount")):
			stmap = stMaterial.maps["SubsurfaceAmount"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + '.outColorR', shader + '.transl_weight')
			else:
				mc.setAttr(shader + '.transl_weight', stmap.red)
			stmap = stMaterial.maps["SubsurfaceColor"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + '.outColor', shader + '.transl_color')
			else:
				mc.setAttr(shader + '.transl_color', stmap.red, stmap.green, stmap.blue)

		return shader

################################################################
# SpeedTreeImporterArnoldTranslator5

class SpeedTreeImporterArnoldTranslator5(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree for Arnold 5"
	def haveReadMethod(self):
		return mc.pluginInfo("mtoa", q = True, l = True) # check to see if arnold 5 plugin is available
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		shader = mc.shadingNode("aiStandardSurface", asShader = True)

		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".baseColor")
			else:
				mc.setAttr(shader + ".baseColor", stmap.red, stmap.green, stmap.blue)

		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				bump2dNode = mc.shadingNode("bump2d", asUtility = True)
				mc.setAttr(bump2dNode + ".bumpInterp", 1)
				mc.setAttr(bump2dNode + '.aiFlipR', 0)
				mc.setAttr(bump2dNode + '.aiFlipG', 0)
				mc.setAttr(bump2dNode + '.aiUseDerivatives', 0)
				mc.connectAttr(textureNode + ".outAlpha", bump2dNode + ".bumpValue")
				mc.connectAttr(bump2dNode + ".outNormal", shader + ".normalCamera")

		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColor", shader + ".opacity")
				for shape in aShapes:
					mc.setAttr(shape + ".aiOpaque", 0)

		mc.setAttr(shader + ".specularIOR", 1.333)
		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				roughness = mc.shadingNode("multiplyDivide", asUtility = True)
				mc.setAttr(roughness + ".operation", 1)
				mc.setAttr(roughness + ".input2", 1.5, 1.5, 1.5)
				mc.connectAttr(textureNode + ".outColor", roughness + ".input1")
				mc.connectAttr(roughness + ".outputX", shader + ".specularRoughness")

			else:
				mc.setAttr(shader + ".specularRoughness", 1 - stmap.red)

		if (stMaterial.maps.has_key("SubsurfaceAmount")):
			stmap = stMaterial.maps["SubsurfaceAmount"]
			mc.setAttr(shader + '.thinWalled', 1)
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + '.outColorR', shader + '.subsurface')
			else:
				mc.setAttr(shader + '.subsurface', stmap.red)
			stmap = stMaterial.maps["SubsurfaceColor"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + '.outColor', shader + '.subsurfaceColor')
			else:
				mc.setAttr(shader + '.subsurfaceColor', stmap.red, stmap.green, stmap.blue)

		return shader

################################################################
# SpeedTreeImporterArnoldTranslator

class SpeedTreeImporterArnoldTranslator(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree for Arnold"
	def haveReadMethod(self):
		return mc.pluginInfo("mtoa", q = True, l = True) # check to see if arnold plugin is available
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		shader = mc.shadingNode("aiStandard", asShader = True)

		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".color")
			else:
				mc.setAttr(shader + ".Color", stmap.red, stmap.green, stmap.blue)

		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				bump2dNode = mc.shadingNode("bump2d", asUtility = True)
				mc.setAttr(bump2dNode + ".bumpInterp", 1)
				mc.setAttr(bump2dNode + '.aiFlipR', 0)
				mc.setAttr(bump2dNode + '.aiFlipG', 0)
				mc.setAttr(bump2dNode + '.aiUseDerivatives', 0)
				mc.connectAttr(textureNode + ".outAlpha", bump2dNode + ".bumpValue")
				mc.connectAttr(bump2dNode + ".outNormal", shader + ".normalCamera")

		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColor", shader + ".opacity")
				for shape in aShapes:
					mc.setAttr(shape + ".aiOpaque", 0)

		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				roughness = mc.shadingNode("multiplyDivide", asUtility = True)
				mc.setAttr(roughness + ".operation", 1)
				mc.setAttr(roughness + ".input2", 0.8, 0.8, 0.8)
				mc.connectAttr(textureNode + ".outColor", roughness + ".input1")
				mc.connectAttr(roughness + ".outputX", shader + ".specularRoughness")
				mc.connectAttr(textureNode + ".outputX", shader + ".specularWeight")

			else:
				mc.setAttr(shader + ".specularRoughness", 1 - stmap.red)

		if (stMaterial.maps.has_key("SubsurfaceAmount")):
			stmap = stMaterial.maps["SubsurfaceAmount"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + '.outColorR', shader + '.Ksss')
			else:
				mc.setAttr(shader + '.Ksss', stmap.red)
			stmap = stMaterial.maps["SubsurfaceColor"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + '.outColor', shader + '.KsssColor')
			else:
				mc.setAttr(shader + '.KsssColor', stmap.red, stmap.green, stmap.blue)

		return shader

################################################################
# SpeedTreeImporterRendermanTranslator

class SpeedTreeImporterRendermanTranslator(SpeedTreeImporterTranslatorBase):
	description = "SpeedTree for Renderman"
	def haveReadMethod(self):
		return mc.pluginInfo("RenderMan_for_Maya", q = True, l = True) # check to see if renderman plugin is available
	def CreateMaterial(self, stMaterial, aShapes, blendInTexcoord):
		shader = mc.shadingNode("PxrSurface", asShader = True)

		mc.setAttr(shader + ".diffuseDoubleSided", 1)
		if (stMaterial.maps.has_key("Color")):
			stmap = stMaterial.maps["Color"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + ".outColor", shader + ".diffuseColor")
			else:
				mc.setAttr(shader + ".diffuseColor", stmap.red, stmap.green, stmap.blue)

		if (stMaterial.maps.has_key("Normal")):
			stmap = stMaterial.maps["Normal"]
			if (stmap.file):
				normalNode = mc.shadingNode("PxrNormalMap", asUtility = True)
				if (stmap.file.find("<UDIM>") > -1):
					mc.setAttr(normalNode + ".filename", stmap.file.replace("<UDIM>", "_MAPID_"), type = "string")
					mc.setAttr(normalNode + ".atlasStyle", 1)
				else:
					mc.setAttr(normalNode + ".filename", stmap.file, type = "string")
				mc.setAttr(normalNode + ".flipY", 1)
				mc.connectAttr(normalNode + ".resultN", shader + ".bumpNormal")

		if (stMaterial.maps.has_key("Opacity")):
			stmap = stMaterial.maps["Opacity"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + ".outColorR", shader + ".presence")

		mc.setAttr(shader + ".specularDoubleSided", stMaterial.twoSided)
		mc.setAttr(shader + ".roughSpecularDoubleSided", stMaterial.twoSided)
		mc.setAttr(shader + ".specularEdgeColor", 1, 1, 1)
		mc.setAttr(shader + ".specularFresnelMode", 1)
		mc.setAttr(shader + ".specularModelType", 1)
		if (stMaterial.maps.has_key("Gloss")):
			stmap = stMaterial.maps["Gloss"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				roughness = mc.shadingNode("reverse", asUtility = True)
				mc.connectAttr(textureNode + ".outColor", roughness + ".input")
				mc.connectAttr(roughness + ".outputX", shader + ".diffuseRoughness")
				mc.connectAttr(roughness + ".outputX", shader + ".specularRoughness")
			else:
				mc.setAttr(shader + ".diffuseRoughness", 1.0 - stmap.red)
				mc.setAttr(shader + ".specularRoughness", 1.0 - stmap.red)

		if (stMaterial.maps.has_key("SubsurfaceAmount")):
			stmap = stMaterial.maps["SubsurfaceAmount"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.setAttr(textureNode + ".colorSpace", "Raw", type="string")
				mc.connectAttr(textureNode + '.outColorR', shader + '.diffuseTransmitGain')
			else:
				mc.setAttr(shader + '.diffuseTransmitGain', stmap.red)
			stmap = stMaterial.maps["SubsurfaceColor"]
			if (stmap.file):
				textureNode = self.CreateFileTexture(stmap.file)
				mc.connectAttr(textureNode + '.outColor', shader + '.diffuseTransmitColor')
			else:
				mc.setAttr(shader + '.diffuseTransmitColor', stmap.red, stmap.green, stmap.blue)

		return shader

################################################################
# initializePlugin

def initializePlugin(mObject):
	mPlugin = OpenMayaMPx.MFnPlugin(mObject, "SpeedTree", "8.0", "Any")
	for subclass in SpeedTreeImporterTranslatorBase.__subclasses__():
		mPlugin.registerFileTranslator(subclass.description, None, lambda:OpenMayaMPx.asMPxPtr(subclass( )), None, None, True)


################################################################
# uninitializePlugin

def uninitializePlugin(mObject):
	mPlugin = OpenMayaMPx.MFnPlugin(mObject)
	for subclass in SpeedTreeImporterTranslatorBase.__subclasses__():
		mPlugin.deregisterFileTranslator(subclass.description)

