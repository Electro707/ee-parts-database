"""
E7EPD GUI Application
"""
from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QWidget, QTableWidget, QHBoxLayout

class PartsTable(QTableWidget):
    def __init__(self):
        super().__init__()

class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.parts = PartsTable()
        self.parts.setRowCount(2)
        self.parts.setColumnCount(6)
        self.parts.setHorizontalHeaderLabels(["Name", "Hex Code", "Color"])

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.parts)


def run_ui():
    app = QApplication([])

    widget = MainWidget()
    widget.resize(800, 600)
    widget.show()

    return app.exec()