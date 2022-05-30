#! usr/bin/python
# -*- coding: ISO-8859-1 -*-
from os import listdir
from os.path import isfile, join, splitext
import json
import os

defaultProject="trashtown_2112"

projectsData ={
    "trashtown_2112":
        {
            "path": "B:\\trashtown_2112",
            "assetsDir": "B:\\trashtown_2112\\assets",
            "assetsDbDir": "B:\\trashtown_2112\\database",
        },
    "swarovski_2205":
        {
            "path": "I:\\swarovski_2205",
            "assetsDir": "I:\\swarovski_2205\\assets",
            "assetsDbDir": "I:\\swarovski_2205\\assets\\database",
        },
    "candyUp_partage":
        {
            "path": "I:\\candyUp_partage",
            "assetsDir": "I:\\candyUp_partage\\assets",
            "assetsDbDir": "I:\\candyUp_partage\\assets\\database",
        },

    "roger":
        {
            "path": "I:\\roger_2112",
            "assetsDir": "I:\\roger_2112\\assets",
            "assetsDbDir": "I:\\roger_2112\\assets\\database",
        }
}



def getCurrentProject():
    project = os.getenv("CURRENT_PROJECT")
    #computer = os.environ['COMPUTERNAME']
    if project in projectsData.keys():
        currentProject = project
    else:
        currentProject = defaultProject
    print("CURRENT PROJECT: %s"%(currentProject))
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
