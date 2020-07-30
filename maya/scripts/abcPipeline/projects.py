#! usr/bin/python
# -*- coding: ISO-8859-1 -*-
from os import listdir
from os.path import isfile, join, splitext
import json
import os

the_path = "W:\\Drive partagés\\paradise_2005".decode('utf-8').encode('cp1252')
print the_path
# FIX AN ISSUE WITH ACCENT
if os.path.exists(the_path):

    projectsData ={
        "paradise_2005":
        {
            "path": "W:\\paradise_2005",
            "assetsDir": "W:\\paradise_2005\\assets",
    	    "assetsDbDir": os.path.join(the_path, "assets\\database")
        }
    }
elif os.path.exists("W:\Shared drives\paradise_2005"):

    projectsData ={
        "paradise_2005":
        {
            "path": "W:\\paradise_2005",
            "assetsDir": "W:\\paradise_2005\\assets",
    	    "assetsDbDir": "W:\\Shared Drives\\paradise_2005\\assets\\database"
        }
    }
else:
    pass
computers ={
"default" : "paradise_2005",
"SPRINTER-01": "paradise_2005",
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
