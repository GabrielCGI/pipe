import os
import sys
import json
import logging

PRISM_QT_LIB = r"C:\ILLOGIC_APP\Prism\2.0.16\app\PythonLibs\Python3"
sys.path.append(os.path.join(PRISM_QT_LIB, "PySide"))
sys.path.append(PRISM_QT_LIB)

from ..checks import check as m_check

from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtSvg  import *

logger = logging.getLogger(__name__)

UI_DIR = os.path.dirname(__file__)
ICON_PATH = os.path.join(UI_DIR, 'Icons')
palettePath = os.path.join(UI_DIR, 'defaultPalette.json')
style_path = os.path.join(UI_DIR, 'style.qss')

with open(palettePath, "r") as file:
    palettedata = json.load(file)
with open(style_path, "r") as file:
    style_content = file.read()
for key, value in palettedata.items():
    style_content = style_content.replace(key, value)

def load_colored_svg(path, color, size,opacity=1.0):
    with open(path, 'r', encoding='utf-8') as file:
        svg_data = file.read()

    # Replace 'currentColor' with the actual color code
    svg_data = svg_data.replace('currentColor', color)

    renderer = QSvgRenderer(bytearray(svg_data, encoding='utf-8'))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setOpacity(opacity)
    renderer.render(painter)
    painter.end()

    return pixmap

