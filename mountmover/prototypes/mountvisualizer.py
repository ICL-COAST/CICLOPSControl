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
        gs = GridSpec(2, 2, figure=self.fig, height_ratios=[1, 1])
        
        x_values = range(0, 360, 20)  # 0, 20, 40, 60, 80
        y_values = [20, 60, 0]

        # Generate the points
        altaz_path = []
        for x in x_values:
            for y in y_values:
                altaz_path.append((x, y))

        targets_az = np.array([t[0] for t in altaz_path])
        targets_el = np.array([t[1] for t in altaz_path])

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
        self.polar_point_target, = self.polar_ax.plot(np.deg2rad(targets_az), 90 - targets_el, 'gx', markersize=4, label='Target')
        for i, (az, el) in enumerate(zip(targets_az, targets_el)):
            self.polar_ax.text(np.deg2rad(az), 90 - el + 10, f'{i+1}', fontsize=8, ha='center', va='center')

        # Polar plot for RA/DEC in Celestial coordinates
        self.polar_ax_cel = self.fig.add_subplot(gs[1, 0], projection='polar')
        self.polar_ax_cel.set_title("RA/DEC Position (Polar)")
        self.polar_ax_cel.set_theta_zero_location('N')  # 0 degrees at North
        self.polar_ax_cel.set_theta_direction(-1)       # Clockwise
        self.polar_ax_cel.set_ylim(-90, 90)  # Set radial limits from 0 to 90 degrees
        self.polar_ax_cel.set_yticks([0, 30, 60, 90])  # Radial ticks at these altitudes
        self.polar_ax_cel.set_yticklabels(['90°', '60°', '30°', '0°'])  # Invert labels (90° at center)
        self.polar_ax_cel.grid(True)
        self.polar_point_cel, = self.polar_ax_cel.plot([], [], 'ro', markersize=8)
        self.polar_point_cel_target, = self.polar_ax_cel.plot([], [], 'gx', markersize=8, label='Target')

        # Add Az-El rectangular plot
        self.azel_ax = self.fig.add_subplot(gs[0, 1])
        self.azel_ax.set_title("Az-El Position")
        self.azel_ax.set_xlabel("Azimuth (°)")
        self.azel_ax.set_ylabel("Elevation (°)")
        self.azel_ax.set_xlim(0, 360)
        self.azel_ax.set_ylim(0, 90)
        self.azel_ax.grid(True)
        self.azel_point, = self.azel_ax.plot([], [], 'bo', markersize=8)
        self.azel_point_target, = self.azel_ax.plot(targets_az, targets_el, 'gx', markersize=4, label='Target')
        for i, (az, el) in enumerate(zip(targets_az, targets_el)):
            self.azel_ax.text(az + 10, el + 5, f'{i+1}', fontsize=8, ha='center', va='center')

        # Add RA/DEC rectangular plot in celestial coordinates
        self.azel_ax_cel = self.fig.add_subplot(gs[1, 1])
        self.azel_ax_cel.set_title("RA/DEC Position")
        self.azel_ax_cel.set_xlabel("Right Ascension (°)")
        self.azel_ax_cel.set_ylabel("Declination (°)")
        self.azel_ax_cel.set_xlim(0, 24)
        self.azel_ax_cel.set_ylim(-90, 90)
        self.azel_ax_cel.grid(True)
        self.azel_point_cel, = self.azel_ax_cel.plot([], [], 'bo', markersize=8)
        self.azel_point_cel_target, = self.azel_ax_cel.plot([], [], 'gx', markersize=8, label='Target')

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
                ra = self.mount.RightAscension
                dec = self.mount.Declination
                target_ra = self.mount.RightAscension
                target_dec = self.mount.Declination

                # print(f"Current Position - Az: {az}, Alt: {alt}, RA: {ra}, Dec: {dec}")
                # print(f"Target Position - RA: {target_ra}, Dec: {target_dec}")

                # Update display with new position
                self.update_display(az, alt, ra, dec, target_ra, target_dec)
            except Exception as e:
                print(f"Error updating position: {e}")
                
        # Schedule the next update if still running
        if self.running:
            self.root.after(self.update_interval_ms, self.update_mount_position)
    
    def update_display(self, azimuth, altitude, ra, dec, target_ra=None, target_dec=None):
        """Update the visualizer with new position data"""
        # Convert azimuth to radians for polar plot
        az_rad = np.radians(azimuth)
        
        # Update polar plot (with direct r = altitude to show altitude from horizon)
        # Horizon is at r=0, zenith at r=90
        r = 90 - altitude  # This makes zenith at center (r=0) and horizon at r=90
        self.polar_point.set_data([az_rad], [r])
        
        # Update Az-El rectangular plot
        self.azel_point.set_data([azimuth], [altitude])

        # Update celestial polar plot (RA/DEC)
        ra_rad = np.radians(ra)
        dec_rad = np.radians(dec)
        self.polar_point_cel.set_data([ra_rad * 15], [dec_rad])

        # Update celestial Az-El rectangular plot
        self.azel_point_cel.set_data([ra], [dec])

        # If target coordinates are provided, update them as well
        if target_ra is not None and target_dec is not None:
            target_ra_rad = np.radians(target_ra)
            target_dec_rad = np.radians(target_dec)
            self.polar_point_cel_target.set_data([target_ra_rad * 15], [target_dec_rad])
            self.azel_point_cel_target.set_data([target_ra], [target_dec])
        else:
            # If no target coordinates, clear the target points
            self.polar_point_cel_target.set_data([], [])
            self.azel_point_cel_target.set_data([], [])

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
    except KeyboardInterrupt:
        print("Exiting visualizer...")
    finally:
        # Clean up COM
        pythoncom.CoUninitialize()