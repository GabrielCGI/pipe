from ControlRoomPart import *
from pymel.core import *


class CameraPart(ControlRoomPart):

    # Getter of the renderable cameras in the scene
    @staticmethod
    def __get_renderable_cameras():
        cameras = ls(type="camera")
        renderable_cameras = []
        for cam in cameras:
            if getAttr(cam + ".renderable"):
                renderable_cameras.append(cam)
        return renderable_cameras

    def __init__(self, control_room):
        super(CameraPart, self).__init__(control_room, "Camera")
        self.__ui_combobox_cameras = None
        self.__cam_selected = None
        self.__camera_created_callback = None

        renderable_cameras = CameraPart.__get_renderable_cameras()
        if self.__cam_selected is None and len(renderable_cameras) > 0:
            self.__cam_selected = renderable_cameras[0]
        nb_cam = len(renderable_cameras)

        if nb_cam == 0:
            warning("There is no renderable camera set in render settings")
        elif nb_cam > 1:
            confirmDialog(title="Too many cam",
                          message="Did you know you have " + str(nb_cam) + " cameras set as renderable?", button=["Ok"])

    def populate(self):
        content = QFormLayout()
        content.setContentsMargins(4, 4, 1, 4)

        lbl_cbb_cameras = QLabel("Renderable Camera")
        self.__ui_combobox_cameras = QComboBox()
        self.__ui_combobox_cameras.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        content.addRow(lbl_cbb_cameras, self.__ui_combobox_cameras)
        self.__ui_combobox_cameras.currentIndexChanged.connect(self.__on_item_camera_changed)

        return content

    def refresh_ui(self):
        cam_selected = self.__cam_selected
        index_selected = None

        self.__ui_combobox_cameras.clear()
        for i, cam in enumerate(CameraPart.__get_renderable_cameras()):
            if cam == cam_selected:
                index_selected = i
            self.__ui_combobox_cameras.addItem(str(cam), cam)

        if index_selected is not None:
            self.__ui_combobox_cameras.setCurrentIndex(index_selected)

    # On selected camera changed
    def __on_item_camera_changed(self, index):
        self.__cam_selected = self.__ui_combobox_cameras.itemData(index)
        self._control_room.cam_changed(self.__cam_selected)

    # On camera created refresh the ui
    def __on_camera_created(self, *args, **kwargs):
        self.refresh_ui()

    def add_callbacks(self):
        self.__camera_created_callback = OpenMaya.MEventMessage.addEventCallback("SelectionChanged",
                                                                                 self.__on_camera_created)

    def remove_callbacks(self):
        OpenMaya.MMessage.removeCallback(self.__camera_created_callback)

    def add_to_preset(self, part_name, preset):
        # Nothing
        pass

    def apply(self, part_name, preset):
        # Nothing
        pass
