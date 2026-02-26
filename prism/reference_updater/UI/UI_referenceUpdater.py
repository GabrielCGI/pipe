from importlib import reload
import qtpy.QtWidgets as qt
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
from pathlib import Path
import json
import os
import re



from ..Core.RU_signal import signal
from ..subprocess import RU_subprocess
reload(RU_subprocess)


PRISM_IMPORT = True
DATA_PARSE = os.path.join(Path(os.path.dirname(__file__)).parent, "configs", "parser_data.json")



class MainUI(qt.QMainWindow):
    def __init__(self, Standalone, prism_Core, parent, scene_file=None):
        super().__init__(parent)
        self.setWindowTitle("Import and Update Assets in scene")
        self.resize(700, 800)
        self.all_combo_product: list[qt.QComboBox] = []
        self.project_path = prism_Core.projectPath.replace("\\", "/")
        self.Standalone = Standalone
        self.scene_file = scene_file
        self.core = None
        

        main_widget = qt.QWidget(self)
        self.setCentralWidget(main_widget)
        main_container = qt.QVBoxLayout(main_widget)


        options = qt.QHBoxLayout()
        main_container.addLayout(options)

        self.consoleMode = qt.QCheckBox("Console mode")
        self.consoleMode.setEnabled(self.Standalone)
        options.addWidget(self.consoleMode)

        options.addStretch()

        refresh = qt.QPushButton("refresh UI")
        refresh.setMinimumWidth(150)
        refresh.clicked.connect(self.startUI)
        options.addWidget(refresh)


        self.tabs = qt.QTabWidget()
        self.tabs.setStyleSheet("border: None")
        main_container.addWidget(self.tabs)


        exec_button = qt.QHBoxLayout()
        main_container.addLayout(exec_button)
        execution = qt.QPushButton("run Scripts")
        execution.clicked.connect(self.startScript)
        exec_button.addWidget(execution)

        autoHerarchie = qt.QPushButton("Auto Herarchie")
        autoHerarchie.clicked.connect(self.startScript)
        exec_button.addWidget(autoHerarchie)

        self.startUI()

    def startUI(self):
        self.tabs.clear()
        self.pannel_add_reference()
        self.panel_Reference_updater()



    # -------------------------- UI et Methode pour l'import des assets --------------------------
    def pannel_add_reference(self):
        table1 = qt.QWidget()
        self.tabs.addTab(table1, "Import References")

        container = qt.QVBoxLayout(table1)
        container.setContentsMargins(0, 10, 0 ,0)
        
        options = qt.QHBoxLayout()
        container.addLayout(options)
        show_product = qt.QLabel("Show Product")
        options.addWidget(show_product)

        self.hide_product = qt.QCheckBox("Show only this Product")
        self.hide_product.toggled.connect(lambda nul: self.changeAllComboAssets(False))
        options.addWidget(self.hide_product)

        self.select_product_show = qt.QComboBox()
        self.select_product_show.addItems(["Rigging", "Modeling", "USD", "toRig"])
        self.select_product_show.currentTextChanged.connect(lambda nul: self.changeAllComboAssets(True))
        self.select_product_show.setMinimumHeight(24)
        options.addWidget(self.select_product_show)


        self.folder_assets = qt.QTabWidget()
        container.addWidget(self.folder_assets)
        self.createTabsImport()
    
    def changeAllComboAssets(self, change):
        new_product = self.select_product_show.currentText()
        for combo, titre_index, row in self.all_combo_product:
            if change:
                combo.setCurrentText(new_product)

            if new_product not in combo.currentText() and self.hide_product.isChecked():
                self.folder_assets.widget(titre_index).setRowHidden(row, True)
            else:
                self.folder_assets.widget(titre_index).setRowHidden(row, False)
            
    def createTabsImport(self):
        folder = self.project_path + "03_Production/Assets"
        index = 0
        for titre in os.listdir(folder):
            if titre in self.dataHide("Assets", "hide_PahtAssets"):
                continue

            table = qt.QTableWidget()
            table.setObjectName(titre)

            table.setColumnCount(4)
            table.setHorizontalHeaderLabels([titre, "Nombre d'importations", "Products", "Versions"])
            items = self.findElement(f"{folder}/{titre}", "Assets", "hide_assets")
            table.setRowCount(len(items))
            
            for row, item_name in enumerate(items):
                item = qt.QTableWidgetItem(item_name)
                item.setFlags(item.flags() & ~qtc.Qt.ItemIsEditable)
                item.setFlags(item.flags() & ~qtc.Qt.ItemIsSelectable)
                table.setItem(row, 0, item)


                spin = NoWheelSpinBox()
                spin.setMinimum(0)
                spin.setMaximum(100)
                table.setCellWidget(row, 1, spin)

                combo = qt.QComboBox()
                data = self.findElement(f"{folder}/{titre}/{item_name}/Export", "Assets", "hide_products", True)
                combo.addItems(data)
                combo.setCurrentText("Rigging")
                table.setCellWidget(row, 2, combo)


                Qversion = qt.QLabel()
                Qversion.setAlignment(qtc.Qt.AlignCenter)
                table.setCellWidget(row, 3, Qversion)
                if not data:
                    data = [None]
                
                self.refreshVersionImport(Qversion, item, spin, f"{folder}/{titre}/{item_name}/Export/", combo)
                self.all_combo_product.append([combo, index, row])
                combo.currentIndexChanged.connect(
                    lambda nul, w=Qversion, it=item, s=spin, p=f"{folder}/{titre}/{item_name}/Export/", c=combo:
                    self.refreshVersionImport(w, it, s, p, c)
                    )


            self.folder_assets.addTab(table, titre)
            table.horizontalHeader().setResizeContentsPrecision(-1)
            table.resizeColumnsToContents()
            index += 1
    
    def refreshVersionImport(self, Qversion, item, spin, path, combo):
        data = combo.currentText()
        version = self.findLastVersionProduct(path, data)
        if version is None:
            item.setFlags(qtc.Qt.NoItemFlags)
            spin.setEnabled(False)
        
        Qversion.setText(version)
    
    def findLastVersionProduct(self, path: str, data: str) -> str:
        if not data:
            return None
        if not os.path.exists(f"{path}/{data}"):
            return None
        if not os.path.isdir(f"{path}/{data}"):
            return None

        return sorted(os.listdir(f"{path}/{data}"))[-1]



    # -------------------------- UI et Methode pour l'update des assets --------------------------
    def panel_Reference_updater(self) -> None:
        table2 = qt.QWidget()
        self.tabs.addTab(table2, "Update References")

        self.container_reference = qt.QVBoxLayout(table2)
        self.container_reference.setContentsMargins(0, 10, 0 ,0)
        
        options = qt.QHBoxLayout()
        self.container_reference.addLayout(options)
        show_reference = qt.QCheckBox("Show Reference not Update")
        show_reference.toggled.connect(self.hide_row)
        options.addWidget(show_reference)

        update_reference = qt.QCheckBox("Update All Reference")
        update_reference.toggled.connect(self.selectAutoUpdate)
        options.addWidget(update_reference)

        self.more_settings = qt.QCheckBox("More Settings")
        self.more_settings.toggled.connect(self.createTabReference)
        options.addWidget(self.more_settings)
        self.all_reference_scene = qt.QTableWidget(self)
        self.container_reference.addWidget(self.all_reference_scene)
        self.createTabReference()

    def createTabReference(self) -> None:
        base = self.project_path + "03_Production"
        
        self.all_reference_scene.clear()
        data_in_scene, nmb_ref = self.getDataScene()
        self.all_reference_scene.setColumnCount(5)
        self.all_reference_scene.setRowCount(nmb_ref)
        self.all_reference_scene.setHorizontalHeaderLabels(["Nodes reference", "Products name", " Actual version", "Last version", "Update version"])

        row = 0
        for info in self.iteration_Data(data_in_scene):
            Versions = ["Unknow"]
            path =f'{base}/{info["Type"]}/{info["cat"]}/{info["item"]}/Export/{info["entity"]}'
            if os.path.exists(path):
                Versions = sorted(os.listdir(path))
            
            # --- 1.Nodes reference column ---
            ref = qt.QTableWidgetItem(info["reference"])
            ref.setData(qtc.Qt.UserRole, info)
            ref.setFlags(ref.flags() & ~qtc.Qt.ItemIsEditable)
            ref.setFlags(ref.flags() & ~qtc.Qt.ItemIsSelectable)
            self.all_reference_scene.setItem(row, 0, ref)

            
            # --- 3.Actual version column ---
            ver = qt.QTableWidgetItem(info["version"])
            ver.setFlags(ver.flags() & ~qtc.Qt.ItemIsEditable)
            ver.setFlags(ver.flags() & ~qtc.Qt.ItemIsSelectable)
            self.all_reference_scene.setItem(row, 2, ver)

            # --- 4.Last version column ---
            last_version = qt.QLabel(Versions[-1])
            self.all_reference_scene.setCellWidget(row, 3, last_version)
            
            # --- 5.update version column ---
            if self.more_settings.isChecked():
                all_versions = qt.QComboBox()
                all_versions.addItems(Versions)
                all_versions.setCurrentText(info["version"])
                self.all_reference_scene.setCellWidget(row, 4, all_versions)
            else:
                take_last = qt.QCheckBox()
                take_last.setEnabled(Versions[-1] != info["version"])
                self.all_reference_scene.setCellWidget(row, 4, take_last)

            # --- 2.Products name column ---
            if self.more_settings.isChecked():
                combo = qt.QComboBox()
                data = self.findElement(f'{base}/{info["Type"]}/{info["cat"]}/{info["item"]}/Export', info["Type"], "hide_products", True)
                combo.addItems(data)
                combo.setCurrentText(info["entity"])
                combo.currentIndexChanged.connect(lambda nul, a=all_versions, la=last_version, p=f'{base}/{info["Type"]}/{info["cat"]}/{info["item"]}/Export', c=combo:
                    self.findAllversion(a, la, p, c)
                    )
                self.all_reference_scene.setCellWidget(row, 1, combo)
            else:
                Qentity = qt.QLabel(info["entity"])
                self.all_reference_scene.setCellWidget(row, 1, Qentity)
            

            # ------- apply color -------
            if not self.more_settings.isChecked():
                self.set_row_color(row, Versions[-1] != info["version"])

            row +=1

        self.all_reference_scene.horizontalHeader().setResizeContentsPrecision(-1)
        self.all_reference_scene.resizeColumnsToContents()

    def iteration_Data(self, data_in_scene: dict[dict]):
        for Type in data_in_scene:
            for cat in data_in_scene[Type]:
                for item in data_in_scene[Type][cat]:
                    for entity in data_in_scene[Type][cat][item]:
                        for i, reference in enumerate(data_in_scene[Type][cat][item][entity]["ref"]):
                            yield {
                            "Type": Type,
                            "cat": cat,
                            "item": item,
                            "entity": entity,
                            "reference": reference,
                            "version": data_in_scene[Type][cat][item][entity]["version"][i]
                            }

    def findAllversion(self, q_versions: qt.QComboBox, last_version: qt.QLabel, base_path: str, combo: qt.QComboBox) -> None:
        currant_product = combo.currentText()
        if not os.path.exists(f"{base_path}/{currant_product}"):
            return 
        Versions = ["Unknow"]
        path =f'{base_path}/{currant_product}'
        if os.path.exists(path):
            Versions = sorted(os.listdir(path))
                
        q_versions.clear()
        q_versions.addItems(Versions)
        last_version.setText(" " + Versions[-1] + " ")
        q_versions.setCurrentText(Versions[-1])

        for Qitem in [combo, q_versions, last_version]:
            Qitem.setFont(qtg.QFont("Segoe", 8, qtg.QFont.Bold))

    def set_row_color(self, row, condiftion):
        for col in range(self.all_reference_scene.columnCount()):
            item = self.all_reference_scene.item(row, col)
            widget = self.all_reference_scene.cellWidget(row, col)
            color = qtg.QColor("Green").darker(200) if not condiftion else qtg.QColor("Red").darker(350)
            if item:
                item.setBackground(color)
                item.setForeground(qtg.QColor("White"))
            if widget:
                t = color.toRgb()
                widget.setStyleSheet(f"background-color: rgb({t.red()}, {t.green()}, {t.blue()}); color: White")

    def hide_row(self, data):
        for row in range(self.all_reference_scene.rowCount()):
            item = self.all_reference_scene.item(row, 0)
            if 0 == item.background().color().redF() and data:
                self.all_reference_scene.setRowHidden(row, True)
            else:
                self.all_reference_scene.setRowHidden(row, False)

    def selectAutoUpdate(self, data):
        for row in range(self.all_reference_scene.rowCount()):
            item: qt.QCheckBox = self.all_reference_scene.cellWidget(row, 4)
            if item.isEnabled():
                item.setChecked(data)



    #  ----------------------------- commun fonction -----------------------------
    def getDataScene(self) -> list[dict, int]:
        if self.Standalone:
            return self.findDataInFile()
        else:
            if self.core is None:
                self.core = self.loadCore()
            return self.core.findAssetsInScene()
    
    def autoHiearchie(self):
        data = {"import":{}, "update":{}}
        
        if self.Standalone:
            self.prepareSubprocess(data)
        else:
            if self.core is None:
                self.core = self.loadCore()
            self.core.ExecutionProcedure(data)

    def startScript(self):
        data = {"import":{}, "update":{}}

        data["import"] = self.getDataToImport()
        data["update"] = self.getDataToUpdate()

        if self.Standalone:
            self.prepareSubprocess(data)
        else:
            if self.core is None:
                self.core = self.loadCore()
            self.core.ExecutionProcedure(data)
        
        self.startUI()
    
    def loadCore(self):
        from ..Core import RU_core
        reload(RU_core)
        return RU_core.RefUpdaterCore(self.Standalone, self.project_path)

    def autoHerarchie(self):
        if self.core is None:
            self.core = self.loadCore()

        return self.core.makeHerarchie()

    def getDataToImport(self):
        toImport = {}
        for tab_index in range(self.folder_assets.count()):
            widget_table: qt.QTableWidget = self.folder_assets.widget(tab_index)
            Type_table = self.folder_assets.tabText(tab_index)
            for row in range(widget_table.rowCount()):
                nmb_import = widget_table.cellWidget(row, 1).value()
                if nmb_import == 0:
                    continue

                asset = widget_table.item(row, 0).text()
                product = widget_table.cellWidget(row, 2).currentText()
                version = widget_table.cellWidget(row, 3).text()
                ref_name = f"{asset}_{product}"
                for _ in range(nmb_import):
                    self.pushData("Assets", Type_table, asset, product, version, ref_name, toImport)
        
        return toImport

    def getDataToUpdate(self):
        update = {}
        for row in range(self.all_reference_scene.rowCount()):
            Qref = self.all_reference_scene.item(row, 0)
            data_root = Qref.data(qtc.Qt.UserRole)
            ref_name = Qref.text()
            need_update = False
            
            Qproduct = self.all_reference_scene.cellWidget(row, 1)
            Qupdate = self.all_reference_scene.cellWidget(row, 4)
            if self.more_settings.isChecked():
                product = Qproduct.currentText()
                version = Qupdate.currentText()
                if product != data_root["entity"] or version != data_root["version"]:
                    need_update = True
            else:
                product = Qproduct.text()
                version = self.all_reference_scene.cellWidget(row, 3).text()
                need_update = Qupdate.isChecked()
            
            if not need_update:
                continue
            
            self.pushData(data_root["Type"], data_root["cat"], data_root["item"], product, version, ref_name, update)
    
        return update

    def pushData(self, Type: str, cat: str, asset: str, product: str, version: str, ref_name: str, data: dict) -> None:
        dict_Type = data.setdefault(Type, {})
        dict_cat = dict_Type.setdefault(cat, {})
        dict_item = dict_cat.setdefault(asset, {})

        if product not in dict_item:
            dict_item[product] = {"ref":[ref_name], "version":[version]}
        else:
            dict_item[product]["ref"].append(ref_name)
            dict_item[product]["version"].append(version)

    def dataHide(self, Type: str, data_find:str) -> list[str]:
        if not DATA_PARSE:
            return []
        
        json_data = None
        with open(DATA_PARSE, "r") as f:
            json_data:dict = json.loads(f.read())
        
        if not json_data:
            return []
        
        return json_data[Type].get(data_find, [])
    
    def findElement(self, path: str, Type: str, data_find: str, only_folder=False) -> list[str]:
        def cantContinue(data):
            for hide_data in data:
                if product.startswith(hide_data[:-1]) and hide_data.endswith("*"):
                    return True
                elif product.endswith(hide_data[1:]) and hide_data.startswith("*"):
                    return True
                elif product == hide_data:
                    return True
            
            return False
        
        if not os.path.exists(path):
            print("le chemin:", path, "n'est pas trouvable")
            return []
        
        good_product = []
        for product in os.listdir(path):
            if only_folder and not os.path.isdir(f"{path}/{product}"):
                continue
            if cantContinue(self.dataHide(Type, data_find)):
                continue
                
            good_product.append(product)

        return good_product



    # ------------------------------- standalone Methode -------------------------------
    def findDataInFile(self):
        #ouvre le fichier en type text pour lire ligne après ligne toute les data du fichier et recuppérer tout les référence de la scene maya
        if self.scene_file is None:
            return {}, None
        
        with open(self.scene_file, "r") as f:
            data_file = f.read()
        
        lignes = re.split(r';\s*', data_file)
        lignes = [l for l in lignes if l.strip()]

        data_ref_in_scene = {"Shots":{}, "Assets":{}}
        nmb_ref = 0
        for ligne in lignes:
            if ligne.startswith("file -r -ns "):
                results = re.findall(r'"([^"]*)"', ligne)
                file_path = results[-1]
                refeenceRN = results[1]

                entity = file_path.split(f"/03_Production/")[-1].split("/")
                Type = data_ref_in_scene.setdefault(entity[0], {})
                cat = Type.setdefault(entity[1], {})
                item = cat.setdefault(entity[2], {})

                if entity[4] not in item:
                    item[entity[4]] = {"ref":[refeenceRN], "version":[entity[5]]}
                else:
                    item[entity[4]]["ref"].append(refeenceRN)
                    item[entity[4]]["version"].append(entity[5])
                
                nmb_ref += 1
        
        return data_ref_in_scene, nmb_ref

    def prepareSubprocess(self, data):
        debug = self.consoleMode.isChecked()
        self.worker_RU = RU_subprocess.Worker(self.scene_file, data, debug)

        if not debug:
            self.waiter_RU = LoadingWindow("start execution")
            self.worker_RU.finished.connect(self.waiter_RU.close)
            self.waiter_RU.show()
        
        self.worker_RU.start()




class NoWheelSpinBox(qt.QSpinBox):
    def wheelEvent(self, event):
        event.ignore()
    



class LoadingWindow(qt.QWidget):
    def __init__(self, msg):
        super().__init__()
        self.setWindowTitle("Chargement...")
        self.setStyleSheet("background-color: #232323;")
        self.resize(500, 500)
        signal.connect(self.changeText)
        
        layout = qt.QVBoxLayout()
        self.setLayout(layout)


        self.scroller = qt.QScrollArea()
        layout.addWidget(self.scroller)

        data = qt.QVBoxLayout(self.scroller)
        self.all_return = qt.QLabel("")
        self.all_return.setWordWrap(True)
        data.addWidget(self.all_return)
        data.addStretch()


        self.progress_bar = qt.QProgressBar(self)
        layout.addWidget(self.progress_bar)
        self.progress_bar.setRange(0, 0)  # 0,0 → mode indéterminé (boucle infinie)

    
    def changeText(self, texte):
        old = self.all_return.text()
        self.all_return.setText(old + "\n" + texte)