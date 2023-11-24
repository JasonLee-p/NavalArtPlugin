# -*- coding: utf-8 -*-
"""
定义基础的OpenGL绘制对象
"""
from abc import abstractmethod
from typing import Union

import numpy as np

from ..shaders import FragmentShaderCode, VertexShaderCode

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


class PlotObj:
    def __init__(self, GL_widget, color: Union[QColor, None] = None):
        """
        初始化一个绘制对象
        :param GL_widget: 用于绘制的OpenGL窗口
        """
        self.GL_widget = GL_widget
        self.shader_program = GL_widget.shader_program
        self.VAO = glGenVertexArrays(1)  # 顶点数组对象
        self.VBO = glGenBuffers(1)  # 顶点缓冲对象
        self.EBO = glGenBuffers(1)  # 索引缓冲对象
        self.vertices: Union[np.ndarray, None] = None  # 顶点数据
        self.indices: Union[np.ndarray, None] = None
        self.color = color if color else QColor(127, 127, 127, 255)
        self.init_plot_data()
        self._init_shader()

    def _init_shader(self):
        """
        初始化着色器
        """
        # 顶点着色器
        vertex_shader = QOpenGLShader(QOpenGLShader.Vertex, self.shader_program)
        vertex_shader.compileSourceCode(VertexShaderCode)
        # 片段着色器
        fragment_shader = QOpenGLShader(QOpenGLShader.Fragment, self.shader_program)
        fragment_shader.compileSourceCode(FragmentShaderCode)
        # 着色器程序
        self.shader_program.addShader(vertex_shader)
        self.shader_program.addShader(fragment_shader)
        self.shader_program.link()
        self.shader_program.bind()

    @abstractmethod
    def init_plot_data(self, *args, **kwargs):
        """
        初始化绘制数据
        """
        pass


    def draw(self):
        """
        绘制
        """
        glUseProgram(self.shader_program.programId())
        glBindVertexArray(self.VAO)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glUseProgram(0)
