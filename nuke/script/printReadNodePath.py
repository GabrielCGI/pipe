def listReadNode():
    nodes = nuke.allNodes('Read')  # Grab all nodes with the class 'Read'. Valid classes include 'Write', 'ReadGeo', etc
    source_list = []  # Initialised empty list

    for node in nodes:
        path = node["file"].value()  # Retrieve value from "file" attribute
        name = path  # Access the last value in array for path after splitting it with "/" delimiter
        source_list.append(name)  # Add/append name into source_list

    result = "\nList of Read nodes:\n"
    print(result)

    for name in sorted(source_list):
        print(name)
listReadNode()