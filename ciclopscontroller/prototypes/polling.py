import win32com.client
from time import perf_counter

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


counts = 0
mount = connect_to_mount()
if mount:
    while True:
        try:
            # Example: Get current position
            start_time = perf_counter()
            azi = mount.Azimuth
            alt = mount.Altitude
            # mount.MoveAxis(0, 0.1)  # Move RA axis
            # mount.MoveAxis(1, 0.1)  # Move RA axis
            counts += 1
            elapsed_time = perf_counter() - start_time
            print(f"Current Position - Azimuth: {azi:<.2f}, Altitude: {alt:<.2f} (Elapsed Time: {elapsed_time:.2f}s)")
            # print(f"Current Position - RA: {ra}, Dec: {dec} (Counts: {counts})")
            # if counts % 100 == 0:
                # print(f"Current Position - RA: {ra}, Dec: {dec} (Counts: {counts})")

        except Exception as e:
            print(f"Error accessing mount: {e}")
        # break