from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget
from ciclopscontroller.ui.choosertab import ChooserTab
from ciclopscontroller.ui.controltab.controltab import ControlTab

from ciclopscontroller.controllers.satcontroller import SatController
from ciclopscontroller.controllers.mountcontroller import MountController
from ciclopscontroller.controllers.timecontroller import TimeController

class MainWindow(QMainWindow):
    def __init__(self, time_controller, mount_controller, sat_controller):
        super().__init__()

        self.time_controller = time_controller
        self.mount_controller = mount_controller
        self.sat_controller = sat_controller

        self.setWindowTitle("Satellite Orbit Visualizer")
        self.setGeometry(100, 100, 800, 600)
        
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.control_tab = ControlTab(sat_controller, mount_controller, time_controller)
        self.tabs.addTab(self.control_tab, "Control")
        
        self.chooser_tab = ChooserTab()
        self.tabs.addTab(self.chooser_tab, "Chooser")

