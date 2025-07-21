import pyqtgraph as pg
import pyqtgraph.opengl as gl

import numpy as np

from ciclopscontroller.controllers.satcontroller import PositionFrame

class SkyChartView(pg.PlotWidget):
    def __init__(self, sat_controller, time_controller):
        super().__init__()

        self.sat_controller = sat_controller
        self.time_controller = time_controller

        self.setup_ui()
        self.animation_update()

    def setup_ui(self):
        # self.setBackground('k')
        # self.setTitle("Sky Chart")

        north_label = pg.TextItem("N", color=(255, 0, 0))
        north_label.setPos(0, 1.1)
        north_label.setAnchor((0.5, 0.5))
        self.addItem(north_label)

        east_label = pg.TextItem("E", color=(255, 0, 0))
        east_label.setPos(-1.1, 0)
        east_label.setAnchor((0.5, 0.5))
        self.addItem(east_label)

        south_label = pg.TextItem("S", color=(255, 0, 0))
        south_label.setPos(0, -1.1)
        south_label.setAnchor((0.5, 0.5))
        self.addItem(south_label)

        west_label = pg.TextItem("W", color=(255, 0, 0))
        west_label.setPos(1.1, 0)
        west_label.setAnchor((0.5, 0.5))
        self.addItem(west_label)

        north_marker = pg.ScatterPlotItem(
            pos=np.array([[0, 2]]),  # North marker at the top
            pen=pg.mkPen(color=(255, 0, 0)),
            brush=pg.mkBrush(color=(255, 0, 0)),
            size=10
        )
        self.addItem(north_marker)

        self.setAspectLocked(True)
        self.setXRange(-1.5, 1.5)
        self.setYRange(-1.5, 1.5)

        horizon_circle = pg.QtWidgets.QGraphicsEllipseItem(-1, -1, 2, 2)
        horizon_circle.setPen(pg.mkPen(color=(255, 255, 255, 100), width=1))
        self.addItem(horizon_circle)

        self.sat_marker = pg.ScatterPlotItem(
            pos = np.array([[0, 0]]),  # Will be updated in animation_update
            pen=pg.mkPen(color=(255, 255, 255)),
            brush=pg.mkBrush(color=(255, 255, 255, 255)),
            size=10
        )
        self.addItem(self.sat_marker)


        self.sat_trail = pg.PlotCurveItem(
            x = np.array([-1, 0, 1]),  # Will be updated in animation_update
            y = np.array([0, 0, 0]),
            pen=pg.mkPen(color=(0, 255, 255), width=2),
            # antialias=True
        )
        self.addItem(self.sat_trail)

    def animation_update(self):
        sat_position = self.sat_controller.get_sat_position(PositionFrame.ALTAZ)
        sat_trail_positions = self.sat_controller.get_trail_positions(-30, 60, 100, PositionFrame.ALTAZ) # Alt, Az

        if sat_position is not None:
            self.sat_marker.setData(pos=self.altaz_to_skychart(sat_position))
        if sat_trail_positions is not None:
            skychart_trail = self.altaz_to_skychart(sat_trail_positions)
            self.sat_trail.setData(x=skychart_trail[:, 0], y=skychart_trail[:, 1])

    def altaz_to_skychart(self, altaz):
        if altaz.ndim == 1:
            altaz = altaz.reshape(1, 2)
        radius = 1 - altaz[:, 0] * 2 / np.pi
        east = - radius * np.sin(altaz[:, 1])
        north = radius * np.cos(altaz[:, 1])
        return np.array([east, north]).T
