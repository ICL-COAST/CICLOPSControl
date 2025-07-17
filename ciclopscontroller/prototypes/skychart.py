#!/usr/bin/env python3
"""
Sky Chart Plotter
A simple application to plot star positions and constellations using PyQtGraph and PySide6
"""

import sys
import numpy as np
from datetime import datetime
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QSlider, QDateTimeEdit, 
    QComboBox, QGroupBox
)
from PySide6.QtCore import Qt, QDateTime, Slot
from pyqtgraph.Qt import QtCore

# Sample star data (right ascension, declination, magnitude)
# Format: (RA in hours, DEC in degrees, magnitude)
SAMPLE_STARS = [
    # Bright stars in the sky
    (2.53, 89.26, 2.0),   # Polaris (North Star)
    (6.75, -16.72, 0.5),  # Sirius (brightest star)
    (5.92, 7.41, 0.4),    # Betelgeuse (in Orion)
    (5.24, -8.20, 0.2),   # Rigel (in Orion)
    (14.66, -60.83, 0.1), # Alpha Centauri
    (19.85, 8.87, 0.8),   # Altair
    (18.62, 38.78, 0.1),  # Vega
    (22.14, -46.96, 1.2), # Fomalhaut
    (22.96, -29.62, 1.1), # Formalhaut
    # Add more stars as needed
]

# Sample constellation lines as pairs of star indices
SAMPLE_CONSTELLATIONS = [
    # Ursa Major (Big Dipper) - simplified
    [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)],
    # Orion - simplified
    [(7, 8), (8, 9), (9, 10), (10, 11)],
    # Add more constellations as needed
]

class SkyChartPlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sky Chart Plotter")
        self.setGeometry(100, 100, 800, 600)
        
        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('k')  # Black background for sky
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.showGrid(False, False)
        
        # Set up plot axes
        self.plot_widget.setXRange(-1.2, 1.2)
        self.plot_widget.setYRange(-1.2, 1.2)
        self.plot_widget.getPlotItem().hideAxis('bottom')
        self.plot_widget.getPlotItem().hideAxis('left')
        
        # Add circle for horizon
        horizon_circle = pg.QtWidgets.QGraphicsEllipseItem(-1, -1, 2, 2)
        horizon_circle.setPen(pg.mkPen('w', width=1))
        self.plot_widget.addItem(horizon_circle)
        
        # Create scatter plot item for stars
        self.scatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 120))
        self.plot_widget.addItem(self.scatter)
        
        # Add directional labels (N, E, S, W)
        self.add_direction_labels()
        
        # Control panel
        control_panel = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_panel)
        
        # Date and time selector
        date_time_layout = QHBoxLayout()
        date_time_layout.addWidget(QLabel("Date and Time:"))
        self.date_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.date_time_edit.setCalendarPopup(True)
        self.date_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.date_time_edit.dateTimeChanged.connect(self.update_plot)
        date_time_layout.addWidget(self.date_time_edit)
        control_layout.addLayout(date_time_layout)
        
        # Location selector (simplified)
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location:"))
        self.location_combo = QComboBox()
        self.location_combo.addItems(["New York (40.7°N, 74.0°W)", 
                                      "London (51.5°N, 0.1°W)", 
                                      "Tokyo (35.7°N, 139.8°E)", 
                                      "Sydney (33.9°S, 151.2°E)"])
        self.location_combo.currentIndexChanged.connect(self.update_plot)
        location_layout.addWidget(self.location_combo)
        control_layout.addLayout(location_layout)
        
        # Magnitude slider
        mag_layout = QHBoxLayout()
        mag_layout.addWidget(QLabel("Magnitude limit:"))
        self.magnitude_slider = QSlider(Qt.Horizontal)
        self.magnitude_slider.setMinimum(0)
        self.magnitude_slider.setMaximum(60)
        self.magnitude_slider.setValue(40)
        self.magnitude_slider.valueChanged.connect(self.update_plot)
        mag_layout.addWidget(self.magnitude_slider)
        self.mag_value_label = QLabel("4.0")
        mag_layout.addWidget(self.mag_value_label)
        control_layout.addLayout(mag_layout)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Update button
        update_button = QPushButton("Update Chart")
        update_button.clicked.connect(self.update_plot)
        button_layout.addWidget(update_button)
        
        # Reset button
        reset_button = QPushButton("Reset View")
        reset_button.clicked.connect(self.reset_view)
        button_layout.addWidget(reset_button)
        
        control_layout.addLayout(button_layout)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.plot_widget, stretch=4)
        self.main_layout.addWidget(control_panel, stretch=1)
        
        # Initial plot
        self.update_plot()
    
    def add_direction_labels(self):
        # Add North label
        north_label = pg.TextItem("N", color=(255, 0, 0))
        north_label.setPos(0, -1.1)
        north_label.setAnchor((0.5, 0.5))
        self.plot_widget.addItem(north_label)
        
        # Add East label
        east_label = pg.TextItem("E", color=(255, 0, 0))
        east_label.setPos(1.1, 0)
        east_label.setAnchor((0.5, 0.5))
        self.plot_widget.addItem(east_label)
        
        # Add South label
        south_label = pg.TextItem("S", color=(255, 0, 0))
        south_label.setPos(0, 1.1)
        south_label.setAnchor((0.5, 0.5))
        self.plot_widget.addItem(south_label)
        
        # Add West label
        west_label = pg.TextItem("W", color=(255, 0, 0))
        west_label.setPos(-1.1, 0)
        west_label.setAnchor((0.5, 0.5))
        self.plot_widget.addItem(west_label)
    
    @Slot()
    def update_plot(self):
        # Clear existing constellation lines
        for item in self.plot_widget.items():
            if isinstance(item, pg.PlotCurveItem):
                self.plot_widget.removeItem(item)
        
        # Get current magnitude limit
        mag_limit = self.magnitude_slider.value() / 10.0
        self.mag_value_label.setText(f"{mag_limit:.1f}")
        
        # In a real app, calculate star positions based on time and location
        # For this example, we'll just use the sample data
        
        # Convert RA/Dec to x/y coordinates (simplified azimuthal projection)
        spots = []
        for ra, dec, mag in SAMPLE_STARS:
            if mag <= mag_limit:  # Only show stars brighter than the magnitude limit
                # Convert RA/Dec to radians
                ra_rad = ra * np.pi / 12.0  # RA is in hours (0-24)
                dec_rad = dec * np.pi / 180.0  # Dec is in degrees
                
                # Simple stereographic projection
                # This is a simplified mapping and doesn't account for time/location
                r = (np.pi/2 - dec_rad) / (np.pi/2)
                x = r * np.cos(ra_rad)
                y = r * np.sin(ra_rad)
                
                # Size based on magnitude (brighter = larger)
                size = max(3, (7 - mag) * 2)
                
                spots.append({
                    'pos': (x, y),
                    'size': size,
                    'brush': pg.mkBrush(255, 255, 255, 200)
                })
        
        self.scatter.setData(spots)
        
        # Draw constellation lines (simplified version)
        # In a real app, these would be calculated based on the projected star positions
        for i, (x, y, _) in enumerate(SAMPLE_STARS[:10]):
            # Just draw some sample lines between adjacent stars
            if i > 0:
                ra1, dec1, _ = SAMPLE_STARS[i-1]
                ra2, dec2, _ = SAMPLE_STARS[i]
                
                # Convert to x/y
                ra1_rad = ra1 * np.pi / 12.0
                dec1_rad = dec1 * np.pi / 180.0
                r1 = (np.pi/2 - dec1_rad) / (np.pi/2)
                x1 = r1 * np.cos(ra1_rad)
                y1 = r1 * np.sin(ra1_rad)
                
                ra2_rad = ra2 * np.pi / 12.0
                dec2_rad = dec2 * np.pi / 180.0
                r2 = (np.pi/2 - dec2_rad) / (np.pi/2)
                x2 = r2 * np.cos(ra2_rad)
                y2 = r2 * np.sin(ra2_rad)
                
                # Create line
                line = pg.PlotCurveItem([x1, x2], [y1, y2], pen=pg.mkPen('c', width=1))
                self.plot_widget.addItem(line)
    
    @Slot()
    def reset_view(self):
        self.plot_widget.setXRange(-1.2, 1.2)
        self.plot_widget.setYRange(-1.2, 1.2)
        self.date_time_edit.setDateTime(QDateTime.currentDateTime())
        self.magnitude_slider.setValue(40)
        self.location_combo.setCurrentIndex(0)
        self.update_plot()

def main():
    app = QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)  # Enable antialiasing for prettier plots
    window = SkyChartPlotter()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()