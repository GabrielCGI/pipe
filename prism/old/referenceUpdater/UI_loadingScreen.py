import qtpy.QtWidgets as qt



class LoadingWindow(qt.QWidget):
    def __init__(self, msg):
        super().__init__()
        self.setWindowTitle("Chargement...")
        self.setFixedSize(300, 100)
        self.setStyleSheet("background-color: #232323;")

        layout = qt.QVBoxLayout()
        self.text = qt.QLabel(msg)
        layout.addWidget(self.text)

        self.progress_bar = qt.QProgressBar(self)
        #self.progress_bar.setStyleSheet("")
        self.progress_bar.setRange(0, 0)  # 0,0 → mode indéterminé (boucle infinie)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)