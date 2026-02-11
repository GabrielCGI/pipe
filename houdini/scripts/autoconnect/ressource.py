import json
import os

EXTENSION = None
MAPS_TAG = None
THUMBNAILS_DIR = None
LOADED = False

def load():
    global EXTENSION
    global MAPS_TAG
    global LOADED
    global THUMBNAILS_DIR
    
    ressource_path = os.path.join(
        os.path.dirname(__file__),
        "ressource",
        "ressources.json")
    
    with open(ressource_path, 'r') as file:
        data = json.load(file)
        
    EXTENSION = data["Extension"]
    MAPS_TAG = data['Map_tags']
    THUMBNAILS_DIR = data['Thumbnails_dir']
    LOADED = True
    
    
# For debug purpose only
# This module is not expected to be use a __main__ 
# for something else than debug
if __name__ == "__main__":
    print(LOADED)
    load()
    print(EXTENSION)
    print(MAPS_TAG)
    print(LOADED)
    for i in MAPS_TAG.items():
        print(i)
        
        # Uncomment to print more
        #  |
        #  |
        # \ /
        #  '
        
        # map name: str
        # print(i[0])
        
        # map data: dict (keyword and signature)
        # print(i[1]["keywords"])
        # print(i[1]["signature"])