import re
import os

from . import ressource as ressource

VERSION_PATTERN = r"v\d{3,9}"
UDIM_PATTERN = r"\d{4}$"

def loadRessource():
    if not ressource.LOADED:
        ressource.load()

def firstKeyWord(path):
    name = os.path.splitext(os.path.splitext(os.path.split(path)[1])[0])[0]
    lowpath = name.lower()
    lowpath:str = os.path.splitext(lowpath)[0]
    
    loadRessource()
    for map in ressource.MAPS_TAG.items():
        for keyword in map[1]['keywords']:
            keyword_match = re.search(f"_{keyword}(\.|_|$)", lowpath)
            if keyword_match:
                return re.search(keyword, lowpath).span()
    return None

def getVersions(path):
    match = re.search(VERSION_PATTERN, path)
    
    if match is None:
        return False
    
    if len(match.group(0)):
        return match.group(0)[1:]
    
    return False 
          
class Map:
    
    def __init__(self, path):
        self.path = path
        self.name = None
        self.maps_type = None
        self.signature = None
        
    def __eq__(self, maps):
        return (self.maps_type == maps.maps_type and
                self.signature == maps.signature)
        
    def parseMaps(self) -> bool:
        lowpath:str = self.name.lower()
        lowpath:str = os.path.splitext(lowpath)[0]
        loadRessource()
        for map in ressource.MAPS_TAG.items():
            for keyword in map[1]['keywords']:
                keyword_match = re.search(f"_{keyword}(\.|_|$)", lowpath)
                if keyword_match:
                    self.maps_type = map[0]
                    self.signature = map[1]['signature']
                    return True
        return False
    
    def parseUdim(self) -> bool:
        path = os.path.splitext(self.path)
        udim = re.search(UDIM_PATTERN, path[0])
        if udim is None:
            self.path = path[0] + ".<UDIM>" + path[1]
            return False
        else:
            self.path = re.sub(UDIM_PATTERN, "<UDIM>", path[0]) + path[1]
            return True 
        
    def parse(self):
        
        self.name = os.path.splitext(os.path.splitext(os.path.split(self.path)[1])[0])[0]
        if not self.parseMaps():
            return False
        self.parseUdim()
        self.path = self.path.replace(os.sep, '/')

        return True
  
class VersionMap(Map):
    
    def __init__(self, path):
        super().__init__(path)
        self.version = None
        
    def parseVersion(self):
        self.version = getVersions(self.path)
        
    def parse(self):
    
        self.name = os.path.splitext(os.path.splitext(os.path.split(self.path)[1])[0])[0]
        if not self.parseMaps():
            return False
        
        self.parseVersion()
        self.parseUdim()
        self.path = self.path.replace(os.sep, '/')
        return True
          

    
