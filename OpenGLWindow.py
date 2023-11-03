# -*- coding: utf-8 -*-
"""
OpenGL窗口
"""
import struct
import time

import numpy as np
from OpenGL import GL
from PyQt5.QtCore import QByteArray

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5 import _QOpenGLFunctions_2_0  # 这个库必须导入，否则打包后会报错
from PyQt5.QtGui import (
    QOpenGLVersionProfile, QOpenGLShaderProgram, QOpenGLShader, QOpenGLBuffer,
    QOpenGLVertexArrayObject, QQuaternion, QPen, QPainter, QSurfaceFormat, QOffscreenSurface, QOpenGLContext)
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.raw.GL.VERSION.GL_2_0 import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_PROJECTION, GL_MODELVIEW, GL_LINE_STIPPLE

from ship_reader.NA_design_reader import NAPart, AdjustableHull, NAPartNode
from GL_plot import *
from GUI import *
from shader_program import shader_program
from util_funcs import CONST
from right_widgets.right_operation_editing import OperationEditing

VERTEX_SHADER = shader_program.VS

FRAGMENT_SHADER = shader_program.FS


# # 片段着色器代码（包括FXAA抗锯齿）
# with open("FragmentShader.frag", "r") as f:
#     FRAGMENT_SHADER = f.read()


def reset_matrix(func):
    def _wrapper(*args, **kwargs):
        self = args[0]
        # 保存原来的矩阵
        self.gl2_0.glMatrixMode(GL_PROJECTION)
        self.gl2_0.glPushMatrix()
        self.gl2_0.glLoadIdentity()
        self.gl2_0.glOrtho(0, self.width, self.height, 0, -1, 1)
        self.gl2_0.glMatrixMode(GL_MODELVIEW)
        self.gl2_0.glPushMatrix()
        self.gl2_0.glLoadIdentity()
        func(*args, **kwargs)
        # 恢复原来的矩阵
        self.gl2_0.glMatrixMode(GL_PROJECTION)
        self.gl2_0.glPopMatrix()
        self.gl2_0.glMatrixMode(GL_MODELVIEW)
        self.gl2_0.glPopMatrix()

    return _wrapper


class Camera:
    """
    摄像机类，用于处理视角变换
    """
    all_cameras = []

    def __init__(self, width, height, sensitivity):
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

    def change_view(self, mode):
        # 切换正交投影和透视投影
        if mode == OpenGLWin.Perspective:
            self.fovy = 45
        elif mode == OpenGLWin.Orthogonal:
            self.fovy = 0

    def change_target(self, tar):
        self.pos = tar + (self.pos - self.tar).normalized() * self.distance
        self.tar = tar
        self.angle = self.calculate_angle()

    def calculate_angle(self):
        return QVector3D(self.tar - self.pos).normalized()

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


