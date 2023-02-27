#! usr/bin/python
# -*- coding: ISO-8859-1 -*-
from os import listdir
from os.path import isfile, join, splitext
import json
import os

defaultProject="trashtown_2112"

projectsData ={
    "battlestar_2206":
        {
            "path": "I:\\battlestar_2206",
            "assetsDir": "I:\\battlestar_2206\\assets",
            "assetsDbDir": "I:\\battlestar_2206\\assets\\_database",
        },
    "trashtown_2112":
        {
            "path": "B:\\trashtown_2112",
            "assetsDir": "B:\\trashtown_2112\\assets",
            "assetsDbDir": "B:\\trashtown_2112\\assets\\_database",
        },
    "swarovski_2205":
        {
            "path": "I:\\swarovski_2205",
            "assetsDir": "I:\\swarovski_2205\\assets",
            "assetsDbDir": "I:\\swarovski_2205\\assets\\database",
        },
    "guerlain_2206":
        {
            "path": "I:\\guerlain_2206",
            "assetsDir": "I:\\guerlain_2206\\assets",
            "assetsDbDir": "I:\\guerlain_2206\\assets\\database",
        },

    "swaRedSwan_2209":
        {
            "path": "I:\\swaRedSwan_2209",
            "assetsDir": "I:\\swaRedSwan_2209\\assets",
            "assetsDbDir": "I:\\swaRedSwan_2209\\assets\\database",
        }
}



def getCurrentProject():
    project = os.getenv("CURRENT_PROJECT")
    project =project.split("/")[-1]

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
