"""
ui module
"""
import sys
import os

import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui2
import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# Maya version specific imports
maya_version = int(cmds.about(apiVersion=True))

if maya_version >= 20250000:
    from PySide6.QtCore import *
    from PySide6.QtGui import *
    from PySide6.QtWidgets import *
    from shiboken6 import wrapInstance
else:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from shiboken2 import wrapInstance

if sys.version_info >= (3, 0):
    import mods.globals as g
    import mods.options as options
    import mods.tween as tween
else:
    import globals as g
    import options as options
    import tween as tween

tweener_window = None


def maya_useNewAPI():
    pass


def get_main_maya_window():
    ptr = omui.MQtUtil.mainWindow()

    if sys.version_info < (3, 0):
        try:
            ptr = int(ptr)
        except NameError:
            pass

    return wrapInstance(ptr, QMainWindow)


def show(restore=False):
    TweenerUIScript(restore=restore)


def close():
    if cmds.workspaceControl('tweenerUIWindowWorkspaceControl', exists=True):
        cmds.deleteUI('tweenerUIWindowWorkspaceControl')


def add_shelf_button(path=None):
    """
    Setup shelf button (during installation)
    """

    if not path:
        path = g.plugin_path

    if path.endswith('/'):
        path = path[:-1]

    icon_path = path + '/icons/tweener-icon.png'

    gShelfTopLevel = mel.eval('$tmpVar=$gShelfTopLevel')
    tabs = cmds.tabLayout(gShelfTopLevel, query=True, childArray=True)

    for tab in tabs:
        if cmds.shelfLayout(tab, query=True, visible=True):
            cmds.shelfButton(parent=tab, annotation='Open Tweener', label='Tweener',
                             image=icon_path,
                             useAlpha=True, style='iconOnly',
                             command="import maya.cmds as cmds\n"
                                     "if cmds.pluginInfo('tweener.py', q=True, registered=True):\n"
                                     "\tif cmds.pluginInfo('tweener.py', q=True, loaded=False):\n"
                                     "\t\tcmds.loadPlugin('tweener.py')\n"
                                     "\tcmds.tweener()\n"
                                     "else:\n"
                                     "\tcmds.warning('tweener.py is not registered')")


