import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QMouseEvent, QWheelEvent, QVector4D, QMatrix4x4
from PyQt5.QtGui import QOpenGLVersionProfile

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.raw.GL.VERSION.GL_2_0 import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_PROJECTION, GL_MODELVIEW, GL_LINE_STIPPLE

from NA_design_reader import Part, AdjustableHull
from OpenGL_objs import *
from GUI.QtGui import *
from utils import FragmentShader

VERTEX_SHADER = """
#version 330
layout(location = 0) in vec3 position;
void main() {
    gl_Position = vec4(position, 1.0);
}
"""

FRAGMENT_SHADER = FragmentShader.FS


# # 片段着色器代码（包括FXAA抗锯齿）
# with open("FragmentShader.frag", "r") as f:
#     FRAGMENT_SHADER = f.read()


class OpenGLWin(QOpenGLWidget):
    # 操作模式
    Selectable = 1
    UnSelectable = 0
    # 3D物体显示模式
    ShowAll = 11
    ShowZX = 22
    ShowYX = 33
    ShowLeft = 44

    def __init__(self, camera_sensitivity):
        self.mode = OpenGLWin.Selectable
        super(OpenGLWin, self).__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.width = QOpenGLWidget.width(self)
        self.height = QOpenGLWidget.height(self)
        self.theme_color = GLTheme
        self.light_pos = QVector3D(1000, 700, 1000)
        self.fovy = 45
        # OpenGL
        self.gl = None
        self.texture = None
        self.shaderProgram = None
        self.vbo = None
        self.vao = None
        # 3D物体
        self.environment_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        # 不同模式下显示的物体
        self.show_3d_obj_mode = OpenGLWin.ShowAll
        self.all_3d_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        self.zx_layer_obj = []  # 横剖面模式
        self.yx_layer_obj = []  # 纵剖面模式
        self.left_view_obj = []  # 左视图线框模式
        self.showMode_showSet_map = {
            OpenGLWin.ShowAll: self.all_3d_obj,
            OpenGLWin.ShowZX: self.zx_layer_obj,
            OpenGLWin.ShowYX: self.yx_layer_obj,
            OpenGLWin.ShowLeft: self.left_view_obj
        }
        # 船体所有零件，用于选中
        self.ShipsAllParts = []
        for gl_plot_obj in self.all_3d_obj["钢铁"]:
            if type(gl_plot_obj) == NAHull:
                self.ShipsAllParts = gl_plot_obj.Parts
        # 事件
        self.camera = Camera(self.width, self.height, camera_sensitivity)
        self.lastPos = QPoint()
        self.select_start = None
        self.select_end = None
        self.all_gl_objects = GLObject.all_objects
        self.selected_gl_objects = []

    def initializeGL(self) -> None:
        self.init_gl()  # 初始化OpenGL相关参数
        # self.vbo = glGenBuffers(1)  # 创建VBO
        # self.vao = glGenVertexArrays(1)  # 创建VAO
        # glBindVertexArray(self.vao)  # 绑定VAO
        # glBindBuffer(GL_ARRAY_BUFFER, self.vbo)  # 绑定VBO
        # # self.gl.glBufferData(GL_ARRAY_BUFFER, self.all_gl_objects[0].nbytes,
        # #              self.all_gl_objects, self.gl.GL_STATIC_DRAW)  # 将数据传入VBO
        # self.gl.glVertexAttribPointer(0, 3, self.gl.GL_FLOAT, self.gl.GL_FALSE, 0, None)  # 设置顶点属性指针
        # self.gl.glEnableVertexAttribArray(0)  # 启用顶点属性数组
        # self.gl.glBindBuffer(self.gl.GL_ARRAY_BUFFER, 0)  # 解绑VBO
        # self.gl.glBindVertexArray(0)  # 解绑VAO
        # # 创建着色器程序
        # self.shaderProgram = self.gl.glCreateProgram()
        # # 创建顶点着色器
        # vertexShader = glCreateShader(GL_VERTEX_SHADER)
        # glShaderSource(vertexShader, VERTEX_SHADER)
        # self.gl.glCompileShader(vertexShader)
        # # 创建片段着色器
        # fragmentShader = glCreateShader(GL_FRAGMENT_SHADER)
        # glShaderSource(fragmentShader, FRAGMENT_SHADER)
        # self.gl.glCompileShader(fragmentShader)
        # # 将着色器附加到程序上
        # self.gl.glAttachShader(self.shaderProgram, vertexShader)
        # self.gl.glAttachShader(self.shaderProgram, fragmentShader)
        # self.gl.glLinkProgram(self.shaderProgram)  # 链接着色器程序
        # self.gl.glUseProgram(self.shaderProgram)  # 使用着色器程序
        # 设置背景颜色
        self.gl.glClearColor(*self.theme_color["背景"])
        # 基础物体
        self.environment_obj["海面"].append(GridLine(
            self.gl, scale=10, num=50, central=(0, 0, 0), color=(0.1, 0.2, 0.5, 1)))
        self.environment_obj["光源"].append(LightSphere(
            self.gl, central=self.light_pos, radius=20))

    def paintGL(self) -> None:
        # 获取窗口大小
        width = QOpenGLWidget.width(self)
        height = QOpenGLWidget.height(self)
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self.init_view()
        # 清除颜色缓存和深度缓存
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
        # 设置相机
        self.gl.glLoadIdentity()  # 重置矩阵
        self.gl.glDisable(GL_LINE_STIPPLE)  # 禁用虚线模式
        self.set_camera()  # 设置相机
        # # 使用VBO
        # glBindBuffer(self.gl.GL_ARRAY_BUFFER, self.vbo)
        # glBindVertexArray(self.vao)
        # 绘制物体

        for mt, objs in self.environment_obj.items():  # 绘制环境物体
            for obj in objs:
                obj.draw(self.gl, material=mt, theme_color=self.theme_color)

        if self.show_3d_obj_mode == OpenGLWin.ShowAll:  # 船体显示模式
            for mt, objs in self.all_3d_obj.items():
                for obj in objs:
                    obj.draw(self.gl, material=mt, theme_color=self.theme_color)
        else:  # 剖面显示模式
            for obj in self.showMode_showSet_map[self.show_3d_obj_mode]:
                obj.draw(self.gl, theme_color=self.theme_color)

        self.draw_selected_objs()  # 绘制被选中的物体
        if self.select_start and self.select_end:  # 绘制选择框
            self.draw_select_box()

    def draw_selected_objs(self):
        # 材料设置
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_AMBIENT, self.theme_color["被选中"][0])
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_DIFFUSE, self.theme_color["被选中"][1])
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SPECULAR, self.theme_color["被选中"][2])
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SHININESS, self.theme_color["被选中"][3])
        for obj in self.selected_gl_objects:
            try:
                for draw_method, faces_dots in obj.plot_faces.items():
                    # draw_method是字符串，需要转换为OpenGL的常量
                    for face in faces_dots:
                        self.gl.glBegin(eval(f"self.gl.{draw_method}"))
                        if len(face) == 3 or len(face) == 4:
                            normal = get_normal(face[0], face[1], face[2])
                        elif len(face) > 12:
                            normal = get_normal(face[0], face[6], face[12])
                        else:
                            continue
                        self.gl.glNormal3f(normal.x(), normal.y(), normal.z())
                        for dot in face:
                            self.gl.glVertex3f(dot[0], dot[1], dot[2])
                        self.gl.glEnd()
            except AttributeError as e:
                pass
        self.gl.glEnd()

    def draw_select_box(self):
        """
        转变为二维视角，画出选择框
        """
        # 保存原来的矩阵
        self.gl.glMatrixMode(GL_PROJECTION)
        self.gl.glPushMatrix()
        self.gl.glLoadIdentity()
        self.gl.glOrtho(0, self.width, self.height, 0, -1, 1)
        self.gl.glMatrixMode(GL_MODELVIEW)
        self.gl.glPushMatrix()
        self.gl.glLoadIdentity()
        # 颜色
        self.gl.glColor4f(*self.theme_color["选择框"][0])
        # 重设材质
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_AMBIENT, self.theme_color["选择框"][0])
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_DIFFUSE, self.theme_color["选择框"][1])
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SPECULAR, self.theme_color["选择框"][2])
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SHININESS, self.theme_color["选择框"][3])
        # 画虚线框
        self.gl.glEnable(GL_LINE_STIPPLE)  # 启用虚线模式
        self.gl.glLineStipple(0, 0x00FF)  # 设置虚线的样式
        self.gl.glBegin(self.gl.GL_LINE_LOOP)
        self.gl.glVertex2f(self.select_start.x(), self.select_start.y())
        self.gl.glVertex2f(self.select_start.x(), self.select_end.y())
        self.gl.glVertex2f(self.select_end.x(), self.select_end.y())
        self.gl.glVertex2f(self.select_end.x(), self.select_start.y())
        self.gl.glEnd()
        # 画中间的半透明框
        self.gl.glColor4f(1, 1, 1, 0.2)
        self.gl.glBegin(self.gl.GL_QUADS)
        # 重设材质
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_AMBIENT, (1.0, 1.0, 1.0, 0.1))
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_DIFFUSE, (1.0, 1.0, 1.0, 0.1))
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SPECULAR, (1.0, 1.0, 1.0, 0.1))
        self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SHININESS, (0,))
        # 画四边形
        self.gl.glVertex2f(self.select_start.x(), self.select_start.y())
        self.gl.glVertex2f(self.select_start.x(), self.select_end.y())
        self.gl.glVertex2f(self.select_end.x(), self.select_end.y())
        self.gl.glVertex2f(self.select_end.x(), self.select_start.y())
        self.gl.glEnd()
        # 恢复原来的矩阵
        self.gl.glMatrixMode(GL_PROJECTION)
        self.gl.glPopMatrix()
        self.gl.glMatrixMode(GL_MODELVIEW)
        self.gl.glPopMatrix()

    def add_selected_objects_when_click(self):
        pos = self.select_start
        min_distance = 100000
        min_distance_part = None
        for part in self.ShipsAllParts:
            if type(part) == AdjustableHull:
                dots = [part.Pos]
                # print(QOpenGLWidget.width(self), QOpenGLWidget.height(self))
                s_dots = self.transform_points(self.camera.fovy, self.camera.pos, self.camera.up, self.camera.angle,
                                               QOpenGLWidget.width(self), QOpenGLWidget.height(self), dots)
                dot = s_dots[0]
                distance = np.sqrt((dot[0] - pos.x()) ** 2 + (dot[1] - pos.y()) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    min_distance_part = part
            else:
                continue
        if min_distance < 100:  # 如果距离小于100像素，就将零件加入到选中列表中
            self.selected_gl_objects.append(min_distance_part)

    def add_selected_objects_of_selectBox(self):
        if self.select_start and self.select_end:
            min_x = min(self.select_start.x(), self.select_end.x())
            max_x = max(self.select_start.x(), self.select_end.x())
            min_y = min(self.select_start.y(), self.select_end.y())
            max_y = max(self.select_start.y(), self.select_end.y())
            # 获取屏幕
            for part in self.ShipsAllParts:
                if type(part) == AdjustableHull:
                    dots = [part.Pos]
                    # print(QOpenGLWidget.width(self), QOpenGLWidget.height(self))
                    s_dots = self.transform_points(self.camera.fovy, self.camera.pos, self.camera.up, self.camera.angle,
                                                   QOpenGLWidget.width(self), QOpenGLWidget.height(self), dots)
                    dot = s_dots[0]
                    if min_x < dot[0] < max_x and min_y < dot[1] < max_y:
                        # 如果顶点在选择框内，就将零件加入到选中列表中
                        self.selected_gl_objects.append(part)
                else:
                    continue

    @staticmethod
    def get_matrix():
        """
        获取当前的坐标变换矩阵
        :return:
        """
        matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        matrix = np.array(matrix).reshape(4, 4)
        return matrix

    @staticmethod
    def transform_points(fovy, pos, up, angle, width, height, points):
        """
        :param fovy:
        :param pos: QVector
        :param up: 相机的正方向，一般为 [0, 1, 0]
        :param angle:
        :param width:
        :param height:
        :param points:
        :return:
        """
        pos = np.array([pos.x(), pos.y(), pos.z()])
        up = np.array([up.x(), up.y(), up.z()])
        angle = np.array([angle.x(), angle.y(), angle.z()])
        points = np.array(points)
        # 计算相机坐标系的基向量
        forward = angle / np.linalg.norm(angle)
        right = np.cross(up, forward)
        up = np.cross(forward, right)
        # 计算投影矩阵
        f = 1 / np.tan(np.radians(fovy) / 2)
        aspect_ratio = width / height
        near = 0.1
        far = 1000
        projection_matrix = np.array([
            [f / aspect_ratio, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (near + far) / (near - far), (2 * near * far) / (near - far)],
            [0, 0, -1, 0]
        ])
        world_to_camera = np.array([
            [right[0], right[1], right[2], -np.dot(right, pos)],
            [up[0], up[1], up[2], -np.dot(up, pos)],
            [-forward[0], -forward[1], -forward[2], np.dot(forward, pos)],
            [0, 0, 0, 1]
        ])
        points_camera = np.dot(world_to_camera, np.hstack([points, np.ones((points.shape[0], 1))]).T)
        # 应用投影矩阵，得到屏幕坐标
        points_screen = np.dot(projection_matrix, points_camera)
        # 归一化坐标
        points_screen /= points_screen[3]
        # 将屏幕坐标从[-1, 1]映射到屏幕像素坐标
        screen_x = (1 - points_screen[0]) * width / 2
        screen_y = (1 - points_screen[1]) * height / 2
        return np.vstack([screen_x, screen_y]).T

    # ----------------------------------------------------------------------------------------------事件

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self.camera.zoom(-0.12)
        else:
            self.camera.zoom(0.12)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:  # 左键按下
            self.selected_gl_objects.clear()
            self.select_start = event.pos() if self.mode == OpenGLWin.Selectable else None
            self.lastPos = event.pos() if self.mode == OpenGLWin.UnSelectable else None
        elif event.button() == Qt.RightButton:  # 右键按下
            self.lastPos = event.pos()
        elif event.button() == Qt.MidButton:  # 中键按下
            self.lastPos = event.pos()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:  # 左键绘制选择框
            self.select_end = event.pos() if self.mode == OpenGLWin.Selectable else None
            self.lastPos = event.pos() if self.mode == OpenGLWin.UnSelectable else None
            self.update()
        elif event.buttons() == Qt.MidButton:  # 中键平移
            dx = event.x() - self.lastPos.x()
            dy = event.y() - self.lastPos.y()
            self.camera.translate(dx, dy)
            self.lastPos = event.pos()
            self.update()
        elif event.buttons() == Qt.RightButton:  # 右键旋转
            dx = event.x() - self.lastPos.x()
            dy = event.y() - self.lastPos.y()
            self.camera.rotate(dx, dy)
            self.lastPos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:  # 左键释放
            if self.select_start and self.select_end:
                self.add_selected_objects_of_selectBox() if self.mode == OpenGLWin.Selectable else None
                self.select_start = None
                self.select_end = None
            elif self.select_end is None and self.select_start:
                self.add_selected_objects_when_click() if self.mode == OpenGLWin.Selectable else None
                self.select_start = None
                self.select_end = None
        self.update()

    def set_camera(self):
        gluLookAt(self.camera.pos.x(), self.camera.pos.y(), self.camera.pos.z(),
                  self.camera.tar.x(), self.camera.tar.y(), self.camera.tar.z(),
                  self.camera.up.x(), self.camera.up.y(), self.camera.up.z())

    def init_gl(self) -> None:
        version_profile = QOpenGLVersionProfile()
        version_profile.setVersion(2, 0)
        self.gl = self.context().versionFunctions(version_profile)
        self.init_view()  # 初始化视角
        self.init_light()  # 初始化光源
        self.init_render()  # 初始化渲染模式

    def init_light(self):
        # 添加光源
        self.gl.glEnable(self.gl.GL_LIGHTING)
        self.gl.glEnable(self.gl.GL_LIGHT0)
        self.gl.glLightfv(self.gl.GL_LIGHT0, self.gl.GL_POSITION, (
            self.light_pos.x(), self.light_pos.y(), self.light_pos.z(),  # 光源位置
            100.0))
        self.gl.glLightfv(self.gl.GL_LIGHT0, self.gl.GL_AMBIENT, (1.0, 1.0, 1.0, 1.0))  # 设置环境光
        self.gl.glLightfv(self.gl.GL_LIGHT0, self.gl.GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))  # 设置漫反射光
        self.gl.glLightfv(self.gl.GL_LIGHT0, self.gl.GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))  # 设置镜面光
        # 设置光照模型
        self.gl.glLightModelfv(self.gl.GL_LIGHT_MODEL_AMBIENT, (1.0, 1.0, 1.0, 1.0))  # 设置全局环境光
        self.gl.glLightModelf(self.gl.GL_LIGHT_MODEL_TWO_SIDE, 0.0)  # Q: 这个参数如果我写1会怎样？

    def init_view(self):
        # 适应窗口大小
        self.gl.glViewport(0, 0, self.width, self.height)
        self.gl.glMatrixMode(GL_PROJECTION)
        self.gl.glLoadIdentity()
        aspect_ratio = self.width / self.height
        gluPerspective(self.fovy, aspect_ratio, 0.1, 10000.0)  # 设置透视投影
        self.gl.glMatrixMode(GL_MODELVIEW)
        self.gl.glLoadIdentity()

    def init_render(self):
        self.gl.glShadeModel(self.gl.GL_SMOOTH)  # 设置阴影平滑模式
        self.gl.glClearDepth(1.0)  # 设置深度缓存
        self.gl.glEnable(self.gl.GL_DEPTH_TEST)  # 启用深度测试
        self.gl.glDepthFunc(self.gl.GL_LEQUAL)  # 所作深度测试的类型
        self.gl.glHint(self.gl.GL_PERSPECTIVE_CORRECTION_HINT, self.gl.GL_NICEST)  # 告诉系统对透视进行修正
        self.gl.glEnable(self.gl.GL_NORMALIZE)  # 启用法向量规范化
        self.gl.glEnable(self.gl.GL_BLEND)  # 启用混合
        self.gl.glBlendFunc(self.gl.GL_SRC_ALPHA, self.gl.GL_ONE_MINUS_SRC_ALPHA)  # 设置混合因子
        self.gl.glEnable(self.gl.GL_TEXTURE_2D)  # 启用纹理
        self.gl.glEnable(self.gl.GL_LINE_SMOOTH)  # 启用线条平滑
        # self.gl.glEnable(self.gl.GL_POLYGON_SMOOTH)  # 启用多边形平滑
        self.gl.glEnable(self.gl.GL_CULL_FACE)  # 启用背面剔除
        self.gl.glCullFace(self.gl.GL_BACK)  # 剔除背面
        # self.gl.glEnable(self.gl.GL_VERTEX_PROGRAM_POINT_SIZE)  # 启用点大小
        # self.gl.glEnable(self.gl.GL_VERTEX_PROGRAM_TWO_SIDE)  # 启用两面渲染
        # self.gl.glEnable(self.gl.GL_VERTEX_PROGRAM_POINT_SIZE_ARB)  # 启用点大小
        # self.gl.glEnable(self.gl.GL_VERTEX_PROGRAM_TWO_SIDE_ARB)  # 启用两面渲染
        # self.gl.glEnable(self.gl.GL_MULTISAMPLE)  # 启用多重采样
        # self.gl.glEnable(self.gl.GL_SAMPLE_ALPHA_TO_COVERAGE)  # 启用alpha到coverage
        # self.gl.glEnable(self.gl.GL_SAMPLE_ALPHA_TO_ONE)  # 启用alpha到one
        # self.gl.glEnable(self.gl.GL_SAMPLE_COVERAGE)  # 启用采样覆盖
        # self.gl.glEnable(self.gl.GL_SAMPLE_MASK)  # 启用采样掩码
        # self.gl.glEnable(self.gl.GL_SAMPLE_SHADING)  # 启用采样着色
        # self.gl.glEnable(self.gl.GL_SAMPLE_COVERAGE_INVERT)  # 启用采样覆盖反转
        # self.gl.glEnable(self.gl.GL_SAMPLE_COVERAGE_VALUE)  # 启用采样覆盖值
        # self.gl.glEnable(self.gl.GL_SAMPLE_MASK_VALUE)  # 启用采样掩码值
        # self.gl.glEnable(self.gl.GL_SAMPLE_BUFFERS)  # 启用采样缓冲区
