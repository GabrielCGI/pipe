
from . import map as mp

class Shader:
    
    def __init__(self, name):
        self.name = name
        self.maps = []
        self.selected_maps = []
        
    def existMaps(self, mat):
        for maps in self.maps:
            if maps == mat:
                return maps
        return None
        
    def parse(self, maps_path):
        
        maps = mp.Map(maps_path)
        
        if maps.parse():
            mat = self.existMaps(maps)
            
            # Take the last map parsed
            if mat is not None:
                mat.path = maps.path
            else:
                self.maps.append(maps)
            return True
        return False

class VersionShader(Shader):
    
    def __init__(self, name):
        super().__init__(name)
        self.allVersionsMaps = {}
        
    def existMaps(self, mat):
        for map_name, _ in self.allVersionsMaps.items():
            if map_name == mat.name:
                return map_name
        return None
        
    def parse(self, maps_path):
        
        maps = mp.VersionMap(maps_path)
        
        if maps.parse():
            mat: str = self.existMaps(maps)
            
            # If the map already exists 
            # with a different version
            if mat is not None:
                is_new_version = True
                for map in self.allVersionsMaps[mat]:
                    if map.version == maps.version:
                        is_new_version = False
                if is_new_version:
                    self.allVersionsMaps[mat].append(maps)
                else:
                    return False
            else:
                self.allVersionsMaps[maps.name] = [maps]
            return True
        
        return False
    
    def setLatestMap(self):
        self.maps.clear()
        
        for _, y in self.allVersionsMaps.items():
            latest_map = y[0]
            for map in y:
                if latest_map.version < map.version:
                    latest_map = map
                    
            self.maps.append(latest_map)
    
    def setSelected(self, map):
        containMap = False
        for i in range(len(self.maps)):
            if map == self.maps[i]:
                self.maps[i] = map
                containMap = True
        if not containMap:
            self.maps.append(map)