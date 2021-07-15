#! usr/bin/python
# -*- coding: ISO-8859-1 -*-
from os import listdir
from os.path import isfile, join, splitext
import json
import os



projectsData ={
    "swarovski_2106":
        {
            "path": "B:\\swarovski_2106",
            "assetsDir": "B:\\swarovski_2106\\asset",
            "assetsDbDir": "B:\\swarovski_2106\\asset\\database",
        }
}

computers ={
"default" : "swarovski_2106",
"SPRINTER-01": "swarovski_2106",
}

def getCurrentProject():
    computer = os.environ['COMPUTERNAME']
    if computer in computers:
        currentProject = computers[computer]
    else:
        currentProject = computers["default"]

    return currentProject

def getProjectData(project):
    data = projectsData.get(project)
    return data

def getCurrentProjectData():
	getCurrentProjectData = getProjectData(getCurrentProject())
	return getCurrentProjectData

def buildAssetDb():
    """
    Look in the database directory and build a dictionary with asset data
    """
    assetsDbDir = getCurrentProjectData()['assetsDbDir']
    assetsList = [asset for asset in listdir(assetsDbDir) if isfile(join(assetsDbDir,asset))]
    assetsDbDic = {}
    for asset in assetsList:
        filepath = join(assetsDbDir,asset)
        with open(filepath) as json_file:
            assetData = json.load(json_file)
        assetName, file_extension = splitext(asset)
        assetsDbDic[assetName]=assetData
    return assetsDbDic
