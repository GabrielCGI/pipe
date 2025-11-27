from ..tool_models.ActionTool import *
from common.utils import *
import maya.cmds as cmds


class ApplyPeak(ActionTool):
    def __init__(self):
        super().__init__(
            name="Apply Peak",
            pref_name="apply_peak",
            description=(
                "Apply a small 'peak' style texture "
                "deformer to the selected mesh."
            ),
            button_text="Apply peak"
        )
        self.__selection = []

    def __retrieve_selection(self):
        """
        Retrieve the selection
        :return:
        """
        self.__selection.clear()
        self.__selection = cmds.ls(sl=True, dag=True, shapes=True) or []

    def on_selection_changed(self):
        """
        Refresh the button on selection changed
        :return:
        """
        self.__retrieve_selection()
        self.__refresh_btn()

    def __refresh_btn(self):
        """
        Refresh the button
        :return:
        """
        self._action_btn.setEnabled(len(self.__selection) > 0)

    def _action(self):
        """
        Set constant mtoa_constant_anim_time and mtoa_constant_anim_time for each StandIn
        :return:
        """
        #TODO ask value with maya api
        strength = self.ask_strength()
        if strength is None:
            cmds.confirmDialog(
                title="Invalid value",
                message="Input value is not a number.",
                button=['OK'],
                defaultButton='OK'
            )
            return
        self.apply_small_peak_texture_deformer(strength, tex_value=0.05)

    def populate(self):
        """
        Populate the CharacterTimeSetTool UI
        :return: layout
        """
        layout = super(ApplyPeak, self).populate()
        self.__retrieve_selection()
        self.__refresh_btn()
        return layout
    
    
    def ask_strength(self) -> float:
        result = cmds.promptDialog(
            title='Enter peak strength',
            message='Enter a number :',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel',
            text=1.0
        )

        value = None
        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True)
            try:
                value = float(text)
                print("Input value :", value)
            except ValueError:
                cmds.warning("Input value is not a number.")
        return value

    
    
    def apply_small_peak_texture_deformer(self, strength=1.0, tex_value=0.05):
        """
        Apply a small 'peak' style texture deformer to the selected mesh.
        Wrapped in a single undo chunk so everything undoes in one step.
        """
        # Start undo chunk
        cmds.undoInfo(openChunk=True)
        created = []

        try:
            # Get selected shapes
            sel = cmds.ls(sl=True, dag=True, shapes=True) or []
            if not sel:
                cmds.warning("Select at least one mesh object.")
                return

            for shape in sel:
                # Create the texture deformer on this shape
                deformer, handle = cmds.textureDeformer(
                    shape,
                    envelope=1,
                    strength=strength,
                    offset=0,
                    vectorStrength=(1, 1, 1),
                    vectorOffset=(0, 0, 0),
                    vectorSpace="Object",
                    direction="Handle",
                    pointSpace="UV",
                    exclusive=""
                )

                # Match your echo commands
                cmds.setAttr(deformer + ".direction", 0)
                cmds.setAttr(
                    deformer + ".texture",
                    tex_value, tex_value, tex_value,
                    type="double3"
                )

                # Optional: move the handle a bit in Y to make a visible "peak"
                cmds.setAttr(handle + ".ty", strength)

                created.append((deformer, handle))

            print("Created texture deformers:", created)
            cmds.select(sel)
            return created

        finally:
            # Close undo chunk even if something errors
            cmds.undoInfo(closeChunk=True)