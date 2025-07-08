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
    if mount.CanMoveAxis(0) and mount.CanMoveAxis(1):  # Check Alt/Az capability
        print(f"Slewing to Az: {azimuth}, Alt: {altitude}")
        # For 10Micron, we need to set tracking off for Alt/Az slewing
        tracking_state = mount.Tracking
        mount.Tracking = False
        
        # Slew to position
        mount.SlewToAltAz(azimuth, altitude)
        
        # Wait for slew to complete
        while mount.Slewing:
            print("Slewing...", end="\r")
            time.sleep(0.5)
        
        # Restore original tracking state
        mount.Tracking = tracking_state
        
        print(f"Position reached: Az={mount.Azimuth}, Alt={mount.Altitude}")
    else:
        print("Mount does not support direct Alt/Az slewing")

def slew_radec(mount, ra, dec):
    """Slew to RA/Dec coordinates (using calibrated model)"""
    print(f"Slewing to RA: {ra}, Dec: {dec}")
    
    # Ensure tracking is on for RA/Dec slewing
    mount.Tracking = True
    
    # Slew to position
    mount.SlewToCoordinates(ra, dec)
    
    # Wait for slew to complete
    while mount.Slewing:
        print("Slewing...", end="\r")
        time.sleep(0.5)
    
    print(f"Position reached: RA={mount.RightAscension}, Dec={mount.Declination}")

def follow_path(mount, points, coordinate_type="altaz"):
    """Follow a predetermined path of points"""
    for point in points:
        if coordinate_type.lower() == "altaz":
            az, alt = point
            slew_altaz(mount, az, alt)
        else:  # radec
            ra, dec = point
            slew_radec(mount, ra, dec)
        
        # Wait between points
        time.sleep(2)

def main():
    # For OmniSim: "ASCOM.Simulator.Telescope"
    # For real mount, leave blank to use chooser
    mount = connect_to_mount("ASCOM.Simulator.Telescope")
    if not mount:
        return
    
    try:
        # Example path - replace with your desired coordinates
        # Format: [(az1, alt1), (az2, alt2), ...]
        altaz_path = [
            (180, 45),
            (190, 50),
            (200, 55),
            (210, 50),
            (220, 45)
        ]
        
        print("Following Alt/Az path...")
        follow_path(mount, altaz_path, "altaz")
        
        # Example RA/Dec path
        # Format: [(ra1, dec1), (ra2, dec2), ...]
        radec_path = [
            (12.5, 45),
            (12.6, 46),
            (12.7, 47),
            (12.8, 46),
            (12.9, 45)
        ]
        
        print("Following RA/Dec path...")
        follow_path(mount, radec_path, "radec")
        
    finally:
        # Always disconnect
        if mount.Connected:
            mount.Connected = False
            print("Disconnected from mount")

if __name__ == "__main__":
    main()