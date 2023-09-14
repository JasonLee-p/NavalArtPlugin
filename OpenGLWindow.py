import numpy as np
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QOpenGLWidget, QApplication, QToolButton
from PyQt5.QtGui import QMouseEvent, QWheelEvent, QSurfaceFormat, QKeyEvent
from PyQt5.QtGui import QOpenGLVersionProfile

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.raw.GL.VERSION.GL_2_0 import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_PROJECTION, GL_MODELVIEW, GL_LINE_STIPPLE

from NA_design_reader import AdjustableHull, Part
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


def show_state(txt, msg_type='process', label=None):
    """
    显示状态栏信息
    :param txt:
    :param msg_type:
    :param label:
    :return:
    """
    color_map = {
        'warning': 'orange',
        'success': f"{FG_COLOR0}",
        'process': 'gray',
        'error': f"{FG_COLOR1}",
    }
    if msg_type in color_map:
        label.setStyleSheet(f'color: {color_map[msg_type]};')
    else:
        label.setStyleSheet(f'color: {FG_COLOR0};')
    label.setText(txt)


class OpenGLWin(QOpenGLWidget):
    # 操作模式
    Selectable = 1
    UnSelectable = 0
    # 3D物体显示模式
    ShowAll = 11
    ShowZX = 22
    ShowYX = 33
    ShowLeft = 44

    def __init__(self, camera_sensitivity, using_various_mode=False, show_state_label=None):
        self.operation_mode = OpenGLWin.Selectable
        self.show_3d_obj_mode = OpenGLWin.ShowAll
        self.using_various_mode = using_various_mode  # 是否使用全部四种显示模式

        super(OpenGLWin, self).__init__()
        # ===================================================================================设置基本参数
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.width = QOpenGLWidget.width(self)
        self.height = QOpenGLWidget.height(self)
        self.theme_color = GLTheme
        self.light_pos = QVector3D(1000, 700, 1000)
        self.fovy = 45
        # ==================================================================================OpenGL初始化
        self.gl = None
        self.texture = None
        self.shaderProgram = None
        self.vbo = None
        self.vao = None
        # ========================================================================================3D物体
        self.environment_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        # 四种不同模式下显示的物体
        self.all_3d_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        if self.using_various_mode:
            self.zx_layer_obj = []  # 横剖面模式
            self.yx_layer_obj = []  # 纵剖面模式
            self.left_view_obj = []  # 左视图线框模式
            self.showMode_showSet_map = {
                OpenGLWin.ShowAll: self.all_3d_obj,
                OpenGLWin.ShowZX: self.zx_layer_obj,
                OpenGLWin.ShowYX: self.yx_layer_obj,
                OpenGLWin.ShowLeft: self.left_view_obj
            }
        self.ShipsAllParts = []  # 船体所有零件，用于选中时遍历
        for gl_plot_obj in self.all_3d_obj["钢铁"]:
            if type(gl_plot_obj) == NAHull:
                self.ShipsAllParts = gl_plot_obj.Parts
                self.zx_layer_obj.extend(gl_plot_obj.xzLayers)
        # =========================================================================================事件
        self.camera = Camera(self.width, self.height, camera_sensitivity)
        self.lastPos = QPoint()  # 上一次鼠标位置
        self.select_start = None  # 选择框起点
        self.select_end = None  # 选择框终点
        self.rotate_start = None  # 旋转起点
        self.all_gl_objects = GLObject.all_objects  # 所有的GL对象 # TODO：暂时不用
        self.selected_gl_objects = {
            self.ShowAll: [], self.ShowZX: [], self.ShowYX: [], self.ShowLeft: []
        }
        self.show_state_label = show_state_label
        # ========================================================================================子控件
        self.mod1_button = QToolButton(self)
        self.mod2_button = QToolButton(self)
        self.mod3_button = QToolButton(self)
        self.mod4_button = QToolButton(self)
        self.ModBtWid = 55
        self.mod_buttons = [self.mod1_button, self.mod2_button, self.mod3_button, self.mod4_button]
        self.init_mode_toolButton()

    def initializeGL(self) -> None:
        self.init_gl()  # 初始化OpenGL相关参数
        # 创建着色器程序
        self.shaderProgram = self.gl.glCreateProgram()
        # 创建顶点着色器
        vertexShader = self.gl.glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertexShader, VERTEX_SHADER)
        self.gl.glCompileShader(vertexShader)
        # 创建片段着色器
        fragmentShader = self.gl.glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragmentShader, FRAGMENT_SHADER)
        self.gl.glCompileShader(fragmentShader)
        # 将着色器附加到程序上
        self.gl.glAttachShader(self.shaderProgram, vertexShader)
        self.gl.glAttachShader(self.shaderProgram, fragmentShader)
        # self.gl.glLinkProgram(self.shaderProgram)  # 链接着色器程序
        # self.gl.glUseProgram(self.shaderProgram)  # 使用着色器程序
        # ===============================================================================绘制
        # 设置背景颜色
        self.gl.glClearColor(*self.theme_color["背景"])
        # 基础物体
        self.environment_obj["海面"].append(GridLine(
            self.gl, scale=10, num=50, central=(0, 0, 0), color=(0.1, 0.2, 0.5, 1)))
        self.environment_obj["光源"].append(LightSphere(
            self.gl, central=self.light_pos, radius=20))
        # ===============================================================================绘制
        self.vbo = self.gl.glGenBuffers(1)  # 创建VBO
        # self.vao = self.gl.glGenVertexArrays(1)  # 创建VAO
        # self.gl.glBindVertexArray(self.vao)  # 绑定VAO
        self.gl.glBindBuffer(self.gl.GL_ARRAY_BUFFER, self.vbo)  # 绑定VBO

    def paintGL(self) -> None:
        # 获取窗口大小
        width = QOpenGLWidget.width(self)
        height = QOpenGLWidget.height(self)
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self.init_view()
            for button in self.mod_buttons:
                right = QOpenGLWidget.width(self) - 10 - 4 * (self.ModBtWid + 10)
                index = self.mod_buttons.index(button)
                button.setGeometry(right + 10 + index * (self.ModBtWid + 10), 10, self.ModBtWid, 30)
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
        elif self.using_various_mode:  # 如果包含各种模式
            for obj in self.showMode_showSet_map[self.show_3d_obj_mode]:
                obj.draw(self.gl, theme_color=self.theme_color)

        self.draw_selected_objs()  # 绘制被选中的物体
        if self.select_start and self.select_end:  # 绘制选择框
            self.draw_select_box()

    def init_mode_toolButton(self):
        self.mod1_button.setText("全视图")
        self.mod2_button.setText("横剖面")
        self.mod3_button.setText("纵剖面")
        self.mod4_button.setText("左视图")
        self.mod1_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowAll))
        self.mod2_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowZX))
        self.mod3_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowYX))
        self.mod4_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowLeft))
        for button in self.mod_buttons:
            button.setCheckable(True)
            button.setFont(QFont("微软雅黑", 8))
            button.setStyleSheet(f"QToolButton{{"
                                 f"color: {FG_COLOR0};"
                                 f"background-color: {BG_COLOR1};"
                                 f"border: 1px solid {BG_COLOR1};"
                                 f"border-radius: 5px;}}"
                                 # 按下时的样式
                                 f"QToolButton:checked{{"
                                 f"color: {FG_COLOR0};"
                                 f"background-color: {BG_COLOR3};"
                                 f"border: 1px solid {BG_COLOR3};"
                                 f"border-radius: 5px;}}"
                                 )
        self.mod1_button.setChecked(True)

    def set_show_3d_obj_mode(self, mode):
        self.show_3d_obj_mode = mode
        if mode == OpenGLWin.ShowAll:
            self.mod1_button.setChecked(True)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(False)
            self.show_3d_obj_mode = OpenGLWin.ShowAll
        elif mode == OpenGLWin.ShowZX:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(True)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(False)
            self.show_3d_obj_mode = OpenGLWin.ShowZX
        elif mode == OpenGLWin.ShowYX:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(True)
            self.mod4_button.setChecked(False)
            self.show_3d_obj_mode = OpenGLWin.ShowYX
        elif mode == OpenGLWin.ShowLeft:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(True)
            self.show_3d_obj_mode = OpenGLWin.ShowLeft
        self.update()

    def draw_selected_objs(self):
        # print(self.selected_gl_objects)
        if self.show_3d_obj_mode == OpenGLWin.ShowAll:
            # 材料设置
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_AMBIENT, self.theme_color["被选中"][0])
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_DIFFUSE, self.theme_color["被选中"][1])
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SPECULAR, self.theme_color["被选中"][2])
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SHININESS, self.theme_color["被选中"][3])
            for obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                if type(obj) != AdjustableHull:
                    continue  # TODO: 未来要加入Part类的绘制方法，而不是只能绘制AdjustableHull
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
        elif self.show_3d_obj_mode == OpenGLWin.ShowZX:
            # 材料设置
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_AMBIENT, self.theme_color["被选中"][0])
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_DIFFUSE, self.theme_color["被选中"][1])
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SPECULAR, self.theme_color["被选中"][2])
            self.gl.glMaterialfv(self.gl.GL_FRONT_AND_BACK, self.gl.GL_SHININESS, self.theme_color["被选中"][3])
            for obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                for part, dots in obj.PartsDotsMap.items():
                    # self.gl.glNormal3f(0, 1, 0)
                    # self.gl.glBegin(self.gl.GL_POLYGON)
                    # for dot in dots[::-1]:
                    #     self.gl.glVertex3f(*dot)
                    # self.gl.glEnd()
                    # self.gl.glNormal3f(0, -1, 0)
                    # self.gl.glBegin(self.gl.GL_POLYGON)
                    # for dot in dots:
                    #     self.gl.glVertex3f(dot[0], dot[1], dot[2])
                    # self.gl.glEnd()

                    self.gl.glLineWidth(1.3)
                    color = self.theme_color["选择框"][0]
                    self.gl.glColor4f(*color)
                    self.gl.glBegin(self.gl.GL_LINE_LOOP)
                    for dot in dots[::-1]:
                        self.gl.glVertex3f(*dot)
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

    def get_choosing_obj_list(self):
        if self.show_3d_obj_mode == OpenGLWin.ShowAll:
            return self.ShipsAllParts
        elif self.show_3d_obj_mode == OpenGLWin.ShowZX:
            return self.zx_layer_obj
        elif self.show_3d_obj_mode == OpenGLWin.ShowYX:
            return self.yx_layer_obj
        elif self.show_3d_obj_mode == OpenGLWin.ShowLeft:
            return self.left_view_obj
        else:
            return []

    def add_selected_objects_when_click(self):
        pos = self.select_start
        min_distance = 100000
        min_distance_part = None
        for obj in self.get_choosing_obj_list():
            if type(obj) in (AdjustableHull, Part):
                dots = [obj.Pos]
            elif type(obj) == NaHullXZLayer:
                dots = obj.Pos_list
            else:  # TODO: 其他模式下的选中
                dots = []
            if len(dots) == 0:
                continue
            s_dots = self.transform_points(self.camera.fovy, self.camera.pos, self.camera.up, self.camera.angle,
                                           QOpenGLWidget.width(self), QOpenGLWidget.height(self), dots)
            for dot in s_dots:
                distance = np.sqrt((dot[0] - pos.x()) ** 2 + (dot[1] - pos.y()) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    min_distance_part = obj
        if min_distance < 100:  # 如果距离小于100像素，就将零件加入到选中列表中
            return min_distance_part
        return None

    def add_selected_objects_of_selectBox(self):
        if self.select_start and self.select_end:
            result = []
            min_x = min(self.select_start.x(), self.select_end.x())
            max_x = max(self.select_start.x(), self.select_end.x())
            min_y = min(self.select_start.y(), self.select_end.y())
            max_y = max(self.select_start.y(), self.select_end.y())
            # 获取屏幕
            for obj in self.get_choosing_obj_list():
                if type(obj) in (AdjustableHull, Part):
                    dots = [obj.Pos]
                elif type(obj) == NaHullXZLayer:
                    dots = obj.Pos_list
                else:  # TODO: 其他模式下的选中
                    dots = []
                if len(dots) == 0:
                    continue
                s_dots = self.transform_points(self.camera.fovy, self.camera.pos, self.camera.up, self.camera.angle,
                                               QOpenGLWidget.width(self), QOpenGLWidget.height(self), dots)
                for dot in s_dots:
                    if min_x < dot[0] < max_x and min_y < dot[1] < max_y:
                        result.append(obj)
            return result
        return []

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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # 数字1234切换显示模式
        if event.key() == Qt.Key_1:
            self.set_show_3d_obj_mode(OpenGLWin.ShowAll)
        elif event.key() == Qt.Key_2:
            self.set_show_3d_obj_mode(OpenGLWin.ShowZX)
        elif event.key() == Qt.Key_3:
            self.set_show_3d_obj_mode(OpenGLWin.ShowYX)
        elif event.key() == Qt.Key_4:
            self.set_show_3d_obj_mode(OpenGLWin.ShowLeft)
        # a键摄像机目标回（0, 0, 0）
        if event.key() == Qt.Key_A:
            self.camera.change_target(QVector3D(0, 0, 0))
            self.update()
        # ====================================================================================Alt键
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            # 如果当前有且仅有一个被选中的AdjustableHull，就寻找其上方的AdjustableHull
            if self.show_3d_obj_mode != OpenGLWin.ShowAll:
                return
            if event.key() not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                return
            # 获取当前被选中的AdjustableHull
            for selected_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                _min = None
                for color, part_set in self.all_3d_obj["钢铁"][0].DrawMap.items():
                    for obj in part_set:
                        if type(obj) != AdjustableHull or obj == selected_obj:
                            continue
                        if obj.Pos[0] != selected_obj.Pos[0]:
                            continue
                        if event.key() == Qt.Key_Up and (  # ======================================Alt上键
                                obj.Pos[2] == selected_obj.Pos[2]):
                            if obj.Pos[1] > selected_obj.Pos[1]:
                                if _min is None or obj.Pos[1] < _min.Pos[1]:
                                    show_state("选区上移", "success", self.show_state_label)
                                    _min = obj
                        elif event.key() == Qt.Key_Down and (  # ==================================Alt下键
                                obj.Pos[2] == selected_obj.Pos[2]):
                            if obj.Pos[1] < selected_obj.Pos[1]:
                                if _min is None or obj.Pos[1] > _min.Pos[1]:
                                    show_state("选区下移", "success", self.show_state_label)
                                    _min = obj
                        # 如果摄像机方向朝向x负方向，左键就往前（z正方向）找，右键就往后（z负方向）找
                        elif (event.key() == Qt.Key_Left and self.camera.angle.x() < 0) or (
                                event.key() == Qt.Key_Right and self.camera.angle.x() > 0):
                            if obj.Pos[2] > selected_obj.Pos[2] and obj.Pos[1] == selected_obj.Pos[1]:
                                if _min is None or obj.Pos[2] < _min.Pos[2]:
                                    show_state("选区前移", "success", self.show_state_label)
                                    _min = obj
                        elif (event.key() == Qt.Key_Right and self.camera.angle.x() < 0) or (
                                event.key() == Qt.Key_Left and self.camera.angle.x() > 0):
                            if obj.Pos[2] < selected_obj.Pos[2] and obj.Pos[1] == selected_obj.Pos[1]:
                                if _min is None or obj.Pos[2] > _min.Pos[2]:
                                    show_state("选区后移", "success", self.show_state_label)
                                    _min = obj
                if _min is not None:  # =====================================================如果找到了
                    if _min not in self.selected_gl_objects[self.show_3d_obj_mode]:
                        index = self.selected_gl_objects[self.show_3d_obj_mode].index(selected_obj)
                        self.selected_gl_objects[self.show_3d_obj_mode][index] = _min
                    else:
                        self.selected_gl_objects[self.show_3d_obj_mode].remove(selected_obj)
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self.camera.zoom(-0.11)
        else:
            self.camera.zoom(0.11)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:  # 左键按下
            self.select_start = event.pos() if self.operation_mode == OpenGLWin.Selectable else None
            self.lastPos = event.pos() if self.operation_mode == OpenGLWin.UnSelectable else None
            # 判断是否按下shift，如果没有按下，就清空选中列表
            if QApplication.keyboardModifiers() != Qt.ShiftModifier:
                self.selected_gl_objects[self.show_3d_obj_mode].clear()
        elif event.button() == Qt.RightButton:  # 右键按下
            self.rotate_start = event.pos()
            self.lastPos = event.pos()
        elif event.button() == Qt.MidButton:  # 中键按下
            self.lastPos = event.pos()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:  # 左键绘制选择框
            self.select_end = event.pos() if self.operation_mode == OpenGLWin.Selectable else None
            self.lastPos = event.pos() if self.operation_mode == OpenGLWin.UnSelectable else None
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
            if self.operation_mode == OpenGLWin.Selectable:
                if QApplication.keyboardModifiers() != Qt.ShiftModifier:  # 如果shift没有按下：
                    if self.select_start and self.select_end:
                        self.selected_gl_objects[self.show_3d_obj_mode].extend(self.add_selected_objects_of_selectBox())
                    elif self.select_end is None and self.select_start:
                        if self.add_selected_objects_when_click() is not None:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(
                                self.add_selected_objects_when_click())
                    self.select_start = None
                    self.select_end = None
                elif QApplication.keyboardModifiers() == Qt.ShiftModifier:  # 如果shift按下：
                    if self.select_start and self.select_end:
                        add_list = self.add_selected_objects_of_selectBox()
                        for add_obj in add_list:
                            if add_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                                self.selected_gl_objects[self.show_3d_obj_mode].remove(add_obj)
                            else:
                                self.selected_gl_objects[self.show_3d_obj_mode].append(add_obj)
                    elif self.select_end is None and self.select_start:
                        add_obj = self.add_selected_objects_when_click()
                        # 选择性地添加或删除物体
                        if add_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                            self.selected_gl_objects[self.show_3d_obj_mode].remove(add_obj)
                        else:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(add_obj)
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


class OpenGLWin2(QOpenGLWidget):
    # 操作模式
    Selectable = 1
    UnSelectable = 0
    # 3D物体显示模式
    ShowAll = 11
    ShowZX = 22
    ShowYX = 33
    ShowLeft = 44

    def __init__(self, camera_sensitivity):
        super().__init__()

        # 配置OpenGL格式
        _format = QSurfaceFormat()
        _format.setVersion(4, 3)  # 指定OpenGL版本为3.3
        _format.setProfile(QSurfaceFormat.CoreProfile)  # 使用Core Profile
        _format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)  # 双缓冲
        _format.setDepthBufferSize(24)  # 设置深度缓冲区大小
        self.setFormat(_format)
        # VAO和VBO的相关变量
        self.vao = None
        self.vbo = None
        # 摄像机属性
        self.camera = Camera(self.width, self.height, camera_sensitivity)

    def initializeGL(self):
        # 初始化OpenGL函数
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)  # 启用背面剔除
        glCullFace(GL_BACK)  # 剔除背面
        glFrontFace(GL_CCW)  # 设置逆时针为正面
        # 创建VAO VBO
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        # 初始化VAO和VBO
        self.init_vao_vbo()

    def paintGL(self):
        glClearColor(0.3, 0.3, 0.3, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # 设置视角
        # glLoadIdentity()
        # 绘制一个基本正方体
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 36)
        glBindVertexArray(0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)

    def init_vao_vbo(self):
        vertices = [
            # 顶点坐标
            -1.0, 0.0, -1.0,
            1.0, 0.0, -1.0,
            1.0, 0.0, 1.0,
            -1.0, 0.0, 1.0,
        ]
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, len(vertices) * 4, np.array(vertices, dtype=np.float32), GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindVertexArray(0)
