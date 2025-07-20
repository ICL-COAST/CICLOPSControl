from ciclopscontroller.controllers.timecontroller import TimeController
from PySide6.QtCore import QObject


class SatController(QObject):
    def __init__(self, time_controller):
        super().__init__()
        self.time_controller = time_controller

    def get_sat_position(self):
        # Placeholder for satellite position retrieval logic
        return None
    
    def get_trail_positions(self, start_time, end_time, n_points):
        # Placeholder for satellite trail position retrieval logic
        return None
    
    def get_sun_direction(self):
        return None