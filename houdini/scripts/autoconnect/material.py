
import re
import os
from collections import defaultdict

materials = defaultdict(list)
type = defaultdict(list)

materials = {
    "BaseColor" : ["basecolor"],
    "Roughness" : ["roughness"],
    "Metallic" : ["metallic"],
    "Height" : ["height"],
    "Normal" : ["normal"]
}

data_types = {
    "Raw" : ["raw"],
    "ACEScg" : ["acescg"],
    "Normal_Raw" : ["normal_raw"]
}
    
def firstKeyWord(path):
    lowpath = path.lower()
    for material in materials.items():
        for keyword in material[1]:
            if keyword in lowpath:
                return re.search(keyword, lowpath).span()
    return None
            
class Material:
    
    def __init__(self, path):
        self.path = path
        self.material_type = None
        self.data_type = None
        self.udim = None
        
    def parseMaterial(self) -> bool:
        lowpath = self.path.lower()
        for material in materials.items():
            for keyword in material[1]:
                if keyword in lowpath:
                    self.material_type = material[0]
                    return True
        return False

    def parseDataType(self) -> bool:
        lowpath = self.path.lower()
        for type in data_types.items():
            for keyword in type[1]:
                if keyword in lowpath:
                    self.data_type = type[0]
                    return True
        return False
    
    def parseUdim(self) -> bool:
        path = os.path.splitext(self.path)[0]
        self.udim = re.search("\d{4}$", path).group(0)
        if self.udim is None:
            return False
        else:
            return True 
        
    def parse(self):
        
        if not self.parseMaterial():
            return False
        if not self.parseDataType():
            return False
        if not self.parseUdim():
            return False
        
        return True
            
class Shader:
    
    def __init__(self, name):
        self.name = name
        self.materials = []
        
    def __eq__(self, name):
        self.name = name
        
    def existMaterial(self, mat_type):
        for material in self.materials:
            if mat_type == material.material_type:
                return material
        return None
        
    def parse(self, material_path):
        
        material = Material(material_path)
        
        if material.parse():
            mat = self.existMaterial(material.material_type)
            if mat is not None:
                version = re.search("v\d{4}", mat.path)
                print(version.group(0))
                print(mat.path)
            else:
                self.materials.append(material)
                return True
        return False