class OpenGLWin(QOpenGLWidget):
    # 操作模式
    Selectable = 1
    UnSelectable = 0
    # 3D物体显示模式
    ShowAll = 11
    ShowXZ = 22
    ShowXY = 33
    ShowLeft = 44
    # 选择模式（子模式）
    ShowObj = 111
    ShowDotNode = 222
    # 视图模式
    Perspective = "perspective"
    Orthogonal = "orthogonal"

    def save_current_image(self, save_dir, prj_name):
        """
        获取当前画面中物体图像，背景为透明，格式为png
        :param save_dir: 保存路径
        :param prj_name: 项目名称
        :return:
        """
        # 在线程A中创建一个QOpenGLContext
        offScreen_surface = QOffscreenSurface()
        offScreen_surface.create()
        offScreen_context = QOpenGLContext()
        offScreen_context.create()
        offScreen_context.makeCurrent(offScreen_surface)
        # 删除所有环境物体
        self.environment_obj["海面"].clear()
        self.environment_obj["光源"].clear()
        self.paintGL()
        self.update()
        # 获取当前画面中物体图像，裁剪边缘，背景为透明，格式为png
        cut = 0
        image = self.grabFramebuffer()
        image = image.copy(cut, cut, image.width() - 2 * cut, image.height() - 2 * cut)
        image = image.convertToFormat(QImage.Format_ARGB32)
        # 检查路径
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        # 保存图片
        image.save(os.path.join(save_dir, f"{prj_name}.png"))
        # 恢复环境物体
        self.environment_obj["海面"].append(GridLine(
            self.gl2_0, scale=10, num=50, central=(0, 0, 0), color=self.theme_color["海面"][0]))
        self.environment_obj["光源"].append(LightSphere(
            self.gl2_0, central=self.light_pos, radius=20))
        self.paintGL()
        self.update()

    def __init__(self, camera_sensitivity, using_various_mode=False, show_statu_func=None):
        self.show_statu_func = show_statu_func
        self.operation_mode = OpenGLWin.Selectable
        self.show_3d_obj_mode = (OpenGLWin.ShowAll, OpenGLWin.ShowObj)
        self.using_various_mode = using_various_mode  # 是否使用全部四种显示模式
        self.view_mode = OpenGLWin.Perspective  # 视图模式

        super(OpenGLWin, self).__init__()
        # ===================================================================================设置基本参数
        self.setMouseTracking(True)
        # 设置鼠标样式
        self.cs = Qt.ArrowCursor
        self.setCursor(self.cs)
        self.setFocusPolicy(Qt.StrongFocus)  # 设置焦点策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # 设置右键菜单策略
        self.width = QOpenGLWidget.width(self)
        self.height = QOpenGLWidget.height(self)
        self.theme_color = GLTheme
        self.light_pos = QVector3D(1000, 700, 1000)
        self.fovy = 45
        # ==================================================================================OpenGL初始化
        self.gl2_0 = None
        self.gl_commands = {
            (OpenGLWin.ShowAll, OpenGLWin.ShowObj): [None, False],
            (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode): [None, False],
            (OpenGLWin.ShowXZ, OpenGLWin.ShowObj): [None, False],
            (OpenGLWin.ShowXZ, OpenGLWin.ShowDotNode): [None, False],
            (OpenGLWin.ShowXY, OpenGLWin.ShowObj): [None, False],
            (OpenGLWin.ShowXY, OpenGLWin.ShowDotNode): [None, False],
            (OpenGLWin.ShowLeft, OpenGLWin.ShowObj): [None, False],
            (OpenGLWin.ShowLeft, OpenGLWin.ShowDotNode): [None, False]
        }
        # ========================================================================================3D物体
        self.environment_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        # 四种不同模式下显示的物体
        self.all_3d_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        if self.using_various_mode:
            self.xz_layer_obj = []  # 横剖面模式
            self.xy_layer_obj = []  # 纵剖面模式
            self.left_view_obj = []  # 左视图线框模式
            self.xzLayer_node = []  # 所有横剖面的节点
            self.xyLayer_node = []  # 所有纵剖面的节点
            self.leftView_node = []  # 所有左视图的节点
        self.prj_all_parts = []  # 船体所有零件，用于选中时遍历
        for gl_plot_obj in self.all_3d_obj["钢铁"]:
            if isinstance(gl_plot_obj, NAHull):
                for _color, parts in gl_plot_obj.ColorPartsMap.items():
                    for part in parts:
                        self.prj_all_parts.append(part)
                self.xz_layer_obj.extend(gl_plot_obj.xzLayers)
                self.xy_layer_obj.extend(gl_plot_obj.xyLayers)
                self.left_view_obj.extend(gl_plot_obj.leftViews)
        # =========================================================================================事件
        self.camera = Camera(self.width, self.height, camera_sensitivity)
        self.initialized = False
        self.camera_movable = True  # 摄像机是否可移动
        self.lastPos = QPoint()  # 上一次鼠标位置
        self.select_start = None  # 选择框起点
        self.select_end = None  # 选择框终点
        self.rotate_start = None  # 旋转起点
        self.selectObjOrigin_map = {  # 从哪个集合中取出选中的对象
            (OpenGLWin.ShowAll, OpenGLWin.ShowObj): NAPart,
            (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode): NAPartNode,
            (OpenGLWin.ShowXZ, OpenGLWin.ShowObj): NaHullXZLayer,
            (OpenGLWin.ShowXZ, OpenGLWin.ShowDotNode): NAXZLayerNode,
            (OpenGLWin.ShowXY, OpenGLWin.ShowObj): NaHullXYLayer,
            (OpenGLWin.ShowXY, OpenGLWin.ShowDotNode): NAXYLayerNode,
            (OpenGLWin.ShowLeft, OpenGLWin.ShowObj): NaHullLeftView,
            (OpenGLWin.ShowLeft, OpenGLWin.ShowDotNode): NALeftViewNode
        }
        self.selected_gl_objects = {
            (OpenGLWin.ShowAll, OpenGLWin.ShowObj): [],  # 选中的零件
            (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode): [],  # 选中的节点
            (OpenGLWin.ShowXZ, OpenGLWin.ShowObj): [],  # 选中的xz层
            (OpenGLWin.ShowXZ, OpenGLWin.ShowDotNode): [],  # 选中的节点
            (OpenGLWin.ShowXY, OpenGLWin.ShowObj): [],  # 选中的xy层
            (OpenGLWin.ShowXY, OpenGLWin.ShowDotNode): [],  # 选中的节点
            (OpenGLWin.ShowLeft, OpenGLWin.ShowObj): [],  # 选中的左视图
            (OpenGLWin.ShowLeft, OpenGLWin.ShowDotNode): [],  # 选中的节点
        }
        # ========================================================================================子控件
        self.fps_label = QLabel(self)
        self._init_fps_label()
        if self.using_various_mode:
            self.mod1_button = QToolButton(self)
            self.mod2_button = QToolButton(self)
            self.mod3_button = QToolButton(self)
            self.mod4_button = QToolButton(self)
            self.subMod1_button = QToolButton(self)
            self.subMod2_button = QToolButton(self)
            self.ModBtWid = 55
            self.mod_buttons = [self.mod1_button, self.mod2_button, self.mod3_button, self.mod4_button]
            self.subMod_buttons = [self.subMod1_button, self.subMod2_button]
            self.init_mode_toolButton()

    def initializeGL(self) -> None:
        self.init_gl()  # 初始化OpenGL相关参数
        # ===============================================================================绘制
        # 设置背景颜色
        glClearColor(*self.theme_color["背景"])
        # 基础物体
        self.environment_obj["海面"].append(GridLine(
            self.gl2_0, scale=10, num=50, central=(0, 0, 0), color=self.theme_color["海面"][0]))
        self.environment_obj["光源"].append(LightSphere(
            self.gl2_0, central=self.light_pos, radius=20))
        # ===============================================================================绘制
        self.initialized = True

    def paintGL(self) -> None:
        """
        绘制
        所有的对象在绘制的时候都会绑定self.glWin = self
        :return:
        """
        st = time.time()
        self.before_draw()
        # ============================================================================= 绘制物体
        for mt, objs in self.environment_obj.items():  # 绘制环境物体
            [obj.draw(self.gl2_0, material=mt, theme_color=self.theme_color) for obj in objs]
        if not self.all_3d_obj["钢铁"] and self.using_various_mode:
            self.draw_loading_objs()
        else:  # 绘制船体
            self.draw_main_objs()
            # 开启辅助光
            self.gl2_0.glEnable(GL_LIGHT1)
            self.draw_selected_objs()
            self.draw_temp_objs()
            self.draw_2D_objs()
            # 关闭辅助光
            self.gl2_0.glDisable(GL_LIGHT1)
        if time.time() - st != 0:  # 刷新FPS
            self.fps_label.setText(f"FPS: {round(1 / (time.time() - st), 1)}")

    def repaintGL(self):
        # 重新渲染
        for _mode in self.gl_commands.keys():
            self.gl_commands[_mode][1] = True
        self.paintGL()
        for _mode in self.gl_commands.keys():
            self.gl_commands[_mode][1] = False
        self.update()

    def before_draw(self):
        # 获取窗口大小，如果窗口大小改变，就重新初始化
        width = QOpenGLWidget.width(self)
        height = QOpenGLWidget.height(self)
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            try:
                self.init_view()
            except GLError:
                pass
            # 更新按钮位置
            if self.using_various_mode:
                right = QOpenGLWidget.width(self) - 10 - 4 * (self.ModBtWid + 10)
                sub_right = QOpenGLWidget.width(self) - 10 - 2 * (self.ModBtWid + 35)
                for button in self.mod_buttons:
                    index = self.mod_buttons.index(button)
                    button.setGeometry(right + 10 + index * (self.ModBtWid + 10), 10, self.ModBtWid, 28)
                for button in self.subMod_buttons:
                    index = self.subMod_buttons.index(button)
                    button.setGeometry(sub_right + 10 + index * (self.ModBtWid + 35), 50, self.ModBtWid + 25, 23)
        # 清除颜色缓冲区和深度缓冲区
        self.gl2_0.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # 设置相机
        self.gl2_0.glLoadIdentity()  # 重置矩阵
        self.gl2_0.glDisable(GL_LINE_STIPPLE)  # 禁用虚线模式
        self.set_camera() if self.camera_movable else None

    def draw_loading_objs(self):
        parts = AdjustableHull.hull_design_tab_id_map.copy().values()
        for part in parts:  # TODO: 优化绘制
            part.glWin = self
            if isinstance(part, AdjustableHull):
                part.draw_pre(self.gl2_0)
                ...
        self.update()
        return

    def draw_main_objs(self):
        self.gl2_0.glLoadName(0)
        # =========================================================================== 全视图部件模式
        if self.show_3d_obj_mode[0] == OpenGLWin.ShowAll:  # 如果有钢铁物体，就绘制钢铁物体
            if self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):  # 是部件模式
                if self.using_various_mode:
                    for part in NAPart.hull_design_tab_id_map.copy().values():
                        part.glWin = self
                        if not isinstance(part, AdjustableHull):
                            continue
                        part.draw(self.gl2_0)
                else:
                    for mt, objs in self.all_3d_obj.items():
                        for obj in objs:
                            obj.glWin = self
                            obj.draw(self.gl2_0, material=mt, theme_color=self.theme_color)
            elif self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode):  # 是节点模式
                if self.using_various_mode:
                    for part in NAPart.hull_design_tab_id_map.copy().values():
                        part.glWin = self
                        if not isinstance(part, AdjustableHull):
                            continue

                        part.draw(self.gl2_0, transparent=True)

                else:
                    for mt, objs in self.all_3d_obj.items():
                        for obj in objs:
                            obj.glWin = self
                            obj.draw(self.gl2_0, material=mt, theme_color=self.theme_color, transparent=True)
                self.gl2_0.glEnable(self.gl2_0.GL_LIGHT1)  # 启用光源1
                for node in NAPartNode.id_map.copy().values():
                    node.draw(self.gl2_0, theme_color=self.theme_color)
                self.gl2_0.glDisable(self.gl2_0.GL_LIGHT1)
        # ================================================================================= 其他模式
        elif self.using_various_mode and self.show_3d_obj_mode[0] != OpenGLWin.ShowAll:
            for obj in self.selectObjOrigin_map[self.show_3d_obj_mode].id_map.copy().values():
                obj.glWin = self
                obj.draw(self.gl2_0, theme_color=self.theme_color)
        self.gl2_0.glLoadName(0)

    def draw_selected_objs(self):
        if self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):  # 如果是模式1的部件模式
            for obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                if not isinstance(obj, AdjustableHull):
                    continue  # TODO: 未来要加入Part类的绘制方法，而不是只能绘制AdjustableHull
                obj.draw_selected(self.gl2_0, theme_color=self.theme_color)
        elif self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode):
            for node in self.selected_gl_objects[self.show_3d_obj_mode]:
                if not isinstance(node, NAPartNode):
                    continue
                if node.selected_genList and not node.update_selectedList:
                    self.gl2_0.glCallList(node.selected_genList)
                    continue
                node.selected_genList = glGenLists(1)
                self.gl2_0.glNewList(node.selected_genList, GL_COMPILE_AND_EXECUTE)  # Execute表示创建后立即执行
                self.gl2_0.glColor4f(*self.theme_color["橙色"][0])
                self.gl2_0.glPointSize(6)
                self.gl2_0.glBegin(self.gl2_0.GL_POINTS)
                self.gl2_0.glVertex3f(*node.pos)
                self.gl2_0.glEnd()
                self.gl2_0.glEndList()

        elif self.show_3d_obj_mode[0] in (OpenGLWin.ShowXZ, OpenGLWin.ShowXY, OpenGLWin.ShowLeft):
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

                    self.gl2_0.glLineWidth(2)
                    color = self.theme_color["橙色"][0]
                    self.gl2_0.glColor4f(*color)
                    self.gl2_0.glBegin(self.gl2_0.GL_LINE_LOOP)
                    for dot in dots[::-1]:
                        self.gl2_0.glVertex3f(*dot)
                    self.gl2_0.glEnd()

    def draw_select_box(self):
        """
        转变为二维视角，画出选择框
        """
        # 画虚线框
        self.gl2_0.glColor4f(*self.theme_color["选择框"][0])
        self.gl2_0.glEnable(GL_LINE_STIPPLE)  # 启用虚线模式
        self.gl2_0.glLineStipple(0, 0x00FF)  # 设置虚线的样式
        self.gl2_0.glBegin(self.gl2_0.GL_LINE_LOOP)
        self.gl2_0.glVertex2f(self.select_start.x(), self.select_start.y())
        self.gl2_0.glVertex2f(self.select_start.x(), self.select_end.y())
        self.gl2_0.glVertex2f(self.select_end.x(), self.select_end.y())
        self.gl2_0.glVertex2f(self.select_end.x(), self.select_start.y())
        self.gl2_0.glEnd()

    def draw_temp_objs(self):
        for obj in TempObj.all_objs.copy():
            obj.glWin = self
            obj.draw(self.gl2_0, theme_color=self.theme_color)

    @reset_matrix
    def draw_2D_objs(self):
        if self.select_start and self.select_end:
            self.draw_select_box()

    def change_view_mode(self):
        if self.view_mode == OpenGLWin.Perspective:
            self.view_mode = OpenGLWin.Orthogonal
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glLoadIdentity()
            self.gl2_0.glOrtho(-self.width / 2, self.width / 2, -self.height / 2, self.height / 2, -1000, 1000)
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            self.gl2_0.glLoadIdentity()
            self.camera.change_view(OpenGLWin.Orthogonal)
            self.paintGL()
            self.update()
        elif self.view_mode == OpenGLWin.Orthogonal:
            self.view_mode = OpenGLWin.Perspective
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glLoadIdentity()
            self.gl2_0.glFrustum(-self.width / 2, self.width / 2, -self.height / 2, self.height / 2, 500, 100000)
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            self.gl2_0.glLoadIdentity()
            self.camera.change_view(OpenGLWin.Perspective)
            self.paintGL()
            self.update()

    def _init_fps_label(self):
        self.fps_label.setGeometry(10, 10, 100, 20)
        style = str(  # 透明背景
            f"color: {FG_COLOR0};"
            f"background-color: rgba(0, 0, 0, 0);"
        )
        self.fps_label.setStyleSheet(style)

    # noinspection PyUnresolvedReferences
    def init_mode_toolButton(self):
        self.mod1_button.setText("全视图1")
        self.mod2_button.setText("横剖面2")
        self.mod3_button.setText("纵剖面3")
        self.mod4_button.setText("左视图4")
        self.subMod1_button.setText("部件模式P")
        self.subMod2_button.setText("节点模式N")
        self.mod1_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowAll))
        self.mod2_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowXZ))
        self.mod3_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowXY))
        self.mod4_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowLeft))
        self.subMod1_button.clicked.connect(lambda: self.set_show_3d_obj_sub_mode(OpenGLWin.ShowObj))
        self.subMod2_button.clicked.connect(lambda: self.set_show_3d_obj_sub_mode(OpenGLWin.ShowDotNode))
        for button in self.mod_buttons + self.subMod_buttons:
            button.setCheckable(True)
            button.setFont(FONT_7)
            button.setStyleSheet(
                f"QToolButton{{"
                f"color: {FG_COLOR0};"
                f"background-color: {BG_COLOR1};"
                f"border: 1px solid {BG_COLOR1};"
                f"border-radius: 6px;}}"
                # 鼠标悬停时的样式
                f"QToolButton:hover{{"
                f"color: {FG_COLOR0};"
                f"background-color: {BG_COLOR2};"
                f"border: 1px solid {BG_COLOR2};"
                f"border-radius: 6px;}}"
                # 按下时的样式
                f"QToolButton:checked{{"
                f"color: {FG_COLOR0};"
                f"background-color: {BG_COLOR3};"
                f"border: 1px solid {BG_COLOR3};"
                f"border-radius: 6px;}}"
            )
        self.mod1_button.setChecked(True)
        self.subMod1_button.setChecked(True)

    def set_show_3d_obj_mode(self, father_mode):
        """
        修改父模式，不修改子模式
        :param father_mode: 父模式
        :return:
        """
        sub_mode = self.show_3d_obj_mode[1]
        self.show_3d_obj_mode = (father_mode, sub_mode)
        if father_mode == OpenGLWin.ShowAll:
            self.mod1_button.setChecked(True)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(False)
            self.show_statu_func("切换至全视图模式 (1)", "success")
        elif father_mode == OpenGLWin.ShowXZ:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(True)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(False)
            self.show_statu_func("切换至横剖面模式 (2)", "success")
        elif father_mode == OpenGLWin.ShowXY:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(True)
            self.mod4_button.setChecked(False)
            self.show_statu_func("切换至纵剖面模式 (3)", "success")
        elif father_mode == OpenGLWin.ShowLeft:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(True)
            self.show_statu_func("切换至左视图模式 (4)", "success")
        self.update()

    def set_show_3d_obj_sub_mode(self, sub_mode):
        father_mode = self.show_3d_obj_mode[0]
        self.show_3d_obj_mode = (father_mode, sub_mode)
        if sub_mode == OpenGLWin.ShowObj:
            self.subMod1_button.setChecked(True)
            self.subMod2_button.setChecked(False)
            self.show_statu_func("切换至部件模式 (1)", "success")
        elif sub_mode == OpenGLWin.ShowDotNode:
            self.subMod1_button.setChecked(False)
            self.subMod2_button.setChecked(True)
            self.show_statu_func("切换至节点模式 (2)", "success")
        self.update()

    def add_selected_objects_when_click(self):
        pos = self.select_end
        if self.show_3d_obj_mode[1] == OpenGLWin.ShowObj:
            # 将屏幕坐标点转换为OpenGL坐标系中的坐标点
            _x, _y = pos.x(), self.height - pos.y() - 1
            # 使用拾取技术来确定被点击的三角形
            if self.view_mode == OpenGLWin.Perspective:  # 如果是透视投影模式：
                glSelectBuffer(2 ** 20)
                glRenderMode(GL_SELECT)
                glInitNames()
                glPushName(0)
                self.gl2_0.glViewport(0, 0, self.width, self.height)
                self.gl2_0.glMatrixMode(GL_PROJECTION)
                self.gl2_0.glPushMatrix()
                self.gl2_0.glLoadIdentity()  # 重置矩阵
                gluPickMatrix(_x, _y, 1, 1, [0, 0, self.width, self.height])
                # 设置透视投影
                aspect_ratio = self.width / self.height
                gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)  # 设置透视投影
                self.gl2_0.glMatrixMode(GL_MODELVIEW)
                self.paintGL()  # 重新渲染场景
                self.gl2_0.glMatrixMode(GL_PROJECTION)
                self.gl2_0.glPopMatrix()
                self.gl2_0.glMatrixMode(GL_MODELVIEW)
                hits = glRenderMode(GL_RENDER)
            else:  # 如果是正交投影模式：
                glSelectBuffer(2 ** 20)
                glRenderMode(GL_SELECT)
                glInitNames()
                glPushName(0)
                self.gl2_0.glViewport(0, 0, self.width, self.height)
                self.gl2_0.glMatrixMode(GL_PROJECTION)
                self.gl2_0.glPushMatrix()
                self.gl2_0.glLoadIdentity()
                gluPickMatrix(_x, _y, 1, 1, [0, 0, self.width, self.height])
                self.gl2_0.glOrtho(-self.width / 2, self.width / 2, -self.height / 2, self.height / 2, -1000, 1000)
                self.gl2_0.glMatrixMode(GL_MODELVIEW)
                self.paintGL()
                self.gl2_0.glMatrixMode(GL_PROJECTION)
                self.gl2_0.glPopMatrix()
                self.gl2_0.glMatrixMode(GL_MODELVIEW)
                hits = glRenderMode(GL_RENDER)
            # self.show_statu_func(f"{len(hits)}个零件被选中", "success")
            # 在hits中找到深度最小的零件
            if self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):
                id_map = NAPart.hull_design_tab_id_map
            else:
                id_map = self.selectObjOrigin_map[self.show_3d_obj_mode].id_map
            min_depth = 100000
            min_depth_part = None
            for hit in hits:
                _name = hit.names[0]
                if _name in id_map:
                    part = id_map[_name]
                    if hit.near < min_depth:
                        min_depth = hit.near
                        min_depth_part = part
            if min_depth_part:
                return min_depth_part
        else:  # 如果是节点模式，扩大选择范围
            min_x, max_x = pos.x() - 5, pos.x() + 5
            # 对y翻转
            min_y, max_y = self.height - pos.y() - 1 - 5, self.height - pos.y() - 1 + 5
            # 使用拾取技术来确定被点击的三角形
            glSelectBuffer(2 ** 20)
            glRenderMode(GL_SELECT)
            glInitNames()
            glPushName(0)
            self.gl2_0.glViewport(0, 0, self.width, self.height)
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glPushMatrix()
            self.gl2_0.glLoadIdentity()
            aspect_ratio = self.width / self.height
            # 设置选择框
            gluPickMatrix(
                (max_x + min_x) / 2, (max_y + min_y) / 2, max_x - min_x, max_y - min_y, [0, 0, self.width, self.height]
            )
            # 设置透视投影
            gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)
            # 转换回模型视图矩阵
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            self.paintGL()
            # 恢复原来的矩阵
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glPopMatrix()
            # 转换回模型视图矩阵
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            # 获取选择框内的物体
            hits = glRenderMode(GL_RENDER)
            id_map = self.selectObjOrigin_map[self.show_3d_obj_mode].id_map
            for hit in hits:
                _name = hit.names[0]
                if _name in id_map:
                    part = id_map[_name]
                    return part

    def add_selected_objects_of_selectBox(self):
        result = []
        if not (self.select_start and self.select_end):
            return result
        # 转化为OpenGL坐标系
        min_x = min(self.select_start.x(), self.select_end.x())
        max_x = max(self.select_start.x(), self.select_end.x())
        # 对y翻转
        min_y = min(self.height - self.select_start.y() - 1, self.height - self.select_end.y() - 1)
        max_y = max(self.height - self.select_start.y() - 1, self.height - self.select_end.y() - 1)
        if max_x - min_x < 3 or max_y - min_y < 3:  # 排除过小的选择框
            return result
        # 使用拾取技术来确定被点击的三角形
        if self.view_mode == OpenGLWin.Perspective:  # 如果是透视投影模式：
            glSelectBuffer(2 ** 20)
            glRenderMode(GL_SELECT)
            glInitNames()
            glPushName(0)
            self.gl2_0.glViewport(0, 0, self.width, self.height)
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glPushMatrix()
            self.gl2_0.glLoadIdentity()  # 重置矩阵
            # 设置选择框
            gluPickMatrix(
                (max_x + min_x) / 2, (max_y + min_y) / 2, max_x - min_x, max_y - min_y, [0, 0, self.width, self.height]
            )
            # 设置透视投影
            aspect_ratio = self.width / self.height
            gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)  # 设置透视投影
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            self.paintGL()  # 重新渲染场景
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glPopMatrix()
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            hits = glRenderMode(GL_RENDER)
        else:  # 如果是正交投影模式：
            glSelectBuffer(2 ** 20)
            glRenderMode(GL_SELECT)
            glInitNames()
            glPushName(1)
            self.gl2_0.glViewport(0, 0, self.width, self.height)
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glPushMatrix()
            self.gl2_0.glLoadIdentity()
            gluPickMatrix(
                (max_x + min_x) / 2, (max_y + min_y) / 2, max_x - min_x, max_y - min_y, [0, 0, self.width, self.height]
            )
            self.gl2_0.glOrtho(-self.width / 2, self.width / 2, -self.height / 2, self.height / 2, -1000, 1000)
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            self.paintGL()
            self.gl2_0.glMatrixMode(GL_PROJECTION)
            self.gl2_0.glPopMatrix()
            self.gl2_0.glMatrixMode(GL_MODELVIEW)
            hits = glRenderMode(GL_RENDER)
        if self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):
            id_map = NAPart.hull_design_tab_id_map.copy()
        else:
            id_map = self.selectObjOrigin_map[self.show_3d_obj_mode].id_map.copy()
        for hit in hits:
            _name = hit.names[0]
            if _name in id_map:
                part = id_map[_name]
                if part not in result:
                    result.append(part)
        return result

    def singlePart_add2xzLayer(self):
        """
        以该零件根据零件关系图，扩展选区
        :return:
        """
        if self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):
            if len(self.selected_gl_objects[self.show_3d_obj_mode]) >= 1:
                # 以该零件为根，扩展选区
                for part in self.selected_gl_objects[self.show_3d_obj_mode]:
                    if part not in part.allParts_relationMap.basicMap:
                        # 找不到零件，可能是因为零件被细分后从关系图中删除了，直接跳过  # TODO: 要优化在细分零件后对关系图的替换重置函数
                        continue
                    relation_map = part.allParts_relationMap.basicMap[part]
                    # 先向前后
                    for sub_part in relation_map[CONST.FRONT]:
                        if sub_part not in self.selected_gl_objects[self.show_3d_obj_mode]:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(sub_part)
                    for sub_part in relation_map[CONST.BACK]:
                        if sub_part not in self.selected_gl_objects[self.show_3d_obj_mode]:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(sub_part)
                    # 再向左右
                    ...  # TODO: 未来要加入左右扩展

    def singlePart_add2xyLayer(self):
        """
        以该零件根据零件关系图，扩展选区
        :return:
        """
        if self.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):
            if len(self.selected_gl_objects[self.show_3d_obj_mode]) >= 1:
                for part in self.selected_gl_objects[self.show_3d_obj_mode]:
                    if part not in part.allParts_relationMap.basicMap:  # TODO: 这里不明原因，零件不在basicMap中，可能是因为撤回操作DrawMap取深拷贝的问题
                        continue
                    relation_map = part.allParts_relationMap.basicMap[part]
                    # 先向上下
                    for sub_part in relation_map[CONST.UP]:
                        if sub_part not in self.selected_gl_objects[self.show_3d_obj_mode]:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(sub_part)
                    for sub_part in relation_map[CONST.DOWN]:
                        if sub_part not in self.selected_gl_objects[self.show_3d_obj_mode]:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(sub_part)
                    # 再向左右
                    ...  # TODO: 未来要加入左右扩展
        # for part in self.selected_gl_objects[self.show_3d_obj_mode]:
        #     print(part.glWin)
        # print("=====================================")

    @staticmethod
    def get_matrix():
        """
        获取当前的坐标变换矩阵
        :return:
        """
        matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
        matrix = np.array(matrix).reshape(4, 4)
        return matrix

    # ----------------------------------------------------------------------------------------------事件

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.using_various_mode:
            # 数字1234切换显示模式
            if event.key() == Qt.Key_1:
                self.set_show_3d_obj_mode(OpenGLWin.ShowAll)
            elif event.key() == Qt.Key_2:
                self.set_show_3d_obj_mode(OpenGLWin.ShowXZ)
            elif event.key() == Qt.Key_3:
                self.set_show_3d_obj_mode(OpenGLWin.ShowXY)
            elif event.key() == Qt.Key_4:
                self.set_show_3d_obj_mode(OpenGLWin.ShowLeft)
            elif event.key() == Qt.Key_P:  # p键切换显示模式
                self.set_show_3d_obj_sub_mode(OpenGLWin.ShowObj)
            elif event.key() == Qt.Key_N:  # n键切换显示模式
                self.set_show_3d_obj_sub_mode(OpenGLWin.ShowDotNode)
        # a键摄像机目标回（0, 0, 0）
        if event.key() == Qt.Key_A:
            self.camera.change_target(QVector3D(0, 0, 0))
            self.show_statu_func("摄像机目标回到原点(a)", "success")
            self.update()
        # ====================================================================================Alt键
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            if self.show_3d_obj_mode[0] != OpenGLWin.ShowAll:
                return
            if event.key() not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                return
            # 获取当前被选中的AdjustableHull
            for selected_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                if selected_obj not in selected_obj.allParts_relationMap.basicMap:
                    continue
                selected_obj_relations = selected_obj.allParts_relationMap.basicMap[selected_obj]
                next_obj = None
                move_direction = None
                if event.key() == Qt.Key_Up:  # ==============================================Alt上键
                    up_objs = selected_obj_relations[CONST.UP]
                    if len(up_objs) != 0:
                        next_obj = list(up_objs.keys())[0]
                        move_direction = "上"
                elif event.key() == Qt.Key_Down:  # ==========================================Alt下键
                    down_objs = selected_obj_relations[CONST.DOWN]
                    if len(down_objs) != 0:
                        next_obj = list(down_objs.keys())[0]
                        move_direction = "下"
                elif (event.key() == Qt.Key_Left and self.camera.angle.x() < 0) or (
                        event.key() == Qt.Key_Right and self.camera.angle.x() > 0):  # =========Alt左键
                    front_objs = selected_obj_relations[CONST.FRONT]
                    if len(front_objs) != 0:
                        next_obj = list(front_objs.keys())[0]
                        move_direction = "前"
                elif (event.key() == Qt.Key_Right and self.camera.angle.x() < 0) or (
                        event.key() == Qt.Key_Left and self.camera.angle.x() > 0):  # =========Alt右键
                    back_objs = selected_obj_relations[CONST.BACK]
                    if len(back_objs) != 0:
                        next_obj = list(back_objs.keys())[0]
                        move_direction = "后"
                if next_obj is not None:
                    index = self.selected_gl_objects[self.show_3d_obj_mode].index(selected_obj)
                    self.selected_gl_objects[self.show_3d_obj_mode][index] = next_obj
                    self.show_statu_func(f"选区{move_direction}移", "success")
                elif len(self.selected_gl_objects[self.show_3d_obj_mode]) > 1:
                    # 删除当前选中的AdjustableHull
                    index = self.selected_gl_objects[self.show_3d_obj_mode].index(selected_obj)
                    self.selected_gl_objects[self.show_3d_obj_mode].pop(index)
                    self.show_statu_func(f"删除选区(Alt+{event.key()})", "success")
            self.paintGL()
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        elif event.angleDelta().y() > 0:
            self.camera.zoom(-0.11)
        else:
            self.camera.zoom(0.11)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        elif event.button() == Qt.LeftButton:  # 左键按下
            if self.operation_mode == OpenGLWin.Selectable:
                self.select_start = event.pos()
                self.lastPos = event.pos()
                if OperationEditing.is_editing:
                    return
                # 判断是否按下shift，如果没有按下，就清空选中列表
                if QApplication.keyboardModifiers() != Qt.ShiftModifier:
                    self.selected_gl_objects[self.show_3d_obj_mode].clear()
            else:
                self.lastPos = event.pos()
        elif event.button() == Qt.RightButton:  # 右键按下
            self.rotate_start = event.pos()
            self.lastPos = event.pos()
        elif event.button() == Qt.MidButton:  # 中键按下
            self.lastPos = event.pos()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        if event.buttons() == Qt.LeftButton:  # 左键绘制选择框
            if OperationEditing.is_editing:
                return
            self.select_end = event.pos() if self.operation_mode == OpenGLWin.Selectable else None
            self.lastPos = event.pos() if self.operation_mode == OpenGLWin.UnSelectable else None
        elif event.buttons() == Qt.RightButton or event.buttons() == Qt.MidButton:  # 右键或中键旋转
            # 如果鼠标到达屏幕边缘，光标位置就移动到另一侧
            if event.x() < 0:
                QCursor.setPos(self.mapToGlobal(QPoint(self.width - 1, event.y())))
                self.lastPos = QPoint(self.width - 1, event.y())
            elif event.x() > self.width - 1:
                QCursor.setPos(self.mapToGlobal(QPoint(0, event.y())))
                self.lastPos = QPoint(0, event.y())
            elif event.y() < 0:
                QCursor.setPos(self.mapToGlobal(QPoint(event.x(), self.height - 1)))
                self.lastPos = QPoint(event.x(), self.height - 1)
            elif event.y() > self.height - 1:
                QCursor.setPos(self.mapToGlobal(QPoint(event.x(), 0)))
                self.lastPos = QPoint(event.x(), 0)
            elif event.buttons() == Qt.MidButton:  # 中键平移
                dx = event.x() - self.lastPos.x()
                dy = event.y() - self.lastPos.y()
                self.camera.translate(dx, dy)
                self.lastPos = event.pos()
            elif event.buttons() == Qt.RightButton:  # 右键旋转
                dx = event.x() - self.lastPos.x()
                dy = event.y() - self.lastPos.y()
                self.camera.rotate(dx, dy)
                self.lastPos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        elif event.button() == Qt.LeftButton:  # 左键释放
            if self.operation_mode == OpenGLWin.Selectable:
                if OperationEditing.is_editing:
                    self.select_start = None
                    self.select_end = None
                    return
                self.select_end = event.pos()
                # if self.select_start and self.select_end:
                if abs(event.x() - self.select_start.x()) < 3 and abs(event.y() - self.select_start.y()) < 3:
                    # 作为单击事件处理，调用click拾取函数
                    _p = self.add_selected_objects_when_click()
                    add_list = [_p] if _p is not None else []
                else:
                    # 往选中列表中添加选中的物体
                    add_list = self.add_selected_objects_of_selectBox()
                for add_obj in add_list:
                    if add_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                        self.selected_gl_objects[self.show_3d_obj_mode].remove(add_obj)
                    else:
                        self.selected_gl_objects[self.show_3d_obj_mode].append(add_obj)
                self.show_statu_func(f"已选中{len(self.selected_gl_objects[self.show_3d_obj_mode])}个对象", 'process')
                self.select_start = None
                self.select_end = None

    def set_camera(self):
        gluLookAt(self.camera.pos.x(), self.camera.pos.y(), self.camera.pos.z(),
                  self.camera.tar.x(), self.camera.tar.y(), self.camera.tar.z(),
                  self.camera.up.x(), self.camera.up.y(), self.camera.up.z())

    def init_gl(self) -> None:
        version_profile2_0 = QOpenGLVersionProfile()
        version_profile2_0.setVersion(2, 0)
        self.gl2_0 = self.context().versionFunctions(version_profile2_0)
        self.init_view()  # 初始化视角
        self.init_light()  # 初始化光源
        self.init_render()  # 初始化渲染模式

    def init_light(self):
        # 添加光源
        self.gl2_0.glEnable(self.gl2_0.GL_LIGHTING)
        self.gl2_0.glEnable(self.gl2_0.GL_LIGHT0)
        # 主光源
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_POSITION, (
            self.light_pos.x(), self.light_pos.y(), self.light_pos.z(),  # 光源位置
            100.0))
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_AMBIENT, self.theme_color["主光源"][0])  # 设置环境光
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_DIFFUSE, self.theme_color["主光源"][1])  # 设置漫反射光
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_SPECULAR, self.theme_color["主光源"][2])  # 设置镜面光
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_SPOT_DIRECTION, (0.0, 0.0, 0.0))  # 设置聚光方向
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_SPOT_EXPONENT, (0.0,))  # 设置聚光指数
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_SPOT_CUTOFF, (180.0,))  # 设置聚光角度
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT0, self.gl2_0.GL_QUADRATIC_ATTENUATION, (0.0,))  # 设置二次衰减
        # 辅助光源
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_POSITION, (
            self.light_pos.x(), self.light_pos.y(), self.light_pos.z(),  # 光源位置
            100.0))
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_AMBIENT, self.theme_color["辅助光"][0])  # 设置环境光
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_DIFFUSE, self.theme_color["辅助光"][1])  # 设置漫反射光
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_SPECULAR, self.theme_color["辅助光"][1])  # 设置镜面光
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_SPOT_DIRECTION, (0.0, 0.0, 0.0))  # 设置聚光方向
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_SPOT_EXPONENT, (0.0,))  # 设置聚光指数
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_SPOT_CUTOFF, (180.0,))  # 设置聚光角度
        self.gl2_0.glLightfv(self.gl2_0.GL_LIGHT1, self.gl2_0.GL_QUADRATIC_ATTENUATION, (0.0,))  # 设置二次衰减

    def init_view(self):
        # 适应窗口大小
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.width / self.height
        gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)  # 设置透视投影
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def init_render(self):
        glShadeModel(GL_SMOOTH)  # 设置阴影平滑模式
        glClearDepth(1.0)  # 设置深度缓存
        glEnable(GL_DEPTH_TEST)  # 启用深度测试
        # 设置深度缓冲为32位
        f = QSurfaceFormat()
        f.setDepthBufferSize(32)
        self.setFormat(f)
        glDepthFunc(GL_LEQUAL)  # 所作深度测试的类型
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)  # 告诉系统对透视进行修正
        glEnable(GL_NORMALIZE)  # 启用法向量规范化
        glEnable(GL_AUTO_NORMAL)  # 启用自动法向量
        glEnable(GL_BLEND)  # 启用混合
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # 设置混合因子
        # 平滑
        glEnable(GL_POINT_SMOOTH)  # 启用点平滑
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)  # 设置点平滑提示
        glEnable(GL_LINE_SMOOTH)  # 启用线条平滑
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)  # 设置线条平滑提示
        # glEnable(GL_POLYGON_SMOOTH)  # 启用多边形平滑
        # glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST)  # 设置多边形平滑提示
        # 抗锯齿
        glEnable(GL_MULTISAMPLE)  # 启用多重采样
        glEnable(GL_SAMPLE_ALPHA_TO_COVERAGE)  # 启用alpha值对多重采样的影响
        glSampleCoverage(1, GL_TRUE)  # 设置多重采样的抗锯齿比例
        # 线性差值
        glEnable(GL_TEXTURE_2D)  # 启用纹理
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)  # 设置纹理映射的透视修正
        glHint(GL_TEXTURE_COMPRESSION_HINT, GL_NICEST)  # 设置纹理压缩提示
        glHint(GL_FRAGMENT_SHADER_DERIVATIVE_HINT, GL_NICEST)  # 设置片段着色器的提示
        #
        glEnable(GL_COLOR_MATERIAL)  # 启用颜色材质
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)  # 设置颜色材质的面和材质
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, (0.5, 0.5, 0.5, 0.5))  # 设置环境光反射光
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.5, 0.5, 0.5, 0.5))  # 设置漫反射光
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.5, 0.5, 0.5, 0.5))  # 设置镜面反射光
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, (10.0,))  # 设置镜面反射指数
        #
        # 背面剔除
        glEnable(GL_CULL_FACE)  # 启用背面剔除
        glCullFace(GL_BACK)  # 剔除背面
        glFrontFace(GL_CCW)  # 设置逆时针为正面
        glPolygonOffset(1, 1)  # 设置多边形偏移


