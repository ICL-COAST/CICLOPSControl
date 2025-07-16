from OpenGL.GL import (GL_TEXTURE_2D, GL_RGBA, GL_UNSIGNED_BYTE,
                          glEnable, glGenTextures, glBindTexture, glTexParameteri
                          , GL_LINEAR, GL_NEAREST, GL_CLAMP_TO_BORDER, GL_PROXY_TEXTURE_2D
                          , glTexImage2D, glGetTexLevelParameteriv, GL_TEXTURE_WIDTH
                          , GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_WRAP_S
                          , GL_TEXTURE_WRAP_T, glColor4f, glBegin, glEnd
                          , glVertex3f, glTexCoord2f, glDisable, GL_QUADS)
import numpy as np
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem


class GLTexturedSphereItem(GLGraphicsItem):
    def __init__(self, data, r=6371, smooth=False, glOptions="translucent", parentItem=None):
        """

        ==============  =======================================================================================
        **Arguments:**
        data            Volume data to be rendered. *Must* be 3D numpy array (x, y, RGBA) with dtype=ubyte.
                        (See functions.makeRGBA)
        smooth          (bool) If True, the volume slices are rendered with linear interpolation
        ==============  =======================================================================================
        """
        self.r = r
        self.smooth = smooth
        self._needUpdate = False
        super().__init__(parentItem=parentItem)
        self.setData(data)
        self.setGLOptions(glOptions)
        self.texture = None

    def initializeGL(self):
        if self.texture is not None:
            return
        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)

    def setData(self, data):
        self.data = data
        self._needUpdate = True
        self.update()

    def _updateTexture(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        if self.smooth:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        # glTexParameteri(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_BORDER)
        shape = self.data.shape

        ## Test texture dimensions first
        glTexImage2D(
            GL_PROXY_TEXTURE_2D,
            0,
            GL_RGBA,
            shape[0],
            shape[1],
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )
        if glGetTexLevelParameteriv(GL_PROXY_TEXTURE_2D, 0, GL_TEXTURE_WIDTH) == 0:
            raise Exception(
                "OpenGL failed to create 2D texture (%dx%d); too large for this hardware."
                % shape[:2]
            )

        data = np.ascontiguousarray(self.data.transpose((1, 0, 2)))
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            shape[0],
            shape[1],
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            data,
        )
        glDisable(GL_TEXTURE_2D)

    def paint(self):
        if self._needUpdate:
            self._updateTexture()
            self._needUpdate = False
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        self.setupGLState()

        glColor4f(1, 1, 1, 1)

        theta = np.linspace(0, np.pi, 32, dtype="float32")
        phi = np.linspace(0, 2 * np.pi, 64, dtype="float32")
        t_n = theta / np.pi
        p_n = phi / (2 * np.pi)

        glBegin(GL_QUADS)
        for j in range(len(theta) - 1):
            for i in range(len(phi) - 1):
                xyz_nw = self.to_xyz(phi[i], theta[j])
                xyz_sw = self.to_xyz(phi[i], theta[j + 1])
                xyz_se = self.to_xyz(phi[i + 1], theta[j + 1])
                xyz_ne = self.to_xyz(phi[i + 1], theta[j])

                glTexCoord2f(p_n[i], t_n[j])
                glVertex3f(xyz_nw[0], xyz_nw[1], xyz_nw[2])
                glTexCoord2f(p_n[i], t_n[j + 1])
                glVertex3f(xyz_sw[0], xyz_sw[1], xyz_sw[2])
                glTexCoord2f(p_n[i + 1], t_n[j + 1])
                glVertex3f(xyz_se[0], xyz_se[1], xyz_se[2])
                glTexCoord2f(p_n[i + 1], t_n[j])
                glVertex3f(xyz_ne[0], xyz_ne[1], xyz_ne[2])

        glEnd()
        glDisable(GL_TEXTURE_2D)

    def to_xyz(self, phi, theta):
        theta = np.pi - theta
        xpos = self.r * np.sin(theta) * np.cos(phi)
        ypos = self.r * np.sin(theta) * np.sin(phi)
        zpos = self.r * np.cos(theta)
        return xpos, ypos, zpos


if __name__ == "__main__":        
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    from PIL import Image
    import os

    app = pg.mkQApp("GLImageItem Example")
    w = gl.GLViewWidget()
    w.show()
    w.setWindowTitle("pyqtgraph example: GLImageItem")
    w.setCameraPosition(distance=20)

    earth_image = Image.open(os.path.join(os.path.dirname(__file__), "earth_texture.jpg")).transpose(Image.ROTATE_90).transpose(Image.FLIP_LEFT_RIGHT)
    earth_array = np.array(earth_image)

    if earth_array.shape[2] == 3:  # RGB image
        earth_rgba = np.zeros((earth_array.shape[0], earth_array.shape[1], 4), dtype=np.uint8)
        earth_rgba[..., :3] = earth_array
        earth_rgba[..., 3] = 255  # Full opacity
    else:
        earth_rgba = earth_array

    # v1 = GLTexturedSphereItem(np.clip(smooth, 0, 255))
    v1 = GLTexturedSphereItem(earth_rgba)
    w.addItem(v1)

    pg.exec()