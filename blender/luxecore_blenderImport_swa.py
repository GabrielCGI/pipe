import bpy
import fnmatch

def set_luxcore_render_settings():
    scene = bpy.context.scene

    # Ensure LuxCore is the current renderer
    scene.render.engine = 'LUXCORE'

    # Enable Hybrid Back/Forward for Path Tracer
    scene.luxcore.config.path.hybridbackforward_enable = True
    scene.luxcore.config.path.hybridbackforward_lightpartition = 100
    scene.luxcore.config.path.hybridbackforward_glossinessthresh = 0.3

    scene.luxcore.config.path.depth_total = 5
    scene.luxcore.config.path.depth_specular = 1
    scene.luxcore.config.path.depth_diffuse = 1
    scene.luxcore.config.path.depth_glossy = 1
    scene.world.luxcore.light = 'none'

    # Enable halt conditions and set samples
    scene.luxcore.halt.enable = True
    scene.luxcore.halt.use_samples = True
    scene.luxcore.halt.samples = 1024
    scene.luxcore.halt.use_noise_thresh = False
    scene.luxcore.halt.use_light_samples = True
    scene.luxcore.halt.light_samples = 300
    scene.luxcore.halt.noise_thresh = 15
    scene.luxcore.config.device = 'OCL'

    #AOV Caustic
    bpy.context.view_layer.luxcore.aovs.caustic = True


    # Enable denoiser
    scene.luxcore.denoiser.enabled = False

    # Enable caustics
    scene.luxcore.config.enable_caustics = True



    # Set viewport halt time
    scene.luxcore.viewport.halt_time = 30

    # Set resolution
    #scene.render.resolution_x = 2048
    #scene.render.resolution_y = 2048
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '16'

    scene.render.fps = 25

def clean_scene():
    # Names of default objects to remove
    default_names = {"Camera", "Cube", "Light", "full_shotCam"}

    for obj in list(bpy.data.objects):
        if obj.name in default_names:
            print(f"Deleting object: {obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)


def set_caustic_light(pattern="shadow*"):
    for obj in bpy.context.scene.objects:
        if obj.type != 'LIGHT':
            continue

        light = obj.data  # datablock
        print("OBJ:", obj.name, "| DATA:", light.name, "| TYPE:", light.type)

        if not (fnmatch.fnmatch(obj.name, pattern) or fnmatch.fnmatch(light.name, pattern)):
            continue

        print(f"Configuring caustic light: {obj.name} (data: {light.name})")

        # 1) force AREA
        light.type = 'AREA'
        light.luxcore.exposure = 4

        # 2) maintenant size existe
        if hasattr(light, "size"):
            light.size = 15.0
        else:
            # normalement jamais, mais on garde safe
            print("Light has no 'size' attribute even after setting AREA")

        # LuxCore
        if hasattr(light, "luxcore") and hasattr(light.luxcore, "is_laser"):
            light.luxcore.is_laser = True
        else:
            print("LuxCore not available on this light (skip is_laser)")

        return

    print(f"No light found matching pattern: {pattern}")


def set_mats():
    for mat in bpy.data.materials:
        print(f"Checking material: {mat.name}")

        # Optional but recommended: ensure nodes are enabled
        mat.use_nodes = True

        # LuxCore setting
        mat.luxcore.use_cycles_nodes = True

        nt = mat.node_tree
        if not nt or "Principled BSDF" not in nt.nodes:
            continue

        p = nt.nodes["Principled BSDF"]

        if len(p.inputs) <= 28:
            print(f"Principled inputs too short in {mat.name}")
            continue

        # Emission OFF for everyone
        p.inputs[28].default_value = 0.0

        # Transmission ON only for crystal materials
        if "crystal" in mat.name.lower():
            p.inputs[18].default_value = 1.0
            print(f"Crystal tuned: {mat.name}")

def run():
    set_luxcore_render_settings()
    set_mats()
    set_caustic_light()
    clean_scene()

