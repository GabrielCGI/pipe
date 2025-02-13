import re
import glob
import os

VERSION_PATTERN = r"v\d{3,9}"

def findDirectory(subnets):
    """
    Find every files candidates for an update based on shader already
    present in a material library.
    
    Warning: Multiple usages of glob search, potentially
    computationnal heavy.
    """
    
    map_list_per_subnet = []
    for subnet in subnets:
        map_list_per_subnet.append([])
        for node in subnet.children():
            if node.type().name() == 'mtlximage':
                map_path = node.parm('file').eval()
                if map_path is not None:
                    map_list_per_subnet[-1].append(map_path)
                
    file_list = []
    for i, subnet_map_list in enumerate(map_list_per_subnet):
        file_list.append([])
        for map_name in subnet_map_list:
            versionMatch = re.search(VERSION_PATTERN, map_name)
            if versionMatch is None:
                file_list[i].append(map_name)
            else:
                span = versionMatch.span()
                globpath = map_name[:span[0]] + "*" + map_name[span[1]:]
                file_list[i] += glob.glob(pathname=globpath)
        file_list[i] = list(set(file_list[i]))
    
    return file_list

map_list_per_subnet = [
    ['I:/swaDisney_2411/03_Production/Assets/Sets/podium/Libraries/textures/v009/DefaultMaterial_BaseColor_ACEScg.1001.exr'],
    [
        'I:/swaDisney_2411/03_Production/Assets/Sets/podium/Libraries/textures/v009/DefaultMaterial_BaseColor_ACEScg.1001.exr',
        'I:/swaDisney_2411/03_Production/Assets/Sets/podium/Libraries/textures/v009/DefaultMaterial_BaseColor_ACEScg.1001.exr'
    ],
    ['I:/swaDisney_2411/03_Production/Assets/Sets/podium/Libraries/textures/v001/podium_Modeling_v003_pinkPaper_mat_BaseColor_ACEScg.exr'],
    ['I:/swaDisney_2411/03_Production/Assets/Sets/podium/Libraries/textures/v009/DefaultMaterial_BaseColor_ACEScg.1001.exr']
]

map_list = findDirectory(map_list_per_subnet)

for i, shader in enumerate(map_list):
    print(i)
    for map_possible in shader:
        print(f"---{map_possible}")