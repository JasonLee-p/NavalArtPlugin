from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtGui import QMouseEvent, QWheelEvent
from PyQt5.QtGui import QOpenGLVersionProfile

# from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GLU import gluPerspective, gluLookAt, gluProject
# from OpenGL.raw.GL.VERSION.GL_2_0 import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
from OpenGL.raw.GL.VERSION.GL_1_0 import GL_PROJECTION, GL_MODELVIEW, GL_LINE_STIPPLE

from OpenGL_objs import *
from GUI.QtGui import *

# 顶点着色器代码
VERTEX_SHADER = """
#version 330
layout(location = 0) in vec3 position;
void main() {
    gl_Position = vec4(position, 1.0);
}
"""

# 片段着色器代码（包括FXAA抗锯齿）
FRAGMENT_SHADER = """
#version 330
uniform sampler2D tex;

out vec4 fragColor;

void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 resolution = vec2(800.0, 600.0);  // 设置分辨率

    vec3 color = texture(tex, fragCoord.xy / resolution).rgb;

    // FXAA抗锯齿
    vec3 luma = vec3(0.299, 0.587, 0.114);
    float lumaNW = dot(texture(tex, (fragCoord.xy + vec2(-1.0, -1.0)) / resolution).rgb, luma);
    float lumaNE = dot(texture(tex, (fragCoord.xy + vec2(1.0, -1.0)) / resolution).rgb, luma);
    float lumaSW = dot(texture(tex, (fragCoord.xy + vec2(-1.0, 1.0)) / resolution).rgb, luma);
    float lumaSE = dot(texture(tex, (fragCoord.xy + vec2(1.0, 1.0)) / resolution).rgb, luma);
    float lumaM = dot(color, luma);

    vec2 dir = vec2(lumaNW + lumaNE - lumaSW - lumaSE, lumaNW + lumaSW - lumaNE - lumaSE);
    vec2 offset = dir * vec2(1.0 / resolution.x, 1.0 / resolution.y);

    vec3 rgbA = 0.5 * (
        texture(tex, fragCoord.xy / resolution + offset).rgb +
        texture(tex, fragCoord.xy / resolution - offset).rgb
    );

    vec3 rgbB = rgbA * 0.5 + 0.25 * (
        texture(tex, fragCoord.xy / resolution + offset * 2.0).rgb +
        texture(tex, fragCoord.xy / resolution - offset * 2.0).rgb
    );

    fragColor = vec4(mix(rgbA, rgbB, 0.5), 1.0);
}
"""


