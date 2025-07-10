import win32com.client
import time
from datetime import datetime

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

def slew_altaz(mount, azimuth, altitude):
    """Slew to Alt/Az coordinates (using calibrated model)"""
    if not mount.CanSlewAltAzAsync:
        print("Mount does not support Alt/Az slewing asynchronously")
        return
    if mount.CanMoveAxis(0) and mount.CanMoveAxis(1):  # Check Alt/Az capability
        # For 10Micron, we need to set tracking off for Alt/Az slewing
        tracking_state = mount.Tracking
        mount.Tracking = False
        # mount.Tracking = True

        # Slew to position
        mount.SlewToAltAzAsync(azimuth, altitude)
        # mount.SlewToCoordinatesAsync(azimuth, altitude)
        print(f"Slewing to Az: {azimuth}, Alt: {altitude}")
        time.sleep(2)
        mount.AbortSlew() 
        mount.MoveAxis(0, 0.01)
        mount.MoveAxis(1, 0.01)
        print("Slew aborted")
        
        # Wait for slew to complete
        # while mount.Slewing:
        #     print("Slewing...", end="\r")
        #     time.sleep(0.5)
        
        # Restore original tracking state
        mount.Tracking = tracking_state
        
        print(f"Position reached: Az={mount.Azimuth}, Alt={mount.Altitude}")
    else:
        print("Mount does not support direct Alt/Az slewing")

def follow_path(mount, points):
    """Follow a predetermined path of points"""
    for point in points:
        az, alt = point
        slew_altaz(mount, az, alt)

def main():
    # For OmniSim: "ASCOM.Simulator.Telescope"
    # For real mount, leave blank to use chooser
    mount = connect_to_mount("ASCOM.Simulator.Telescope")
    if not mount:
        return
    
    try:
        # Example path - replace with your desired coordinates
        # Format: [(az1, alt1), (az2, alt2), ...]
        # altaz_path = [
        #     (60, 20),
        #     (120, 20),
        #     (45, 45),
        #     (135, 45),
        #     (270, 20),
        #     (180, 45)
        # ]
        # altaz_path = [
        #     (4, -20),
        #     (4, 20),
        #     (12, 0),
        #     (20, 20),
        #     (20, -20)
        # ]
        x_values = range(0, 360, 20)  # 0, 20, 40, 60, 80
        y_values = [20, 60, 0]

        # Generate the points
        altaz_path = []
        for x in x_values:
            for y in y_values:
                altaz_path.append((x, y))

        print("Following Alt/Az path...")
        follow_path(mount, altaz_path)
        
        # Example RA/Dec path
        # Format: [(ra1, dec1), (ra2, dec2), ...]
        
    finally:
        # Always disconnect
        if mount.Connected:
            mount.Connected = False
            print("Disconnected from mount")

if __name__ == "__main__":
    main()