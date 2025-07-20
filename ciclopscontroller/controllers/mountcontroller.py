from PySide6.QtCore import QObject

from ciclopscontroller.controllers.timecontroller import TimeController
from ciclopscontroller.controllers.satcontroller import SatController

class MountController(QObject):
    def __init__(self, time_controller: TimeController, sat_controller: SatController):
        super().__init__()
        self.time_controller = time_controller
        self.sat_controller = sat_controller

