from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget
from ciclopscontroller.ui.choosertab import ChooserTab
from ciclopscontroller.ui.controltab import ControlTab

class SatelliteOrbitVisualizerGL(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Satellite Orbit Visualizer")
        self.setGeometry(100, 100, 800, 600)
        
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.control_tab = ControlTab()
        self.tabs.addTab(self.control_tab, "Control")
        
        self.chooser_tab = ChooserTab()
        self.tabs.addTab(self.chooser_tab, "Chooser")

