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

from .basic_widgets import *
# from OpenGL_plot_objs.shaders import *

from OpenGL.GL import *
from OpenGL.GLU import *

VERTEX_SHADER = """
#version 330 core

layout(location = 0) in vec3 inPosition; // 顶点位置
layout(location = 1) in vec3 inNormal;   // 顶点法向量

out vec3 FragPos;      // 片段位置（传递给片段着色器）
out vec3 Normal;       // 法向量（传递给片段着色器）

uniform mat4 model;    // 模型矩阵
uniform mat4 view;     // 视图矩阵
uniform mat4 projection; // 投影矩阵

void main() {
    FragPos = vec3(model * vec4(inPosition, 1.0)); // 将顶点变换到世界坐标系
    Normal = inNormal; // 计算法向量并变换到世界坐标系

    gl_Position = projection * view * vec4(FragPos, 1.0); // 计算最终的顶点位置
}

"""

FRAGMENT_SHADER = """
#version 330 core
in vec3 FragPos;                           // 片段位置
in vec3 Normal;                            // 法向量

// 渲染选项

uniform vec3 lightPos;                     // 光源位置
uniform vec3 viewPos;                      // 观察者位置
uniform vec3 lightColor;                   // 光源颜色
uniform vec3 objectColor;                  // 物体颜色

uniform float ambientStrength = 0.1;       // 环境光强度
uniform float specularStrength = 0.4;      // 镜面光强度
uniform int shininess = 16;                // 镜面光高光大小

out vec4 FragColor;

// FXAA抗锯齿函数
vec3 applyFXAA(sampler2D tex, vec2 fragCoord, vec2 resolution, float reduceMul, float reduceMin) {
    vec3 rgbNW = texture(tex, (fragCoord + vec2(-1.0, -1.0)) / resolution).xyz;
    vec3 rgbNE = texture(tex, (fragCoord + vec2(1.0, -1.0)) / resolution).xyz;
    vec3 rgbSW = texture(tex, (fragCoord + vec2(-1.0, 1.0)) / resolution).xyz;
    vec3 rgbSE = texture(tex, (fragCoord + vec2(1.0, 1.0)) / resolution).xyz;
    vec3 rgbM = texture(tex, fragCoord / resolution).xyz;
    vec3 luma = vec3(0.299, 0.587, 0.114);
    vec4 fragColor;
    float lumaNW = dot(rgbNW, luma);
    float lumaNE = dot(rgbNE, luma);
    float lumaSW = dot(rgbSW, luma);
    float lumaSE = dot(rgbSE, luma);
    float lumaM = dot(rgbM, luma);
    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));
    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));
    

    vec2 dir;
    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));
    dir.y = ((lumaNW + lumaSW) - (lumaNE + lumaSE));

    float dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * (0.25 * reduceMul), reduceMin);

    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);
    dir = min(vec2(reduceMul, reduceMul), max(vec2(-reduceMul, -reduceMul), dir * rcpDirMin)) * resolution;

    vec3 rgbA = 0.5 * (texture(tex, fragCoord / resolution + dir / resolution).xyz +
                       texture(tex, fragCoord / resolution - dir / resolution).xyz);
    vec3 rgbB = rgbA * 0.5 + 0.25 * (texture(tex, fragCoord / resolution + dir / resolution * 2.0).xyz +
                                        texture(tex, fragCoord / resolution - dir / resolution * 2.0).xyz);
    float lumaB = dot(rgbB, luma);
    if ((lumaB < lumaMin) || (lumaB > lumaMax)) {
        fragColor = vec4(rgbA, 1.0);
    } else {
        fragColor = vec4(rgbB, 1.0);
    }
    return fragColor;
}

void main() {
    // 计算光线方向和法向量之间的角度
    vec3 lightDir = normalize(lightPos - FragPos);
    float diff = max(dot(Normal, lightDir), 0.0);

    // 计算角度的权重
    float angleWeight = (diff + 1.0) / 2.0; // 角度值范围从[-1,1]映射到[0,1]

    // 使用角度权重来混合颜色
    vec3 diffuse = mix(lightColor * objectColor, objectColor, angleWeight);

    // 环境光照计算
    vec3 ambient = ambientStrength * lightColor;

    // 镜面光照计算
    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, Normal);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
    vec3 specular = specularStrength * spec * lightColor;

    // 最终颜色
    vec3 result = (ambient + diffuse + specular);
    vec4 FragColor = vec4(result, 1.0);
}
"""


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
        self.pos = QVector3D(100, 20, 40)  # 摄像机的位置
        self.angle = self.calculate_angle()  # 摄像机的方向
        self.distance = (self.tar - self.pos).length()  # 摄像机到目标的距离
        self.up = QVector3D(0, 1, 0)  # 摄像机的上方向，y轴正方向
        self.fovy = 45
        # 灵敏度
        self.sensitivity = sensitivity
        Camera.all_cameras.append(self)

    @property
    def modelview_matrix(self):
        matrix = QMatrix4x4()
        return matrix.lookAt(self.pos, self.tar, self.up)

    @property
    def model_matrix(self):
        matrix = QMatrix4x4()
        return matrix.lookAt(self.pos, self.tar, self.up)

    @property
    def projection_matrix(self):
        matrix = QMatrix4x4()
        return matrix.perspective(self.fovy, self.width / self.height, 0.1, 100000)

    @property
    def viewport(self):
        return 0, 0, self.width, self.height

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
        # 统计数据
        self.paint_start_time = 0
        # 设置基本参数
        self.theme_color = GLTheme
        self.lightPos = QVector3D(5000, 3000, 5000)
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
        # 判断窗口大小是否改变
        if self.width != QOpenGLWidget.width(self) or self.height != QOpenGLWidget.height(self):
            self.resizeGL(QOpenGLWidget.width(self), QOpenGLWidget.height(self))
            self.width, self.height = QOpenGLWidget.width(self), QOpenGLWidget.height(self)
        # 清除屏幕
        glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("view", self.viewMatrix())  # 设置视角
        self.shaderProgram.setUniformValue("model", self.modelMatrix())  # 设置模型矩阵
        self.shaderProgram.setUniformValue("viewPos", self.camera.pos)  # 设置视角位置
        self.shaderProgram.setUniformValue("objectColor", QVector3D(0.5, 0.5, 0.5))  # 设置物体颜色
        # 绘制
        self.vao.bind()
        for tag, objs in self.plot_objs.items():
            for obj in objs:
                obj.draw()
        self.vao.release()
        self.shaderProgram.release()
        self.parent().update()
        print(f"[INFO] {1000 / (time.time() - self.paint_start_time)} FPS")
        self.paint_start_time = time.time()

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
        objectColor = QVector3D(0.3, 0.3, 0.3)
        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("lightPos", self.lightPos)
        self.shaderProgram.setUniformValue("lightColor", self.lightColor)
        self.shaderProgram.setUniformValue("viewPos", self.camera.pos)
        self.shaderProgram.setUniformValue("objectColor", objectColor)

        # 创建顶点数组对象和顶点缓冲区
        self.vao = QOpenGLVertexArrayObject(self)
        self.vao.create()
        self.vao.bind()
        self.vao.release()

    def resizeGL(self, w, h):
        # 设置视口和投影矩阵
        glViewport(0, 0, w, h)
        _projection = self.projectionMatrix()
        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("projection", _projection)
        self.shaderProgram.release()

    def viewMatrix(self):
        view = QMatrix4x4()
        view.lookAt(self.camera.pos, self.camera.tar, self.camera.up)
        return view

    def modelMatrix(self):
        model = QMatrix4x4()
        model.rotate(self.camera.angle.x(), 1.0, 0.0, 0.0)
        model.rotate(self.camera.angle.y(), 0.0, 1.0, 0.0)
        model.rotate(self.camera.angle.z(), 0.0, 0.0, 1.0)
        return model

    def projectionMatrix(self):
        pj = QMatrix4x4()
        pj.perspective(self.camera.fovy, self.width / self.height, 0.1, 2000.0)
        return pj

    def init_render(self):
        glClearColor(*self.theme_color["背景"])
        glFrontFace(GL_CCW)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        # 设置深度测试
        glEnable(GL.GL_DEPTH_TEST)
        glDepthFunc(GL.GL_LESS)

    def mousePressEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        self.lastPos = event.pos()
        self.update()

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
        self.update()

    def mouseReleaseEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        self.lastPos = None
        self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.camera.zoom(-0.11)
        else:
            self.camera.zoom(0.11)
        self.update()

    def update(self):
        super().update()
        self.parent().update()
