import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QMouseEvent, QKeyEvent
from OpenGL.GL import *
from OpenGL.GLU import *


class FirstPersonGLWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setCursor(Qt.BlankCursor)

        # Camera settings
        self.position = np.array([0.0, 0.0, 5.0], dtype=np.float32)
        self.yaw = -90.0
        self.pitch = 0.0
        self.last_mouse_pos = None
        self.sensitivity = 0.1
        self.speed = 0.1

        self.keys = set()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_movement)
        self.timer.start(16)  # ~60 FPS

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, w / h if h != 0 else 1, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera transformation
        direction = self.get_direction()
        center = self.position + direction
        gluLookAt(*self.position, *center, 0, 1, 0)

        # Render a cube
        glBegin(GL_QUADS)
        glColor3f(1, 0, 0)
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, 1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, -1, -1)
        glEnd()

    def get_direction(self):
        rad_yaw = np.radians(self.yaw)
        rad_pitch = np.radians(self.pitch)
        x = np.cos(rad_yaw) * np.cos(rad_pitch)
        y = np.sin(rad_pitch)
        z = np.sin(rad_yaw) * np.cos(rad_pitch)
        return np.array([x, y, z], dtype=np.float32)

    def update_movement(self):
        direction = self.get_direction()
        right = np.cross(direction, [0, 1, 0])
        up = np.cross(right, direction)

        if Qt.Key_W in self.keys:
            self.position += direction * self.speed
        if Qt.Key_S in self.keys:
            self.position -= direction * self.speed
        if Qt.Key_A in self.keys:
            self.position -= right * self.speed
        if Qt.Key_D in self.keys:
            self.position += right * self.speed

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.last_mouse_pos is None:
            self.last_mouse_pos = event.position()
            return

        dx = event.position().x() - self.last_mouse_pos.x()
        dy = self.last_mouse_pos.y() - event.position().y()  # Invert y-axis

        self.last_mouse_pos = event.position()

        self.yaw += dx * self.sensitivity
        self.pitch += dy * self.sensitivity
        self.pitch = np.clip(self.pitch, -89.0, 89.0)

    def keyPressEvent(self, event: QKeyEvent):
        self.keys.add(event.key())

    def keyReleaseEvent(self, event: QKeyEvent):
        self.keys.discard(event.key())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("First-Person OpenGL Viewer")
        self.resize(800, 600)
        self.setCentralWidget(FirstPersonGLWidget())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
