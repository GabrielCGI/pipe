import bpy
import json

# Path to the JSON file containing shader information
json_file_path = 'D:/aiStandardSurface_shaders.json'  # Update this path as needed

# Load shader data from the JSON file
with open(json_file_path, 'r') as json_file:
    shader_data = json.load(json_file)

# Function to create a LuxCore glass material
def create_luxcore_glass_material(name, color, ior, roughness):
    mat = bpy.data.materials.new(name=name)
    node_tree = bpy.data.node_groups.new(name="Nodes_" + mat.name, type="luxcore_material_nodes")
    mat.luxcore.node_tree = node_tree
    node_tree.use_fake_user = True

    nodes = node_tree.nodes
    output = nodes.new("LuxCoreNodeMatOutput")
    glass_node = nodes.new("LuxCoreNodeMatGlass")
    glass_node.location = (-200, 0)

    # Set the glass material properties
    glass_node.inputs[0].default_value = (color[0], color[1], color[2])
    glass_node.inputs[2].default_value = ior
    glass_node.rough = True
    glass_node.inputs[6].default_value = roughness

    node_tree.links.new(glass_node.outputs[0], output.inputs[0])

    return mat

# Function to create a LuxCore metal material
def create_luxcore_metal_material(name, color, roughness):
    mat = bpy.data.materials.new(name=name)
    node_tree = bpy.data.node_groups.new(name="Nodes_" + mat.name, type="luxcore_material_nodes")
    mat.luxcore.node_tree = node_tree
    node_tree.use_fake_user = True

    nodes = node_tree.nodes
    output = nodes.new("LuxCoreNodeMatOutput")
    metal_node = nodes.new("LuxCoreNodeMatMetal")
    metal_node.location = (-200, 0)

    # Set the metal material properties
    metal_node.inputs[0].default_value = (color[0], color[1], color[2])
    metal_node.inputs[2].default_value = roughness

    node_tree.links.new(metal_node.outputs[0], output.inputs[0])

    return mat

# Iterate over materials in Blender and replace them based on the shader data
for mat in bpy.data.materials:
    if mat.name in shader_data:
        shader = shader_data[mat.name]
        base_color = shader['base_color']
        transmission_color = shader['transmission_color']
        ior = shader.get('specularIOR', 1.5)  # Default IOR value
        roughness = shader.get('specularRoughness', 0.2)  # Default roughness value

        if shader['metalness'] == 1.0:
            # Create and assign LuxCore metal material
            new_mat = create_luxcore_metal_material(mat.name + "_LuxCoreMetal",base_color, roughness)
        elif shader['transmission_weight'] == 1.0:
            # Create and assign LuxCore glass material
            new_mat = create_luxcore_glass_material(mat.name + "_LuxCoreGlass", transmission_color, ior, roughness)
        else:
            continue  # Skip if neither condition is met

        # Assign the new material to all objects using the old material
        for obj in bpy.data.objects:
            for slot in obj.material_slots:
                if slot.material == mat:
                    slot.material = new_mat

        # Delete the old material
        bpy.data.materials.remove(mat)

print("Material replacement complete.")
