from ..ControlRoomPart import *
from ..FormSlider import *
import pymel.core as pm


class AdaptiveSamplingPart(ControlRoomPart):
    def __init__(self, control_room, part_name):
        """
        Constructor
        :param control_room
        :param part_name
        """
        super(AdaptiveSamplingPart, self).__init__(control_room, "Adaptive Sampling", part_name)
        self.__form_sliders = [
            FormSlider(self._control_room, FormSliderType.IntSlider, "Max Camera (AA)", part_name,
                       "defaultArnoldRenderOptions.AASamplesMax","max_camera_aa", 0, 20, 200),
            FormSlider(self._control_room, FormSliderType.FloatSlider, "Adaptive Treshold", part_name,
                       "defaultArnoldRenderOptions.AAAdaptiveThreshold", "adaptive_treshold", 0, 1),
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

    def __create_adaptive_sampling_override(self):
        """
        Create an override for the adaptive sampling field
        :return:
        """
        self.__adaptive_sampling_override = cr.ControlRoom.create_override("defaultArnoldRenderOptions",
                                                                           "enableAdaptiveSampling")

    def __remove_adaptive_sampling_override(self):
        """
        Remove the override for the adaptive sampling field
        :return:
        """
        cr.ControlRoom.remove_override(self.__adaptive_sampling_override)
        self.__adaptive_sampling_override = None

    def __retrieve_adaptive_sampling_override(self):
        """
        Retrieve the override for the adaptive sampling field
        :return:
        """
        self.__adaptive_sampling_override = cr.ControlRoom.retrieve_override("defaultArnoldRenderOptions",
                                                                             "enableAdaptiveSampling")

    def populate(self):
        """
        Generate the UI content of the AdaptiveSamplingPart
        :return: content
        """
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
        """
        Refresh the UI
        :return:
        """
        try:
            adaptive_sampling_enabled = pm.getAttr("defaultArnoldRenderOptions.enableAdaptiveSampling")
            for fs in self.__form_sliders:
                fs.refresh_ui()

            visible_layer = render_setup.instance().getVisibleRenderLayer()
            is_default_layer = visible_layer.name() == "defaultRenderLayer"
            self.__action_add_adaptive_sampling_override.setEnabled(
                not is_default_layer and self.__adaptive_sampling_override is None)
            self.__action_remove_adaptive_sampling_override.setEnabled(
                not is_default_layer and self.__adaptive_sampling_override is not None)

            stylesheet_lbl = self._control_room.get_stylesheet_color_for_field(
                self._part_name, "enable_adaptive_sampling",
                adaptive_sampling_enabled, self.__adaptive_sampling_override)

            hovered_preset = self._control_room.get_hovered_preset()
            if hovered_preset and hovered_preset.contains(self._part_name, "enable_adaptive_sampling"):
                self._preset_hovered = True
                self.__ui_enable_cb.setChecked(hovered_preset.get(self._part_name, "enable_adaptive_sampling"))
                self._preset_hovered = False
            else:
                self.__ui_enable_cb.setChecked(adaptive_sampling_enabled)

            self.__ui_enable_cb.setStyleSheet("QCheckBox{" + stylesheet_lbl + "}")
            self.__retrieve_adaptive_sampling_override()
        except:
            pass

    def __on_enable_changed(self, state):
        """
        On checkbox enable adaptive sampling changed
        :param state
        :return:
        """
        if not self._preset_hovered:
            pm.setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling", state == 2)

    def add_callbacks(self):
        """
        Add the callbacks
        :return:
        """
        self.__enable_callback = pm.scriptJob(
            attributeChange=["defaultArnoldRenderOptions.enableAdaptiveSampling", self.refresh_ui])
        for fs in self.__form_sliders:
            fs.add_callbacks()
        self.__layer_callback = pm.scriptJob(event=["renderLayerManagerChange", self.refresh_ui])

    def remove_callbacks(self):
        """
        Remoave the callbacks
        :return:
        """
        pm.scriptJob(kill=self.__enable_callback)
        for fs in self.__form_sliders:
            fs.remove_callbacks()
        pm.scriptJob(kill=self.__layer_callback)

    def add_to_preset(self, preset):
        """
        Add fields to a preset
        :param preset
        :return:
        """
        preset.set(self._part_name, "enable_adaptive_sampling", pm.getAttr("defaultArnoldRenderOptions.enableAdaptiveSampling"))
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            preset.set(self._part_name, key, pm.getAttr(field))

    def apply(self, preset):
        """
        Apply a preset on the part
        :param preset
        :return:
        """
        if preset.contains(self._part_name, "enable_adaptive_sampling"):
            pm.setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling", preset.get(self._part_name, "enable_adaptive_sampling"))
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            if preset.contains(self._part_name, key):
                pm.setAttr(field, preset.get(self._part_name, key))
