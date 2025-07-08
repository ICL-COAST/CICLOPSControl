import win32com.client
import time
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.dates import date2num, DateFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from matplotlib.gridspec import GridSpec
import pythoncom  # For COM initialization

class MountVisualizer:
    def __init__(self, mount=None, window_title="Mount Position Visualizer"):
        # Store mount reference
        self.mount = mount
        
        # Create Tkinter window
        self.root = tk.Tk()
        self.root.title(window_title)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.geometry("800x600")
        
        # Create figure with both polar and rectangular plots
        self.fig = Figure(figsize=(8, 8))  # Increased height to accommodate extra plot
        gs = GridSpec(3, 2, figure=self.fig, height_ratios=[2, 1, 1])
        
        # Polar plot for Alt/Az
        self.polar_ax = self.fig.add_subplot(gs[0, 0], projection='polar')
        self.polar_ax.set_title("Alt/Az Position (Polar)")
        self.polar_ax.set_theta_zero_location('N')  # 0 degrees at North
        self.polar_ax.set_theta_direction(-1)       # Clockwise
        self.polar_ax.set_ylim(0, 90)  # Set radial limits from 0 to 90 degrees
        self.polar_ax.set_yticks([0, 30, 60, 90])  # Radial ticks at these altitudes
        self.polar_ax.set_yticklabels(['90°', '60°', '30°', '0°'])  # Invert labels (90° at center)
        self.polar_ax.grid(True)
        self.polar_point, = self.polar_ax.plot([], [], 'ro', markersize=8)
        
        # Add Az-El rectangular plot
        self.azel_ax = self.fig.add_subplot(gs[0, 1])
        self.azel_ax.set_title("Az-El Position")
        self.azel_ax.set_xlabel("Azimuth (°)")
        self.azel_ax.set_ylabel("Elevation (°)")
        self.azel_ax.set_xlim(0, 360)
        self.azel_ax.set_ylim(0, 90)
        self.azel_ax.grid(True)
        self.azel_point, = self.azel_ax.plot([], [], 'bo', markersize=8)
        
        # Embed plot in Tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # Status display
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(fill=tk.X)
        
        self.alt_label = tk.Label(self.status_frame, text="Alt: --°")
        self.alt_label.pack(side=tk.LEFT, padx=10)
        
        self.az_label = tk.Label(self.status_frame, text="Az: --°")
        self.az_label.pack(side=tk.LEFT, padx=10)
        
        self.running = True
        self.fig.tight_layout()
        
        # Update interval in milliseconds for polling the mount
        self.update_interval_ms = 50  # 20 Hz refresh rate
    
    def update_mount_position(self):
        """Poll the mount for position and update display"""
        if self.running and self.mount and self.mount.Connected:
            try:
                # Get current position from mount
                az = self.mount.Azimuth
                alt = self.mount.Altitude
                
                # Update display with new position
                self.update_display(az, alt)
            except Exception as e:
                print(f"Error updating position: {e}")
                
        # Schedule the next update if still running
        if self.running:
            self.root.after(self.update_interval_ms, self.update_mount_position)
    
    def update_display(self, azimuth, altitude):
        """Update the visualizer with new position data"""
        # Convert azimuth to radians for polar plot
        az_rad = np.radians(azimuth)
        
        # Update polar plot (with direct r = altitude to show altitude from horizon)
        # Horizon is at r=0, zenith at r=90
        r = 90 - altitude  # This makes zenith at center (r=0) and horizon at r=90
        self.polar_point.set_data([az_rad], [r])
        
        # Update Az-El rectangular plot
        self.azel_point.set_data([azimuth], [altitude])
    
        # Update status labels
        self.alt_label.config(text=f"Alt: {altitude:.2f}°")
        self.az_label.config(text=f"Az: {azimuth:.2f}°")
        
        # Refresh canvas
        self.canvas.draw_idle()
    
    def on_close(self):
        """Handle window close event"""
        self.running = False
        self.root.quit()
        self.root.destroy()
    
    def set_mount(self, mount):
        """Set or change the mount being monitored"""
        self.mount = mount
    
    def start(self):
        """Start the visualization with mount polling"""
        # Start polling for mount position
        if self.mount:
            self.update_mount_position()
        
        # Start the Tkinter main loop
        self.root.mainloop()

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
    # Initialize COM
    pythoncom.CoInitialize()
    
    try:
        # Connect to the mount
        print("Select your telescope mount...")
        # mount = connect_to_mount()
        mount = connect_to_mount("ASCOM.Simulator.Telescope")
        
        if mount:
            # Create and start visualizer
            visualizer = MountVisualizer(mount=mount)
            visualizer.start()
        else:
            print("No mount selected. Exiting...")
    
    finally:
        # Clean up COM
        pythoncom.CoUninitialize()