class DesignTabGLWinMenu(QMenu):
    def __init__(self, gl_win):
        super().__init__()
        self.GlWin = gl_win
        # 设置样式
        self.style = f"""
            QMenu {{
                background-color: {BG_COLOR0};
                color: {FG_COLOR0};
                border: 5px solid {BG_COLOR0};
                border-radius: 8px;
            }}
            QMenu::item {{
                background-color: {BG_COLOR0};
                color: {FG_COLOR0};
            }}
            QMenu::item:disabled {{
                background-color: {BG_COLOR0};
                color: {GRAY};
            }}
            QMenu::item:selected {{
                background-color: {BG_COLOR1};
                color: {FG_COLOR0}; 
            }}
        """
        self.setStyleSheet(self.style)
        # 右键菜单
        self.expand_select_area_A = QAction("选区扩展 Ctrl+E", self)
        self.edit_select_area_A = QAction("编辑选区 Shift+E", self)
        self.undo_A = QAction("撤销 Ctrl+Z", self)
        self.redo_A = QAction("重做 Ctrl+Shift+Z", self)
        self.delete_selected_objects_A = QAction("删除 Delete", self)
        self.add_selected_objects_A = QAction("添加 Ctrl+Shift+A", self)
        self.import_selected_objects_A = QAction("导入 I", self)
        self.export_selected_objects_A = QAction("导出 O", self)
        # 扩展选区子菜单
        self.add_selected_objects_menu = QMenu("扩大选区", self)
        self.expand_select_area_A.setMenu(self.add_selected_objects_menu)  # 添加动作
        self.add_selected_objects_A_y = QAction("至xz水平面 Ctrl+E+Y", self.add_selected_objects_menu)
        self.add_selected_objects_A_z = QAction("至xy纵截面 Ctrl+E+Z", self.add_selected_objects_menu)
        self.add_selected_objects_menu.addAction(self.add_selected_objects_A_y)
        self.add_selected_objects_menu.addAction(self.add_selected_objects_A_z)

        self.actions = {
            self.expand_select_area_A: False,
            self.edit_select_area_A: False,
            self.undo_A: False,
            self.redo_A: False,
            self.delete_selected_objects_A: False,
            self.add_selected_objects_A: False,
            self.import_selected_objects_A: True,
            self.export_selected_objects_A: True
        }
        for action, available in self.actions.items():
            action.setEnabled(available)
            self.addAction(action)

    # noinspection PyUnresolvedReferences
    def connect_basic_funcs(self, undo_func, redo_func, delete_func, add_func, import_func, export_func):
        self.undo_A.triggered.connect(undo_func)
        self.redo_A.triggered.connect(redo_func)
        self.delete_selected_objects_A.triggered.connect(delete_func)
        self.add_selected_objects_A.triggered.connect(add_func)
        self.import_selected_objects_A.triggered.connect(import_func)
        self.export_selected_objects_A.triggered.connect(export_func)

    # noinspection PyUnresolvedReferences
    def connect_expand_select_area_funcs(self, add2xzLayer_func, add2xyLayer_func):
        self.add_selected_objects_A_y.triggered.connect(add2xzLayer_func)
        self.add_selected_objects_A_z.triggered.connect(add2xyLayer_func)


