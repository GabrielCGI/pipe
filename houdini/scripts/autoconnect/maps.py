
import re
import ressource
import os
import houdinilog as hlog
from collections import defaultdict


def loadRessource():
    if not ressource.LOADED:
        ressource.load()

def firstKeyWord(path):
    lowpath = path.lower()
    
    loadRessource()
    for map in ressource.MAPS_TAG.items():
        for keyword in map[1]:
            if keyword in lowpath:
                return re.search(keyword, lowpath).span()
    return None

def getVersions(path):
    return re.search("v\d{4}", path).group(0)[1:]
            
class Maps:
    
    def __init__(self, path):
        self.path = path
        self.name = None
        self.maps_type = None
        self.signature = None
        
    def isEqual(self, maps):
        return (self.maps_type == maps.maps_type and
                self.signature == maps.signature)
        
    def parseMaps(self) -> bool:
        lowpath = self.path.lower()
        loadRessource()
        for map in ressource.MAPS_TAG.items():
            for keyword in map[1]:
                if keyword in lowpath:
                    self.maps_type = map[0]
                    return True
        return False

    def parseSignature(self) -> bool:
        lowpath = self.path.lower()
        loadRessource()
        for type in ressource.SIGNATURE.items():
            for keyword in type[1]:
                if keyword in lowpath:
                    self.signature = type[0]
                    return True
        return False
    
    def parseUdim(self) -> bool:
        path = os.path.splitext(self.path)
        udim = re.search("\d{4}$", path[0]).group(0)
        if udim is None:
            self.path = path[0] + "<UDIM>" + path[1]
            return False
        else:
            self.path = re.sub("\d{4}$", "<UDIM>", path[0]) + path[1]
            return True 
        
    def parse(self):
        
        if not self.parseMaps():
            return False
        if not self.parseSignature():
            return False
        self.parseUdim()
        self.name = os.path.splitext(os.path.splitext(os.path.split(self.path)[1])[0])[0]
        
        return True
            
class Shader:
    
    def __init__(self, name):
        self.name = name
        self.maps = []
        
    def existMaps(self, mat):
        for maps in self.maps:
            if maps.isEqual(mat):
                return maps
        return None
        
    def parse(self, maps_path):
        
        maps = Maps(maps_path)
        
        if maps.parse():
            mat = self.existMaps(maps)
            if mat is not None:
                if getVersions(mat.path) < getVersions(maps.path):
                    mat.path = maps.path
            else:
                self.maps.append(maps)
                return True
        return False