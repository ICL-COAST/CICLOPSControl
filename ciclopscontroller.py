from ciclopscontroller.ui.mainwindow import SatelliteOrbitVisualizerGL
import pyqtgraph as pg
import sys
from PySide6.QtWidgets import QApplication 
from PySide6.QtCore import QTimer

import signal

if __name__ == "__main__":
    # pg.setConfigOption(antialias=True)

    app = QApplication(sys.argv)
    window = SatelliteOrbitVisualizerGL()
    window.show()


    def signal_handler(signal, frame):
        app.quit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec())