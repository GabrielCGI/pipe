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
    scene.luxcore.halt.samples = 1500
    scene.luxcore.halt.use_noise_thresh = True
    scene.luxcore.halt.noise_thresh = 15

    # Enable denoiser
    scene.luxcore.denoiser.enabled = False

    # Enable caustics
    scene.luxcore.config.enable_caustics = True



    # Set viewport halt time
    scene.luxcore.viewport.halt_time = 30

    # Set resolution
    scene.render.resolution_x = 2048
    scene.render.resolution_y = 2048
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


def set_caustic_light():
    for light in bpy.data.lights:
        if fnmatch.fnmatch(light.name, "lights/shadow*"):
            print(f"Configuring caustic light: {light.name}")

            # Blender light type
            light.type = 'AREA'
            light.size = 5.0
            light.gain = 1
            light.exposure = 6

            # LuxCore-specific setting
            light.luxcore.is_laser = True

            return  # only the first matching light

    print("No light found matching pattern: lights/shadow*")

def set_mats():
    for mat in bpy.data.materials:
        print(f"Checking material: {mat.name}")

        # Optional but recommended: ensure nodes are enabled
        mat.use_nodes = True

        # LuxCore setting
        mat.luxcore.use_cycles_nodes = True

def run():
    set_luxcore_render_settings()
    set_mats()
    clean_scene()

