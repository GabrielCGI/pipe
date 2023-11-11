from ..tool_models.ActionTool import *

from common.utils import *

class ViewportShader(ActionTool):
    def __init__(self):
        # TODO Modify fields as you want (pref_name should be unique)
        super().__init__(name="Viewport Shader",pref_name="vp_shader",
                         description="Create viewport shader for glass objects", button_text="Run", tooltip="Iterate over all shadings group and create a viewport shader if transmission detected")

    def _action(self):

        for sg in pm.ls(type='shadingEngine'):
            # Check for aiSurfaceShader connection
            ai_surface_shader = sg.aiSurfaceShader.inputs()
            if not ai_surface_shader:
                surface_shader = sg.surfaceShader.inputs()
                if surface_shader:
                    shader = surface_shader[0]

                    # Check if transmission is not zero
                    if shader.hasAttr('transmission') and shader.transmission.get() > 0:
                        # Create new aiStandardSurface shader
                        new_shader = pm.shadingNode('aiStandardSurface', asShader=True)
                        new_shader_name = f"{shader.name()}_VP"
                        new_shader.rename(new_shader_name)

                        # Set baseColor to transmission color of the previous shader
                        if shader.hasAttr('transmissionColor'):
                            new_shader.baseColor.set(shader.transmissionColor.get())

                        # Connect the shaders to the shading group
                        shader.outColor >> sg.aiSurfaceShader
                        new_shader.outColor >> sg.surfaceShader
                    else:
                        # Handle case where there is no transmission or surface shader is not aiStandardSurface
                        print(f"No transmission found for shader: {shader.name()}")
