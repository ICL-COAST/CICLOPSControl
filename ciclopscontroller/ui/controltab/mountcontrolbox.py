from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDoubleSpinBox
from ciclopscontroller.controllers.mountcontroller import MountController

class MountControlBox(QGroupBox):
    def __init__(self, mount_controller: MountController):
        super().__init__()

        self.mount_controller = mount_controller
        
        self.setup_ui()

    def setup_ui(self):

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
        
