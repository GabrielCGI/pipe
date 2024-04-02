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
            if not first_input.node().type() == 'aiMultiply':
                print('Not multiply')
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
            ((0.0, 0.0, 0.0), 0.101),
            ((0.608, 0.608, 0.608), 0.355),
            ((0.314, 0.314, 0.314), 0.0),
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
        multiply_node = pm.shadingNode('aiMultiply', asUtility=True)

        # Connect the custom ramp node's outColor to the second input of the aiMultiply node
        ramp_node.outColor >> multiply_node.input2

        # Connect the existing or new input to the first input of the aiMultiply node
        input_to_multiply >> multiply_node.input1

        # Connect the aiMultiply.outColor to the shader's transmission color attribute
        multiply_node.outColor >> shader.transmissionColor
