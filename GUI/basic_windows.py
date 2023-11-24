# -*- coding: utf-8 -*-
"""
窗口基类
"""
from OpenGL import GL
from PySide2.QtOpenGL import QGLWidget

from .basic_widgets import *
from OpenGL_plot_objs.shaders import *

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


class GLWindow(QGLWidget):

    def __init__(self, proj_mode: Literal['ortho', 'perspective'] = 'perspective'):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)  # 关闭窗口时自动释放资源
        self.setAutoFillBackground(False)
        self.setMinimumSize(400, 300)
        # ===================================================================================设置基本参数
        self.fovy = 45
        self.proj_mode = proj_mode
        self.theme_color = GLTheme
        # ========================================================================================着色器
        self.shaderProgram = None
        self.vao = None
        self.vbo = None
        # ========================================================================================视角
        self.width = QGLWidget.width(self)
        self.height = QGLWidget.height(self)
        self.lastPos = None  # 上一次鼠标位置
        self.select_start = None  # 选择框起点
        self.select_end = None  # 选择框终点
        # ========================================================================================子控件

    def init_view(self):
        # 适应窗口大小
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.width / self.height
        gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)  # 设置透视投影
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def before_paint(self):
        # 获取窗口大小，如果窗口大小改变，就重新初始化
        width, height = QGLWidget.width(self), QGLWidget.height(self)
        if width != self.width or height != self.height:
            self.width, self.height = width, height
            self.init_view()
        # 清除颜色缓冲区和深度缓冲区
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # 设置相机
        glLoadIdentity()  # 重置矩阵
        glDisable(GL_LINE_STIPPLE)  # 禁用虚线模式
        # self.set_camera() if self.camera_movable else None

    def set_camera(self):
        ...

    def paintGL(self):
        self.before_paint()
        # 绘制坐标轴
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(100, 0, 0)
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 100, 0)
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 100)
        glEnd()

    def initializeGL(self):
        glEnable(GL.GL_DEPTH_TEST)
        glClearColor(*self.theme_color["背景"])
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.shaderProgram = QOpenGLShaderProgram()
        self.shaderProgram.addShaderFromSourceCode(QOpenGLShader.Vertex, VertexShaderCode)
        self.shaderProgram.addShaderFromSourceCode(QOpenGLShader.Fragment, FragmentShaderCode)
        self.shaderProgram.link()
        self.shaderProgram.bind()
        self.vao = QOpenGLVertexArrayObject()
        self.vao.create()
        self.vao.bind()
        self.vbo = QOpenGLBuffer()
        self.vbo.create()
        self.vbo.bind()
        self.vbo.setUsagePattern(QOpenGLBuffer.StaticDraw)
        self.vao.release()
        self.vbo.release()
        self.shaderProgram.release()
