import sys
import numpy as np
from datetime import datetime, timedelta
from time import perf_counter
import skyfield.api as sf
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QSlider, QLabel, QComboBox,
                             QGroupBox, QDoubleSpinBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import signal
import os
import math
import astropy.units as u
import astropy.coordinates as coord
from astropy.time import Time as astropy_time

import win32com.client

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
        self.time_step = timedelta(seconds=1)
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
        self.london_lat = 51.5074  # degrees North
        # self.london_lat = 49  # degrees North
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

        self.mount_timer = QTimer()
        self.mount_timer.timeout.connect(self.mount_step)
        self.mount = None
        self.mount_ra = 0
        self.mount_dec = 0
        self.mount_az = 0
        self.mount_el = 0
        self.mount_marker = None
        self.tracking_satellite = False

        self.azel_positions = None
        self.azel_derivatives = None

        self.az_integral_error = 0
        self.el_integral_error = 0
        self.az_last_error = 0
        self.el_last_error = 0

        self.cycle_start = 0
        self.dt = 0
        self.cycle_end = 0
    def closeEvent(self, event: QCloseEvent):
        self.stop_mount_motion()
        event.accept()

    def stop_mount_motion(self):
        """Stop the mount motion and disconnect"""
        if self.mount is not None:
            self.mount.AbortSlew()
            self.mount.MoveAxis(0, 0)
            self.mount.MoveAxis(1, 0)

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
        controls_layout = QVBoxLayout(controls_container)

        controls_sublayout = QHBoxLayout()
        controls_layout.addLayout(controls_sublayout)

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
        
        controls_sublayout.addWidget(sat_group)
        
        # Camera/View Controls
        view_group = QGroupBox("View Controls")
        view_layout = QVBoxLayout(view_group)
        
        view_reset_btn = QPushButton("Reset View")
        view_reset_btn.clicked.connect(self.reset_view)
        view_layout.addWidget(view_reset_btn)
        
        controls_sublayout.addWidget(view_group)
        
        # Add controls to main layout
        main_layout.addWidget(controls_container)
        controls_container.setMaximumHeight(200)
        
        # Set the central widget
        self.setCentralWidget(main_widget)

        # Mount Controls
        mount_group = QGroupBox("Mount Controls")
        mount_layout = QVBoxLayout(mount_group)
        mount_btn_layout = QHBoxLayout()
        self.track_btn = QPushButton("Start Tracking")
        self.track_btn.clicked.connect(self.toggle_mount_tracking)
        mount_btn_layout.addWidget(self.track_btn)

        self.freeze_btn = QPushButton("Freeze Mount")
        self.freeze_btn.clicked.connect(self.mount_freeze)
        mount_btn_layout.addWidget(self.freeze_btn)

        self.manual_slew_btn = QPushButton("Manual Slew")
        self.manual_slew_btn.clicked.connect(self.manual_slew)
        mount_btn_layout.addWidget(self.manual_slew_btn)

        #Target Azimuth and Elevation
        self.azimuth_label = QLabel("Azimuth (°):")
        self.azimuth_spinbox = QDoubleSpinBox()
        self.azimuth_spinbox.setRange(0, 360)
        self.azimuth_spinbox.setValue(0)
        self.azimuth_spinbox.setSingleStep(1)
        mount_btn_layout.addWidget(self.azimuth_label)
        mount_btn_layout.addWidget(self.azimuth_spinbox)
        self.elevation_label = QLabel("Elevation (°):")
        self.elevation_spinbox = QDoubleSpinBox()
        self.elevation_spinbox.setRange(0, 90)
        self.elevation_spinbox.setValue(0)
        self.elevation_spinbox.setSingleStep(1)
        mount_btn_layout.addWidget(self.elevation_label)
        mount_btn_layout.addWidget(self.elevation_spinbox)

        mount_layout.addLayout(mount_btn_layout)
        controls_sublayout.addWidget(mount_group)

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
    
    def teme_to_itrs(self, satellite, t):
        """
        Convert satellite position from TEME to ITRS reference frame.
        
        Args:
            satellite: Skyfield satellite object
            t: Skyfield time object
            
        Returns:
            np.ndarray: Position vector [x, y, z] in ITRS frame (km)
        """
        # Get the satellite position in GCRS frame
        gcrs_position = satellite.at(t)
        
        # Convert to ITRS (Earth-fixed) frame
        itrs_position = gcrs_position.itrf_xyz().km
        
        return itrs_position
    
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
                    self.current_time.hour, self.current_time.minute, self.current_time.second + self.current_time.microsecond / 1000000.0)
        
        # Create a Skyfield Topos object for London's location
        london = sf.wgs84.latlon(self.london_lat, self.london_lon)
        
        # Get London's position in the ITRS frame
        london_geocentric = london.at(t)
        london_itrs_pos = london_geocentric.itrf_xyz().km
        
        # Calculate the relative position vector (satellite position relative to London)
        rel_position = teme_position - london_itrs_pos
        
        # Convert to topographic frame
        # The ITRS frame has Z pointing along Earth's rotation axis, X pointing to the 
        # Greenwich meridian, and Y completing the right-handed system
        
        # Get London's latitude and longitude in radians
        lat = np.radians(self.london_lat)
        lon = np.radians(self.london_lon)
        
        # Rotation matrix from ITRS to [East, North, Up]
        sin_lon = np.sin(lon)
        cos_lon = np.cos(lon)
        sin_lat = np.sin(lat)
        cos_lat = np.cos(lat)
        
        rotation = np.array([
            [-sin_lon, cos_lon, 0],
            [-sin_lat*cos_lon, -sin_lat*sin_lon, cos_lat],
            [cos_lat*cos_lon, cos_lat*sin_lon, sin_lat]
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
            tuple: (azimuth, elevation) in radians
        """
        east, north, up = topo_position
        
        # Calculate horizontal distance
        horizontal_distance = np.sqrt(east**2 + north**2)
        
        # Azimuth angle (in radians)
        azimuth = np.arctan2(east, north)

        # Elevation angle (in radians)
        elevation = np.arctan2(up, horizontal_distance)

        return azimuth, elevation
    
    def azel_to_sky(self, azimuth, elevation):
        """
        Convert azimuth and elevation angles to sky chart coordinates (East, North).

        Args:
            azimuth (float): Azimuth angle in degrees
            elevation (float): Elevation angle in degrees
            
        Returns:
            tuple: (East, North) coordinates in sky chart coordinates
        """
        # radius = np.cos(elevation)  # Radius in the sky chart
        radius = 1 - elevation * 2 / np.pi
        east = - radius * np.sin(azimuth) # Negative x for East in sky chart
        north = radius * np.cos(azimuth)
        return east, north

    def toggle_animation(self):
        """Start or stop animation"""
        if self.is_animating:
            self.timer.stop()
            self.is_animating = False
            self.dt = 0
            self.animation_btn.setText("Start Animation")
        else:
            # Set timer to 100fps (10ms interval)
            self.timer.start(10)
            self.is_animating = True
            self.dt = 0
            self.cycle_start = perf_counter()
            self.cycle_end = perf_counter()
            self.animation_btn.setText("Stop Animation")
    
    def animation_step(self):
        """Perform one step in the animation"""
        # Advance time based on animation speed
        self.current_time += self.time_step * self.animation_speed * self.dt
        self.time_label.setText(f"Current Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]}")
        
        # Update Earth-related elements
        self.update_terminator_circle()
        
        # Rotate the Earth mesh based on time
        # Earth rotates 15 degrees per hour (360/24)
        utc_hour = self.current_time.hour + self.current_time.minute / 60.0 + self.current_time.second / 3600.0 + self.current_time.microsecond / 3600000000.0
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
        self.dt = self.cycle_end - self.cycle_start
        self.cycle_start = perf_counter()


    def update_satellite_position(self):
        """Update only the satellite position marker - fast update"""
        if not self.sat_combo.currentText():
            return
            
        sat_name = self.sat_combo.currentText()
        satellite = self.satellites[sat_name]
        
        # Calculate current position in ITRS
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day, 
                    self.current_time.hour, self.current_time.minute, self.current_time.second + self.current_time.microsecond / 1000000.0)
        
        # Get position in ITRS (Earth-fixed) frame
        current_pos = self.teme_to_itrs(satellite, t)
        
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
        # Convert to rectangular coordinates for sky chart
        sky_x, sky_y = self.azel_to_sky(azimuth, elevation)

        # Create or update sky marker
        if self.sky_marker is None:
            self.sky_marker = pg.ScatterPlotItem(
                pen=pg.mkPen('y', width=2),
                brush=pg.mkBrush(255, 255, 0, 200),
                size=10
            )
            self.sky_widget.addItem(self.sky_marker)
        else:
            self.sky_marker.setData(pos=np.array([[sky_x, sky_y]]))

    def update_orbit_trail(self):
        """Update the orbit trail - less frequent update"""
        if not self.sat_combo.currentText():
            return
            
        sat_name = self.sat_combo.currentText()
        satellite = self.satellites[sat_name]
        
        # Calculate trail length
        trail_hours = self.trail_spinbox.value()
        start_time = self.current_time - timedelta(hours=trail_hours)
        
        # Calculate orbit points in ITRS
        positions = self.compute_satellite_positions(satellite, start_time, self.current_time, points=100, use_itrs=True)
        
        # Create or update orbit trail
        if self.orbit_trail is None:
            self.orbit_trail = gl.GLLinePlotItem(pos=positions, color=(1, 0, 0, 1), width=2)
            self.view_widget.addItem(self.orbit_trail)
        else:
            self.orbit_trail.setData(pos=positions)

        # Create or update topographic trail
        topo_start = self.current_time - timedelta(minutes=5)
        topo_end = self.current_time + timedelta(minutes=5)
        topo_positions = self.compute_satellite_positions(satellite, topo_start, topo_end, points=100, use_itrs=True)
        topo_positions = [self.teme_to_topographic(pos) for pos in topo_positions]
        
        if self.topo_trail is None:
            self.topo_trail = gl.GLLinePlotItem(pos=topo_positions, color=(0, 1, 0, 1), width=2)
            self.topo_widget.addItem(self.topo_trail)
        else:
            self.topo_trail.setData(pos=topo_positions)

        sky_positions = [self.topo_to_azel(pos) for pos in topo_positions]
        sky_positions = [self.azel_to_sky(azimuth, elevation) for azimuth, elevation in sky_positions]
        
        if self.sky_trail is None:
            self.sky_trail = pg.PlotCurveItem(
                x=[pos[0] for pos in sky_positions],
                y=[pos[1] for pos in sky_positions],
                pen=pg.mkPen('r', width=2)
            )
            self.sky_widget.addItem(self.sky_trail)
        else:
            self.sky_trail.setData(
                x=[pos[0] for pos in sky_positions],
                y=[pos[1] for pos in sky_positions]
            )

    def update_london_marker(self):
        """Add or update a marker for London in the ITRS reference frame"""
        # Create a Skyfield Topos object for London's location
        london = sf.wgs84.latlon(self.london_lat, self.london_lon)
        
        # Get the current time in Skyfield format
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day,
                    self.current_time.hour, self.current_time.minute, self.current_time.second)
        
        # Calculate London's position in the ITRS frame
        london_geocentric = london.at(t)
        london_itrs_pos = london_geocentric.itrf_xyz().km
        
        # Create or update marker with the ITRS position
        if self.london_marker is None:
            self.london_marker = gl.GLScatterPlotItem(
                pos=np.array([london_itrs_pos]),
                color=(1, 0, 0, 1),  # Red color
                size=10
            )
            self.view_widget.addItem(self.london_marker)
        else:
            self.london_marker.setData(pos=np.array([london_itrs_pos]))

    def update_terminator_circle(self):
        """Calculate and display the terminator circle (day/night boundary)"""
        # Calculate Sun position relative to Earth at current time
        t = self.ts.utc(self.current_time.year, self.current_time.month, self.current_time.day, 
                    self.current_time.hour, self.current_time.minute, self.current_time.second)
        obstime = astropy_time(self.current_time)

        sun_itrs = (self.sun - self.earth).at(t).position.km
        sun_itrs = coord.SkyCoord(x=sun_itrs[0] * u.km, y=sun_itrs[1] * u.km, z=sun_itrs[2] * u.km, frame='icrs', representation_type='cartesian', obstime=obstime)
        sun_pos = sun_itrs.transform_to('itrs').cartesian.xyz.value
        sun_direction = sun_pos / np.linalg.norm(sun_pos)

        
        # Generate points for the terminator circle
        n_points = 100
        circle_points = []
        
        # Find two vectors perpendicular to sun_direction and to each other
        u_vector = np.array([0, 0, 1])
        if abs(np.dot(u_vector, sun_direction)) > 0.9:
            u_vector = np.array([1, 0, 0])

        u_vector = u_vector - np.dot(u_vector, sun_direction) * sun_direction
        u_vector = u_vector / np.linalg.norm(u_vector)
        v_vector = np.cross(sun_direction, u_vector)
        v_vector = v_vector / np.linalg.norm(v_vector)

        # Generate circle points
        for i in range(n_points + 1):
            angle = 2 * math.pi * i / n_points
            point = self.earth_radius * (u_vector * math.cos(angle) + v_vector * math.sin(angle))
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
    
    def compute_satellite_positions(self, satellite, start_time, end_time, points=100, use_itrs=False):
        """Compute satellite positions over a time range"""
        time_range = np.linspace(0, (end_time - start_time).total_seconds(), points)
        positions = []
        
        for t in time_range:
            time = start_time + timedelta(seconds=t)
            t_sf = self.ts.utc(time.year, time.month, time.day, 
                          time.hour, time.minute, time.second)
            
            if use_itrs:
                # Get position in ITRS (Earth-fixed) frame
                pos = self.teme_to_itrs(satellite, t_sf)
            else:
                # Get position in original frame (TEME)
                pos = satellite.at(t_sf).position.km
                
            positions.append(pos)
            
        return np.array(positions)
    
    def load_tle_data(self):
        """Load satellite TLE data from a file"""
        # file_name, _ = QFileDialog.getOpenFileName(self, "Open TLE File", "", "Text Files (*.txt);;All Files (*)")
        
        # if file_name:
        # try:
        import os
        satellites = sf.load.tle_file(os.path.join(os.path.dirname(__file__), 'tle.txt'))
        for sat in satellites:
            self.satellites[sat.name] = sat
            self.sat_combo.addItem(sat.name)
        
        self.update_orbits()
        # except Exception as e:
        #     print(f"Error loading TLE file: {e}")
    
    def on_time_slider_changed(self, value):
        """Update time when slider changes"""
        value = value / 100
        # self.current_time = datetime.now() + timedelta(hours=value)
        self.current_time = datetime(2025, 7, 15, 0, 0, 0) + timedelta(hours=value)
        self.time_label.setText(f"Current Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update Earth-related visuals
        self.update_terminator_circle()
        
        # Rotate Earth based on new time - not needed in ITRS frame since Earth is fixed
        # utc_hour = self.current_time.hour + self.current_time.minute / 60.0 + self.current_time.second / 3600.0
        # angle = (utc_hour * 15) % 360
        # self.earth_mesh.resetTransform()
        # self.earth_mesh.rotate(angle, 0, 0, 1)
        
        # Update London marker
        self.update_london_marker()
        
        # Update satellite orbit
        self.update_orbits()
    
    def on_speed_changed(self, value):
        """Update animation speed"""
        self.animation_speed = value
        # Don't change timer interval - keep it at 100fps
        # The speed now controls how much time advances per frame
    
    def mount_step(self):
        self.update_mount_position()

    def update_mount_position(self):
        """Update mount position in the 3D view"""
        if self.mount is None or not self.mount.Connected:
            return
        
        # Get mount position
        self.mount_ra = self.mount.RightAscension
        self.mount_dec = self.mount.Declination
        self.mount_az = self.mount.Azimuth
        self.mount_el = self.mount.Altitude
  
        
        east, north = self.azel_to_sky(np.radians(self.mount_az), np.radians(self.mount_el))

        # Create or update mount marker in the sky chart
        if self.mount_marker is None:
            self.mount_marker = pg.ScatterPlotItem(
                pen=pg.mkPen('g', width=2),
                brush=pg.mkBrush(0, 0, 255, 200),
                size=10
            )
            self.sky_widget.addItem(self.mount_marker)
        else:
            self.mount_marker.setData(pos=np.array([(east, north)]))
            
        if self.tracking_satellite:
            if self.azel_derivatives is not None and self.azel_positions is not None:
                # Find closest time in azel_derivatives
                closest_time = min(self.azel_derivatives[:, 0], key=lambda t: abs(t - self.current_time))
                closest_index = np.where(self.azel_derivatives[:, 0] == closest_time)[0][0]
                # closest_index = np.where(self.azel_derivatives[:, 0] == closest_time)[0][0] + 13
                
                # Get azimuth and elevation derivatives
                az_derivative = self.azel_derivatives[closest_index, 1]
                el_derivative = self.azel_derivatives[closest_index, 2]

                target_az = np.mod(self.azel_positions[closest_index][0][0], 2 * np.pi)
                target_el = self.azel_positions[closest_index][0][1]

                az_error = np.rad2deg(target_az) - self.mount_az
                el_error = np.rad2deg(target_el) - self.mount_el

                az_derivative_error = az_error - self.az_last_error
                el_derivative_error = el_error - self.el_last_error

                self.az_last_error = az_error
                self.el_last_error = el_error
                # Update integral errors
                if self.dt > 0.01:
                    self.az_integral_error += az_error * self.dt
                    self.el_integral_error += el_error * self.dt
                else:
                    self.az_integral_error += az_error * 0.01
                    self.el_integral_error += el_error * 0.01

                # self.mount.AbortSlew()  # Stop any ongoing slew
                # self.mount.SlewToAltAzAsync(np.mod(np.rad2deg(target_az), 360), np.rad2deg(target_el))

                # print(f"Time: {closest_time}, Az Derivative: {az_derivative:.4f}, El Derivative: {el_derivative:.4f}")

                kp = 10
                kd = 0
                ki = 0
                az_nudge = kp * az_error + kd * az_derivative_error + ki * self.az_integral_error
                el_nudge = kp * el_error + kd * el_derivative_error + ki * self.el_integral_error
                # print(f"Az Nudge: {az_nudge:.2f}, El Nudge: {el_nudge:.2f}, Az Error: {az_error:.2f}, El Error: {el_error:.2f}, Az Integral Error: {self.az_integral_error:.2f}, El Integral Error: {self.el_integral_error:.2f}")

                # Move mount based on derivatives
                self.mount.MoveAxis(0, np.clip(np.rad2deg(az_derivative) + az_nudge, -5, 5))
                self.mount.MoveAxis(1, np.clip(np.rad2deg(el_derivative) + el_nudge, -5, 5))

    def toggle_mount_tracking(self):
        """Toggle mount tracking on/off"""
        if self.mount:
        # if True:
            self.az_integral_error = 0
            self.el_integral_error = 0

            if not self.tracking_satellite:
                self.track_btn.setText("Stop Tracking")
                self.tracking_satellite = True
                sat_name = self.sat_combo.currentText()
                satellite = self.satellites[sat_name]
                itrs_positions = self.compute_satellite_positions(satellite, self.current_time, self.current_time + timedelta(minutes=10), points=10000, use_itrs=True)
                topo_positions = np.array([self.teme_to_topographic(pos) for pos in itrs_positions])
                timedeltas = np.linspace(0, timedelta(minutes=10).total_seconds(), 10000)
                times = np.array([self.current_time + timedelta(seconds=t) for t in timedeltas])
                # print(times.shape, topo_positions.shape)

                azel_values = np.array([self.topo_to_azel(pos) for pos in topo_positions])
                az_values = azel_values[:, 0]  # First column is azimuth
                el_values = azel_values[:, 1]  # Second column is elevation
                
                # Store positions and times separately or as a list of tuples
                self.azel_positions = [(azel, time) for azel, time in zip(azel_values, times)]

                az_unwrapped = np.unwrap(az_values)

                az_derivatives = np.gradient(az_unwrapped, timedeltas)
                el_derivatives = np.gradient(el_values, timedeltas)

                self.azel_derivatives = np.column_stack((times, az_derivatives, el_derivatives))

            else:
                self.tracking_satellite = False
                self.mount.MoveAxis(0, 0)  # Stop all movement
                self.mount.MoveAxis(1, 0)
                self.track_btn.setText("Start Tracking")

    def mount_freeze(self):
        """Toggle mount freeze on/off"""
        if self.mount:
            self.stop_mount_motion()
            self.tracking_satellite = False
            self.track_btn.setText("Start Tracking")
        
    def manual_slew(self):
        """Slew mount to specified azimuth and elevation"""
        if self.mount:
            azimuth = self.azimuth_spinbox.value()
            elevation = self.elevation_spinbox.value()
            self.mount.SlewToAltAzAsync(azimuth, elevation)

def connect_to_mount(driver_id=None):
    """Connect to mount - either specific driver or show chooser"""
    if driver_id is None:
        # Launch ASCOM Chooser to select mount
        chooser = win32com.client.Dispatch("ASCOM.Utilities.Chooser")
        chooser.DeviceType = "Telescope"
        driver_id = chooser.Choose(None)
        if not driver_id:
            print("No mount selected")
            return None
    
    # Create mount instance
    mount = win32com.client.Dispatch(driver_id)
    
    # Connect to the mount
    if not mount.Connected:
        mount.Connected = True

    print(f"Connected to: {mount.Description}")
    
    return mount


if __name__ == "__main__":
    # Enable antialiasing for prettier plots
    pg.setConfigOptions(antialias=True)
    
    app = QApplication(sys.argv)
    window = SatelliteOrbitVisualizerGL()
    # screen = app.screens()[1]
    # window.move(screen.geometry().topLeft())
    window.maximumSize()


    window.show()

    def signal_handler(signal, frame):
        """Handle exit signal"""
        window.stop_mount_motion()
        app.quit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    timer = QTimer()
    timer.start(100)  # Small interval to check signals
    timer.timeout.connect(lambda: None)
    
    mount = connect_to_mount("ASCOM.Simulator.Telescope")
    if mount:
        window.mount = mount
        window.mount_timer.start(10) #100hz loop

    sys.exit(app.exec())