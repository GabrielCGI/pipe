import os
import pymel.core as pm
import importlib
import logging
import re
import projects as projects



currentProject = projects.getCurrentProject()
projectsData = projects.getProjectData(currentProject)
assetsDir = projectsData.get("assetsDir")
assetsDic = projects.buildAssetDb()   #Get dictionnary of all asset for th current project


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def swap_namespace(geo,newNamespace):
	oldNamespace = geo.split(":")[0]
	geo = geo.replace(oldNamespace, newNamespace)
	return geo


class Char():
	def __init__(self, name, namespace):
		self.name = name
		self.ns =  namespace
		self.version = self.getVersion(namespace)
		self.geos = self.list_geo(name, namespace)
		self.is_valid =  self.check_is_valid(self.geos)

	def getVersion(self, namespace):
		for i in range(-3,-0):
			end =  namespace[i:]
			if end.isdigit(): return end.zfill(2)
		return "00"

	def check_is_valid(self, geos):
		if not geos:
			logger.debug("No geo found on %s_%s"%(self.name,self.version))
			return False
		for geo in geos:
			if len(pm.ls(geo))>1:
				logger.error("More than one object matches name: %s"%geo)
				return False
		return True

	def list_geo(self, name, namespace):
		geos = assetsDic[name]["geo"]
		newgeos = [swap_namespace(g, namespace) for g in geos if pm.objExists(swap_namespace(g, namespace))]
		return newgeos

def list_char_in_scene():
	char_list=[]
	namespaces = pm.namespaceInfo(listOnlyNamespaces=True, recurse=True)
	for ns in namespaces:
		for name in assetsDic.keys():
			match = False
			if name+"_" in ns and "rigging" in ns :
				match = True
				break

		if match == True:
			char = Char(name, ns)
			if char.is_valid:
				char_list.append(char)
	return char_list

def exportAbc(char, export_dir, start, end):
	abc_name= char.name+"_"+char.version
	path =  os.path.join(export_dir, abc_name+".abc")
	path = path.replace("\\","/")

	command = ""
	command += "-frameRange %s %s"%(start, end)
	command += " -writeVisibility  -stripNamespaces  -worldSpace -dataFormat ogawa -eulerFilter "
	if not char.geos:
		logger.error("Fail to export %s_%s"%(char.name,char.version))
		logger.error("Geo list empty %s"%char.geos)
		return
	for geo in char.geos:
		command += " -root %s"%geo

	command += " -file \"%s\""%(path)
	logger.info("Start export on: %s"%char.ns)
	logger.info(command)
	pm.refresh(suspend=True)
	pm.AbcExport(j= command)
	pm.refresh(suspend=False)
	logger.info("Succes !")

char_list = list_char_in_scene()
