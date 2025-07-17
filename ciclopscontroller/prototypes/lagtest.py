import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np
from time import perf_counter
class testLine():
    def __init__(self, view, distance, length, n_points=100):
        self.distance = distance
        self.length = length
        self.n_points = n_points
        self.view = view

        self.point = gl.GLScatterPlotItem(
            pos=[(distance, 0, 0)],
            size=1,
            color=(1, 0, 0, 1),
            pxMode=False
        )
        self.view.addItem(self.point)
        self.line = gl.GLLinePlotItem(
            pos=self.generate_points(0),
            color=(1, 1, 1, 1),
            width=2,
            antialias=True
        )
        self.view.addItem(self.line)
    def generate_points(self, t):
        points = []
        # for i in range(self.n_points):
        #     x = self.distance * np.cos(i * self.length / self.n_points / self.distance + t)
        #     y = self.distance * np.sin(i * self.length / self.n_points / self.distance + t)
        #     points.append((x, y, 0))
        for i in range(self.n_points):
            # points.append((self.distance, 0, i* self.length / self.n_points))
            points.append((self.distance, 0, i))
        return points
    
    def update(self, t):
        # data = self.generate_points(t)
        self.point.setData(pos=[(self.distance * np.cos(t), self.distance * np.sin(t), 0)])
        # self.line.setData(pos=data)


class GLTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GL Test")
        self.setGeometry(100, 100, 800, 600)


        self.widget = gl.GLViewWidget()
        self.widget.setCameraPosition(distance=100)

        self.fps_label = QLabel("FPS: 0")
        
        self.lines = []
        for i in range(500):
            line = testLine(self.widget, distance=i+1, length=i+1, n_points=10)
            self.lines.append(line)


        self.last_time = perf_counter()


        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.addWidget(self.widget)
        main_layout.addWidget(self.fps_label)
        self.setCentralWidget(main_widget)

        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def animate(self):
        current_time = perf_counter()
        delta_time = current_time - self.last_time
        self.last_time = current_time

        self.fps_label.setText(f"FPS: {1 / delta_time:.2f}")

        for line in self.lines:
            line.update(perf_counter() / 10)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GLTest()
    window.show()
    sys.exit(app.exec())