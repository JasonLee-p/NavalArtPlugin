# -*- coding: utf-8 -*-
"""
窗口基类
"""
import struct
import time
import typing

import numpy as np
from OpenGL import GL
from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL_plot_objs.shaders import VERTEX_SHADER, FRAGMENT_SHADER
from .basic_widgets import *

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
    def __init__(self, message, msg_type):
        super().__init__()
        self.setWindowTitle("错误")
        self.setWindowIcon(QIcon(QPixmap(ICO_IMAGE)))
        self.setWindowFlags(Qt.WindowCloseButtonHint)
        self.setFixedSize(300, 150)
        self.message = message
        self.msg_type = msg_type
        self.init_ui()
        color_print(f"[ERROR] {message}", "red")

    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(TextLabel(self, self.message))
        self.main_layout.addWidget(EnsureButton(self))
        self.main_layout.addWidget(CancelButton(self))
        self.show()


class Camera:
    """
    摄像机类，用于处理视角变换
    """
    all_cameras = []

    def __init__(self, width, height, sensitivity: typing.Dict[str, float] = None):
        self.width = width
        self.height = height
        self.tar = QVector3D(0, 0, 0)  # 摄像机的目标位置
        self.pos = QVector3D(100, 0, 0)  # 摄像机的位置
        self.angle = self.calculate_angle()  # 摄像机的方向
        self.distance = (self.tar - self.pos).length()  # 摄像机到目标的距离
        self.up = QVector3D(0, 1, 0)  # 摄像机的上方向，y轴正方向
        self.fovy = 45
        # 灵敏度
        self.sensitivity = sensitivity
        Camera.all_cameras.append(self)

    @property
    def model_matrix(self):
        """
        模型矩阵，用于将物体从模型坐标系变换到世界坐标系
        :return:
        """
        model_matrix = QMatrix4x4()
        model_matrix.rotate(self.angle.x(), 1, 0, 0)
        model_matrix.rotate(self.angle.y(), 0, 1, 0)
        model_matrix.rotate(self.angle.z(), 0, 0, 1)
        return model_matrix

    @property
    def view_matrix(self):
        view_matrix = QMatrix4x4()
        view_matrix.lookAt(self.pos, self.tar, self.up)
        return view_matrix

    @property
    def proj_matrix(self):
        proj_matrix = QMatrix4x4()
        proj_matrix.perspective(self.fovy, self.width / self.height, 0.1, 5000)
        return proj_matrix

    def change_target(self, tar):
        self.pos = tar + (self.pos - self.tar).normalized() * self.distance
        self.tar = tar
        self.angle = self.calculate_angle()

    def calculate_angle(self):
        vec = self.tar - self.pos
        return QVector3D(vec.x(), vec.y(), vec.z()).normalized()

    def translate(self, dx, dy):
        """
        根据鼠标移动，沿视角法相平移摄像头
        :param dx:
        :param dy:
        :return:
        """
        dx = dx * 2 * self.sensitivity["平移"]
        dy = dy * 2 * self.sensitivity["平移"]
        rate_ = self.distance / 1500
        left = QVector3D.crossProduct(self.angle, self.up).normalized()
        up = QVector3D.crossProduct(left, self.angle).normalized()
        self.tar += up * dy * rate_ - left * dx * rate_
        self.pos += up * dy * rate_ - left * dx * rate_
        self.distance = (self.tar - self.pos).length()

    def zoom(self, add_rate):
        """
        缩放摄像机
        """
        self.pos = self.tar + (self.pos - self.tar) * (1 + add_rate * self.sensitivity["缩放"])
        self.distance = (self.tar - self.pos).length()

    def rotate(self, dx, dy):
        """
        根据鼠标移动，以视点为锚点，等距，旋转摄像头
        """
        _rate = 0.2
        dx = dx * self.sensitivity["旋转"] * _rate
        dy = dy * self.sensitivity["旋转"] * _rate
        left = QVector3D.crossProduct(self.angle, self.up).normalized()
        up = QVector3D.crossProduct(left, self.angle).normalized()
        # 计算旋转矩阵
        rotation = QQuaternion.fromAxisAndAngle(up, -dx) * QQuaternion.fromAxisAndAngle(left, -dy)
        # 更新摄像机位置
        self.pos -= self.tar  # 将坐标系原点移到焦点
        self.pos = rotation.rotatedVector(self.pos)  # 应用旋转
        self.pos += self.tar  # 将坐标系原点移回来
        # 更新摄像机的方向向量
        self.angle = rotation.rotatedVector(self.angle)
        # 如果到顶或者到底，就不再旋转
        if self.angle.y() > 0.99 and dy > 0:
            return
        if self.angle.y() < -0.99 and dy < 0:
            return

    @property
    def save_data(self):
        # return {"tar": list(self.tar), "pos": list(self.pos), "fovy": int(self.fovy)}
        return {"tar": [self.tar.x(), self.tar.y(), self.tar.z()],
                "pos": [self.pos.x(), self.pos.y(), self.pos.z()],
                "fovy": int(self.fovy)}

    def __str__(self):
        return str(
            f"target:     {self.tar.x()}, {self.tar.y()}, {self.tar.z()}\n"
            f"position:   {self.pos.x()}, {self.pos.y()}, {self.pos.z()}\n"
            f"angle:      {self.angle.x()}, {self.angle.y()}, {self.angle.z()}\n"
            f"distance:   {self.distance}\n"
            f"sensitivity:\n"
            f"    zoom:   {self.sensitivity['缩放']}\n"
            f"    rotate: {self.sensitivity['旋转']}\n"
            f"    move:   {self.sensitivity['平移']}\n"
        )


class PerspectiveCamera:
    def __init__(self, fov: float = 45.0, aspect: float = 1.0, zNear: float = 0.1, zFar: float = 5000.0):
        """
        注意，变量首选使用Qt的数据类型，而不是Python或numpy的数据类型
        :param fov: 视角
        :param aspect: 宽高比
        :param zNear: 近裁剪面
        :param zFar: 远裁剪面
        """
        self.fov = fov
        self.aspect = aspect
        self.zNear = zNear
        self.zFar = zFar
        self.proj_matrix = None
        #


class OrthoCamera:
    def __init__(self, left: float = -1.0, right: float = 1.0, bottom: float = -1.0, top: float = 1.0,
                 zNear: float = 0.1, zFar: float = 5000.0):
        """
        注意，变量首选使用Qt的数据类型，而不是Python或numpy的数据类型
        :param left: 左裁剪面
        :param right: 右裁剪面
        """
        self.left = left
        self.right = right
        self.bottom = bottom
        self.top = top
        self.zNear = zNear
        self.zFar = zFar
        self.proj_matrix = None


class GLWidget(QOpenGLWidget):
    def __init__(self, proj_mode):
        self.proj_mode = proj_mode
        super().__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(WIN_WID - 200, WIN_HEI - 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 统计数据和状态
        self.paint_start_time = 0
        # 设置基本参数
        self.theme_color = GLTheme
        self.lightPos = QVector3D(0, 3000, 0)
        self.lightColor = QVector3D(1, 1, 1)
        self.fovy = 45
        # 绘制对象
        self.shaderProgram = None
        self.vao = None
        self.plot_objs = {}
        # 视角
        self.lastPos = None  # 上一次鼠标位置
        self.select_start = None  # 选择框起点
        self.select_end = None  # 选择框终点
        self.width, self.height = QOpenGLWidget.width(self), QOpenGLWidget.height(self)
        self.camera = Camera(self.width, self.height, {"缩放": 0.4, "旋转": 0.4, "平移": 0.4})

    def paintGL(self):
        super().paintGL()
        # 判断窗口大小是否改变
        if self.width != QOpenGLWidget.width(self) or self.height != QOpenGLWidget.height(self):
            self.resizeGL(QOpenGLWidget.width(self), QOpenGLWidget.height(self))
        # 清除屏幕
        glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("view", self.camera.view_matrix)  # 设置视角
        self.shaderProgram.setUniformValue("model", self.camera.model_matrix)  # 设置模型矩阵
        self.shaderProgram.setUniformValue("viewPos", self.camera.pos)  # 设置视角位置
        self.shaderProgram.setUniformValue("objectColor", QVector4D(0.5, 0.5, 0.5, 1.0))  # 设置物体颜色
        # 绘制
        self.vao.bind()
        st = time.time()
        total_num = 0
        for tag, objs in self.plot_objs.items():
            for obj in objs:
                obj.paint_obj()
                total_num += obj.indices.size
        self.vao.release()
        # 限制帧率
        print(f"[INFO] FPS: {1 / (time.time() - self.paint_start_time):.2f}")
        self.paint_start_time = time.time()
        self.parent().update()

    def initializeGL(self):
        super().initializeGL()
        # 初始化OpenGL
        self.init_render()
        glEnable(GL.GL_DEPTH_TEST)

        # 编译着色器程序
        self.shaderProgram = QOpenGLShaderProgram()
        vertexShader = QOpenGLShader(QOpenGLShader.Vertex, self)
        vertexShader.compileSourceCode(VERTEX_SHADER)
        fragmentShader = QOpenGLShader(QOpenGLShader.Fragment, self)
        fragmentShader.compileSourceCode(FRAGMENT_SHADER)
        self.shaderProgram.addShader(vertexShader)
        self.shaderProgram.addShader(fragmentShader)
        self.shaderProgram.link()
        # 在initializeGL方法中更新着色器的uniform变量
        objectColor = QVector4D(0.5, 0.5, 0.5, 1.0)
        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("lightPos", self.lightPos)
        self.shaderProgram.setUniformValue("lightColor", self.lightColor)
        self.shaderProgram.setUniformValue("viewPos", self.camera.pos)
        self.shaderProgram.setUniformValue("objectColor", objectColor)
        self.shaderProgram.release()

        # 创建顶点数组对象
        self.vao = QOpenGLVertexArrayObject(self)
        self.vao.create()
        self.vao.bind()
        self.vao.release()

    def resizeGL(self, w, h):
        # 设置视口和投影矩阵
        glViewport(0, 0, w, h)
        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("projection", self.camera.proj_matrix)
        self.width, self.height = QOpenGLWidget.width(self), QOpenGLWidget.height(self)
        self.camera.width, self.camera.height = self.width, self.height

    def init_render(self):
        glClearColor(*self.theme_color["背景"])
        glFrontFace(GL_CCW)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        # 设置深度测试
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

    def mousePressEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        self.lastPos = event.pos()
        self.parent().update()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MiddleButton:
            dx = event.x() - self.lastPos.x()
            dy = event.y() - self.lastPos.y()
            self.camera.translate(dx, dy)
            self.lastPos = event.pos()
        elif event.buttons() == Qt.RightButton:
            dx = event.x() - self.lastPos.x()
            dy = event.y() - self.lastPos.y()
            self.camera.rotate(dx, dy)
            self.lastPos = event.pos()
        self.parent().update()

    def mouseReleaseEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        self.lastPos = None
        self.parent().update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.camera.zoom(-0.11)
        else:
            self.camera.zoom(0.11)
        self.parent().update()
