import pyqtgraph as pg
import pyqtgraph.opengl as gl


class SkyChartView(pg.PlotWidget):
    def __init__(self, sat_controller, time_controller):
        super().__init__()

        self.sat_controller = sat_controller
        self.time_controller = time_controller

        self.setup_ui()

    def setup_ui(self):
        self.setBackground('k')
        self.setTitle("Sky Chart")
        
        # Set up axes
        self.getAxis('bottom').setLabel('Right Ascension (h)')
        self.getAxis('left').setLabel('Declination (°)')
        
        # Add grid
        self.showGrid(x=True, y=True)
        
        # Example data
        self.plot([0, 1, 2], [0, 1, 0], pen='w', symbol='o', symbolSize=5)