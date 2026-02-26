import os

from . import map as mp


class Shader:
    def __init__(self, name: str):
        self.name = name.lower()
        self.unversionned_map: list[mp.Map] = []
        self.latest_maps: list[mp.VersionMap] = []
        self.selected_maps: list[mp.Map] = []
        self.allVersionsMaps: dict = {}

    def isEmpty(self) -> bool:
        return not (len(self.allVersionsMaps) or len(self.unversionned_map))

    def existMaps(self, mat: mp.Map, versionned=False):
        if not versionned:
            for maps in self.unversionned_map:
                if maps == mat:
                    return maps
            return None
        else:
            for map_name, _ in self.allVersionsMaps.items():
                if map_name == mat.name:
                    return map_name
            return None

    def _parse_map(self, map_path: str) -> bool:
        map = mp.Map(map_path)
        if map.parse():
            mat: mp.Map = self.existMaps(map, versionned=False)
            # Take the last map parsed
            if mat is not None:
                mat.path = map.path
            else:
                self.unversionned_map.append(map)
            return True
        return False

    def _parse_version_map(self, map_path: str) -> bool:
        new_map = mp.VersionMap(map_path)
        if new_map.parse():
            mat: str = self.existMaps(new_map, versionned=True)
            # If the map already exists
            # with a different version
            if mat is not None:
                is_new_version = True
                map_versions: list[mp.VersionMap] = self.allVersionsMaps.get(mat, [])
                for map in map_versions:
                    if map.version == new_map.version:
                        is_new_version = False
                if is_new_version:
                    map_versions.append(new_map)
                else:
                    return False
            else:
                self.allVersionsMaps[new_map.name] = [new_map]
            return True
        return False

    def parse(self, map_path: str) -> bool:
        map_directory = os.path.dirname(map_path)
        version_match = mp.VERSION_PATTERN_COMPILE.search(map_directory)
        if version_match is None:
            return self._parse_map(map_path)
        else:
            return self._parse_version_map(map_path)

    def setLatestMap(self):
        self.latest_maps.clear()
        for _, y in self.allVersionsMaps.items():
            latest_map: mp.VersionMap = y[0]
            for map in y:
                if latest_map.version < map.version:
                    latest_map = map
            self.latest_maps.append(latest_map)
