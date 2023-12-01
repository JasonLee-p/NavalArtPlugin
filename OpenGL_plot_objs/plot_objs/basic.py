# -*- coding: utf-8 -*-
"""
定义基础的OpenGL绘制对象
"""
from abc import abstractmethod
from typing import Union

import numpy as np
from PySide6.QtOpenGL import *

from ..shaders import FragmentShaderCode, VertexShaderCode

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


class PlotObj:
    def __init__(self):
        self.vao = QOpenGLVertexArrayObject()
        self.vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.vertices = []  # Your vertex data goes here

    def initialize(self):
        self.vao.create()
        self.vao.bind()

        self.vbo.create()
        self.vbo.bind()
        self.vbo.allocate(self.vertices, len(self.vertices) * 4)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        self.vao.release()

    def draw(self):
        self.vao.bind()
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices)//3)
        self.vao.release()