class TweenerUI(MayaQWidgetDockableMixin, QDialog):
    def __init__(self, parent=None):
        super(TweenerUI, self).__init__(parent=parent)

        # set slider window properties
        self.setWindowTitle('Tweener')

        if os.name == 'nt':  # windows platform
            self.setWindowFlags(Qt.Window)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        # maya's automatic window management, maybe not needed after workspace control
        # self.setProperty("saveWindowPref", True)

        # variables
        self.idle_callback = None
        self.dragging = False
        self.busy = False
        self.live_preview = True

        # define window dimensions
        self.setMinimumWidth(apply_dpi_scaling(418))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        # style
        self.setStyleSheet(
            'QLineEdit { padding: 0 %spx; border-radius: %spx; }'
            'QLineEdit:disabled { color: rgb(128, 128, 128); background-color: rgb(64, 64, 64); }'
            'QLabel:disabled { background-color: none; }'
            'QPushButton { padding: 0; border-radius: %spx; background-color: rgb(93, 93, 93); }'
            'QPushButton:hover { background-color: rgb(112, 112, 112); }'
            'QPushButton:pressed { background-color: rgb(29, 29, 29); }'
            'QPushButton:checked { background-color: rgb(82, 133, 166); }' % (
                apply_dpi_scaling(3),
                apply_dpi_scaling(2),
                apply_dpi_scaling(1))
        )

        widget_height = apply_dpi_scaling(16)

        # setup central widget and layout
        main_widget = self
        main_layout = QVBoxLayout(main_widget)
        # self.setCentralWidget(main_widget)

        margin = apply_dpi_scaling(4)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(apply_dpi_scaling(4))

        # top button layout
        self.toolbar_widget = QWidget(main_widget)
        main_layout.addWidget(self.toolbar_widget)

        toolbar_layout = QHBoxLayout(self.toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # mode buttons
        self.interpolation_mode = options.BlendingMode.between
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(apply_dpi_scaling(2))
        mode_between_btn = ModeButton(mode=options.BlendingMode.between,
                                      icon='icons/between.svg')
        mode_towards_btn = ModeButton(mode=options.BlendingMode.towards,
                                      icon='icons/towards.svg')
        mode_average_btn = ModeButton(mode=options.BlendingMode.average,
                                      icon='icons/average.svg')
        mode_curve_tangent_btn = ModeButton(mode=options.BlendingMode.curve,
                                            icon='icons/curve.svg')
        mode_default_btn = ModeButton(mode=options.BlendingMode.default,
                                      icon='icons/default.svg')

        mode_between_btn.clicked.connect(self.set_mode_button)
        mode_between_btn.setChecked(True)
        mode_towards_btn.clicked.connect(self.set_mode_button)
        mode_average_btn.clicked.connect(self.set_mode_button)
        mode_curve_tangent_btn.clicked.connect(self.set_mode_button)
        mode_default_btn.clicked.connect(self.set_mode_button)

        mode_between_btn.setToolTip(options.BlendingMode.between.tooltip)
        mode_towards_btn.setToolTip(options.BlendingMode.towards.tooltip)
        mode_average_btn.setToolTip(options.BlendingMode.average.tooltip)
        mode_curve_tangent_btn.setToolTip(options.BlendingMode.curve.tooltip)
        mode_default_btn.setToolTip(options.BlendingMode.default.tooltip)

        self.mode_button_group = QButtonGroup()
        self.mode_button_group.addButton(mode_between_btn)
        self.mode_button_group.addButton(mode_towards_btn)
        self.mode_button_group.addButton(mode_average_btn)
        self.mode_button_group.addButton(mode_curve_tangent_btn)
        self.mode_button_group.addButton(mode_default_btn)

        self.mode_button_group.setId(mode_between_btn,
                                     options.BlendingMode.between.idx)
        self.mode_button_group.setId(mode_towards_btn,
                                     options.BlendingMode.towards.idx)
        self.mode_button_group.setId(mode_average_btn,
                                     options.BlendingMode.average.idx)
        self.mode_button_group.setId(mode_curve_tangent_btn,
                                     options.BlendingMode.curve.idx)
        self.mode_button_group.setId(mode_default_btn,
                                     options.BlendingMode.default.idx)

        mode_layout.addWidget(mode_between_btn)
        mode_layout.addWidget(mode_towards_btn)
        mode_layout.addWidget(mode_average_btn)
        mode_layout.addWidget(mode_curve_tangent_btn)
        mode_layout.addWidget(mode_default_btn)

        # misc buttons
        misc_button_layout = QHBoxLayout()
        misc_button_layout.setSpacing(apply_dpi_scaling(2))

        self.overshoot_btn = ModeButton(icon='icons/overshoot.svg')
        self.overshoot_btn.clicked.connect(self.overshoot_button_clicked)
        self.overshoot_btn.setToolTip('Toggle Overshoot')

        self.keyhammer_btn = ModeButton(icon='icons/keyhammer.svg', is_checkable=False)
        self.keyhammer_btn.clicked.connect(self.keyhammer_button_clicked)
        self.keyhammer_btn.setToolTip('Hammer Keys')

        self.tick_draw_special_btn = ModeButton(icon='icons/tick-special.svg', is_checkable=False, mini_button=True)
        self.tick_draw_special_btn.clicked.connect(self.tick_draw_special_clicked)
        self.tick_draw_special_btn.setToolTip('Set special tick color for keyframe')

        self.tick_draw_normal_btn = ModeButton(icon='icons/tick-normal.svg', is_checkable=False, mini_button=True)
        self.tick_draw_normal_btn.clicked.connect(self.tick_draw_normal_clicked)
        self.tick_draw_normal_btn.setToolTip('Set normal tick color for keyframe')

        self.live_preview_btn = ModeButton(icon='icons/live-preview.svg', is_checkable=True)
        self.live_preview_btn.clicked.connect(self.live_preview_clicked)
        self.live_preview_btn.setToolTip('Live Preview')

        misc_button_layout.addWidget(self.overshoot_btn)
        misc_button_layout.addSpacerItem(QSpacerItem(8, 1, QSizePolicy.Minimum, QSizePolicy.Minimum))
        misc_button_layout.addWidget(self.keyhammer_btn)
        misc_button_layout.addSpacerItem(QSpacerItem(8, 1, QSizePolicy.Minimum, QSizePolicy.Minimum))
        misc_button_layout.addWidget(self.tick_draw_special_btn)
        misc_button_layout.addWidget(self.tick_draw_normal_btn)
        misc_button_layout.addSpacerItem(QSpacerItem(8, 1, QSizePolicy.Minimum, QSizePolicy.Minimum))
        misc_button_layout.addWidget(self.live_preview_btn)

        # fraction buttons
        self.preset_widget = QWidget(main_widget)
        main_layout.addWidget(self.preset_widget)

        self.preset_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        preset_layout = QHBoxLayout(self.preset_widget)
        preset_layout.setContentsMargins(0, 0, 0, 0)

        preset_layout.setSpacing(apply_dpi_scaling(2))
        rad = apply_dpi_scaling(12)
        self.preset_0_btn = PresetButton(radius=rad, fraction=0.0000)
        self.preset_1_btn = PresetButton(radius=rad, fraction=0.1667)
        self.preset_2_btn = PresetButton(radius=rad, fraction=0.2500)
        self.preset_3_btn = PresetButton(radius=rad, fraction=0.3333)
        self.preset_4_btn = PresetButton(radius=rad, fraction=0.5000)
        self.preset_5_btn = PresetButton(radius=rad, fraction=0.6667)
        self.preset_6_btn = PresetButton(radius=rad, fraction=0.7500)
        self.preset_7_btn = PresetButton(radius=rad, fraction=0.8333)
        self.preset_8_btn = PresetButton(radius=rad, fraction=1.0000)

        self.preset_0_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_0_btn))
        self.preset_1_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_1_btn))
        self.preset_2_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_2_btn))
        self.preset_3_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_3_btn))
        self.preset_4_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_4_btn))
        self.preset_5_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_5_btn))
        self.preset_6_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_6_btn))
        self.preset_7_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_7_btn))
        self.preset_8_btn.clicked.connect(lambda: self.fraction_clicked(self.preset_8_btn))

        preset_layout.addWidget(self.preset_0_btn)
        preset_layout.addWidget(self.preset_1_btn)
        preset_layout.addWidget(self.preset_2_btn)
        preset_layout.addWidget(self.preset_3_btn)
        preset_layout.addWidget(self.preset_4_btn)
        preset_layout.addWidget(self.preset_5_btn)
        preset_layout.addWidget(self.preset_6_btn)
        preset_layout.addWidget(self.preset_7_btn)
        preset_layout.addWidget(self.preset_8_btn)

        # slider
        slider_widget = QWidget(main_widget)
        main_layout.addSpacerItem(QSpacerItem(1, 8, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        main_layout.addWidget(slider_widget)
        slider_widget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        slider_layout = QHBoxLayout(slider_widget)
        slider_layout.setContentsMargins(0, 0, 0, 0)
        slider_layout.setSpacing(apply_dpi_scaling(4))

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFixedHeight(widget_height + apply_dpi_scaling(3))
        self.slider.setMinimumWidth(apply_dpi_scaling(100))
        self.slider.setTickInterval(1)

        self.slider.sliderPressed.connect(self.slider_pressed)
        self.slider.valueChanged.connect(self.slider_changed)
        self.slider.sliderReleased.connect(self.slider_released)

        groove_height = apply_dpi_scaling(10)
        groove_border_radius = int(groove_height / 2.0)
        groove_margin = apply_dpi_scaling(4)
        handle_border = apply_dpi_scaling(1)
        handle_margin = apply_dpi_scaling(-3) - handle_border
        handle_width = groove_height - 2 * handle_margin - 2 * handle_border
        handle_border_radius = int((handle_width + handle_border * 2) / 2.0)

        self.slider_style_normal = ("QSlider::groove:horizontal {"
                                    "background-color: #2B2B2B;"
                                    "border: 0px solid #2B2B2B;"
                                    "height: %spx;"
                                    "border-radius: %spx;"
                                    "margin: 0 %spx; padding: 0;"
                                    "}"
                                    "QSlider::handle:horizontal {"
                                    "background: #BDBDBD;"
                                    "width: %spx;"  # groove height = 10, plus margin -3px * 2 === 16px
                                    "border: %spx solid #2b2b2b;"
                                    "border-radius: %spx;"
                                    "margin: %spx 0; padding: 0;"  # negative margin expands outside groove
                                    "}" % (groove_height, groove_border_radius,
                                           groove_margin,
                                           handle_width, handle_border,
                                           handle_border_radius, handle_margin))

        self.slider_style_overshoot = ("QSlider::groove:horizontal {"
                                       "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                                       "stop:0.25 #48AAB5, stop:0.250001 #2B2B2B, stop: 0.75 #2B2B2B, stop:0.750001 #48AAB5);"
                                       "border: 0px solid #2B2B2B;"
                                       "height: %spx;"
                                       "border-radius: %spx;"
                                       "margin: 0 %spx; padding: 0;"
                                       "}"
                                       "QSlider::handle:horizontal {"
                                       "background: #BDBDBD;"
                                       "width: %spx;"  # groove height = 10, plus margin -3px * 2 === 16px
                                       "border: %spx solid #2b2b2b;"
                                       "border-radius: %spx;"
                                       "margin: %spx 0; padding: 0;"  # negative margin expands outside groove
                                       "}" % (groove_height, groove_border_radius,
                                              groove_margin,
                                              handle_width, handle_border,
                                              handle_border_radius, handle_margin))

        self.slider.setStyleSheet(self.slider_style_normal)

        slider_layout.setAlignment(self.slider, Qt.AlignCenter)
        slider_layout.addWidget(self.slider)

        # slider value label and version label
        slider_label_layout = QHBoxLayout(main_widget)
        slider_label_layout.setContentsMargins(0, 0, 0, 0)
        slider_label_layout.setSpacing(0)

        self.slider_label = QLabel('')
        self.slider_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

        version_label = QLabel(g.plugin_version)
        version_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version_label.setStyleSheet('color: rgba(255, 255, 255, 54); font-size: %spx;' % (apply_dpi_scaling(10)))

        slider_label_layout.addWidget(QWidget())  # empty widget to balance layout
        slider_label_layout.addWidget(self.slider_label)
        slider_label_layout.addWidget(version_label)

        # combine layouts
        toolbar_layout.addLayout(mode_layout)
        toolbar_layout.addStretch()
        toolbar_layout.addLayout(misc_button_layout)

        main_layout.addLayout(slider_label_layout)

        # right click menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_popup)
        self.popupMenu = QMenu()

        self.toolbar_action = self.PBSaveFileCB = self.popupMenu.addAction("Toolbar")
        self.toolbar_action.setCheckable(True)
        self.toolbar_action.triggered.connect(self.popup_toolbar_clicked)

        self.preset_action = self.PBSaveFileCB = self.popupMenu.addAction("Preset Buttons")
        self.preset_action.setCheckable(True)
        self.preset_action.triggered.connect(self.popup_presets_clicked)

        self.tick_draw_special_action = self.PBSaveFileCB = self.popupMenu.addAction("Special Key Tick Color")
        self.tick_draw_special_action.setCheckable(True)
        self.tick_draw_special_action.triggered.connect(self.popup_tick_draw_special_clicked)

        self.load_preferences()
        self.set_mode_button()
        self.update_slider_range()
        self.update_preset_buttons()

    def show_popup(self, position):
        self.popupMenu.exec_(self.mapToGlobal(position))

    def popup_toolbar_clicked(self, checked):
        self.toolbar_widget.setVisible(checked)
        options.save_toolbar(checked)

    def popup_presets_clicked(self, checked):
        self.preset_widget.setVisible(checked)
        options.save_presets(checked)

    def popup_tick_draw_special_clicked(self, checked):
        options.save_tick_draw_special(checked)

    def slider_pressed(self):
        self.dragging = True
        slider_value = self.slider.value() / 100.0

        blend = slider_value / 100.0

        self.interpolation_mode = self.mode_button_group.checkedButton().mode()

        # only update when maya is idle to prevent multiple calls without seeing the result
        self.idle_callback = om.MEventMessage.addEventCallback('idle', self.slider_changed)

        if self.live_preview:
            # disable undo on first call, so we don't get 2 undos in queue
            # both press and release add to the same cache, so it should be safe
            cmds.undoInfo(stateWithoutFlush=False)
            cmds.tweener(t=blend, newCache=True, type=self.interpolation_mode.idx)
            cmds.undoInfo(stateWithoutFlush=True)

            tween.interpolate(blend=blend, mode=self.interpolation_mode)

            if options.load_tick_draw_special():
                tween.tick_draw_special_custom(special=True)

    def slider_changed(self, *args):
        if self.busy or not self.dragging:
            return

        self.busy = True
        slider_value = self.slider.value()

        self.slider_label.setText('%.1f' % (slider_value / 100.0))

        if self.live_preview:
            blend = slider_value / 10000.0
            tween.interpolate(blend=blend, mode=self.interpolation_mode)

            view = omui2.M3dView()
            view = view.active3dView()
            view.refresh()

        QApplication.processEvents()
        self.busy = False

    def slider_released(self):
        self.dragging = False
        slider_value = self.slider.value() / 100.0

        blend = slider_value / 100.0
        if self.live_preview:
            cmds.tweener(t=blend, newCache=False, type=self.interpolation_mode.idx)
        else:
            cmds.tweener(t=blend, newCache=True, type=self.interpolation_mode.idx)

            if options.load_tick_draw_special():
                tween.tick_draw_special_custom(special=True)

        mode = options.load_interpolation_mode()
        default_value = 5000 if mode is options.BlendingMode.between else 0
        self.slider.setValue(default_value)
        self.slider_label.setText('')

        om.MEventMessage.removeCallback(self.idle_callback)

    def fraction_clicked(self, button):
        value = button.value

        self.interpolation_mode = self.mode_button_group.checkedButton().mode()
        cmds.undoInfo(openChunk=True, chunkName="tweener")
        try:
            cmds.tweener(t=value, newCache=True, type=self.interpolation_mode.idx)
            # cmds.tweener(t=value, newCache=False, type=self.interpolation_mode.idx)
        finally:
            cmds.undoInfo(closeChunk=True)

    def load_preferences(self):
        # set which mode button is checked
        try:
            button = self.mode_button_group.button(
                options.load_interpolation_mode().idx)
            if button is not None:
                button.setChecked(True)
        except Exception as e:
            sys.stdout.write('# %s\n' % e)
            for b in self.mode_button_group.buttons():
                b.setChecked(True)
                break

        # overshoot button checked state
        try:
            self.overshoot_btn.setChecked(options.load_overshoot())
        except Exception as e:
            self.overshoot_btn.setChecked(False)
            sys.stdout.write('# %s\n' % e)

        self.overshoot_button_clicked()  # simulate button click to setup slider values

        # live preview state
        try:
            self.live_preview_btn.setChecked(options.load_live_preview())
        except Exception as e:
            self.live_preview_btn.setChecked(True)
            sys.stdout.write('# %s\n' % e)

        self.live_preview_clicked()  # simulate clicked to setup values

        # visibility of toolbar and preset buttons
        try:
            v_t = options.load_toolbar()
            v_p = options.load_presets()
            v_tds = options.load_tick_draw_special()
            self.toolbar_widget.setVisible(v_t)
            self.toolbar_action.setChecked(v_t)
            self.preset_widget.setVisible(v_p)
            self.preset_action.setChecked(v_p)
            self.tick_draw_special_action.setChecked(v_tds)
        except Exception as e:
            sys.stdout.write('# %s\n' % e)

    def set_mode_button(self):
        options.save_interpolation_mode(int(self.mode_button_group.checkedId()))
        self.interpolation_mode = self.mode_button_group.checkedButton().mode()
        self.update_slider_range()
        self.update_preset_buttons()

    def overshoot_button_clicked(self):
        # save setting
        checked = self.overshoot_btn.isChecked()
        options.save_overshoot(checked)

        self.update_slider_range()
        self.update_preset_buttons()

    def update_slider_range(self):
        overshoot = options.load_overshoot()
        mode = options.load_interpolation_mode()

        if mode == options.BlendingMode.between:
            min_value = -5000 if overshoot else 0
            max_value = 15000 if overshoot else 10000
            self.slider.setValue(5000)
        else:
            min_value = -20000 if overshoot else -10000
            max_value = 20000 if overshoot else 10000
            self.slider.setValue(0)

        self.slider.setMinimum(min_value)
        self.slider.setMaximum(max_value)

        if overshoot:
            self.slider.setStyleSheet(self.slider_style_overshoot)
        else:
            self.slider.setStyleSheet(self.slider_style_normal)

    def update_preset_buttons(self):
        overshoot = self.overshoot_btn.isChecked()

        # without overshoot
        if not overshoot and self.interpolation_mode == options.BlendingMode.between:
            self.preset_0_btn.set_value(0.0000)
            self.preset_1_btn.set_value(0.1250)
            self.preset_2_btn.set_value(0.2500)
            self.preset_3_btn.set_value(0.3333)
            self.preset_4_btn.set_value(0.5000)
            self.preset_5_btn.set_value(0.6667)
            self.preset_6_btn.set_value(0.7500)
            self.preset_7_btn.set_value(0.8750)
            self.preset_8_btn.set_value(1.0000)
        elif not overshoot and self.interpolation_mode in [options.BlendingMode.towards,
                                                           options.BlendingMode.average,
                                                           options.BlendingMode.curve,
                                                           options.BlendingMode.default]:
            self.preset_0_btn.set_value(-1.0000)
            self.preset_1_btn.set_value(-0.6667)
            self.preset_2_btn.set_value(-0.5000)
            self.preset_3_btn.set_value(-0.3333)
            self.preset_4_btn.set_value(0.0000)
            self.preset_5_btn.set_value(0.3333)
            self.preset_6_btn.set_value(0.5000)
            self.preset_7_btn.set_value(0.6667)
            self.preset_8_btn.set_value(1.0000)

        # with overshoot
        if overshoot and self.interpolation_mode == options.BlendingMode.between:
            self.preset_0_btn.set_value(-0.5000)
            self.preset_1_btn.set_value(-0.2500)
            self.preset_2_btn.set_value(0.0000)
            self.preset_3_btn.set_value(0.2500)
            self.preset_4_btn.set_value(0.5000)
            self.preset_5_btn.set_value(0.7500)
            self.preset_6_btn.set_value(1.0000)
            self.preset_7_btn.set_value(1.2500)
            self.preset_8_btn.set_value(1.5000)
        elif overshoot and self.interpolation_mode in [options.BlendingMode.towards,
                                                       options.BlendingMode.average,
                                                       options.BlendingMode.curve,
                                                       options.BlendingMode.default]:
            self.preset_0_btn.set_value(-2.0000)
            self.preset_1_btn.set_value(-1.5000)
            self.preset_2_btn.set_value(-1.0000)
            self.preset_3_btn.set_value(-0.5000)
            self.preset_4_btn.set_value(0.0000)
            self.preset_5_btn.set_value(0.5000)
            self.preset_6_btn.set_value(1.0000)
            self.preset_7_btn.set_value(1.5000)
            self.preset_8_btn.set_value(2.0000)

    @staticmethod
    def keyhammer_button_clicked():
        cmds.undoInfo(openChunk=True, chunkName="keyHammer")
        try:
            result = cmds.keyHammer()
        finally:
            cmds.undoInfo(closeChunk=True)

        # API 2.0 seems to always return MPxCommand results as a list
        if isinstance(result, list) and len(result) >= 1:
            result = result[0]

        if not result:
            cmds.undo()

    @staticmethod
    def tick_draw_special_clicked():
        cmds.undoInfo(openChunk=True, chunkName="Changing tick color cannot be undone")
        try:
            tween.tick_draw_special(special=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    @staticmethod
    def tick_draw_normal_clicked():
        cmds.undoInfo(openChunk=True, chunkName="Changing tick color cannot be undone")
        try:
            tween.tick_draw_special(special=False)
        finally:
            cmds.undoInfo(closeChunk=True)

    def live_preview_clicked(self):
        checked = self.live_preview_btn.isChecked()
        self.live_preview = checked

        # save setting
        options.save_live_preview(checked)

    @staticmethod
    def v_separator_layout():
        layout = QVBoxLayout()

        layout.addSpacerItem(
            QSpacerItem(8, 1, QSizePolicy.Fixed, QSizePolicy.Fixed))

        frame = QFrame()
        frame.setFrameShape(QFrame.VLine)
        frame.setFixedWidth(apply_dpi_scaling(20))
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(frame)

        layout.addSpacerItem(
            QSpacerItem(8, 1, QSizePolicy.Fixed, QSizePolicy.Fixed))

        return layout


def TweenerUIScript(restore=False):
    """
    Function that gets calls for showing the UI, but also gets called by Maya when the workspace changes, like when
    entering full screen mode.
    """

    global tweener_window

    if tweener_window is None:
        if cmds.workspaceControl('tweenerUIWindowWorkspaceControl', exists=True):
            cmds.deleteUI('tweenerUIWindowWorkspaceControl')

        tweener_window = TweenerUI()
        tweener_window.setObjectName("tweenerUIWindow")

    if restore:
        restored_control = omui.MQtUtil.getCurrentParent()
        mixin_ptr = omui.MQtUtil.findControl(tweener_window.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(int(mixin_ptr), int(restored_control))
    else:
        try:
            tweener_window.show(dockable=True, retain=True,
                                height=tweener_window.sizeHint().height(),
                                checksPlugins=True, requiredPlugin='tweener.py',
                                uiScript="import maya.cmds as cmds;"
                                         "if cmds.pluginInfo('tweener.py', q=True, r=True) "
                                         "and cmds.pluginInfo('tweener.py', q=True, loaded=True) == False: "
                                         "cmds.loadPlugin('tweener.py', quiet=True);"
                                         "cmds.evalDeferred('cmds.tweenerUI(restore=False)', lp=True)")
        except Exception as e:
            sys.stdout.write('Error occured when restoring UI window %s' % str(e))

    # assume this is passed back to the workspace control through the uiScript
    return tweener_window


class ModeButton(QPushButton):
    """
    Subclass for creating the mode buttons (between, towards, curve, default...)
    """

    def __init__(self, label='', icon=None, is_checkable=True,
                 mini_button=False, mode=""):
        super(ModeButton, self).__init__(label)
        self.interpolation_mode = mode

        if mini_button:
            self.setMinimumSize(apply_dpi_scaling(30), apply_dpi_scaling(20))
        else:
            self.setMinimumSize(apply_dpi_scaling(50), apply_dpi_scaling(20))

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.setCheckable(is_checkable)

        if icon:
            if mini_button:
                self.setFixedSize(apply_dpi_scaling(20), apply_dpi_scaling(20))
            else:
                self.setFixedSize(apply_dpi_scaling(40), apply_dpi_scaling(20))

            self.setContentsMargins(0, 0, 0, 0)
            path = g.plugin_path + '/' + icon
            qicon = QIcon(path)
            self.setIconSize(QSize(apply_dpi_scaling(20),
                                   apply_dpi_scaling(20)))  # icons are designed to fit 16x16 but with 2px padding
            self.setIcon(qicon)

    def mode(self):
        return self.interpolation_mode


class PresetButton(QPushButton):
    """
    Subclass for creating and drawing the fraction buttons
    """

    def __init__(self, radius, fraction):
        super(PresetButton, self).__init__()

        self.value = 0
        self.angle = 0
        self.overshoot_angle = 0
        self.set_value(fraction)  # also sets angle

        stroke_w = apply_dpi_scaling(2)
        self.padding_y = apply_dpi_scaling(3)
        self.padding_x = apply_dpi_scaling(3)
        self.pie_rect_size = radius + stroke_w
        self.rect = QRect(self.padding_x, self.padding_y + stroke_w, self.pie_rect_size, self.pie_rect_size)

        # self.setFixedWidth(radius + self.padding_x * 2 + stroke_w)
        self.setFixedHeight(radius + 3 * stroke_w + self.padding_y * 2)
        # self.setFixedSize(radius + self.padding_x * 2 + stroke_w, radius + 3 * stroke_w + self.padding_y * 2)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.stroke_color = QColor(0, 0, 0)
        self.stroke_color.setNamedColor('#3A3A3A')  # maya semi dark gray
        self.base_color = QColor(0, 0, 0)
        self.base_color.setNamedColor('#BDBDBD')  # maya light gray
        self.accent_color = QColor(0, 0, 0)
        self.accent_color.setNamedColor('#DF6E41')  # maya orange
        self.overshoot_color = QColor(0, 0, 0)
        self.overshoot_color.setNamedColor('#48AAB5')  # maya teal

    def paintEvent(self, event):
        # draw the normal button
        super(PresetButton, self).paintEvent(event)

        # init painter
        painter = QPainter(self)
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)

        x = (self.geometry().width() - (
                self.padding_x * 2 + self.pie_rect_size)) / 2
        painter.translate(x, 0)

        # base area
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.stroke_color)
        painter.drawPie(self.rect, (self.angle - 90.0) * -16,
                        (360 - self.angle) * -16)

        # highlighted area
        if 0 < abs(self.angle) < 360:
            painter.setPen(QPen(self.stroke_color, apply_dpi_scaling(1)))
        painter.setBrush(self.accent_color)
        painter.drawPie(self.rect, 90.0 * 16, self.angle * -16)

        # overshoot area
        if 0 < abs(self.overshoot_angle) < 360:
            painter.setPen(QPen(self.stroke_color, apply_dpi_scaling(1)))
        painter.setBrush(self.overshoot_color)
        painter.drawPie(self.rect, 90.0 * 16, self.overshoot_angle * -16)

        # stroke
        painter.setPen(QPen(self.stroke_color, apply_dpi_scaling(1)))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self.rect)

        painter.end()

    def set_value(self, fraction):
        self.value = fraction

        self.angle = min(360.0, max(-360.0, fraction * 360.0))

        if fraction >= 0.0:
            self.overshoot_angle = max(0.0, (fraction - 1.0) * 360.0)
        else:
            self.overshoot_angle = min(0.0, (fraction + 1.0) * 360.0)

        self.overshoot_angle = min(360.0, max(-360.0, self.overshoot_angle))

        if self.angle < 0.0 and options.load_overshoot() and options.load_interpolation_mode() == options.BlendingMode.between:
            self.overshoot_angle = self.angle
            self.angle = 0

        # self.setToolTip(tooltip)
        self.update()


def apply_dpi_scaling(value, asfloat=False):
    if hasattr(cmds, 'mayaDpiSetting'):
        scale = cmds.mayaDpiSetting(query=True, realScaleValue=True)
        result = scale * value
    else:
        result = value

    if asfloat:
        return result
    else:
        return int(round(result))
