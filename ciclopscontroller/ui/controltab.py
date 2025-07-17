from PySide6.QtWidgets import QWidget
import pyqtgraph as pg
import pyqtgraph.opengl as gl
from PySide6.QtWidgets import QVBoxLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QSlider, QPushButton, QDoubleSpinBox
from PySide6.QtCore import Qt
import numpy as np

class ControlTab(QWidget):
    def __init__(self):
        super().__init__()

        self.OrbitView = OrbitView()
        self.TopoView = TopoView()
        self.SkyChartView = SkyChartView()
        
        views_layout = QGridLayout()
        views_layout.addWidget(self.OrbitView, 0, 0)
        views_layout.addWidget(self.TopoView, 0, 1)
        views_layout.addWidget(self.SkyChartView, 0, 2)
        views_layout.setColumnStretch(0, 1)
        views_layout.setColumnStretch(1, 1)
        views_layout.setColumnStretch(2, 1)

        self.controls_container = ControlsContainer()

        main_layout = QVBoxLayout()
        main_layout.addLayout(views_layout)
        main_layout.addWidget(self.controls_container)
        self.setLayout(main_layout)


        


class OrbitView(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.earth_radius = 6371

        self.setCameraPosition(distance=40000)
        self.setBackgroundColor('k')
        
        # Add Earth sphere
        earth_sphere = gl.MeshData.sphere(radius=self.earth_radius, rows=20, cols=20)
        earth_mesh = gl.GLMeshItem(meshdata=earth_sphere, smooth=True, color=(0.1, 0.1, 0.8, 1))
        self.addItem(earth_mesh)


class TopoView(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCameraPosition(distance=1000)
        self.setBackgroundColor('k')
        


class SkyChartView(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackground('k')
        self.setTitle("Sky Chart")
        
        # Set up axes
        self.getAxis('bottom').setLabel('Right Ascension (h)')
        self.getAxis('left').setLabel('Declination (°)')
        
        # Add grid
        self.showGrid(x=True, y=True)
        
        # Example data
        self.plot([0, 1, 2], [0, 1, 0], pen='w', symbol='o', symbolSize=5)

class ControlsContainer(QWidget):
    def __init__(self):
        super().__init__()
        controls_layout = QVBoxLayout()

        time_control_container = TimeControlContainer()
        mount_control_container = MountControlContainer()
        controls_layout.addWidget(time_control_container)
        controls_layout.addWidget(mount_control_container)

        self.setLayout(controls_layout)

class TimeControlContainer(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("Time Control")
        time_layout = QVBoxLayout()
        self.setLayout(time_layout)

        # Items

        self.time_label = QLabel("Current Time:")
        time_layout.addWidget(self.time_label)

        time_slider_layout = QHBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(-600, 1200) #Seconds
        self.time_slider.setValue(0)
        self.time_slider.setTickInterval(60)
        self.time_slider.setTickPosition(QSlider.TicksBelow)
        self.time_slider.valueChanged.connect(self.on_time_slider_changed)
        time_slider_layout.addWidget(QLabel("-10m"))
        time_slider_layout.addWidget(self.time_slider)
        time_slider_layout.addWidget(QLabel("+20m"))
        time_layout.addLayout(time_slider_layout)

        animation_layout = QHBoxLayout()
        self.animation_btn = QPushButton("Play Animation")
        self.animation_btn.setCheckable(True)
        self.animation_btn.setChecked(False)
        self.animation_btn.clicked.connect(self.toggle_animation)
        animation_layout.addWidget(self.animation_btn)

        self.zero_time_btn = QPushButton("Reset Time")
        self.zero_time_btn.clicked.connect(lambda: self.time_slider.setValue(0))
        animation_layout.addWidget(self.zero_time_btn)

        self.now_btn = QPushButton("Set to Now")
        self.now_btn.clicked.connect(self.now_btn_clicked)
        animation_layout.addWidget(self.now_btn)

        self.play_live_btn = QPushButton("Play Live")
        self.play_live_btn.clicked.connect(self.play_live_btn_clicked)
        animation_layout.addWidget(self.play_live_btn)

        speed_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: 1x")
        speed_layout.addWidget(self.speed_label)
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(-2, 4) # Speed factor, 0.1 to 100x in log scale, 2 intervals per decade
        self.speed_slider.setValue(0)
        self.speed_slider.setTickInterval(2)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)
        animation_layout.addLayout(speed_layout)
        time_layout.addLayout(animation_layout)
        self.setLayout(time_layout)

    def on_time_slider_changed(self, value):
        pass

    def toggle_animation(self):
        if self.animation_btn.isChecked():
            self.animation_btn.setText("Pause Animation")
            # Start animation logic here
        else:
            self.animation_btn.setText("Play Animation")
            # Pause animation logic here

    def on_speed_slider_changed(self, value):
        speed_factor = 10 ** (value / 2) # Convert slider value to speed factor
        formatted = f"{speed_factor:.1f}" if speed_factor < 10 else f"{speed_factor:.0f}"
        self.speed_label.setText(f"Speed: {formatted}x")

    def now_btn_clicked(self):
        # Set current time to now logic here
        pass

    def play_live_btn_clicked(self):
        # Set current time to now

        self.animation_btn.setChecked(True)
        self.toggle_animation()


class MountControlContainer(QGroupBox):
    def __init__(self):
        super().__init__()
        self.setTitle("Mount Control")
        mount_layout = QVBoxLayout()
        self.setLayout(mount_layout)

        mount_btn_layout = QHBoxLayout()
        self.track_btn = QPushButton("Start Tracking")
        self.track_btn.setCheckable(True)
        self.track_btn.setChecked(False)
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
    
    def toggle_mount_tracking(self):
        if self.track_btn.isChecked():
            self.track_btn.setText("Stop Tracking")
            # Start tracking logic here
        else:
            self.track_btn.setText("Start Tracking")
            # Stop tracking logic here

    def mount_freeze(self):
        # Freeze mount logic here
        pass

    def manual_slew(self):
        azimuth = self.azimuth_spinbox.value()
        elevation = self.elevation_spinbox.value()
        # Manual slew logic here using azimuth and elevation values
        pass
        
