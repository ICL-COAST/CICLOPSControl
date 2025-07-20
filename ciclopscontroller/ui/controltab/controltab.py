from PySide6.QtWidgets import QWidget
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QSlider, QPushButton, QDoubleSpinBox
from PySide6.QtCore import Qt, QTimer
import numpy as np
from ciclopscontroller.ui.controltab.orbitview import OrbitView
from ciclopscontroller.ui.controltab.topoview import TopoView
from ciclopscontroller.ui.controltab.skychartview import SkyChartView

from ciclopscontroller.controllers.mountcontroller import MountController
from ciclopscontroller.controllers.satcontroller import SatController
from ciclopscontroller.controllers.timecontroller import TimeController

from ciclopscontroller.ui.controltab.timecontrolbox import TimeControlBox
from ciclopscontroller.ui.controltab.mountcontrolbox import MountControlBox

class ControlTab(QWidget):
    def __init__(self, sat_controller, mount_controller, time_controller):
        super().__init__()

        self.sat_controller = sat_controller
        self.mount_controller = mount_controller
        self.time_controller = time_controller

        self.orbit_view = OrbitView(sat_controller, time_controller)
        self.topo_view = TopoView(sat_controller, time_controller)
        self.skychart_view = SkyChartView(sat_controller, time_controller)
        
        views_layout = QGridLayout()
        views_layout.addWidget(self.orbit_view, 0, 0)
        views_layout.addWidget(self.topo_view, 0, 1)
        views_layout.addWidget(self.skychart_view, 0, 2)
        views_layout.setColumnStretch(0, 1)
        views_layout.setColumnStretch(1, 1)
        views_layout.setColumnStretch(2, 1)

        controls_box = QVBoxLayout()

        self.time_control_box = TimeControlBox(self.time_controller, lambda: self.update_views(override=True))
        self.mount_control_box = MountControlBox(self.mount_controller)
        controls_box.addWidget(self.time_control_box)
        controls_box.addWidget(self.mount_control_box)


        main_layout = QVBoxLayout()
        main_layout.addLayout(views_layout)
        main_layout.addLayout(controls_box)
        self.setLayout(main_layout)

        self._timer = QTimer()
        self._timer.timeout.connect(self.update_views)
        self._timer.start(50)

    def update_views(self, override=False):
        self.time_control_box.update_time()

        if self.time_controller.get_running() or override:
            self.orbit_view.animation_update()
            # self.topo_view.animation_update()
            # self.skychart_view.animation_update()