import pyqtgraph as pg
import pyqtgraph.opengl as gl

import numpy as np

class TopoView(gl.GLViewWidget):
    def __init__(self, sat_controller, time_controller):
        super().__init__()

        self.sat_controller = sat_controller
        self.time_controller = time_controller
        self.setup_ui()

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