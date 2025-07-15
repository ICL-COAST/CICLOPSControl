import sys
import numpy as np
from datetime import datetime, timedelta
from time import perf_counter
import skyfield.api as sf
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QSlider, QLabel, QComboBox,
                            QFileDialog, QGroupBox, QDoubleSpinBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import signal
import os
import math

class SatelliteOrbitVisualizerGL(QMainWindow):
    """Main application window using OpenGL for 3D visualization"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("3D Satellite Orbit Visualizer")
        self.resize(1200, 800)
        
        # Initialize data
        self.satellites = {}
        # self.current_time = datetime.now()
        self.current_time = datetime(2025, 7, 15, 0, 0, 0)
        self.time_step = timedelta(minutes=0.1)
        self.animation_speed = 1

        self.is_animating = False
        self.earth_radius = 6371  # km
        self.orbit_items = []
        
        # Cache for orbit trail
        self.orbit_trail = None
        self.current_marker = None
        self.last_trail_update = None
        self.trail_update_interval = 1.0  # Update trail every 1 second

        self.topo_trail = None
        self.topo_marker = None
        
        self.sky_marker = None
        self.sky_trail = None

        # Earth texture and rotation
        self.earth_mesh = None
        self.terminator_circle = None
        self.london_marker = None
        
        # London coordinates (latitude, longitude)
        # self.london_lat = 51.5074  # degrees North
        self.london_lat = 49  # degrees North
        self.london_lon = -0.1278  # degrees East (negative for West)
        
        # Load ephemeris for astronomical calculations
        self.ts = sf.load.timescale()
        self.earth = sf.load('de421.bsp')['earth']
        self.sun = sf.load('de421.bsp')['sun']
        
        # Setup UI
        self.setup_ui()
        
        # Create initial plot
        self.setup_3d_view()

        self.load_tle_data()  # Load TLE data on startup
        
        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.animation_step)

        self.cycle_start = 0
        self.cycle_end = 0

    def setup_ui(self):
        """Create the user interface"""
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 3D view widgets
        self.view_layout = QGridLayout()
        self.view_widget = gl.GLViewWidget()
        self.topo_widget = gl.GLViewWidget()
        self.sky_widget = pg.PlotWidget()

        self.view_layout.addWidget(self.view_widget, 0, 0)
        self.view_layout.addWidget(self.topo_widget, 0, 1)
        self.view_layout.addWidget(self.sky_widget, 0, 2)

        self.view_layout.setColumnStretch(0, 1)
        self.view_layout.setColumnStretch(1, 1)
        self.view_layout.setColumnStretch(2, 1)

        main_layout.addLayout(self.view_layout)

        # Controls container
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        
        # Time controls group
        time_group = QGroupBox("Time Controls")
        time_layout = QVBoxLayout(time_group)
        
        time_slider_layout = QHBoxLayout()
        self.time_label = QLabel(f"Current Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        time_layout.addWidget(self.time_label)
        
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(-240, 240)  # ±24 hours
        self.time_slider.setValue(0)
        self.time_slider.setSingleStep(1)
        self.time_slider.setTickInterval(10)
        self.time_slider.setTickPosition(QSlider.TicksBelow)
        self.time_slider.valueChanged.connect(self.on_time_slider_changed)
        time_slider_layout.addWidget(QLabel("-24h"))
        time_slider_layout.addWidget(self.time_slider)
        time_slider_layout.addWidget(QLabel("+24h"))
        time_layout.addLayout(time_slider_layout)
        
        # Animation controls
        animation_layout = QHBoxLayout()
        self.animation_btn = QPushButton("Start Animation")
        self.animation_btn.clicked.connect(self.toggle_animation)
        animation_layout.addWidget(self.animation_btn)
        
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.1, 10.0)
        self.speed_spinbox.setValue(1.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_spinbox)
        animation_layout.addLayout(speed_layout)
        
        time_layout.addLayout(animation_layout)
        controls_layout.addWidget(time_group)
        
        # Satellite controls group
        sat_group = QGroupBox("Satellite Controls")
        sat_layout = QVBoxLayout(sat_group)
        
        # Add satellite button
        load_layout = QHBoxLayout()
        # self.load_tle_btn = QPushButton("Load TLE")
        # self.load_tle_btn.clicked.connect(self.load_tle_data)
        # load_layout.addWidget(self.load_tle_btn)
        
        self.sat_combo = QComboBox()
        self.sat_combo.currentIndexChanged.connect(self.update_orbits)
        load_layout.addWidget(self.sat_combo)
        sat_layout.addLayout(load_layout)
        
        # Trail length control
        trail_layout = QHBoxLayout()
        trail_layout.addWidget(QLabel("Trail Length:"))
        self.trail_spinbox = QDoubleSpinBox()
        self.trail_spinbox.setRange(0, 24)
        self.trail_spinbox.setValue(2)
        self.trail_spinbox.setSingleStep(0.5)
        self.trail_spinbox.setSuffix(" hours")
        self.trail_spinbox.valueChanged.connect(self.update_orbits)
        trail_layout.addWidget(self.trail_spinbox)
        sat_layout.addLayout(trail_layout)
        
        controls_layout.addWidget(sat_group)
        
        # Camera/View Controls
        view_group = QGroupBox("View Controls")
        view_layout = QVBoxLayout(view_group)
        
        view_reset_btn = QPushButton("Reset View")
        view_reset_btn.clicked.connect(self.reset_view)
        view_layout.addWidget(view_reset_btn)
        
        controls_layout.addWidget(view_group)
        
        # Add controls to main layout
        main_layout.addWidget(controls_container)
        controls_container.setMaximumHeight(200)
        
        # Set the central widget
        self.setCentralWidget(main_widget)

    def setup_3d_view(self):
        """Initialize the 3D view with Earth"""
        # Set view center and distance
        self.view_widget.setCameraPosition(distance=40000)
        
        # Add coordinate axes
        axis = gl.GLAxisItem()
        axis.setSize(10000, 10000, 10000)
        self.view_widget.addItem(axis)
        
        # Add Earth
        sphere_mesh = gl.MeshData.sphere(rows=40, cols=40, radius=self.earth_radius)
        self.earth_mesh = gl.GLMeshItem(meshdata=sphere_mesh, smooth=True, color=(0.2, 0.5, 0.8, 0.8), shader='shaded')
        self.view_widget.addItem(self.earth_mesh)
        
        
        # Grid
        grid = gl.GLGridItem()
        grid.setSize(20000, 20000)
        grid.setSpacing(1000, 1000)
        self.view_widget.addItem(grid)

        #Setup topological view
        self.topo_widget.setCameraPosition(distance=1000)
        topo_axis = gl.GLAxisItem()
        topo_axis.setSize(1000, 1000, 1000)
        topo_grid = gl.GLGridItem()
        topo_grid.setSize(2000, 2000)
        topo_grid.setSpacing(100, 100)
        self.topo_widget.addItem(topo_axis) 
        self.topo_widget.addItem(topo_grid)

        #Setup sky chart
        north_label = pg.TextItem("N", color=(255, 0, 0))
        north_label.setPos(0, 1.1)
        north_label.setAnchor((0.5, 0.5))
        self.sky_widget.addItem(north_label)

        east_label = pg.TextItem("E", color=(255, 0, 0))
        east_label.setPos(-1.1, 0)
        east_label.setAnchor((0.5, 0.5))
        self.sky_widget.addItem(east_label) 

        south_label = pg.TextItem("S", color=(255, 0, 0))
        south_label.setPos(0, -1.1)
        south_label.setAnchor((0.5, 0.5))
        self.sky_widget.addItem(south_label)

        west_label = pg.TextItem("W", color=(255, 0, 0))
        west_label.setPos(1.1, 0)
        west_label.setAnchor((0.5, 0.5))
        self.sky_widget.addItem(west_label)

        self.sky_widget.setAspectLocked(True)
        self.sky_widget.setRange(xRange=(-1.5, 1.5), yRange=(-1.5, 1.5))
        
        horizon_circle = pg.QtWidgets.QGraphicsEllipseItem(-1, -1, 2, 2)
        horizon_circle.setPen(pg.mkPen('w', width=1))
        self.sky_widget.addItem(horizon_circle)

        # Add London marker
        self.update_london_marker()
        
        # Add terminator circle
        self.update_terminator_circle()
    
    def teme_to_topographic(self, teme_position):
        """
        Convert a position vector from TEME reference frame to a topographic frame centered at London.
        
        Args:
            teme_position (np.ndarray): Position vector [x, y, z] in TEME frame (km)
            
        Returns:
            np.ndarray: Position vector [east, north, up] in the topographic frame (km)
        """
        # Get the current time in Skyfield format
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day,
                    self.current_time.hour, self.current_time.minute, self.current_time.second)
        
        # Create a Skyfield Topos object for London's location
        london = sf.wgs84.latlon(self.london_lat, self.london_lon)
        
        # Get London's position in the TEME frame
        london_geocentric = london.at(t)
        london_teme_pos = london_geocentric.position.km
        
        # Calculate the relative position vector (satellite position relative to London)
        rel_position = teme_position - london_teme_pos
        
        # Convert London's ra/dec to radians
        ra, dec, _ = london_geocentric.radec()
        ra = ra.radians
        dec = dec.radians

        # Calculate rotation from TEME to topographic frame (East-North-Up)
        sin_ra = np.sin(ra)
        cos_ra = np.cos(ra)
        sin_dec = np.sin(dec)
        cos_dec = np.cos(dec)

        # Rotation matrix from TEME to [East, North, Up]
        rotation = np.array([
            [-sin_ra, cos_ra, 0],
            [-sin_dec*cos_ra, -sin_dec*sin_ra, cos_dec],
            [cos_dec*cos_ra, cos_dec*sin_ra, sin_dec]
        ])
        
        # Apply rotation to get the position in the topographic frame
        topo_position = rotation @ rel_position
        
        return topo_position  # Returns [east, north, up]

    def topo_to_azel(self, topo_position):
        """
        Convert a topographic position vector to azimuth and elevation angles.
        
        Args:
            topo_position (np.ndarray): Position vector [east, north, up] in the topographic frame (km)
            
        Returns:
            tuple: (azimuth, elevation) in degrees
        """
        east, north, up = topo_position
        
        # Calculate horizontal distance
        horizontal_distance = np.sqrt(east**2 + north**2)
        
        # Azimuth angle (in radians)
        azimuth = np.arctan2(east, north)

        # Elevation angle (in radians)
        elevation = np.arctan2(up, horizontal_distance)

        # Convert angles to degrees
        azimuth = np.degrees(azimuth)
        elevation = np.degrees(elevation)

        return azimuth, elevation

    def toggle_animation(self):
        """Start or stop animation"""
        if self.is_animating:
            self.timer.stop()
            self.is_animating = False
            self.animation_btn.setText("Start Animation")
        else:
            # Set timer to 100fps (10ms interval)
            self.timer.start(10)
            self.is_animating = True
            self.animation_btn.setText("Stop Animation")
    
    def animation_step(self):
        """Perform one step in the animation"""
        # Advance time based on animation speed
        self.current_time += self.time_step * self.animation_speed
        self.time_label.setText(f"Current Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update Earth-related elements
        self.update_terminator_circle()
        
        # Rotate the Earth mesh based on time
        # Earth rotates 15 degrees per hour (360/24)
        utc_hour = self.current_time.hour + self.current_time.minute / 60.0 + self.current_time.second / 3600.0
        angle = (utc_hour * 15) % 360
        
        # Reset and apply rotation
        # self.earth_mesh.resetTransform()
        # self.earth_mesh.rotate(angle, 0, 0, 1)  # Rotate around z-axis
        
        # Update London marker position after Earth rotation
        self.update_london_marker()
        
        # Only update satellite position, not the entire orbit trail
        self.update_satellite_position()
        
        
        # Update orbit trail less frequently
        if (self.last_trail_update is None or 
            (perf_counter() - self.last_trail_update) > self.trail_update_interval):
            self.update_orbit_trail()
            self.last_trail_update = perf_counter()
        
        self.cycle_end = perf_counter()
        print(f"FPS: {1 / (self.cycle_end - self.cycle_start):.2f}")
        self.cycle_start = perf_counter()


    def update_satellite_position(self):
        """Update only the satellite position marker - fast update"""
        if not self.sat_combo.currentText():
            return
            
        sat_name = self.sat_combo.currentText()
        satellite = self.satellites[sat_name]
        
        # Calculate current position
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day, 
                    self.current_time.hour, self.current_time.minute, self.current_time.second)
        current_pos = satellite.at(t).position.km
        
        # Create or update current position marker
        if self.current_marker is None:
            self.current_marker = gl.GLScatterPlotItem(
                pos=np.array([current_pos]),
                color=(1, 1, 0, 1),
                size=15
            )
            self.view_widget.addItem(self.current_marker)
        else:
            self.current_marker.setData(pos=np.array([current_pos]))

        # Create or update topographic marker
        topo_pos = self.teme_to_topographic(current_pos)
        
        if self.topo_marker is None:
            self.topo_marker = gl.GLScatterPlotItem(
                pos=np.array([topo_pos]),
                color=(0, 1, 0, 1),
                size=15
            )
            self.topo_widget.addItem(self.topo_marker)
        else:
            self.topo_marker.setData(pos=np.array([topo_pos]))

        # Convert topographic position to azimuth/elevation
        azimuth, elevation = self.topo_to_azel(topo_pos)

        # Create or update sky marker
        if self.sky_marker is None:
            self.sky_marker = pg.ScatterPlotItem(
                pen=pg.mkPen('y', width=2),
                brush=pg.mkBrush(255, 255, 0, 200),
                size=10
            )
            self.sky_widget.addItem(self.sky_marker)
        else:
            self.sky_marker.setData(pos=np.array([azimuth, elevation]))

    def update_orbit_trail(self):
        """Update the orbit trail - less frequent update"""
        if not self.sat_combo.currentText():
            return
            
        sat_name = self.sat_combo.currentText()
        satellite = self.satellites[sat_name]
        
        # Calculate trail length
        trail_hours = self.trail_spinbox.value()
        start_time = self.current_time - timedelta(hours=trail_hours)
        
        # Calculate orbit points
        positions = self.compute_satellite_positions(satellite, start_time, self.current_time, points=50)
        
        # Create or update orbit trail
        if self.orbit_trail is None:
            self.orbit_trail = gl.GLLinePlotItem(pos=positions, color=(1, 0, 0, 1), width=2)
            self.view_widget.addItem(self.orbit_trail)
        else:
            self.orbit_trail.setData(pos=positions)

        # Create or update topographic trail
        topo_positions = self.compute_satellite_positions(satellite, self.current_time - timedelta(minutes=5), self.current_time + timedelta(minutes=5), points=50)
        topo_positions = [self.teme_to_topographic(pos) for pos in topo_positions]
        if self.topo_trail is None:
            self.topo_trail = gl.GLLinePlotItem(pos=topo_positions, color=(0, 1, 0, 1), width=2)
            self.topo_widget.addItem(self.topo_trail)
        else:
            self.topo_trail.setData(pos=topo_positions)

        sky_positions = [self.topo_to_azel(pos) for pos in topo_positions]
        if self.sky_trail is None:
            self.sky_trail = pg.PlotCurveItem(
                x=[pos[0] for pos in sky_positions],
                y=[pos[1] for pos in sky_positions],
                pen=pg.mkPen('r', width=2)
            )
            self.sky_widget.addItem(self.sky_trail)

    def update_london_marker(self):
        """Add or update a marker for London in the TEME reference frame"""
        # Create a Skyfield Topos object for London's location
        london = sf.wgs84.latlon(self.london_lat, self.london_lon)
        
        # Get the current time in Skyfield format
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day,
                    self.current_time.hour, self.current_time.minute, self.current_time.second)
        
        # Calculate London's position in the TEME frame
        london_geocentric = london.at(t)
        london_teme_pos = london_geocentric.position.km
        
        # Create or update marker with the TEME position
        if self.london_marker is None:
            self.london_marker = gl.GLScatterPlotItem(
                pos=np.array([london_teme_pos]),
                color=(1, 0, 0, 1),  # Red color
                size=10
            )
            self.view_widget.addItem(self.london_marker)
        else:
            self.london_marker.setData(pos=np.array([london_teme_pos]))

    def update_terminator_circle(self):
        """Calculate and display the terminator circle (day/night boundary)"""
        # Calculate Sun position relative to Earth at current time
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day, 
                    self.current_time.hour, self.current_time.minute, self.current_time.second)
        
        sun_pos = (self.sun - self.earth).at(t).position.km
        sun_direction = sun_pos / np.linalg.norm(sun_pos)
        
        # Generate points for the terminator circle
        n_points = 100
        circle_points = []
        
        # Find two vectors perpendicular to sun_direction and to each other
        u = np.array([0, 0, 1])
        if abs(np.dot(u, sun_direction)) > 0.9:
            u = np.array([1, 0, 0])
        
        u = u - np.dot(u, sun_direction) * sun_direction
        u = u / np.linalg.norm(u)
        v = np.cross(sun_direction, u)
        v = v / np.linalg.norm(v)
        
        # Generate circle points
        for i in range(n_points + 1):
            angle = 2 * math.pi * i / n_points
            point = self.earth_radius * (u * math.cos(angle) + v * math.sin(angle))
            circle_points.append(point)
        
        # Create or update line connecting all points
        if self.terminator_circle is None:
            self.terminator_circle = gl.GLLinePlotItem(
                pos=np.array(circle_points),
                color=(0.9, 0.7, 0.2, 1),  # Golden color
                width=2,
                mode='line_strip'
            )
            self.view_widget.addItem(self.terminator_circle)
        else:
            self.terminator_circle.setData(pos=np.array(circle_points))
    def update_orbits(self):
        """Update the satellite orbits in the 3D view - called when settings change"""
        # Clear previous orbit paths
        for item in self.orbit_items:
            self.view_widget.removeItem(item)
        self.orbit_items = []
        
        # Clear cached items
        if self.orbit_trail is not None:
            self.view_widget.removeItem(self.orbit_trail)
            self.orbit_trail = None
        if self.current_marker is not None:
            self.view_widget.removeItem(self.current_marker)
            self.current_marker = None
        
        # Force update of both trail and position
        self.update_orbit_trail()
        self.update_satellite_position()
        self.last_trail_update = perf_counter()
    
    def reset_view(self):
        """Reset the camera view"""
        self.view_widget.setCameraPosition(distance=40000)
    
    def compute_satellite_positions(self, satellite, start_time, end_time, points=100):
        """Compute satellite positions over a time range"""
        time_range = np.linspace(0, (end_time - start_time).total_seconds(), points)
        positions = []
        
        for t in time_range:
            time = start_time + timedelta(seconds=t)
            t = self.ts.utc(time.year, time.month, time.day, 
                          time.hour, time.minute, time.second)
            geocentric = satellite.at(t)
            
            # Get the position in Earth-centered coordinates (km)
            pos = geocentric.position.km
            positions.append(pos)
            
        return np.array(positions)
    
    def load_tle_data(self):
        """Load satellite TLE data from a file"""
        # file_name, _ = QFileDialog.getOpenFileName(self, "Open TLE File", "", "Text Files (*.txt);;All Files (*)")
        
        # if file_name:
        try:
            import os
            satellites = sf.load.tle_file(os.path.join(os.path.dirname(__file__), 'tle.txt'))
            for sat in satellites:
                self.satellites[sat.name] = sat
                self.sat_combo.addItem(sat.name)
            
            self.update_orbits()
        except Exception as e:
            print(f"Error loading TLE file: {e}")
    
    def on_time_slider_changed(self, value):
        """Update time when slider changes"""
        value = value / 100
        # self.current_time = datetime.now() + timedelta(hours=value)
        self.current_time = datetime(2025, 7, 15, 0, 0, 0) + timedelta(hours=value)
        self.time_label.setText(f"Current Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update Earth-related visuals
        self.update_terminator_circle()
        
        # Rotate Earth based on new time
        utc_hour = self.current_time.hour + self.current_time.minute / 60.0 + self.current_time.second / 3600.0
        angle = (utc_hour * 15) % 360
        
        self.earth_mesh.resetTransform()
        self.earth_mesh.rotate(angle, 0, 0, 1)
        
        # Update London marker
        self.update_london_marker()
        
        # Update satellite orbit
        self.update_orbits()
    
    def on_speed_changed(self, value):
        """Update animation speed"""
        self.animation_speed = value
        # Don't change timer interval - keep it at 100fps
        # The speed now controls how much time advances per frame


if __name__ == "__main__":
    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    window = SatelliteOrbitVisualizerGL()
    screen = app.screens()[1]
    window.move(screen.geometry().topLeft())
    window.maximumSize()


    window.show()

    def signal_handler(signal, frame):
        """Handle exit signal"""
        app.quit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    timer = QTimer()
    timer.start(100)  # Small interval to check signals
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec())