from ..tool_models.MultipleActionTool import *


class Exposure(MultipleActionTool):

    def __init__(self):
        actions = {
            "increase": {
                "text": "Increase by 0.5",
                "action": self.__increase,
                "row": 0
            },
            "decrease": {
                "text": "Decrease by 0.5",
                "action": self.__decrease,
                "row": 0
            }
        }
        super().__init__(name="Light Exposure Tools", pref_name="exposure_tool",
                         actions=actions, stretch=1)


    def update_aiExposure(self, decrease_value):
        # List of all light types
        light_types = [
            'areaLight',
            'spotLight',
            'pointLight',
            'directionalLight',
            'ambientLight',
            'aiSkyDomeLight',
            'aiLightPortal',
            'aiPhotometricLight',
            'aiAreaLight'
        ]

        # Iterate through each light type
        for light_type in light_types:
            # Find all lights of the current type
            lights = pm.ls(type=light_type)
            for light in lights:
                # Check if the light has the 'aiExposure' attribute
                if light.hasAttr('aiExposure'):
                    # Get the current value of 'aiExposure'
                    current_value = light.getAttr('aiExposure')
                    # Calculate the new value
                    new_value = current_value + decrease_value
                    # Set the new value of 'aiExposure'
                    light.setAttr('aiExposure', new_value)
                    print(f'{light} aiExposure decreased from {current_value} to {new_value}')

    def __increase(self):
        self.update_aiExposure(0.5)

    def __decrease(self):
        self.update_aiExposure(-0.5)


    def populate(self):
        """
        Populate the Exposure UI
        :return:
        """
        layout = super(Exposure, self).populate()
        return layout
