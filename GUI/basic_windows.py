# -*- coding: utf-8 -*-
"""
窗口基类
"""
import typing

import numpy as np
from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from .basic_widgets import *
from OpenGL_plot_objs.shaders import *

from OpenGL.GL import *
from OpenGL.GLU import *


def rotate_object(angle: float, axis: Union[list, tuple, np.ndarray]):
    # 旋转矩阵
    c = np.cos(np.radians(angle))
    s = np.sin(np.radians(angle))
    x, y, z = axis
    rotation_matrix = np.array([
        [c + x ** 2 * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s, 0.0],
        [y * x * (1 - c) + z * s, c + y ** 2 * (1 - c), y * z * (1 - c) - x * s, 0.0],
        [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z ** 2 * (1 - c), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])
    return rotation_matrix


class MessageBox(QDialog):
    def __str__(self):
        ...


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None, proj_mode: Literal['ortho', 'perspective'] = 'perspective'):
        super(GLWidget, self).__init__(parent)
        self.program = QOpenGLShaderProgram()
        self.proj_mode = proj_mode

        self.object = None
        self.rotation = 0.0

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)

        glClearColor(*GLTheme['背景'])
        if self.object is not None:
            self.object.initialize()

        self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, VertexShaderCode)
        self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, FragmentShaderCode)
        self.program.link()


    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.program.bind()

        model_matrix = QMatrix4x4()
        model_matrix.translate(0.0, 0.0, -5.0)
        model_matrix.rotate(self.rotation, 0.0, 1.0, 0.0)

        self.program.setUniformValue(self.program.uniformLocation("model_matrix"), model_matrix)
        if self.object is not None:
            self.object.draw()

        self.program.release()

        self.rotation += 1.0

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