class OpenGLWin(QOpenGLWidget):
    Selectable = 1
    UnSelectable = 0

    def __init__(self, camera_sensitivity):
        self.mode = OpenGLWin.Selectable
        super(OpenGLWin, self).__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.width = WinWid - 365
        self.height = WinHei - 200
        self.setMaximumSize(self.width, self.height)
        self.theme_color = GLTheme
        self.light_pos = QVector3D(1000, 700, 1000)
        self.fovy = 45
        self.gl = None
        self.texture = None
        self.shaderProgram = None
        self.environment_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}
        self.selected_lines_obj = []
        self.all_3d_obj = {"钢铁": [], "海面": [], "海底": [], "甲板": [], "光源": [], "船底": []}

        # 事件
        self.camera = Camera(self.width, self.height, camera_sensitivity)
        self.lastPos = QPoint()
        self.select_start = None
        self.select_end = None
        self.selected_lines = []
        self.all_gl_objects = GLObject.all_objects

    def initializeGL(self) -> None:
        self.init_gl()
        self.gl.glClearColor(*self.theme_color["背景"])
        # 基础物体
        self.environment_obj["海面"].append(GridLine(
            self.gl, scale=10, num=50, central=(0, 0, 0), color=(0.1, 0.2, 0.5, 1)))
        # self.environment_obj["海底"].append(GridLine(
        #     self.gl, scale=100, num=5, central=(0, -100, 0), color=(0.1, 0.2, 0.5, 1)))
        self.environment_obj["光源"].append(LightSphere(self.gl, central=self.light_pos, radius=20))

    def paintGL(self) -> None:
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
        self.gl.glLoadIdentity()
        self.gl.glDisable(GL_LINE_STIPPLE)  # 禁用虚线模式
        self.set_camera()

        for mt, objs in self.environment_obj.items():
            for obj in objs:
                obj.draw(self.gl, material=mt, theme_color=self.theme_color)

        for mt, objs in self.all_3d_obj.items():
            for obj in objs:
                obj.draw(self.gl, material=mt, theme_color=self.theme_color)

        for obj in self.selected_lines_obj:
            obj.draw(self.gl, material="选择框", theme_color=self.theme_color)

        self.draw_coordinate()
        self.gl.glEnd()
        if self.select_start and self.select_end:
            self.draw_select_box()

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
        self.gl.glColor4f(*self.theme_color["选择框"])
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

    def draw_coordinate(self):
        """
        在左下角另外设置一个三维投影，用于指示实时坐标轴方向，视角跟着self.camera走
        """
        # 保存当前的矩阵模式
        self.gl.glMatrixMode(GL_PROJECTION)
        self.gl.glPushMatrix()
        self.gl.glLoadIdentity()
        # 为坐标轴设置正交投影
        self.gl.glOrtho(0, 50, 0, 50, -1, 1)  # 根据需要调整值
        # 保存当前的矩阵模式和矩阵
        self.gl.glMatrixMode(GL_MODELVIEW)
        self.gl.glPushMatrix()
        self.gl.glLoadIdentity()
        # 绘制坐标轴
        self.gl.glBegin(self.gl.GL_LINES)
        self.gl.glLineWidth(10)
        # # X轴
        # self.gl.glColor3f(1.0, 0.0, 0.0)  # 红色
        # self.gl.glVertex2f(0, 0)
        # self.gl.glVertex2f(100, 0)
        # # Y轴
        # self.gl.glColor3f(0.0, 1.0, 0.0)  # 绿色
        # self.gl.glVertex2f(0, 0)
        # self.gl.glVertex2f(0, 100)
        # # Z轴
        # self.gl.glColor3f(0.0, 0.0, 1.0)  # 蓝色
        # self.gl.glVertex3f(0, 0, 0)
        # self.gl.glVertex3f(0, 0, 100)
        # # 原点
        # self.gl.glColor3f(1.0, 1.0, 1.0)  # 白色
        # self.gl.glVertex3f(0, 0, 0)
        # self.gl.glVertex3f(0, 0, 0)
        self.gl.glEnd()
        # 恢复原来的矩阵模式和矩阵
        self.gl.glMatrixMode(GL_PROJECTION)
        self.gl.glPopMatrix()
        self.gl.glMatrixMode(GL_MODELVIEW)
        self.gl.glPopMatrix()

    def get_selected_objects(self):
        if self.select_start and self.select_end:
            min_x = min(self.select_start.x(), self.select_end.x())
            max_x = max(self.select_start.x(), self.select_end.x())
            min_y = min(self.select_start.y(), self.select_end.y())
            max_y = max(self.select_start.y(), self.select_end.y())

            for objs in self.all_3d_obj.values():
                for obj in objs:
                    pass  # TODO: 选中的物体
            # 高亮显示选中的线
            for dot_set in self.selected_lines:
                obj = LineGroupObject(self.gl)
                obj.lines = {"0": [(1, 0.2, 0), 2, dot_set]}
                self.selected_lines_obj.append(obj)

    def world_to_screen(self, pos: QVector3D) -> QPoint:
        # 获取当前的模型视图矩阵、投影矩阵和视口
        model_view = self.gl.glGetDoublev(self.gl.GL_MODELVIEW_MATRIX)
        projection = self.gl.glGetDoublev(self.gl.GL_PROJECTION_MATRIX)
        viewport = self.gl.glGetIntegerv(self.gl.GL_VIEWPORT)
        # 将世界坐标转换为屏幕坐标
        screen_coords = gluProject(pos.x(), pos.y(), pos.z(), model_view, projection, viewport)
        return QPoint(screen_coords[0] - 1, self.height - screen_coords[1] - 1)  # TODO:

    # ----------------------------------------------------------------------------------------------事件

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self.camera.zoom(-0.2)
        else:
            self.camera.zoom(0.2)
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:  # 左键按下
            self.selected_lines.clear()
            self.selected_lines_obj.clear()
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
                self.get_selected_objects() if self.mode == OpenGLWin.Selectable else None
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
            100.0))  # Q: 这个参数如果我写100会怎样？
        # A: 会变成一个很亮的点光源
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
