import os
import subprocess
import sys
import glob
import concurrent.futures


STYLESHEET = ''
URL = '10.16.34.37'
PORT = 46119


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

        self.usedNuke15 = 0
        self.totalNuke15 = 0
        self.usedNuke13 = 0
        self.totalNuke13 = 0

        self.listLicenses = Qt.QTableWidget()
        self.summaryLabel = Qt.QLabel()
        self.create_list_license()

        
        
        self.setLayout(self.mainLayout)


    def create_list_license(self):

        self.usedNuke15 = 0
        self.totalNuke15 = 0
        self.usedNuke13 = 0
        self.totalNuke13 = 0

        self.data = nuke_requests.main()
        self.listLicenses.setColumnCount(5)
        self.listLicenses.setRowCount(len(self.data))
        self.listLicenses.setHorizontalHeaderLabels(
            [
                'Pool',
                'Nuke 15+',
                'Nuke 13',
                'Users',
                'Click to REMOVE' 
            ]
        )
        self.listLicenses.setSortingEnabled(False)
        self.listLicenses.verticalHeader().setVisible(False)
        for i, pool in enumerate(self.data):
            data = self.data[pool]
            
            license_pool = Qt.QTableWidgetItem(pool)
            license_usage = Qt.QTableWidgetItem('X' if not(data.get('limited')) else "")
            license_limited = Qt.QTableWidgetItem('X' if data.get('limited') else "")
            license_user = Qt.QTableWidgetItem(data.get('user') if data.get('user') else "")
            license_pool.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            license_usage.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            license_limited.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            license_user.setTextAlignment(Qtc.Qt.AlignmentFlag.AlignCenter)
            if data.get('used'):
                license_remove = Qt.QPushButton(text="REMOVE")
                license_remove.clicked.connect(lambda checked, p=pool :  self.confirmation_dialog(p))
                license_remove.setEnabled(True)
                self.listLicenses.setCellWidget(i, 4, license_remove)
            else:
                self.listLicenses.setCellWidget(i, 4, None)


            self.listLicenses.setItem(i, 0, license_pool)
            self.listLicenses.setItem(i, 1, license_usage)
            self.listLicenses.setItem(i, 2, license_limited)
            self.listLicenses.setItem(i, 3, license_user)
            self.listLicenses.setItem(i, 4, Qt.QTableWidgetItem())

            if data.get('used') :
                self.user = data.get('user') if data.get('user') else ""
                self.listLicenses.setCellWidget(i, 4, license_remove)

            if data.get('limited'):
                if data.get('used'):
                    self.usedNuke13+=1
                self.totalNuke13+=1
            else:
                if data.get('used'):
                    self.usedNuke15+=1
                self.totalNuke15+=1

        self.listLicenses.setSizePolicy(
            Qt.QSizePolicy.Policy.Expanding,
            Qt.QSizePolicy.Policy.Expanding
        )

        self.generate_summary()

        self.listLicenses.horizontalHeader().setSectionResizeMode(Qt.QHeaderView.ResizeMode.Stretch)

        self.mainLayout.addWidget(self.listLicenses)



    def confirmation_dialog(self, pool):

        data = self.data[pool]
        current_user = data.get('user') if data.get('user') else ""

        self.confirmDialog = Qt.QMessageBox(self)
        self.confirmDialog.setWindowTitle("Confirm remove")
        self.confirmDialog.setText("Are you sure you want to remove " + current_user + "'s session?")
        self.confirmDialog.setIcon(Qt.QMessageBox.Warning)

        self.confirmDialog.setStandardButtons(Qt.QMessageBox.Ok | Qt.QMessageBox.Cancel)

        self.confirmDialog.okButton = self.confirmDialog.button(Qt.QMessageBox.Ok)
        # self.confirmDialog.okButton.clicked.connect(lambda : self.remove_license(pool))        
        self.confirmDialog.okButton.clicked.connect(lambda : self.remove_license_parallel(pool))
        self.confirmDialog.exec()

    def remove_license_parallel(self, pool):
        ''' 
            Remove user from his license
        '''

        # Get necessary info from data
        handles = self.data[pool]['handles']
        user = self.data[pool].get('user')

        # define path variables for readabiliry
        path = r"R:\softs\rlmutils"
        exe = os.path.join(path , "rlmutil.exe")

        # sub function that calls the rlmremove and returns whether or not it worsk
        def _remove(h):
            p = subprocess.run([exe, 'rlmremove', '-q', URL, str(PORT), 'foundry', str(h)], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            
            not_removed = "not removed" in str(p.stdout)

            if not_removed : 
                return (h , -1)
            else:
                return (h, p.returncode)

        # Parallelise (execute on multiple threads the _remove func)
        max_workers = min(12, len(handles)) # Gotta adapt this to see how far we can push it
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            for h, result in ex.map(_remove, handles):
                if result == -1:
                    notif_text = user + "'s license could not be removed"
                    break
                else : 
                    notif_text = user + "'s license was successfully removed"

        # Display when it's all done
        self.remove_user = Qt.QMessageBox(self)
        self.remove_user.setWindowTitle("Remove user")
        self.remove_user.setText(notif_text)
        self.remove_user.exec()        
        self.create_list_license()


    

    def generate_summary(self):

        self.usedLicenses = self.usedNuke15 + self.usedNuke13
        self.totalLicenses = self.totalNuke15 + self.totalNuke13

        self.summaryLabel.setText(f"Nuke15 licenses used : {self.usedNuke15}/{self.totalNuke15} \n\
Nuke13 licenses used : {self.usedNuke13}/{self.totalNuke13} \n\
Total licenses used : {self.usedLicenses}/{self.totalLicenses}")

        self.mainLayout.addWidget(self.summaryLabel)

        
        
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