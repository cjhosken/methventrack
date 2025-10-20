from PySide6.QtCore import Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL import GL
import numpy as np
import pycolmap

VERTEX_SHADER_SRC = """
#version 330 core
layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_color;

uniform mat4 u_mvp;

out vec3 v_color;

void main()
{
    gl_Position = u_mvp * vec4(a_position, 1.0);
    v_color = a_color;
}
"""

FRAGMENT_SHADER_SRC = """
#version 330 core
in vec3 v_color;
out vec4 FragColor;

void main()
{
    FragColor = vec4(v_color, 1.0);
}
"""

class GLViewport(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(600)
        self.shader_program = None
        self.vao = None
        self.vbo = None
        self.vertices = None
        self.mvp = np.eye(4, dtype=np.float32)  # placeholder MVP matrix

    def initializeGL(self):
        # Modern OpenGL setup
        GL.glClearColor(0.1, 0.1, 0.1, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)

        # Compile shaders
        self.shader_program = self.create_shader(VERTEX_SHADER_SRC, FRAGMENT_SHADER_SRC)

        # Example triangle (can be replaced with reconstruction points)
        self.vertices = np.array([
            # positions        # colors
            -0.6, -0.4, 0.0,   1.0, 0.0, 0.0,
             0.6, -0.4, 0.0,   0.0, 1.0, 0.0,
             0.0,  0.6, 0.0,   0.0, 0.0, 1.0
        ], dtype=np.float32)

        # Setup VAO/VBO
        self.vao = GL.glGenVertexArrays(1)
        self.vbo = GL.glGenBuffers(1)

        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL.GL_STATIC_DRAW)

        # position
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, 6*4, GL.ctypes.c_void_p(0))
        GL.glEnableVertexAttribArray(0)
        # color
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, False, 6*4, GL.ctypes.c_void_p(3*4))
        GL.glEnableVertexAttribArray(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def resizeGL(self, w, h):
        GL.glViewport(0, 0, w, h)

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glUseProgram(self.shader_program)
        GL.glBindVertexArray(self.vao)

        # Set MVP uniform
        mvp_loc = GL.glGetUniformLocation(self.shader_program, "u_mvp")
        GL.glUniformMatrix4fv(mvp_loc, 1, GL.GL_FALSE, self.mvp)

        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)

    def create_shader(self, vertex_src, fragment_src):
        """Compile vertex and fragment shaders into a program."""
        vertex_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertex_shader, vertex_src)
        GL.glCompileShader(vertex_shader)
        if not GL.glGetShaderiv(vertex_shader, GL.GL_COMPILE_STATUS):
            raise RuntimeError(GL.glGetShaderInfoLog(vertex_shader))

        fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(fragment_shader, fragment_src)
        GL.glCompileShader(fragment_shader)
        if not GL.glGetShaderiv(fragment_shader, GL.GL_COMPILE_STATUS):
            raise RuntimeError(GL.glGetShaderInfoLog(fragment_shader))

        program = GL.glCreateProgram()
        GL.glAttachShader(program, vertex_shader)
        GL.glAttachShader(program, fragment_shader)
        GL.glLinkProgram(program)
        if not GL.glGetProgramiv(program, GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(program))

        GL.glDeleteShader(vertex_shader)
        GL.glDeleteShader(fragment_shader)
        return program

    def load_reconstruction(self, reconstruction: pycolmap.Reconstruction):
        """Convert pycolmap reconstruction points to VBO."""
        points = []
        colors = []

        for point_id, point in reconstruction.points3D.items():
            points.append(point.xyz)
            # Random color per point (or from reconstruction if available)
            colors.append([1.0, 0.5, 0.0])

        if not points:
            return

        pts = np.array(points, dtype=np.float32)
        cols = np.array(colors, dtype=np.float32)
        self.vertices = np.hstack([pts, cols]).flatten()

        # Update VBO
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL.GL_STATIC_DRAW)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)

        self.update()