class OpenGLWin2(QOpenGLWidget):
    # 操作模式
    Selectable = 1
    UnSelectable = 0
    # 3D物体显示模式
    ShowAll = 11
    ShowXZ = 22
    ShowXY = 33
    ShowLeft = 44
    # 选择模式（子模式）
    ShowObj = 111
    ShowDotNode = 222

    def __init__(self, camera_sensitivity, using_various_mode=False, show_statu_func=None):
        self.show_statu_func = show_statu_func
        self.operation_mode = OpenGLWin.Selectable
        self.show_3d_obj_mode = (OpenGLWin.ShowAll, OpenGLWin.ShowObj)
        self.using_various_mode = using_various_mode  # 是否使用全部四种显示模式

        super().__init__()

        # ===================================================================================设置基本参数
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)  # 设置十字光标
        self.setFocusPolicy(Qt.StrongFocus)  # 设置焦点策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # 设置右键菜单策略
        self.theme_color = GLTheme
        self.lightPos = QVector3D(5000, 3000, 5000)
        self.lightColor = QVector3D(1, 1, 1)
        self.fovy = 45
        # ========================================================================================3D物体
        # 设置顶点数据
        rd = 10.0
        self.vertices = [
            -rd, -rd, rd, rd, -rd, rd, rd, rd, rd, -rd, rd, rd,
            -rd, -rd, -rd, -rd, rd, -rd, rd, rd, -rd, rd, -rd, -rd,
            -rd, -rd, rd, -rd, rd, rd, -rd, rd, -rd, -rd, -rd, -rd,
            rd, -rd, -rd, rd, rd, -rd, rd, rd, rd, rd, -rd, rd,
            -rd, rd, rd, rd, rd, rd, rd, rd, -rd, -rd, rd, -rd,
            -rd, -rd, rd, -rd, -rd, -rd, rd, -rd, -rd, rd, -rd, rd
        ]
        self.quads_indices = [
            0, 1, 2, 3,  # 前面
            4, 5, 6, 7,  # 后面
            8, 9, 10, 11,  # 左面
            12, 13, 14, 15,  # 右面
            16, 17, 18, 19,  # 上面
            20, 21, 22, 23,  # 下面
        ]
        self.quads_normals = [
            0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1,
            0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1,
            1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0,
            -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0, 0,
            0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0,
            0, -1, 0, 0, -1, 0, 0, -1, 0, 0, -1, 0
        ]
        # 集合
        self.environment_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        # 四种不同模式下显示的物体
        self.all_3d_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        if self.using_various_mode:
            self.xz_layer_obj = []  # 横剖面模式
            self.xy_layer_obj = []  # 纵剖面模式
            self.left_view_obj = []  # 左视图线框模式
            self.xzLayer_node = []  # 所有横剖面的节点
            self.xyLayer_node = []  # 所有纵剖面的节点
            self.leftView_node = []  # 所有左视图的节点
            self.showMode_showSet_map = {  # 正常显示的映射
                (OpenGLWin.ShowAll, OpenGLWin.ShowObj): self.all_3d_obj,
                (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode): self.all_3d_obj,
                (OpenGLWin.ShowXZ, OpenGLWin.ShowObj): self.xz_layer_obj,
                (OpenGLWin.ShowXZ, OpenGLWin.ShowDotNode): self.xz_layer_obj,
                (OpenGLWin.ShowXY, OpenGLWin.ShowObj): self.xy_layer_obj,
                (OpenGLWin.ShowXY, OpenGLWin.ShowDotNode): self.xy_layer_obj,
                (OpenGLWin.ShowLeft, OpenGLWin.ShowObj): self.left_view_obj,
                (OpenGLWin.ShowLeft, OpenGLWin.ShowDotNode): self.left_view_obj
            }
        self.prj_all_parts = []  # 船体所有零件，用于选中时遍历
        for gl_plot_obj in self.all_3d_obj["钢铁"]:
            if isinstance(gl_plot_obj, NAHull):
                for _color, parts in gl_plot_obj.ColorPartsMap.items():
                    for part in parts:
                        self.prj_all_parts.append(part)
                self.xz_layer_obj.extend(gl_plot_obj.xzLayers)
                self.xy_layer_obj.extend(gl_plot_obj.xyLayers)
                self.left_view_obj.extend(gl_plot_obj.leftViews)
        self.selectObjOrigin_map = {  # 从哪个集合中取出选中的对象
            (OpenGLWin.ShowAll, OpenGLWin.ShowObj): NAPart,
            (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode): NAPartNode,
            (OpenGLWin.ShowXZ, OpenGLWin.ShowObj): NaHullXZLayer,
            (OpenGLWin.ShowXZ, OpenGLWin.ShowDotNode): NAXZLayerNode,
            (OpenGLWin.ShowXY, OpenGLWin.ShowObj): NaHullXYLayer,
            (OpenGLWin.ShowXY, OpenGLWin.ShowDotNode): NAXYLayerNode,
            (OpenGLWin.ShowLeft, OpenGLWin.ShowObj): NaHullLeftView,
            (OpenGLWin.ShowLeft, OpenGLWin.ShowDotNode): NALeftViewNode
        }
        self.selected_gl_objects = {
            (OpenGLWin.ShowAll, OpenGLWin.ShowObj): [],  # 选中的零件
            (OpenGLWin.ShowAll, OpenGLWin.ShowDotNode): [],  # 选中的节点
            (OpenGLWin.ShowXZ, OpenGLWin.ShowObj): [],  # 选中的xz层
            (OpenGLWin.ShowXZ, OpenGLWin.ShowDotNode): [],  # 选中的节点
            (OpenGLWin.ShowXY, OpenGLWin.ShowObj): [],  # 选中的xy层
            (OpenGLWin.ShowXY, OpenGLWin.ShowDotNode): [],  # 选中的节点
            (OpenGLWin.ShowLeft, OpenGLWin.ShowObj): [],  # 选中的左视图
            (OpenGLWin.ShowLeft, OpenGLWin.ShowDotNode): [],  # 选中的节点
        }
        # ========================================================================================着色器
        self.shaderProgram = None
        self.vao = None
        self.plot_data = {
            GL_QUADS: {"dots": QByteArray(), "normal": QByteArray()},
            GL_TRIANGLES: {"dots": QByteArray(), "normal": QByteArray()},
            GL_LINES: {"dots": QByteArray(), "normal": QByteArray()},
            GL_POINTS: {"dots": QByteArray(), "normal": QByteArray()},
        }
        self.vbo_all = {
            GL_QUADS: {"dots": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer),
                       "normal": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)},
            GL_TRIANGLES: {"dots": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer),
                           "normal": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)},
            GL_LINES: {"dots": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer),
                       "normal": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)},
            GL_POINTS: {"dots": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer),
                        "normal": QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)},
        }
        # ========================================================================================视角
        self.width = QOpenGLWidget.width(self)
        self.height = QOpenGLWidget.height(self)
        self.lastPos = None  # 上一次鼠标位置
        self.select_start = None  # 选择框起点
        self.select_end = None  # 选择框终点
        self.camera = Camera(self.width, self.height, camera_sensitivity)
        # ========================================================================================子控件
        if self.using_various_mode:
            self.mod1_button = QToolButton(self)
            self.mod2_button = QToolButton(self)
            self.mod3_button = QToolButton(self)
            self.mod4_button = QToolButton(self)
            self.subMod1_button = QToolButton(self)
            self.subMod2_button = QToolButton(self)
            self.ModBtWid = 55
            self.mod_buttons = [self.mod1_button, self.mod2_button, self.mod3_button, self.mod4_button]
            self.subMod_buttons = [self.subMod1_button, self.subMod2_button]
            self.init_mode_toolButton()

    def paintGL(self):
        if QOpenGLWidget.width(self) != self.width or QOpenGLWidget.height(self) != self.height:
            # 获取窗口大小
            width = QOpenGLWidget.width(self)
            height = QOpenGLWidget.height(self)
            if width != self.width or height != self.height:
                self.width = width
                self.height = height
                self.resizeGL(width, height)
                if self.using_various_mode:
                    right = QOpenGLWidget.width(self) - 10 - 4 * (self.ModBtWid + 10)
                    sub_right = QOpenGLWidget.width(self) - 10 - 2 * (self.ModBtWid + 35)
                    for button in self.mod_buttons:
                        index = self.mod_buttons.index(button)
                        button.setGeometry(right + 10 + index * (self.ModBtWid + 10), 10, self.ModBtWid, 28)
                    for button in self.subMod_buttons:
                        index = self.subMod_buttons.index(button)
                        button.setGeometry(sub_right + 10 + index * (self.ModBtWid + 35), 50, self.ModBtWid + 25, 23)
        # 清除屏幕
        glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        # 在光源位置绘制一个扩散光点  # TODO:
        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("view", self.viewMatrix())  # 设置视角
        self.shaderProgram.setUniformValue("model", self.modelMatrix())  # 设置模型矩阵
        self.shaderProgram.setUniformValue("viewPos", self.camera.pos)  # 设置视角位置
        self.shaderProgram.setUniformValue("objectColor", QVector3D(0.5, 0.5, 0.5))  # 设置物体颜`

        # 绘制六个面
        self.vao.bind()
        glDrawElements(GL.GL_QUADS, len(self.quads_indices), GL.GL_UNSIGNED_INT, self.quads_indices)
        self.vao.release()
        # 绘制选区
        if self.select_start and self.select_end:
            self.draw_select_box()
            # 绘制被选中的物体
            # self.draw_selected_objects()

    def initializeGL(self):
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

        i = 0
        for _draw_method, vbo_map in self.vbo_all.items():
            if _draw_method == GL_QUADS:
                self.plot_data[_draw_method]["dots"] = QByteArray(struct.pack('f' * len(self.vertices), *self.vertices))
                self.plot_data[_draw_method]["normal"] = QByteArray(
                    struct.pack('f' * len(self.quads_normals), *self.quads_normals))
            for vbo_type, vbo in vbo_map.items():
                if _draw_method != GL_QUADS:
                    continue
                vbo.create()
                vbo.bind()
                vbo.setUsagePattern(QOpenGLBuffer.StaticDraw)
                vbo.allocate(self.plot_data[_draw_method][vbo_type].data(),
                             self.plot_data[_draw_method][vbo_type].size())
                self.shaderProgram.enableAttributeArray(i)  # 启用顶点属性数组
                self.shaderProgram.setAttributeBuffer(i, GL.GL_FLOAT, 0, 3, 0)  # 设置顶点属性数组
                vbo.release()
                i += 1
        self.vao.release()

    def resizeGL(self, w, h):
        # 设置视口和投影矩阵
        glViewport(0, 0, w, h)
        _projection = self.projectionMatrix()
        self.shaderProgram.bind()
        self.shaderProgram.setUniformValue("projection", _projection)

    def set_show_3d_obj_mode(self, father_mode):
        """
        修改父模式，不修改子模式
        :param father_mode: 父模式
        :return:
        """
        sub_mode = self.show_3d_obj_mode[1]
        self.show_3d_obj_mode = (father_mode, sub_mode)
        if father_mode == OpenGLWin.ShowAll:
            self.mod1_button.setChecked(True)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(False)
            self.show_statu_func("切换至全视图模式 (1)", "success")
        elif father_mode == OpenGLWin.ShowXZ:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(True)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(False)
            self.show_statu_func("切换至横剖面模式 (2)", "success")
        elif father_mode == OpenGLWin.ShowXY:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(True)
            self.mod4_button.setChecked(False)
            self.show_statu_func("切换至纵剖面模式 (3)", "success")
        elif father_mode == OpenGLWin.ShowLeft:
            self.mod1_button.setChecked(False)
            self.mod2_button.setChecked(False)
            self.mod3_button.setChecked(False)
            self.mod4_button.setChecked(True)
            self.show_statu_func("切换至左视图模式 (4)", "success")
        self.update()

    def set_show_3d_obj_sub_mode(self, sub_mode):
        father_mode = self.show_3d_obj_mode[0]
        self.show_3d_obj_mode = (father_mode, sub_mode)
        if sub_mode == OpenGLWin.ShowObj:
            self.subMod1_button.setChecked(True)
            self.subMod2_button.setChecked(False)
            self.show_statu_func("切换至部件模式 (1)", "success")
        elif sub_mode == OpenGLWin.ShowDotNode:
            self.subMod1_button.setChecked(False)
            self.subMod2_button.setChecked(True)
            self.show_statu_func("切换至节点模式 (2)", "success")
        self.update()

    # noinspection PyUnresolvedReferences
    def init_mode_toolButton(self):
        self.mod1_button.setText("全视图1")
        self.mod2_button.setText("横剖面2")
        self.mod3_button.setText("纵剖面3")
        self.mod4_button.setText("左视图4")
        self.subMod1_button.setText("部件模式P")
        self.subMod2_button.setText("节点模式N")
        self.mod1_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowAll))
        self.mod2_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowXZ))
        self.mod3_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowXY))
        self.mod4_button.clicked.connect(lambda: self.set_show_3d_obj_mode(OpenGLWin.ShowLeft))
        self.subMod1_button.clicked.connect(lambda: self.set_show_3d_obj_sub_mode(OpenGLWin.ShowObj))
        self.subMod2_button.clicked.connect(lambda: self.set_show_3d_obj_sub_mode(OpenGLWin.ShowDotNode))
        for button in self.mod_buttons + self.subMod_buttons:
            button.setCheckable(True)
            button.setFont(FONT_8)
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
        self.subMod1_button.setChecked(True)

    def draw_select_box(self):
        """
        在屏幕坐标系绘制选择框
        """
        # 获取选择框的坐标和尺寸
        x1, y1 = self.select_start.x(), self.select_start.y()
        x2, y2 = self.select_end.x(), self.select_end.y()
        width, height = abs(x2 - x1), abs(y2 - y1)
        # 创建QPainter对象
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # 可选的抗锯齿设置
        # 设置选择框的样式
        _col = self.theme_color["选择框"][0]
        _col = QColor(_col[0] * 255, _col[1] * 255, _col[2] * 255, _col[3] * 255)
        # 大间距的虚线
        pen = QPen(_col)
        pen.setDashPattern([6, 6])
        painter.setPen(pen)
        # 绘制选择框
        painter.drawRect(x1, y1, width, height)
        # 绘制半透明的填充
        _col2 = QColor(255, 255, 255, 32)
        painter.fillRect(x1, y1, width, height, _col2)
        # 结束绘制
        painter.end()

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
        # 设置光照
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [self.lightPos.x(), self.lightPos.y(), self.lightPos.z(), 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.5, 0.5, 0.5, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        # 设置材质
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.5, 0.5, 0.5, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)

    def add_selected_objects_when_click(self):
        pos = self.select_start
        if self.show_3d_obj_mode[1] == OpenGLWin.ShowObj:
            # 将屏幕坐标点转换为OpenGL坐标系中的坐标点
            _x, _y = pos.x(), self.height - pos.y() - 1
            # 使用拾取技术来确定被点击的三角形
            glSelectBuffer(512)
            glRenderMode(GL_SELECT)
            glInitNames()
            glPushName(0)
            glViewport(0, 0, self.width, self.height)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluPickMatrix(_x, _y, 1, 1, [0, 0, self.width, self.height])
            # 设置透视投影
            aspect_ratio = self.width / self.height
            gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)  # 设置透视投影
            glMatrixMode(GL_MODELVIEW)
            self.paintGL()  # 重新渲染场景
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            hits = glRenderMode(GL_RENDER)
            # self.show_statu_func(f"{len(hits)}个零件被选中", "success")
            # 在hits中找到深度最小的零件
            id_map = self.selectObjOrigin_map[self.show_3d_obj_mode].id_map
            min_depth = 100000
            min_depth_part = None
            for hit in hits:
                _name = hit.names[0]
                if _name in id_map:
                    part = id_map[_name]
                    if hit.near < min_depth:
                        min_depth = hit.near
                        min_depth_part = part
            if min_depth_part:
                return min_depth_part
        else:  # 如果是节点模式，扩大选择范围
            min_x, max_x = pos.x() - 5, pos.x() + 5
            # 对y翻转
            min_y, max_y = self.height - pos.y() - 1 - 5, self.height - pos.y() - 1 + 5
            # 使用拾取技术来确定被点击的三角形
            glSelectBuffer(128)
            glRenderMode(GL_SELECT)
            glInitNames()
            glPushName(0)
            glViewport(0, 0, self.width, self.height)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            aspect_ratio = self.width / self.height
            # 设置选择框
            gluPickMatrix(
                (max_x + min_x) / 2, (max_y + min_y) / 2, max_x - min_x, max_y - min_y, [0, 0, self.width, self.height]
            )
            # 设置透视投影
            gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)
            # 转换回模型视图矩阵
            glMatrixMode(GL_MODELVIEW)
            self.paintGL()
            # 恢复原来的矩阵
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            # 转换回模型视图矩阵
            glMatrixMode(GL_MODELVIEW)
            # 获取选择框内的物体
            hits = glRenderMode(GL_RENDER)
            id_map = self.selectObjOrigin_map[self.show_3d_obj_mode].id_map
            for hit in hits:  # TODO: 如果不舍弃最后一个，会把一个其他零件也选中，原因未知
                _name = hit.names[0]
                if _name in id_map:
                    part = id_map[_name]
                    return part

    def add_selected_objects_of_selectBox(self):
        result = []
        if not (self.select_start and self.select_end):
            return result
        # 转化为OpenGL坐标系
        min_x = min(self.select_start.x(), self.select_end.x())
        max_x = max(self.select_start.x(), self.select_end.x())
        # 对y翻转
        min_y = min(self.height - self.select_start.y() - 1, self.height - self.select_end.y() - 1)
        max_y = max(self.height - self.select_start.y() - 1, self.height - self.select_end.y() - 1)
        if max_x - min_x < 3 or max_y - min_y < 3:  # 排除过小的选择框
            return result
        # 使用拾取技术来确定被点击的三角形
        glSelectBuffer(2 ** 20)
        glRenderMode(GL_SELECT)
        glInitNames()
        glPushName(0)
        glViewport(0, 0, self.width, self.height)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        aspect_ratio = self.width / self.height
        # 设置选择框
        gluPickMatrix(
            (max_x + min_x) / 2, (max_y + min_y) / 2, max_x - min_x, max_y - min_y, [0, 0, self.width, self.height]
        )
        # 设置透视投影
        gluPerspective(self.fovy, aspect_ratio, 0.1, 2000.0)
        # 转换回模型视图矩阵
        glMatrixMode(GL_MODELVIEW)
        self.paintGL()
        # 恢复原来的矩阵
        glMatrixMode(GL_PROJECTION)
        # glPopMatrix()
        # 转换回模型视图矩阵
        glMatrixMode(GL_MODELVIEW)
        # 获取选择框内的物体
        hits = glRenderMode(GL_RENDER)
        id_map = self.selectObjOrigin_map[self.show_3d_obj_mode].id_map
        for hit in hits[:-1]:  # TODO: 如果不舍弃最后一个，会把一个其他零件也选中，原因未知
            _name = hit.names[0]
            if _name in id_map:
                part = id_map[_name]
                if part not in result:
                    result.append(part)
        return result

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.using_various_mode:
            # 数字1234切换显示模式
            if event.key() == Qt.Key_1:
                self.set_show_3d_obj_mode(OpenGLWin.ShowAll)
            elif event.key() == Qt.Key_2:
                self.set_show_3d_obj_mode(OpenGLWin.ShowXZ)
            elif event.key() == Qt.Key_3:
                self.set_show_3d_obj_mode(OpenGLWin.ShowXY)
            elif event.key() == Qt.Key_4:
                self.set_show_3d_obj_mode(OpenGLWin.ShowLeft)
            elif event.key() == Qt.Key_P:  # p键切换显示模式
                self.set_show_3d_obj_sub_mode(OpenGLWin.ShowObj)
            elif event.key() == Qt.Key_N:  # n键切换显示模式
                self.set_show_3d_obj_sub_mode(OpenGLWin.ShowDotNode)
        # a键摄像机目标回（0, 0, 0）
        if event.key() == Qt.Key_A:
            self.camera.change_target(QVector3D(0, 0, 0))
            self.show_statu_func("摄像机目标回到原点(a)", "success")
            self.update()
        # ====================================================================================Alt键
        if QApplication.keyboardModifiers() == Qt.AltModifier:
            if self.show_3d_obj_mode[0] != OpenGLWin.ShowAll:
                return
            if event.key() not in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                return
            # 获取当前被选中的AdjustableHull
            for selected_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                selected_obj_relations = selected_obj.allParts_relationMap.basicMap[selected_obj]
                next_obj = None
                move_direction = None
                if event.key() == Qt.Key_Up:  # ==============================================Alt上键
                    up_objs = selected_obj_relations[CONST.UP]
                    if len(up_objs) != 0:
                        next_obj = list(up_objs.keys())[0]
                        move_direction = "上"
                elif event.key() == Qt.Key_Down:  # ==========================================Alt下键
                    down_objs = selected_obj_relations[CONST.DOWN]
                    if len(down_objs) != 0:
                        next_obj = list(down_objs.keys())[0]
                        move_direction = "下"
                elif (event.key() == Qt.Key_Left and self.camera.angle.x() < 0) or (
                        event.key() == Qt.Key_Right and self.camera.angle.x() > 0):  # =========Alt左键
                    front_objs = selected_obj_relations[CONST.FRONT]
                    if len(front_objs) != 0:
                        next_obj = list(front_objs.keys())[0]
                        move_direction = "前"
                elif (event.key() == Qt.Key_Right and self.camera.angle.x() < 0) or (
                        event.key() == Qt.Key_Left and self.camera.angle.x() > 0):  # =========Alt右键
                    back_objs = selected_obj_relations[CONST.BACK]
                    if len(back_objs) != 0:
                        next_obj = list(back_objs.keys())[0]
                        move_direction = "后"
                if next_obj is not None:
                    index = self.selected_gl_objects[self.show_3d_obj_mode].index(selected_obj)
                    self.selected_gl_objects[self.show_3d_obj_mode][index] = next_obj
                    self.show_statu_func(f"选区{move_direction}移(Alt+{event.key()})", "success")
                elif len(self.selected_gl_objects[self.show_3d_obj_mode]) > 1:
                    # 删除当前选中的AdjustableHull
                    index = self.selected_gl_objects[self.show_3d_obj_mode].index(selected_obj)
                    self.selected_gl_objects[self.show_3d_obj_mode].pop(index)
                    self.show_statu_func(f"删除选区(Alt+{event.key()})", "success")
        self.update()

    def mousePressEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        elif event.button() == Qt.LeftButton:  # 左键按下
            if self.operation_mode == OpenGLWin.Selectable:
                self.select_start = event.pos()
                self.lastPos = event.pos()
                # 判断是否按下shift，如果没有按下，就清空选中列表
                if QApplication.keyboardModifiers() != Qt.ShiftModifier:
                    self.selected_gl_objects[self.show_3d_obj_mode].clear()
                    add_part = self.add_selected_objects_when_click()
                    if add_part is not None:
                        self.selected_gl_objects[self.show_3d_obj_mode].append(add_part)
                else:  # shift按下时，判断是否点击到了已经选中的物体
                    add_part = self.add_selected_objects_when_click()
                    if add_part is not None:
                        if add_part in self.selected_gl_objects[self.show_3d_obj_mode]:
                            self.selected_gl_objects[self.show_3d_obj_mode].remove(add_part)
                        else:
                            self.selected_gl_objects[self.show_3d_obj_mode].append(add_part)
            else:
                self.lastPos = event.pos()
        elif event.button() == Qt.MidButton:
            self.lastPos = event.pos()
        elif event.button() == Qt.RightButton:
            self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        elif event.buttons() & Qt.LeftButton:
            # 如果shift没有按下，清空选中列表
            if QApplication.keyboardModifiers() != Qt.ShiftModifier and not self.select_end:
                self.selected_gl_objects[self.show_3d_obj_mode].clear()
            self.select_end = event.pos() if self.operation_mode == OpenGLWin.Selectable else None
            self.lastPos = event.pos() if self.operation_mode == OpenGLWin.UnSelectable else None
            self.update()
        elif event.buttons() & Qt.MidButton:
            dx = event.x() - self.lastPos.x()
            dy = event.y() - self.lastPos.y()
            self.camera.translate(dx, dy)
            self.lastPos = event.pos()
            self.update()
        elif event.buttons() & Qt.RightButton:
            dx = event.x() - self.lastPos.x()
            dy = event.y() - self.lastPos.y()
            self.camera.rotate(dx, dy)
            self.lastPos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if QApplication.keyboardModifiers() == Qt.AltModifier:  # Alt按下的时候，不移动视角
            return
        elif event.button() == Qt.LeftButton:  # 左键释放
            if self.operation_mode == OpenGLWin.Selectable:
                if self.select_start and self.select_end:
                    # # 往选中列表中添加选中的物体  # TODO: 选中框选中的物体
                    # add_list = self.add_selected_objects_of_selectBox()
                    # for add_obj in add_list:
                    #     if add_obj in self.selected_gl_objects[self.show_3d_obj_mode]:
                    #         self.selected_gl_objects[self.show_3d_obj_mode].remove(add_obj)
                    #     else:
                    #         self.selected_gl_objects[self.show_3d_obj_mode].append(add_obj)
                    ...
                self.select_start = None
                self.select_end = None
        self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.camera.zoom(-0.11)
        else:
            self.camera.zoom(0.11)
        self.update()
