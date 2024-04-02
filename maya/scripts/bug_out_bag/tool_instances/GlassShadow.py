from ..tool_models.ActionTool import *
from common.utils import *

class GlassShadow(ActionTool):
    def __init__(self):
        # TODO Modify fields as you want (pref_name should be unique)
        super().__init__(name="Glass shadow",pref_name="glass shadow",
                         description="Add a fake glass shadow to selected shaders", button_text="Run", tooltip="The script setup a ramp shader to the transmission color to create a fake caustic effect")

    def _action(self):
        # Iterate over all selected shaders
        for shader in pm.selected():
            print(shader)
            # Check if the shader has a transmission weight greater than 0
            if shader.hasAttr('transmission') and shader.transmission.get() > 0:
                existing_input = None
                # Get the first input connection to the transmissionColor, if any
                inputs = shader.transmissionColor.inputs(plugs=True, connections=True)
                if inputs:
                    first_input = inputs[0][1]  # Getting the source plug of the first connection
                    if not first_input.node().type() == 'aiRaySwitch':
                        print('Not switch')
                        existing_input = first_input
                    else:
                        print("Continue")
                        continue

                if existing_input is None:
                    # Get the current transmissionColor value
                    transmission_color = shader.transmissionColor.get()

                    # Create a colorConstant node with the same color
                    color_constant = pm.shadingNode('colorConstant', asUtility=True)
                    color_constant.inColor.set(transmission_color)
                    input_to_multiply = color_constant.outColor
                else:
                    input_to_multiply = existing_input


                # Create an aiFacingRatio node
                facing_ratio = pm.shadingNode('aiFacingRatio', asUtility=True)

                # Create a new ramp node with a custom name
                ramp_node = pm.shadingNode('ramp', asTexture=True, name='customRamp')

                # Advanced ramp setup with three decimal places
                color_positions = [
                    ((0.2, 0.2, 0.2), 0.101),
                    ((0.608, 0.608, 0.608), 0.355),
                    ((1,1, 1), 0.0),
                    ((0.451, 0.451, 0.451), 0.982),
                    ((0.170, 0.170, 0.170), 0.651),
                    ((0.758, 0.758, 0.758), 0.878)
                ]

                # Apply the color and position parameters to the ramp
                for i, (color, position) in enumerate(color_positions):
                    index = i if i < 5 else i + 1  # Adjusting for the specific ramp setup
                    pm.mel.eval(f'setAttr "{ramp_node.name()}.colorEntryList[{index}].position" {position};')
                    pm.mel.eval(f'setAttr "{ramp_node.name()}.colorEntryList[{index}].color" -type double3 {color[0]} {color[1]} {color[2]};')

                # Connect the aiFacingRatio.outValue to the vCoord of the custom ramp
                facing_ratio.outValue >> ramp_node.vCoord

                # Create an aiMultiply node
                multiply_node = pm.shadingNode('multiplyDivide', asUtility=True)
                raySwitch_node = pm.shadingNode('aiRaySwitch', asUtility=True)
                # Connect the custom ramp node's outColor to the second input of the aiMultiply node
                ramp_node.outColor >> multiply_node.input2

                # Connect the existing or new input to the first input of the aiMultiply node
                input_to_multiply >> multiply_node.input1
                multiply_node.output >> raySwitch_node.shadow
                input_to_multiply  >> raySwitch_node.specularReflection
                input_to_multiply  >> raySwitch_node.diffuseReflection
                input_to_multiply  >> raySwitch_node.diffuseTransmission
                input_to_multiply  >> raySwitch_node.specularTransmission
                input_to_multiply  >> raySwitch_node.camera
                input_to_multiply  >> raySwitch_node.volume
                # Connect the aiMultiply.outColor to the shader's transmission color attribute
                raySwitch_node.outColor >> shader.transmissionColor
