# -*- coding: utf-8 -*-
"""
窗口基类
"""
from .basic_widgets import *

from OpenGL.GL import *
from OpenGL.GLU import *


class MessageBox(QDialog):
    def __str__(self):
        ...


class BasicRootWindow(Window):
    def __init__(self, parent=None, border_radius=10, title=None, size=(400, 300), center_layout=None,
                 resizable=False, hide_top=False, hide_bottom=False, ensure_bt_fill=False):
        ...

    @abstractmethod
    def ensure(self):
        self.close()

    @abstractmethod
    def cancel(self):
        self.close()

    def close(self):
        super().close()
        if self._generate_self_parent:
            self._parent.close()


class GLWindow(QOpenGLWindow):
    def __init__(self, parent=None):
        """
        初始化一个基础的OpenGL窗口
        :param parent:
        """
        super().__init__(parent)
        self.setSurfaceType(QWindow.OpenGLSurface)  # 设置窗口类型为OpenGL
        self.set_gl_version()  # 设置OpenGL版本
        # 获取窗口大小
        self.width = QOpenGLWidget.width(self)
        self.height = QOpenGLWidget.height(self)
        # 初始化OpenGL
        self.initializeGL()
        # 设置OpenGL的投影方式
        self.set_perspective_projection()

    def set_gl_version(self):
        """设置OpenGL版本"""
        _format = QSurfaceFormat()
        _format.setProfile(QSurfaceFormat.CoreProfile)
        _format.setVersion(3, 3)
        _format.setSamples(4)  # 设置多重采样
        self.setFormat(_format)

    def set_perspective_projection(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, self.width / self.height, 0.1, 5000)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def set_ortho_projection(self):
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def initializeGL(self):
        ...
