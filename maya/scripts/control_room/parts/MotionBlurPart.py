from ControlRoomPart import *
from FormSlider import *
from pymel.core import *


class MotionBlurPart(ControlRoomPart):
    def __init__(self, control_room):
        super(MotionBlurPart, self).__init__(control_room, "Motion Blur")
        self.__form_sliders = [
            FormSlider(FormSliderType.IntSlider, "Keys", "defaultArnoldRenderOptions.motion_steps", "motion_blur_keys",
                       2, 30, 300),
            FormSlider(FormSliderType.FloatSlider, "Motion Step", "defaultArnoldRenderOptions.motion_frames",
                       "motion_blur_step", 0, 1),
        ]
        self.__ui_motion_blur_cb = None
        self.__ui_instant_shutter_cb = None
        self.__motion_blur_callback = None
        self.__instant_shutter_callback = None
        self.__layer_callback = None
        self.__motion_blur_override = None
        self.__instant_shutter_override = None
        self.__action_add_motion_blur_override = QAction(text="Add Override")
        self.__action_add_motion_blur_override.triggered.connect(self.__create_motion_blur_override)
        self.__action_remove_motion_blur_override = QAction(text="Remove Override")
        self.__action_remove_motion_blur_override.triggered.connect(self.__remove_motion_blur_override)

        self.__action_add_instant_shutter_override = QAction(text="Add Override")
        self.__action_add_instant_shutter_override.triggered.connect(self.__create_instant_shutter_override)
        self.__action_remove_instant_shutter_override = QAction(text="Remove Override")
        self.__action_remove_instant_shutter_override.triggered.connect(self.__remove_instant_shutter_override)

        self.__retrieve_motion_blur_override()
        self.__retrieve_instant_shutter_override()

    # Create the enable motion blur override
    def __create_motion_blur_override(self):
        self.__motion_blur_override = \
            cr.ControlRoom.create_override("defaultArnoldRenderOptions", "motion_blur_enable")

    # Remove the enable motion blur override
    def __remove_motion_blur_override(self):
        cr.ControlRoom.remove_override(self.__motion_blur_override)
        self.__motion_blur_override = None

    # Retrieve the enable motion blur override
    def __retrieve_motion_blur_override(self):
        self.__motion_blur_override = \
            cr.ControlRoom.retrieve_override("defaultArnoldRenderOptions", "motion_blur_enable")

    # Create the instant shutter override
    def __create_instant_shutter_override(self):
        self.__instant_shutter_override = \
            cr.ControlRoom.create_override("defaultArnoldRenderOptions", "ignoreMotionBlur")

    # Remove the instant shutter override
    def __remove_instant_shutter_override(self):
        cr.ControlRoom.remove_override(self.__instant_shutter_override)
        self.__instant_shutter_override = None

    # Retrieve the instant shutter override
    def __retrieve_instant_shutter_override(self):
        self.__instant_shutter_override = \
            cr.ControlRoom.retrieve_override("defaultArnoldRenderOptions", "ignoreMotionBlur")

    def populate(self):
        content = QVBoxLayout()
        content.setContentsMargins(4, 4, 1, 4)

        lyt_cb = QHBoxLayout()
        self.__ui_motion_blur_cb = QCheckBox("Enable Motion Blur")
        self.__ui_motion_blur_cb.stateChanged.connect(self.__on_motion_blur_changed)
        self.__ui_motion_blur_cb.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.__ui_motion_blur_cb.addAction(self.__action_add_motion_blur_override)
        self.__ui_motion_blur_cb.addAction(self.__action_remove_motion_blur_override)
        lyt_cb.addWidget(self.__ui_motion_blur_cb)
        self.__ui_instant_shutter_cb = QCheckBox("Instantaneous Shutter")
        self.__ui_instant_shutter_cb.stateChanged.connect(self.__on_instant_shutter_changed)
        self.__ui_instant_shutter_cb.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.__ui_instant_shutter_cb.addAction(self.__action_add_instant_shutter_override)
        self.__ui_instant_shutter_cb.addAction(self.__action_remove_instant_shutter_override)
        lyt_cb.addWidget(self.__ui_instant_shutter_cb)
        content.addLayout(lyt_cb)

        form_layout = QFormLayout()
        content.addLayout(form_layout)

        for fs in self.__form_sliders:
            lbl, slider = fs.generate_ui()
            form_layout.addRow(lbl, slider)
        return content

    def refresh_ui(self):
        self.__ui_motion_blur_cb.setChecked(getAttr("defaultArnoldRenderOptions.motion_blur_enable"))
        self.__ui_instant_shutter_cb.setChecked(getAttr("defaultArnoldRenderOptions.ignoreMotionBlur"))
        for fs in self.__form_sliders:
            fs.refresh_ui()

        visible_layer = render_setup.instance().getVisibleRenderLayer()
        is_default_layer = visible_layer.name() == "defaultRenderLayer"
        self.__action_add_motion_blur_override.setEnabled(
            not is_default_layer and self.__motion_blur_override is None)
        self.__action_remove_motion_blur_override.setEnabled(
            not is_default_layer and self.__motion_blur_override is not None)
        self.__action_add_instant_shutter_override.setEnabled(
            not is_default_layer and self.__instant_shutter_override is None)
        self.__action_remove_instant_shutter_override.setEnabled(
            not is_default_layer and self.__instant_shutter_override is not None)

        motion_blur_stylesheet_lbl = "color:" + cr.OVERRIDE_LABEL_COLOR \
            if self.__motion_blur_override is not None else ""
        instant_shutter_stylesheet_lbl = "color:" + cr.OVERRIDE_LABEL_COLOR \
            if self.__instant_shutter_override is not None else ""
        self.__ui_motion_blur_cb.setStyleSheet("QCheckBox{" + motion_blur_stylesheet_lbl + "}")
        self.__ui_instant_shutter_cb.setStyleSheet("QCheckBox{" + instant_shutter_stylesheet_lbl + "}")

    # On motion blur enable checkbox changed
    def __on_motion_blur_changed(self, state):
        setAttr("defaultArnoldRenderOptions.motion_blur_enable", state == 2)

    # On instant shutter checkbox changed
    def __on_instant_shutter_changed(self, state):
        setAttr("defaultArnoldRenderOptions.ignoreMotionBlur", state == 2)

    def add_callbacks(self):
        self.__motion_blur_callback = scriptJob(
            attributeChange=["defaultArnoldRenderOptions.motion_blur_enable", self.refresh_ui])
        self.__instant_shutter_callback = scriptJob(
            attributeChange=["defaultArnoldRenderOptions.ignoreMotionBlur", self.refresh_ui])
        for fs in self.__form_sliders:
            fs.add_callbacks()
        self.__layer_callback = scriptJob(event=["renderLayerManagerChange", self.refresh_ui])

    def remove_callbacks(self):
        scriptJob(kill=self.__motion_blur_callback)
        scriptJob(kill=self.__instant_shutter_callback)
        for fs in self.__form_sliders:
            fs.remove_callbacks()
        scriptJob(kill=self.__layer_callback)

    def add_to_preset(self, part_name, preset):
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            preset.set(part_name, key, getAttr(field))
        preset.set(part_name, "enable", getAttr("defaultArnoldRenderOptions.motion_blur_enable"))
        preset.set(part_name, "instant_shutter", getAttr("defaultArnoldRenderOptions.ignoreMotionBlur"))

    def apply(self, part_name, preset):
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            setAttr(field, preset.get(part_name, key))
        setAttr("defaultArnoldRenderOptions.motion_blur_enable", preset.get(part_name, "enable"))
        setAttr("defaultArnoldRenderOptions.ignoreMotionBlur", preset.get(part_name, "instant_shutter"))
