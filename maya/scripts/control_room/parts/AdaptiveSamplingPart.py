from ControlRoomPart import *
from FormSlider import *
from pymel.core import *


class AdaptiveSamplingPart(ControlRoomPart):
    def __init__(self, control_room):
        super(AdaptiveSamplingPart, self).__init__(control_room, "Adaptive Sampling")
        self.__form_sliders = [
            FormSlider(FormSliderType.IntSlider, "Max Camera (AA)", "defaultArnoldRenderOptions.AASamplesMax",
                       "camera_aa", 0, 20, 200),
            FormSlider(FormSliderType.FloatSlider, "Adaptive Treshold",
                       "defaultArnoldRenderOptions.AAAdaptiveThreshold", "diffuse", 0, 1),
        ]
        self.__ui_enable_cb = None
        self.__enable_callback = None
        self.__layer_callback = None
        self.__adaptive_sampling_override = None
        self.__action_add_adaptive_sampling_override = QAction(text="Add Override")
        self.__action_add_adaptive_sampling_override.triggered.connect(self.__create_adaptive_sampling_override)
        self.__action_remove_adaptive_sampling_override = QAction(text="Remove Override")
        self.__action_remove_adaptive_sampling_override.triggered.connect(self.__remove_adaptive_sampling_override)

        self.__retrieve_adaptive_sampling_override()

    # Create an override for the adaptive sampling field
    def __create_adaptive_sampling_override(self):
        self.__adaptive_sampling_override = cr.ControlRoom.create_override("defaultArnoldRenderOptions",
                                                                           "enableAdaptiveSampling")

    # Remove the override for the adaptive sampling field
    def __remove_adaptive_sampling_override(self):
        cr.ControlRoom.remove_override(self.__adaptive_sampling_override)
        self.__adaptive_sampling_override = None

    # Retrievet he override for the adaptive sampling field
    def __retrieve_adaptive_sampling_override(self):
        self.__adaptive_sampling_override = cr.ControlRoom.retrieve_override("defaultArnoldRenderOptions",
                                                                             "enableAdaptiveSampling")

    def populate(self):
        content = QVBoxLayout()
        content.setContentsMargins(4, 4, 1, 4)

        self.__ui_enable_cb = QCheckBox("Enable Adaptive Sampling")
        self.__ui_enable_cb.stateChanged.connect(self.__on_enable_changed)
        self.__ui_enable_cb.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.__ui_enable_cb.addAction(self.__action_add_adaptive_sampling_override)
        self.__ui_enable_cb.addAction(self.__action_remove_adaptive_sampling_override)

        content.addWidget(self.__ui_enable_cb)

        form_layout = QFormLayout()
        content.addLayout(form_layout)

        for fs in self.__form_sliders:
            lbl, slider = fs.generate_ui()
            form_layout.addRow(lbl, slider)
        return content

    def refresh_ui(self):
        self.__ui_enable_cb.setChecked(getAttr("defaultArnoldRenderOptions.enableAdaptiveSampling"))
        for fs in self.__form_sliders:
            fs.refresh_ui()

        visible_layer = render_setup.instance().getVisibleRenderLayer()
        is_default_layer = visible_layer.name() == "defaultRenderLayer"
        self.__action_add_adaptive_sampling_override.setEnabled(
            not is_default_layer and self.__adaptive_sampling_override is None)
        self.__action_remove_adaptive_sampling_override.setEnabled(
            not is_default_layer and self.__adaptive_sampling_override is not None)

        stylesheet_lbl = "color:" + cr.OVERRIDE_LABEL_COLOR if self.__adaptive_sampling_override is not None else ""
        self.__ui_enable_cb.setStyleSheet("QCheckBox{" + stylesheet_lbl + "}")

    # On checkbox enable adaptive sampling changed
    def __on_enable_changed(self, state):
        setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling", state == 2)

    def add_callbacks(self):
        self.__enable_callback = scriptJob(
            attributeChange=["defaultArnoldRenderOptions.enableAdaptiveSampling", self.refresh_ui])
        for fs in self.__form_sliders:
            fs.add_callbacks()
        self.__layer_callback = scriptJob(event=["renderLayerManagerChange", self.refresh_ui])

    def remove_callbacks(self):
        scriptJob(kill=self.__enable_callback)
        for fs in self.__form_sliders:
            fs.remove_callbacks()
        scriptJob(kill=self.__layer_callback)

    def add_to_preset(self, part_name, preset):
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            preset.set(part_name, key, getAttr(field))
        preset.set(part_name, "enable", getAttr("defaultArnoldRenderOptions.enableAdaptiveSampling"))

    def apply(self, part_name, preset):
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            setAttr(field, preset.get(part_name, key))
        setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling", preset.get(part_name, "enable"))
