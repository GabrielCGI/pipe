import json
import os
from collections import defaultdict

EXTENSION = None
MAPS_TAG = None
SIGNATURE = None
LOADED = False

def load():
    global EXTENSION
    global MAPS_TAG
    global SIGNATURE
    global LOADED
    
    ressource_path = os.path.join(
        os.path.dirname(__file__),
        "ressource",
        "ressources.json")
    
    with open(ressource_path, 'r') as file:
        data = json.load(file)
        
    EXTENSION = data["Extension"]
    MAPS_TAG = data['Map_tags']
    SIGNATURE = data['Signature']
    LOADED = True
    
if __name__ == "__main__":
    print(LOADED)
    load()
    print(EXTENSION)
    print(MAPS_TAG)
    print(SIGNATURE)
    print(LOADED)
    print(MAPS_TAG.items())
    for i in MAPS_TAG.items():
        print(i)
    