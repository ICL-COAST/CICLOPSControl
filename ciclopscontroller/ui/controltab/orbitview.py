import pyqtgraph as pg
import pyqtgraph.opengl as gl

from ciclopscontroller.controllers.satcontroller import SatController
from ciclopscontroller.controllers.timecontroller import TimeController

from ciclopscontroller.ui.glitems.glsphere import GLSphere

import numpy as np

class OrbitView(gl.GLViewWidget):
    def __init__(self, sat_controller, time_controller):
        super().__init__()

        self.sat_controller = sat_controller
        self.time_controller = time_controller

        self.earth_radius = 6371

        self.setup_ui()
        self.animation_update()

    def setup_ui(self):
        self.setCameraPosition(distance=15000)
        self.setBackgroundColor('k')

        self.add_earth()

        self.sat_marker = gl.GLScatterPlotItem(
            pos = np.array([[0, 0, 7000]]),  # Will be updated in animation_update
            color = (1, 1, 1, 1),
            size = 15
        )
        self.sat_marker.setGLOptions('opaque')
        self.addItem(self.sat_marker)


        self.sat_trail = gl.GLLinePlotItem(
            pos = np.array([[-1000, 0, 6900], [0, 0, 7000], [1000, 0, 6900]]),  # Will be updated in animation_update
            color = (0, 1, 1, 1),
            width = 2,
            antialias=True
        )
        self.sat_trail.setGLOptions('opaque')
        self.addItem(self.sat_trail)

        self.observer_marker = gl.GLScatterPlotItem(
            pos = np.array([[0, 0, self.earth_radius]])
        )
        self.observer_marker.setGLOptions('opaque')
        self.addItem(self.observer_marker)

        n_circles = 5
        n_points = 100
        self.terminator = []
        for j in range(n_circles):
            circle_points = []
            circle_radius = self.earth_radius * np.cos(j / n_circles * np.pi / 2)
            for i in range(n_points + 1):
                angle = 2 * np.pi * i / n_points
                x = circle_radius * np.cos(angle)
                y = 0
                z = circle_radius * np.sin(angle)
                circle_points.append([x, y, z])
            self.terminator.append(gl.GLLinePlotItem(
                pos=np.array(circle_points),
                color=(0.2, 0.2, 0.2, 1),
                width=2,
                mode='line_strip',
            ))
            self.terminator[-1].setGLOptions('opaque')
            self.addItem(self.terminator[-1])

    def add_earth(self):
        from PIL import Image
        earth_image = Image.open("ciclopscontroller/images/earth_texture.jpg")
        earth_image = earth_image.transpose(Image.Transpose.ROTATE_90).transpose(Image.Transpose.FLIP_LEFT_RIGHT).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        earth_array = np.array(earth_image)

        if earth_array.shape[2] == 3:  # RGB image
            earth_rgba = np.zeros((earth_array.shape[0], earth_array.shape[1], 4), dtype=np.uint8)
            earth_rgba[..., :3] = earth_array
            earth_rgba[..., 3] = 255  # Full opacity
        else:
            earth_rgba = earth_array
        self.earth_mesh = GLSphere(earth_rgba)
        self.addItem(self.earth_mesh)
    
    def animation_update(self):
        sat_position = self.sat_controller.get_sat_position()
        sat_trail_positions = self.sat_controller.get_trail_positions(-60, 60, 100)
        if sat_position is not None:
            self.sat_marker.setData(pos=np.array([sat_position]))
        if sat_trail_positions is not None:
            self.sat_trail.setData(pos=np.array(sat_trail_positions))

        self.update_terminator()

    def update_terminator(self):
        sun_direction = self.sat_controller.get_sun_direction()
        if sun_direction is None:
            return

        u_vector = np.array([0, 0, 1])
        u_vector = u_vector - np.dot(u_vector, sun_direction) * sun_direction
        u_vector /= np.linalg.norm(u_vector)

        v_vector = np.cross(sun_direction, u_vector)
        v_vector /= np.linalg.norm(v_vector)
        
        for i, circle in enumerate(self.terminator):
            angles = np.linspace(0, 2 * np.pi, 100)
            circle_radius = self.earth_radius * np.cos(i / len(self.terminator) * np.pi / 2)
            circle.setData(pos=
                           np.cos(angles) * u_vector * circle_radius +
                           np.sin(angles) * v_vector * circle_radius +
                            sun_direction * self.earth_radius * np.sin(i / len(self.terminator) * np.pi / 2)
                           )
                
            