class MainDialog(QDialog):

    def __init__(self, checkList='', stateManager='', path='', parent=None):
        super().__init__(parent)
        self.checkList = checkList
        self.stateManager = stateManager
        self.setWindowTitle(f"Sanity check - {path}")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowIcon(QIcon(os.path.join(ICON_PATH,"pinpin_icon.ico")))
        self.setObjectName(u"option_window_container")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QSize(500, 800))
        self.setMaximumSize(QSize(1200, 1000))
        self.setLayoutDirection(Qt.LeftToRight)
        self.setStyleSheet(style_content)
        self.create_scroll_area()
        self.create_widget()
        self.create_layout()
        self.connect_buttons()


    def createCheckRow(self, check):
        margin = 4
        # color
        if check.status:
            lightColor=palettedata['SUCCESS_COLOR_LIGHT']
            darkColor=palettedata['SUCCESS_COLOR_DARK']
            mainColor=palettedata['SUCCESS_COLOR']
        if not check.status:
            if check.severity == m_check.Severity.WARNING:
                lightColor=palettedata['WARNING_COLOR_LIGHT']
                darkColor=palettedata['WARNING_COLOR_DARK']
                mainColor=palettedata['WARNING_COLOR']
            elif check.severity == m_check.Severity.ERROR:
                lightColor=palettedata['FAIL_COLOR_LIGHT']
                darkColor=palettedata['FAIL_COLOR_DARK']
                mainColor=palettedata['FAIL_COLOR']
            else:
                lightColor=palettedata['FAIL_COLOR_LIGHT']
                darkColor=palettedata['FAIL_COLOR_DARK']
                mainColor=palettedata['FAIL_COLOR']
        # create the row header
        headerWidget = QWidget()
        headerWidget.setObjectName(u"headerWidget")
        headerLayout = QHBoxLayout(headerWidget)
        headerLayout.setContentsMargins(margin*5, margin, margin, margin)
        headerWidget.setStyleSheet(f"""
                #headerWidget {{
                    background-color:  {mainColor} ;
                }}
            """)
        headerLabel = QLabel(check.label)
        headerLayout.addWidget(headerLabel)
        headerLayout.addStretch()
        
        # add icons
        # haveFixCheckCase
        if check.have_fix:
            fixLabel = QLabel()
            fixLabel.setPixmap(load_colored_svg(os.path.join(ICON_PATH, "sledgehammer-svgrepo-com.svg"),lightColor, QSize(22, 22),1))
            # fixButton = QPushButton()
            # fixButton.setIcon(QIcon(load_colored_svg(os.path.join(ICON_PATH, "sledgehammer-svgrepo-com.svg"),lightColor, QSize(24, 24))))
            headerLayout.addWidget(fixLabel)
        # is valid
        if not check.status:
            validateLabel = QLabel()
            validateLabel.setPixmap(load_colored_svg(os.path.join(ICON_PATH, "close-square-svgrepo-com.svg"),lightColor, QSize(22, 22),1))
            headerLayout.addWidget(validateLabel)
        # is invalid
        if check.status:
            validateLabel = QLabel()
            validateLabel.setPixmap(load_colored_svg(os.path.join(ICON_PATH, "check-square-svgrepo-com.svg"),lightColor, QSize(22, 22),1))
            headerLayout.addWidget(validateLabel)
        
        toggle_button = QToolButton()
        toggle_button.setObjectName(u"toggle_button")
        toggle_button.setCheckable(True)
        toggle_button.setChecked(False)
        toggle_button.setIcon(QIcon(load_colored_svg(os.path.join(ICON_PATH, "alt-arrow-right-svgrepo-com.svg"),'#ffffff', QSize(24, 24),1)))
        toggle_button.setContentsMargins(0, 0, 0, 0)
        headerLayout.addWidget(toggle_button)
        
        # create the content area
        contentWidget = QWidget()
        contentWidget.setObjectName("contentWidget")
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(margin*4, margin, margin, margin)

        if hasattr(check, "documentation") and check.documentation:
            ruleLabelTitle = QLabel('<b>Documentation :</b>')
            contentLayout.addWidget(ruleLabelTitle)
            ruleLabel = QLabel(check.documentation)
            ruleLabel.setWordWrap(True)
            ruleLabel.setContentsMargins(margin*5, margin, margin, margin)
            contentLayout.addWidget(ruleLabel)

        commentLabelTitle = QLabel('<b>Comment :</b>')
        contentLayout.addWidget(commentLabelTitle)
        commentLabel = QLabel(check.message)
        commentLabel.setWordWrap(True)
        commentLabel.setContentsMargins(margin*5, margin, margin, margin)
        contentLayout.addWidget(commentLabel)

        if hasattr(check, "fixComment") and check.fixComment:
            fixcommentLabelTitle = QLabel('<b>fix :</b>')
            contentLayout.addWidget(fixcommentLabelTitle)
            fixcommentLabel = QLabel(check.fixComment)
            fixcommentLabel.setWordWrap(True)
            fixcommentLabel.setContentsMargins(margin*5, margin, margin, margin)
            contentLayout.addWidget(fixcommentLabel)
        
        contentWidget.setVisible(False)  # hidden by default
        # Toggle behavior
        def toggle_content():
            expanded = toggle_button.isChecked()
            if expanded:
                toggle_button.setIcon(QIcon(load_colored_svg(os.path.join(ICON_PATH, "alt-arrow-down-svgrepo-com.svg"),'#ffffff', QSize(22, 22))))
                headerWidget.setStyleSheet(f"""
                    #headerWidget {{
                        color=#ffffff;
                        background-color:  {mainColor} ;       
                        border-bottom-left-radius: 0px;
                        border-bottom-right-radius: 0px;
                    }}
                """)
            else :
                toggle_button.setIcon(QIcon(load_colored_svg(os.path.join(ICON_PATH, "alt-arrow-right-svgrepo-com.svg"),'#ffffff', QSize(22, 22))))
                headerWidget.setStyleSheet(f"""
                    #headerWidget {{
                        color=#ffffff;
                        background-color:  {mainColor} ;
                        border-bottom-left-radius: {palettedata['BORDER_RADIUS']};
                        border-bottom-right-radius: {palettedata['BORDER_RADIUS']};
                    }}
                """)
            contentWidget.setVisible(expanded)
        toggle_button.clicked.connect(toggle_content)
        # Main container widget with layout
        containerWidget = QWidget()
        containerLayout = QVBoxLayout(containerWidget)
        containerLayout.setSpacing(0)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.addWidget(headerWidget)
        containerLayout.addWidget(contentWidget)
        containerWidget.setStyleSheet(f"""
                #contentWidget {{
                    background-color:  {darkColor} ;
                    border: 2px solid  {mainColor} ;
                }}
            """)
        return containerWidget

    def create_widget(self):
        self.titleLabel = QLabel('waiting for sanity check to complete')
        self.titleLabel.setObjectName("titleLabel")
        self.titleLabel.setAlignment(Qt.AlignCenter)
        #self.refreshButton = QPushButton('Refresh Checks')
        self.cancelButton = QPushButton('Cancel Publish')
        self.cancelButton.setObjectName("cancelButton")
        self.acceptButton = QPushButton('Publish anyways')
        self.acceptButton.setObjectName("acceptButton")
        self.fixAllButton = QPushButton('Fix All Auto-Fixable Issues')
        self.fixAllButton.setObjectName("fixAllButton")

        self.refresh()
        
    def create_scroll_area(self):
        # scroll area
        self.rule_scroll_area = QScrollArea()
        self.rule_scroll_area.setWidgetResizable(True)
        self.rule_scroll_area_layout_widget = QWidget(self)
        self.rule_scroll_area_layout_widget.setObjectName("scroll_widget")
        self.rule_scroll_area_layout = QVBoxLayout(self.rule_scroll_area_layout_widget)
        self.rule_scroll_area.setWidget(self.rule_scroll_area_layout_widget)


    def create_check_widget(self):
        # Delete existing check
        while self.rule_scroll_area_layout.count():
            item = self.rule_scroll_area_layout.takeAt(0)
            if not item:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                self.rule_scroll_area_layout.removeItem(item)
                
        # each rules
        for rulesRow in self.rulesWidgets:
            self.rule_scroll_area_layout.addWidget(rulesRow)

        self.rule_verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.rule_scroll_area_layout.addItem(self.rule_verticalSpacer)
        

    def create_layout(self):
        # main layout
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setSpacing(12)
        self.mainLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        # title layout
        self.title_layout_widget = QWidget()
        self.title_layout_widget.setObjectName("rule_layout_widget")
        self.title_layout = QVBoxLayout()
        self.title_layout_widget.setLayout(self.title_layout)
        self.title_layout.setSpacing(0)
        self.title_layout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.title_layout.addWidget(self.titleLabel)
        self.mainLayout.addWidget(self.title_layout_widget)
        # rules layout
        self.rule_layout_widget = QWidget()
        self.rule_layout_widget.setObjectName("rule_layout_widget")
        self.rule_layout = QVBoxLayout()
        self.rule_layout_widget.setLayout(self.rule_layout)
        self.mainLayout.addWidget(self.rule_layout_widget)
        # scroll area
        self.rule_layout.addWidget(self.rule_scroll_area)
        # bottomButtons
        self.bottomButton_layout_widget = QWidget()
        self.bottomButton_layout_widget.setObjectName("bottomButton_layout_widget")
        self.bottomButton_layout = QGridLayout()
        self.bottomButton_layout_widget.setLayout(self.bottomButton_layout)
        self.bottomButton_layout.addWidget(self.cancelButton, 1, 0, 1, 2)
        self.bottomButton_layout.addWidget(self.acceptButton, 0, 0)
        self.bottomButton_layout.addWidget(self.fixAllButton, 0, 1)
        # self.bottomButton_layout.addWidget(self.refreshButton)
        self.mainLayout.addWidget(self.bottomButton_layout_widget)

    def refresh(self):
        logger.info(
            'Refresh check list with '
            f'{len(self.checkList)} new checks.')
        # Pass check again
        self.has_error = False
        self.has_no_error = True
        self.has_warning = False
        self.failed_check=[]
        self.success_check=[]

        for check in self.checkList:
            try:
                check.run(self.stateManager)
            except Exception as e:
                logger.error(e)
            if not check.status:
                self.failed_check.append(check)
                self.has_no_error = False
                if check.severity == m_check.Severity.ERROR:
                    self.has_error = True
                if check.severity == m_check.Severity.WARNING:
                    self.has_warning = True
            else:
                self.success_check.append(check)

        self.failed_check.sort(key=lambda x: x.severity)

        self.checkList = self.failed_check + self.success_check

        self.acceptButton.setEnabled(not self.has_error)
        
        # Create new check
        self.rulesWidgets=[]
        for check in self.checkList:
            layout = self.createCheckRow(check)
            self.rulesWidgets.append(layout)
        self.create_check_widget()

        # update the title
        if self.checkList:
            checkNumber=len(self.checkList)
            text=f'{len(self.success_check)}/{checkNumber} check passed'
            # Change text size
            font = self.titleLabel.font()
            font.setBold(True)
            font.setPointSize(24)  # 24 pt size
            self.titleLabel.setFont(font)
        else:
            text='no Rules detected'
        
        
        if self.has_warning == True:
            warningColor=palettedata['WARNING_COLOR_VERY_LIGHT']
            self.titleLabel.setStyleSheet(f"color: {warningColor};")
        if self.has_error == True:
            warningColor=palettedata['FAIL_COLOR_VERY_LIGHT']
            self.titleLabel.setStyleSheet(f"color: {warningColor};")
        if self.has_no_error == True:
            warningColor=palettedata['SUCCESS_COLOR_VERY_LIGHT']
            self.titleLabel.setStyleSheet(f"color: {warningColor};")
        self.titleLabel.setText(text)

        # update the publish button
        if self.has_no_error == True:
            self.acceptButton.setText('Publish')
            
    def run_fix(self):
        for check in self.checkList:
            if not check.status and check.have_fix:
                try:
                    check.fix(self.stateManager)
                except Exception as e:
                    logger.error(e)
        self.refresh()

    def connect_buttons(self):
        self.cancelButton.clicked.connect(self.reject)
        self.acceptButton.clicked.connect(self.accept)
        self.fixAllButton.clicked.connect(self.run_fix)
        # self.refreshButton.clicked.connect(self.refresh)
