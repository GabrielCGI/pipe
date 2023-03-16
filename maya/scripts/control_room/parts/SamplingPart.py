from ControlRoomPart import *
from FormSlider import *
from pymel.core import *


class SamplingPart(ControlRoomPart):
    def __init__(self, control_room):
        super(SamplingPart, self).__init__(control_room, "Sampling")
        self.__form_sliders = [
            FormSlider(FormSliderType.IntSlider, "Camera (AA)",
                       "defaultArnoldRenderOptions.AASamples", "camera_aa", 0, 10, 100),
            FormSlider(FormSliderType.IntSlider, "Diffuse",
                       "defaultArnoldRenderOptions.GIDiffuseSamples", "diffuse", 0, 10, 100),
            FormSlider(FormSliderType.IntSlider, "Specular",
                       "defaultArnoldRenderOptions.GISpecularSamples", "specular", 0, 10, 100),
            FormSlider(FormSliderType.IntSlider, "Transmission",
                       "defaultArnoldRenderOptions.GITransmissionSamples", "transmission", 0, 10, 100),
            FormSlider(FormSliderType.IntSlider, "SSS",
                       "defaultArnoldRenderOptions.GISssSamples", "sss", 0, 10, 100),
            FormSlider(FormSliderType.IntSlider, "Volume Indirect",
                       "defaultArnoldRenderOptions.GIVolumeSamples", "indirect_vol", 0, 10, 100),
            FormSlider(FormSliderType.IntSlider, "Ray Depth Diffuse",
                       "defaultArnoldRenderOptions.GIDiffuseDepth", "ray_depth_diffuse", 0, 16, 160),
            FormSlider(FormSliderType.IntSlider, "Ray Depth Specular",
                       "defaultArnoldRenderOptions.GISpecularDepth", "ray_depth_specular", 0, 16, 160),
        ]
        self.__ui_progressive_render_cb = None
        self.__progressive_render_callback = None
        self.__layer_callback = None

        self.__progressive_render_override = None
        self.__action_add_progressive_render_override = QAction(text="Add Override")
        self.__action_add_progressive_render_override.triggered.connect(self.__create_progressive_render_override)
        self.__action_remove_progressive_render_override = QAction(text="Remove Override")
        self.__action_remove_progressive_render_override.triggered.connect(self.__remove_progressive_render_override)

        self.__retrieve_progressive_render_override()

    # Create progressive render override
    def __create_progressive_render_override(self):
        self.__progressive_render_override = cr.ControlRoom.create_override("defaultArnoldRenderOptions",
                                                                            "enableProgressiveRender")

    # Remove progressive render override
    def __remove_progressive_render_override(self):
        cr.ControlRoom.remove_override(self.__progressive_render_override)
        self.__progressive_render_override = None

    # Retrieve progressive render override
    def __retrieve_progressive_render_override(self):
        self.__progressive_render_override = cr.ControlRoom.retrieve_override("defaultArnoldRenderOptions",
                                                                              "enableProgressiveRender")

    def populate(self):
        content = QVBoxLayout()
        content.setContentsMargins(4, 4, 1, 4)

        self.__ui_progressive_render_cb = QCheckBox("Enable Progressive Render")
        self.__ui_progressive_render_cb.stateChanged.connect(self.__on_progressive_render_changed)
        self.__ui_progressive_render_cb.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.__ui_progressive_render_cb.addAction(self.__action_add_progressive_render_override)
        self.__ui_progressive_render_cb.addAction(self.__action_remove_progressive_render_override)

        content.addWidget(self.__ui_progressive_render_cb)

        form_layout = QFormLayout()
        content.addLayout(form_layout)

        for fs in self.__form_sliders:
            lbl, slider = fs.generate_ui()
            form_layout.addRow(lbl, slider)
        return content

    def refresh_ui(self):
        visible_layer = render_setup.instance().getVisibleRenderLayer()
        is_default_layer = visible_layer.name() == "defaultRenderLayer"
        self.__ui_progressive_render_cb.setChecked(getAttr("defaultArnoldRenderOptions.enableProgressiveRender"))
        for fs in self.__form_sliders:
            fs.refresh_ui()

        self.__action_add_progressive_render_override.setEnabled(
            not is_default_layer and self.__progressive_render_override is None)
        self.__action_remove_progressive_render_override.setEnabled(
            not is_default_layer and self.__progressive_render_override is not None)

        stylesheet_lbl = "color:" + cr.OVERRIDE_LABEL_COLOR if self.__progressive_render_override is not None else ""
        self.__ui_progressive_render_cb.setStyleSheet("QCheckBox{" + stylesheet_lbl + "}")

    # On enable progressive render checkbox changed
    def __on_progressive_render_changed(self, state):
        setAttr("defaultArnoldRenderOptions.enableProgressiveRender", state == 2)

    def add_callbacks(self):
        self.__progressive_render_callback = scriptJob(
            attributeChange=["defaultArnoldRenderOptions.enableProgressiveRender", self.refresh_ui])
        for fs in self.__form_sliders:
            fs.add_callbacks()
        self.__layer_callback = scriptJob(event=["renderLayerManagerChange", self.refresh_ui])

    def remove_callbacks(self):
        scriptJob(kill=self.__progressive_render_callback)
        for fs in self.__form_sliders:
            fs.remove_callbacks()
        scriptJob(kill=self.__layer_callback)

    def add_to_preset(self, part_name, preset):
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            preset.set(part_name, key, getAttr(field))
        preset.set(part_name, "progressive_render", getAttr("defaultArnoldRenderOptions.enableProgressiveRender"))

    def apply(self, part_name, preset):
        for fs in self.__form_sliders:
            key, field = fs.get_key_preset_and_field()
            setAttr(field, preset.get(part_name, key))
        setAttr("defaultArnoldRenderOptions.enableProgressiveRender", preset.get(part_name, "progressive_render"))
