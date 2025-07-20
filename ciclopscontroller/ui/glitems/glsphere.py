from OpenGL.GL import (GL_TEXTURE_2D, GL_RGBA, GL_UNSIGNED_BYTE,
                      glEnable, glGenTextures, glBindTexture, glTexParameteri,
                      GL_LINEAR, GL_NEAREST, GL_CLAMP_TO_BORDER, GL_PROXY_TEXTURE_2D,
                      glTexImage2D, glGetTexLevelParameteriv, GL_TEXTURE_WIDTH,
                      GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_WRAP_S,
                      GL_TEXTURE_WRAP_T, glColor4f, glBegin, glEnd,
                      glVertex3f, glTexCoord2f, glDisable, GL_TRIANGLES, GL_DEPTH_TEST)
import numpy as np
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem


class GLSphere(GLGraphicsItem):
    def __init__(self, data, r=6371, smooth=False, resolution=(16, 32), glOptions="opaque", parentItem=None):
        """
        ==============  =======================================================================================
        **Arguments:**
        data            Volume data to be rendered. *Must* be 3D numpy array (x, y, RGBA) with dtype=ubyte.
        r               Radius of the sphere
        smooth          (bool) If True, the volume slices are rendered with linear interpolation
        resolution      Tuple (theta_divs, phi_divs) controlling sphere mesh resolution
        ==============  =======================================================================================
        """
        self.r = r
        self.smooth = smooth
        self.resolution = resolution  # (theta divisions, phi divisions)
        self._needUpdate = False
        super().__init__(parentItem=parentItem)
        self.setData(data)
        self.setGLOptions(glOptions)
        self.texture = None
        
        # Pre-compute sphere vertices and texture coordinates
        self._precompute_sphere_mesh()

    def _precompute_sphere_mesh(self):
        """Pre-compute the sphere mesh to avoid recalculations during rendering"""
        theta_divs, phi_divs = self.resolution
        theta = np.linspace(0, np.pi, theta_divs, dtype="float32")
        phi = np.linspace(0, 2 * np.pi, phi_divs, dtype="float32")
        t_n = theta / np.pi
        p_n = phi / (2 * np.pi)
        
        # Create arrays to store coordinates
        self.vertices = []
        self.texcoords = []
        
        for j in range(len(theta) - 1):
            for i in range(len(phi) - 1):
                # Compute texture coordinates for the quad corners
                tex_nw = (p_n[i], t_n[j])
                tex_sw = (p_n[i], t_n[j + 1])
                tex_se = (p_n[i + 1], t_n[j + 1])
                tex_ne = (p_n[i + 1], t_n[j])
                
                # Compute vertex coordinates for the quad corners
                xyz_nw = self.to_xyz(phi[i], theta[j])
                xyz_sw = self.to_xyz(phi[i], theta[j + 1])
                xyz_se = self.to_xyz(phi[i + 1], theta[j + 1])
                xyz_ne = self.to_xyz(phi[i + 1], theta[j])
                
                # Store quad vertices and texture coordinates (as two triangles)
                # First triangle (nw, sw, se)
                self.vertices.append(xyz_nw)
                self.vertices.append(xyz_sw)
                self.vertices.append(xyz_se)
                self.texcoords.append(tex_nw)
                self.texcoords.append(tex_sw)
                self.texcoords.append(tex_se)
                
                # Second triangle (nw, se, ne)
                self.vertices.append(xyz_nw)
                self.vertices.append(xyz_se)
                self.vertices.append(xyz_ne)
                self.texcoords.append(tex_nw)
                self.texcoords.append(tex_se)
                self.texcoords.append(tex_ne)

    def initializeGL(self):
        if self.texture is not None:
            return
        glEnable(GL_TEXTURE_2D)
        self.texture = glGenTextures(1)

    def setData(self, data):
        self.data = data
        self._needUpdate = True
        self.update()
        
    def setResolution(self, resolution):
        """Set the resolution of the sphere mesh"""
        self.resolution = resolution
        self._precompute_sphere_mesh()
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
        shape = self.data.shape

        ## Test texture dimensions first
        glTexImage2D(
            GL_PROXY_TEXTURE_2D, 0, GL_RGBA, shape[0], shape[1], 0, 
            GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        if glGetTexLevelParameteriv(GL_PROXY_TEXTURE_2D, 0, GL_TEXTURE_WIDTH) == 0:
            raise Exception(
                "OpenGL failed to create 2D texture (%dx%d); too large for this hardware."
                % shape[:2]
            )

        data = np.ascontiguousarray(self.data.transpose((1, 0, 2)))
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, shape[0], shape[1], 0, 
            GL_RGBA, GL_UNSIGNED_BYTE, data
        )
        glDisable(GL_TEXTURE_2D)

    def setupGLState(self):
        # Make sure we call the parent method
        super().setupGLState()
        # Explicitly enable depth testing
        glEnable(GL_DEPTH_TEST)

    def paint(self):
        if self._needUpdate:
            self._updateTexture()
            self._needUpdate = False
            
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        
        self.setupGLState()
        
        glColor4f(1, 1, 1, 1)
        
        # Render using triangles for better performance
        glBegin(GL_TRIANGLES)
        for i in range(len(self.vertices)):
            glTexCoord2f(*self.texcoords[i])
            glVertex3f(*self.vertices[i])
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

    def to_xyz(self, phi, theta):
        theta = theta + np.pi
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

    # Load and prepare earth texture
    earth_image = Image.open(os.path.join(os.path.dirname(__file__), "earth_texture.jpg")).transpose(Image.ROTATE_90).transpose(Image.FLIP_LEFT_RIGHT)
    
    # Optionally resize the image to reduce texture size
    # earth_image = earth_image.resize((1024, 512), Image.LANCZOS)
    
    earth_array = np.array(earth_image)

    if earth_array.shape[2] == 3:  # RGB image
        earth_rgba = np.zeros((earth_array.shape[0], earth_array.shape[1], 4), dtype=np.uint8)
        earth_rgba[..., :3] = earth_array
        earth_rgba[..., 3] = 255  # Full opacity
    else:
        earth_rgba = earth_array

    # Create sphere with lower resolution for better performance
    v1 = GLTexturedSphereItem(earth_rgba, resolution=(16, 32))  # Reduced from (32, 64)
    w.addItem(v1)

    pg.exec()