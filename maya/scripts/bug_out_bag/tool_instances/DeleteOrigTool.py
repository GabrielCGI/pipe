from ..tool_models.ActionTool import *


class DeleteOrigTool(ActionTool):
    def __init__(self):
        super().__init__(name="Delete Orig", pref_name="delete_orig_tool",
                         description="Delete intermediate objects of the selected objects", button_text="Delete")
        self.__selection = []

    def _action(self):
        """
        Delete all the Orig
        :return:
        """
        if len(self.__selection) > 0:
            unused_intermediate_objects = []
            for node in self.__selection:
                if len(node.inputs()) == 0 \
                        and len(node.outputs()) == 0 \
                        and node.intermediateObject.get() \
                        and node.referenceFile() is None:
                    unused_intermediate_objects.append(node)
            pm.delete(unused_intermediate_objects)

    def __refresh_btn(self):
        """
        Refresh the button
        :return:
        """
        self._action_btn.setEnabled(len(self.__selection) > 0)

    def __retrieve_selection(self):
        """
        Retrieve all the shapes selected
        :return:
        """
        selection = pm.ls(sl=True)
        self.__selection = pm.listRelatives(selection, shapes=True, allDescendents=True, type="mesh")

    def on_selection_changed(self):
        """
        Refresh the button on selection changed
        :return:
        """
        self.__retrieve_selection()
        self.__refresh_btn()

    def populate(self):
        """
        Populate the DeleteOrigTool UI
        :return:
        """
        layout = super(DeleteOrigTool, self).populate()
        self.__retrieve_selection()
        self.__refresh_btn()
        return layout
