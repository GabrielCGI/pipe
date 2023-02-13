from tool_models.ActionTool import *


class TextureCheckTool(ActionTool):
    def _action(self):
        print(self._name)

    def __init__(self):
        super().__init__(name="Check Texture",pref_name="check_texture",
                         description="Verify the colorspaces of all the textures" ,button_text="Check")