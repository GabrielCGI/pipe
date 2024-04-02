import bpy
import json
import bpy_extras

# Path to the JSON file containing shader information
json_file_path = 'D:/luxcore_tmp/shaders.json'  # Update this path as needed

# Load shader data from the JSON file
with open(json_file_path, 'r') as json_file:
    shader_data = json.load(json_file)

# Function to create a LuxCore glass material
def create_luxcore_glass_material(name, color, ior,transmissionDispersion, roughness):
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
    if transmissionDispersion != 0:
        glass_node.inputs[3].default_value = 0.015
    node_tree.links.new(glass_node.outputs[0], output.inputs[0])

    return mat

def create_luxcore_matte_material(name, color, texture_path=None):
    mat = bpy.data.materials.new(name=name)
    node_tree = bpy.data.node_groups.new(name="Nodes_" + mat.name, type="luxcore_material_nodes")
    mat.luxcore.node_tree = node_tree
    node_tree.use_fake_user = True

    nodes = node_tree.nodes
    output = nodes.new("LuxCoreNodeMatOutput")
    matte_node = nodes.new("LuxCoreNodeMatMatte")
    matte_node.location = (-200, 0)

    matte_node.inputs[0].default_value = (color[0], color[1], color[2])

    if texture_path:
        diffuse_img = bpy_extras.image_utils.load_image(texture_path)
        diffuse_img_node = nodes.new("LuxCoreNodeTexImagemap")
        diffuse_img_node.location = -400, 0
        diffuse_img_node.image = diffuse_img
        node_tree.links.new(diffuse_img_node.outputs[0], matte_node.inputs[0])

    node_tree.links.new(matte_node.outputs[0], output.inputs[0])

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

def set_luxcore_render_settings():
    scene = bpy.context.scene

    # Ensure LuxCore is the current renderer
    scene.render.engine = 'LUXCORE'

    # Enable Hybrid Back/Forward for Path Tracer
    scene.luxcore.config.path.hybridbackforward_enable = True
    scene.luxcore.config.path.hybridbackforward_lightpartition = 100
    scene.luxcore.config.path.depth_total = 5
    scene.luxcore.config.path.depth_specular = 1
    scene.luxcore.config.path.depth_diffuse = 1
    scene.luxcore.config.path.depth_glossy = 1
    scene.world.luxcore.light = 'none'

    # Enable halt conditions and set samples
    scene.luxcore.halt.enable = True
    scene.luxcore.halt.use_samples = True
    scene.luxcore.halt.samples = 1500

    # Enable denoiser
    scene.luxcore.denoiser.enabled = True

    # Enable caustics
    scene.luxcore.config.enable_caustics = True



    # Set viewport halt time
    scene.luxcore.viewport.halt_time = 30
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '16'

    scene.render.fps = 25


def run():
    set_luxcore_render_settings()
    # Iterate over materials in Blender and replace them based on the shader data
    for mat in bpy.data.materials:
        print(f"Checking material: {mat.name}")
        # Skip if the material name already includes 'LuxeCore', indicating it's been converted
        if "LuxCore" in mat.name:
            print(f"Skipping {mat.name} as it has already been converted.")
            continue
        if mat.name in shader_data:
            shader = shader_data[mat.name]
            base_color = shader['baseColor']
            texture_path = shader.get('baseColor_texture', None)
            transmission_color = shader['transmissionColor']
            ior = shader.get('specularIOR', 1.5)  # Default IOR value
            transmissionDispersion = shader.get('transmissionDispersion', 0)
            roughness = shader.get('specularRoughness', 0.2)  # Default roughness value

            print(f"Applying shader data to material: {mat.name}")
            if shader['metalness'] == 0 and shader['transmission'] == 0:
                new_mat = create_luxcore_matte_material(mat.name + "_LuxCoreMatte", base_color, texture_path)
            elif shader['metalness'] == 1.0:

                new_mat = create_luxcore_metal_material(mat.name + "_LuxCoreMetal", base_color, roughness)
                print(f"Created LuxCore metal material: {new_mat.name}")
            elif shader['transmission'] == 1.0:

                new_mat = create_luxcore_glass_material(mat.name + "_LuxCoreGlass", transmission_color, ior, transmissionDispersion, roughness)
                print(f"Created LuxCore glass material: {new_mat.name}")
            else:
                print(f"Skipping material {mat.name}, does not meet conditions.")
                continue  # Skip if neither condition is met

            # Assign the new material to all objects using the old material
            for obj in bpy.data.objects:
                for slot in obj.material_slots:
                    if slot.material == mat:
                        print(f"Assigning new material {new_mat.name} to object: {obj.name}")
                        slot.material = new_mat
        else:
            print(f" /!!!\/!!!\/!!!\/!!!\ Shader data not found for material: {mat.name}")

            # Delete the old material
            bpy.data.materials.remove(mat)

    print("Material replacement complete.")
run()
