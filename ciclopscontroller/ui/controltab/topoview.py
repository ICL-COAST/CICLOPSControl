import pyqtgraph as pg
import pyqtgraph.opengl as gl

from ciclopscontroller.controllers.satcontroller import SatController, PositionFrame
from ciclopscontroller.controllers.timecontroller import TimeController

import numpy as np

class TopoView(gl.GLViewWidget):
    def __init__(self, sat_controller: SatController, time_controller: TimeController):
        super().__init__()

        self.sat_controller = sat_controller
        self.time_controller = time_controller
        self.setup_ui()
        self.animation_update()

    def setup_ui(self):
        self.setCameraPosition(distance=1000)
        self.setBackgroundColor('k')

        topo_axis = gl.GLAxisItem()
        topo_axis.setSize(x=1000, y=1000, z=1000)
        topo_grid = gl.GLGridItem()
        topo_grid.setSize(x=700, y=700)
        topo_grid.setSpacing(x=100, y=100)
        self.addItem(topo_axis)
        self.addItem(topo_grid)
        
        self.sat_marker = gl.GLScatterPlotItem(
            pos = np.array([[0, 0, 500]]),  # Example position, should be updated with satellite position
            color = (1, 1, 1, 1),
            size = 15
        )
        self.sat_marker.setGLOptions('opaque')
        self.addItem(self.sat_marker)


        self.sat_trail = gl.GLLinePlotItem(
            pos = np.array([[-1000, 0, 450], [0, 0, 500], [1000, 0, 450]]),  # Example trail, should be updated with satellite positions
            color = (0, 1, 1, 1),
            width = 2,
            antialias=True
        )
        self.sat_trail.setGLOptions('opaque')
        self.addItem(self.sat_trail)

        north_marker = gl.GLScatterPlotItem(
            pos = np.array([[0, 1000, 0]]),  # Example position for north marker
            color = (1, 0, 0, 1),  # Red color for north marker
            size = 20
        )
        self.addItem(north_marker)

    def animation_update(self):
        sat_position = self.sat_controller.get_sat_position(PositionFrame.TOPO)
        sat_trail_positions = self.sat_controller.get_trail_positions(-30, 60, 100, PositionFrame.TOPO)
        if sat_position is not None:
            self.sat_marker.setData(pos=np.array(sat_position))
        if sat_trail_positions is not None:
            self.sat_trail.setData(pos=np.array(sat_trail_positions))