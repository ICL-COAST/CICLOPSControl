from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Callable

from ciclopscontroller.controllers.timecontroller import TimeController

class TimeControlBox(QGroupBox):
    def __init__(self, time_controller: TimeController, force_update: Callable[[], None]):
        super().__init__()

        self.time_controller = time_controller
        self.force_update = force_update

        self.setTitle("Time Control")
        time_layout = QVBoxLayout()
        self.setLayout(time_layout)

        # Items
        time_label_layout = QHBoxLayout()
        self.time_label_utc_label = QLabel("Real Time (UTC): \nSimulation Time (UTC):")
        self.time_label_utc = QLabel("Time Controller did not load successfully")
        timezone_number = timezone.utc.utcoffset(datetime.now()).total_seconds() / 3600
        self.time_label_local_label = QLabel(f"Local Real Time (UTC{timezone_number:+}): \nLocal Simulation Time (UTC{timezone_number:+}):")
        self.time_label_local = QLabel("Time Controller did not load successfully")
        time_label_layout.addWidget(self.time_label_utc_label)
        time_label_layout.addWidget(self.time_label_utc)
        time_label_layout.addSpacing(20)
        time_label_layout.addWidget(self.time_label_local_label)
        time_label_layout.addWidget(self.time_label_local)
        time_label_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        time_layout.addLayout(time_label_layout)

        time_slider_layout = QHBoxLayout()
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(-600, 1200) #Seconds
        self.time_slider.setValue(0)
        self.time_slider.setTickInterval(60)
        self.time_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.time_slider.valueChanged.connect(self.on_time_slider_changed)
        time_slider_layout.addWidget(QLabel("-10m"))
        time_slider_layout.addWidget(self.time_slider)
        time_slider_layout.addWidget(QLabel("+20m"))
        time_layout.addLayout(time_slider_layout)

        playback_layout = QHBoxLayout()
        self.playback_btn = QPushButton("Play")
        self.playback_btn.setCheckable(True)
        self.playback_btn.setChecked(False)
        self.playback_btn.clicked.connect(self.toggle_playback)
        playback_layout.addWidget(self.playback_btn)

        self.zero_time_btn = QPushButton("Reset Time")
        self.zero_time_btn.clicked.connect(self.zero_btn_clicked)
        playback_layout.addWidget(self.zero_time_btn)

        self.now_btn = QPushButton("Set to Now")
        self.now_btn.clicked.connect(self.now_btn_clicked)
        playback_layout.addWidget(self.now_btn)

        self.play_live_btn = QPushButton("Play Live")
        self.play_live_btn.clicked.connect(self.play_live_btn_clicked)
        playback_layout.addWidget(self.play_live_btn)

        speed_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: 1x")
        speed_layout.addWidget(self.speed_label)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(-2, 4) # Speed factor, 0.1 to 100x in log scale, 2 intervals per decade
        self.speed_slider.setValue(0)
        self.speed_slider.setTickInterval(2)
        self.speed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_layout.addWidget(self.speed_slider)
        self.speed_reset_btn = QPushButton("Reset Speed")
        self.speed_reset_btn.clicked.connect(self.on_speed_reset_btn_clicked)
        speed_layout.addWidget(self.speed_reset_btn)
        playback_layout.addLayout(speed_layout)
        time_layout.addLayout(playback_layout)
        self.setLayout(time_layout)

    def update_time(self):
        datetime_ = self.time_controller.get_datetime()
        self.update_time_label(datetime_)
        self.update_time_slider(self.time_controller._time_since_epoch)

    def on_time_slider_changed(self, value):
        self.force_update()
        if self.time_slider.isSliderDown(): # without this it ran at every slider tick it would set the time, changing timecontroller reference and running way faster than expected!
            self.time_controller.set_time(time_since_epoch=value)

    def update_time_label(self, datetime_: datetime):
        realtime = datetime.now(timezone.utc)
        realtime_utc_string = realtime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        realtime_local_string = realtime.astimezone().strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        simtime_utc_string = datetime_.strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        simtime_local_string = (
            datetime_.replace(tzinfo=ZoneInfo("UTC"))
            .astimezone()
            .strftime('%Y-%m-%d %H:%M:%S.%f')[:-4]
        )
        self.time_label_utc.setText(f'{realtime_utc_string}\n{simtime_utc_string}')
        self.time_label_local.setText(f'{realtime_local_string}\n{simtime_local_string}')

    def update_time_slider(self, time_since_epoch: float):
        if self.time_slider.isSliderDown():
            return
        
        self.time_slider.setValue(round(time_since_epoch))

    def toggle_playback(self):
        if self.playback_btn.isChecked():
            self.time_controller.start_playback()

            self.playback_btn.setText("Pause")
        else:
            self.time_controller.stop_playback()
            
            self.playback_btn.setText("Play")

    def on_speed_slider_changed(self, value):
        speed_factor = 10 ** (value / 2) # Convert slider value to speed factor
        formatted = f"{speed_factor:.1f}" if speed_factor < 10 else f"{speed_factor:.0f}"
        self.speed_label.setText(f"Speed: {formatted}x")

        self.time_controller.set_speed(speed_factor)
    def zero_btn_clicked(self):
        self.time_controller.set_time(time_since_epoch=0)

    def now_btn_clicked(self):
        self.time_controller.set_time(now=True)

    def play_live_btn_clicked(self):
        self.time_controller.set_time(now=True)
        self.playback_btn.setChecked(True)
        self.toggle_playback()
    
    def on_speed_reset_btn_clicked(self):
        self.speed_slider.setValue(0)