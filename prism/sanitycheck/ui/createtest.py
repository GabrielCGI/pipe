from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

class HoverButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)

        self.setStyleSheet("background-color: #3498db; color: white; border: none; padding: 10px; font-size: 16px;")
        
        # Create animation for hover effect
        self.animation = QPropertyAnimation(self, b"styleSheet")
        self.animation.setDuration(300)  # Duration of the animation in milliseconds
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
    def enterEvent(self, event):
        # Start animation to change background color on hover
        self.animation.setStartValue("background-color: #3498db; color: white; border: none; padding: 10px; font-size: 16px;")
        self.animation.setEndValue("background-color: #00ccff; color: white; border: none; padding: 10px; font-size: 16px;")  # Hover color (light blue)
        self.animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # Reverse animation when mouse leaves the button
        self.animation.setStartValue("background-color: #00ccff; color: white; border: none; padding: 10px; font-size: 16px;")
        self.animation.setEndValue("background-color: #3498db; color: white; border: none; padding: 10px; font-size: 16px;")  # Default color (blue)
        self.animation.start()
        super().leaveEvent(event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hover Animation Button")

        # Set up the layout
        layout = QVBoxLayout()
        button = HoverButton("Hover Over Me")
        
        layout.addWidget(button)
        self.setLayout(layout)

app = QApplication([])
window = MainWindow()
window.show()
app.exec_()
