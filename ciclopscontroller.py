from ciclopscontroller.ui.mainwindow import MainWindow
import sys
from PySide6.QtWidgets import QApplication 
from PySide6.QtCore import QTimer, QThread

from ciclopscontroller.controllers.satcontroller import SatController
from ciclopscontroller.controllers.mountcontroller import MountController
from ciclopscontroller.controllers.timecontroller import TimeController

import signal
import atexit

if __name__ == "__main__":
    # pg.setConfigOption(antialias=True)
    app = QApplication(sys.argv)

    time_controller = TimeController()
    time_controller_thread = QThread()
    time_controller.moveToThread(time_controller_thread)

    sat_controller = SatController(time_controller)
    sat_controller_thread = QThread()
    sat_controller.moveToThread(sat_controller_thread)

    mount_controller = MountController(time_controller, sat_controller) 
    mount_controller_thread = QThread()
    mount_controller.moveToThread(mount_controller_thread)

    time_controller_thread.start()
    sat_controller_thread.start()
    mount_controller_thread.start()

    time_controller.initialize_timer()

    window = MainWindow(time_controller, mount_controller, sat_controller)
    window.show()


    def signal_handler(signal, frame):
        app.quit()
    
    def cleanup():
        time_controller_thread.quit()
        sat_controller_thread.quit()
        mount_controller_thread.quit()

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)

    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec())