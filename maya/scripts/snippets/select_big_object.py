import pymel.core as pm

# Step 1: Get a list of all the polygon objects in the scene
polygon_objects = pm.ls(type='mesh')

# Step 2: Create a dictionary with object names as keys and their polycount as values
polycount_dict = {}
for poly in polygon_objects:
    # Getting the parent of the shape node (the transform node) to represent the object
    parent_node = pm.listRelatives(poly, parent=True)[0]
    
    # Get the polycount of the current object
    polycount = pm.polyEvaluate(poly, vertex=True)
    
    # Add to the dictionary only if the polycount is >= 2000
    if polycount >= 2000:
        polycount_dict[parent_node] = polycount

# Step 3: Sort the dictionary by values (polycount) in descending order
sorted_polycount_dict = {k: v for k, v in sorted(polycount_dict.items(), key=lambda item: item[1], reverse=True)}

# Step 4: Print the sorted objects along with their polycount
for obj_name, polycount in sorted_polycount_dict.items():
    print(f'{obj_name}: {polycount} vertices')

# Step 5: Select the 20 most polycount-heavy objects
heavy_objects = list(sorted_polycount_dict.keys())[:20]
pm.select(heavy_objects)
