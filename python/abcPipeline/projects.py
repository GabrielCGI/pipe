from os import listdir
from os.path import isfile, join, splitext
import json
import os

projectsData ={
    "Teaser":
    {
        "path": "B:\\Teaser",
        "assetsDir": "B:\\Teaser\\assets",
	    "assetsDbDir": "B:\\Teaser\\assets\\database"
    },
    "nutro_1909":
    {
        "path": "B:\\nutro_1909",
        "assetsDir": "B:\\nutro_1909\\assets",
	    "assetsDbDir": "B:\\nutro_1909\\assets\\database"
    },
    "dacia_1909":
    {
        "path": "B:\\dacia_1909",
        "assetsDir": "B:\\dacia_1909\\assets",
	    "assetsDbDir": "B:\\dacia_1909\\assets\\database"
    },
    "badRats":
    {
        "path": "B:\\badRats",
        "assetsDir": "B:\\badRats\\assets",
	    "assetsDbDir": "B:\\badRats\\assets\\database"
    }
}

computers ={
"default" : "nutro_1909",
"SPRINTER-01": "nutro_1909",
"SPRINTER-02": "nutro_1909",
"SPRINTER-03": "nutro_1909",
"SPRINTER-04": "nutro_1909",
"SPRINTER-05": "nutro_1909",
}

def getCurrentProject():
    computer = os.environ['COMPUTERNAME']
    if computer in computers:
        currentProject = computers[computer]
    else:
        currentProject = computers["default"]
    print currentProject
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
