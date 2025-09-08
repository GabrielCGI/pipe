import os
import sys
import glob

STYLESHEET = ''

def import_qtpy():
    """
    Try to import qtpy from any prism install found in C:/ILLOGIC_APP/Prism.

    Returns:
        bool: True if the import path is found and False otherwise 
    """
    
    prism_qt_glob_pattern = "C:/ILLOGIC_APP/Prism/*/app/PythonLibs/*"

    found = False
    for path in glob.glob(prism_qt_glob_pattern):
        pyside_path = os.path.join(path, 'PySide')
        if os.path.exists(pyside_path):
            found = True
            break
    
    if not found:
        return False
    root_dir = os.path.dirname(os.path.dirname(path))
    if pyside_path not in sys.path:
        sys.path.append(pyside_path)
    if path not in sys.path:
        sys.path.append(path)
    stylesheet_mod = os.path.join(root_dir, "Scripts/UserInterfacesPrism/stylesheets")
    if not stylesheet_mod in sys.path:
        sys.path.append(stylesheet_mod)
    return True

# Import qt with qtpy of prism to match any version of qt found
# https://pypi.org/project/QtPy/
if import_qtpy():
    from qtpy import QtWidgets as Qt
    from qtpy import QtCore as Qtc
else:
    print(f'qtpy not found in C:/ILLOGIC_APP/Prism', file=sys.stderr)
    sys.exit(1)
    
    
from . import nuke_requests
    
class NukeLicenseParser(Qt.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle('Nuke Licenses')
        self.setMinimumSize(Qtc.QSize(600, 450))
        
        try:
            import blue_moon #type:ignore
            stylesheet = blue_moon.load_stylesheet()
            self.setStyleSheet(stylesheet)
        except Exception as e:
            print(f"Could not load stylesheet:\n\t{e}")

        self.mainLayout = Qt.QVBoxLayout()

        self.refreshButton = Qt.QPushButton(text="Refresh")
        self.refreshButton.clicked.connect(self.create_list_license)
        self.mainLayout.addWidget(self.refreshButton)

        self.listLicenses = Qt.QTableWidget()
        self.create_list_license()
        
        
        self.setLayout(self.mainLayout)


    def create_list_license(self):
        self.data = nuke_requests.main()
        self.listLicenses.setColumnCount(4)
        self.listLicenses.setRowCount(len(self.data))
        self.listLicenses.setHorizontalHeaderLabels(
            [
                'Pool',
                'is Used ?',
                'Limited to nuke 13.x ?',
                'Users'
            ]
        )
        self.listLicenses.setSortingEnabled(False)
        self.listLicenses.verticalHeader().setVisible(False)
        for i, pool in enumerate(self.data):
            data = self.data[pool]
            license_pool = Qt.QTableWidgetItem(pool)
            license_usage = Qt.QTableWidgetItem('X' if data.get('used') else "")
            license_limited = Qt.QTableWidgetItem('X' if data.get('limited') else "")
            license_user = Qt.QTableWidgetItem(data.get('user') if data.get('user') else "")
            license_pool.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            license_usage.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            license_limited.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            license_user.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            
            self.listLicenses.setItem(i, 0, license_pool)
            self.listLicenses.setItem(i, 1, license_usage)
            self.listLicenses.setItem(i, 2, license_limited)
            self.listLicenses.setItem(i, 3, license_user)
            
        self.listLicenses.setSizePolicy(
            Qt.QSizePolicy.Policy.Expanding,
            Qt.QSizePolicy.Policy.Expanding
        )
        
        self.listLicenses.horizontalHeader().setSectionResizeMode(Qt.QHeaderView.ResizeMode.Stretch)

        self.mainLayout.addWidget(self.listLicenses)
        
        
def main():
    app = Qt.QApplication.instance()

    app_start = False
    if app is None:
        app_start = True
        app = Qt.QApplication(sys.argv)
        
    dialog = NukeLicenseParser()
    dialog.show()
    
    if app_start:
        app.exec()
    
    return dialog