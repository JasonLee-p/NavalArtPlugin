"""
    本文件包含了一些OpenGL的实体类，包括：
    1. 线段组对象
    2. 立体对象
    3. 大面对象
    4. 平面对象
    5. 立方体对象
    6. 光源球对象
    7. PTB进阶船壳对象
    8. NA船体对象
    9. 摄像机对象
"""

# 标准库
import math
from abc import abstractmethod
# 第三方库
import numpy as np
from PyQt5.QtGui import QVector3D, QMatrix4x4
# 自定义库
from NA_design_reader import ReadNA, AdjustableHull
from PTB_design_reader import ReadPTB


def get_normal(dot1, dot2, dot3, center=None):
    """
    计算三角形的法向量，输入为元组
    :param dot1: 元组，三角形的第一个点
    :param dot2: 元组，三角形的第二个点
    :param dot3: 元组，三角形的第三个点
    :param center: QVector3D，三角形的中心点
    :return: QVector3D
    """
    if type(center) == tuple:
        center = QVector3D(*center)
    v1 = QVector3D(*dot2) - QVector3D(*dot1)
    v2 = QVector3D(*dot3) - QVector3D(*dot1)
    if center is None:
        return QVector3D.crossProduct(v1, v2).normalized()
    triangle_center = QVector3D(*dot1) + QVector3D(*dot2) + QVector3D(*dot3)
    # 如果法向量与视线夹角大于90度，翻转法向量
    if QVector3D.dotProduct(QVector3D.crossProduct(v1, v2), triangle_center - center) > 0:
        return QVector3D.crossProduct(v1, v2).normalized()
    else:
        return QVector3D.crossProduct(v1, v2).normalized()


class GLObject:
    all_objects = {}

    def __init__(self, gl):
        self.gl = gl
        self.faces = {}


class LineGroupObject(GLObject):
    def __init__(self, gl):
        self.gl = gl
        self.lines = {
            # 序号: [(颜色), 线宽, 点集]
        }
        super(LineGroupObject, self).__init__(gl)

    def get_set(self):
        pass

    def draw(self, gl, theme_color, material):
        gl.glLoadName(id(self) % 4294967296)
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_AMBIENT, theme_color[material][0])
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_DIFFUSE, theme_color[material][1])
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_SPECULAR, theme_color[material][2])
        gl.glMaterialfv(gl.GL_FRONT, gl.GL_SHININESS, theme_color[material][3])
        for num, line in self.lines.items():
            gl.glLineWidth(line[1])
            gl.glColor4f(*line[0])
            gl.glBegin(gl.GL_LINE_STRIP)
            for dot in line[2]:
                gl.glNormal3f(0, 1, 0)
                gl.glVertex3f(*dot)
            gl.glEnd()


class SolidObject(GLObject):

    def __init__(self, gl):
        super(SolidObject, self).__init__(gl)
        self.faces = {
            "color": [0.5, 0.5, 0.5, 1],
            "normal": [],
            "faces": []
        }
        # 颜色，法向量集，面集
        self.center = QVector3D(0, 0, 0)

    def draw(self, gl, material, theme_color):
        gl.glLoadName(id(self) % 4294967296)
        # 四个参数分别是：环境光，漫反射光，镜面反射光，镜面反射光的高光指数
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[material][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[material][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[material][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[material][3])
        gl.glColor4f(*self.faces["color"])
        for normal, face in zip(self.faces["normal"], self.faces["faces"]):
            gl.glBegin(gl.GL_POLYGON)
            gl.glNormal3f(normal.x(), normal.y(), normal.z()) if type(normal) == QVector3D \
                else gl.glNormal3f(normal[0], normal[1], normal[2])
            for dot in face:
                gl.glVertex3f(dot.x(), dot.y(), dot.z()) if type(dot) == QVector3D \
                    else gl.glVertex3f(dot[0], dot[1], dot[2])
            gl.glEnd()

    def get_center(self):
        # 计算中心点
        center = QVector3D(0, 0, 0)
        total = 0
        for face in self.faces["faces"]:
            for dot in face:
                center += QVector3D(*dot)
                total += 1
        center /= total
        return center

    def get_normal(self, vertices):
        normal = QVector3D(0, 0, 0)
        num_vertices = len(vertices)
        if num_vertices == 3:
            v1 = QVector3D(*vertices[0])
            v2 = QVector3D(*vertices[1])
            v3 = QVector3D(*vertices[2])
            normal = QVector3D.crossProduct(v2 - v1, v3 - v1)
        elif num_vertices > 3:
            for i in range(num_vertices):
                current_vertex = QVector3D(*vertices[i])
                next_vertex = QVector3D(*vertices[(i + 1) % num_vertices])
                normal += QVector3D.crossProduct(current_vertex, next_vertex).normalized()
        # 如果法向量与视线夹角大于90度，翻转法向量
        if QVector3D.dotProduct(normal, self.center) > 0:
            normal = -normal
        return normal.normalized()


class GridLine(LineGroupObject):
    def __init__(self, gl, num=50, scale=10, normal=(0, 1, 0), central=(0.0, 0.0, 0.0), color=(0.2, 0.3, 0.7, 1)):
        self.num = num
        self.normal = normal
        self.central = central
        self.color = color
        self.line_width0 = 0.05
        self.line_width1 = 0.6
        super(GridLine, self).__init__(gl)
        for i in range(-num, num + 1):
            if i % 10 == 0 or i == num + 1 or i == -num:
                self.lines[f"{i}"] = [
                    self.color, self.line_width1,
                    [(i * scale + central[0], central[1], -num * scale + central[2]),
                     (i * scale + central[0], central[1], num * scale + central[2])]
                ]
                self.lines[f"{i + num * 2}"] = [
                    self.color, self.line_width1,
                    [(-num * scale + central[0], central[1], i * scale + central[2]),
                     (num * scale + central[0], central[1], i * scale + central[2])]
                ]
            else:
                pass
                # self.lines[f"{i}"] = [
                #     self.color, self.line_width0,
                #     [(i * scale + central[0], central[1], -num * scale + central[2]),
                #      (i * scale + central[0], central[1], num * scale + central[2])]
                # ]
                # self.lines[f"{i + num * 2}"] = [
                #     self.color, self.line_width0,
                #     [(-num * scale + central[0], central[1], i * scale + central[2]),
                #      (num * scale + central[0], central[1], i * scale + central[2])]
                # ]


class LargeSurface(SolidObject):
    def __init__(self, gl, r=10000, normal=(0, 1, 0), central=(0.0, 0.0, 0.0), color=(0.2, 0.3, 0.7, 1)):
        self.r = r
        self.normal = normal
        self.central = central
        self.color = color
        self.dots = []
        for i in range(20):
            self.dots.append((
                (self.central[0] + self.r * math.cos(i * math.pi / 10),
                 self.central[1],
                 self.central[2] + self.r * math.sin(i * math.pi / 10))
            ))
        super(LargeSurface, self).__init__(gl)
        # 圆形面
        self.faces = {
            "color": self.color,
            "normal": [QVector3D(0, 1, 0) for _ in range(20)],
            "faces": [
                ((
                     self.central[0] + self.r * math.cos(i * math.pi / 10),
                     self.central[1],
                     self.central[2] + self.r * math.sin(i * math.pi / 10)
                 ), (
                     self.central[0] + self.r * math.cos((i + 1) * math.pi / 10),
                     self.central[1],
                     self.central[2] + self.r * math.sin((i + 1) * math.pi / 10)
                 ), (
                     self.central[0],
                     self.central[1],
                     self.central[2]
                 ))
                for i in range(20)]
        }

    def draw(self, gl, material, theme_color):
        gl.glLoadName(id(self) % 4294967296)
        super(LargeSurface, self).draw(gl, material, theme_color)


class Surface(SolidObject):
    def __init__(self, gl, scale=(10, 10), normal=(0, 1, 0), central=(0, 0, 0), color=(0.5, 0.5, 0.5, 1)):
        self.scale = scale
        self.normal = normal
        self.central = central
        self.color = color
        super(Surface, self).__init__(gl)
        self.faces = {
            "color": self.color,
            "normal": [QVector3D(0, 1, 0) for _ in range(4)],
            "faces": [(self.central[0] + scale[0], self.central[1], self.central[2] + scale[1]),
                      (self.central[0] + scale[0], self.central[1], self.central[2] - scale[1]),
                      (self.central[0] - scale[0], self.central[1], self.central[2] - scale[1]),
                      (self.central[0] - scale[0], self.central[1], self.central[2] + scale[1])]
        }


class Cube(SolidObject):
    def __init__(self, gl, radius, central, color):
        self.radius = radius
        self.central = central
        self.color = color
        self.dot_set = {
            '上面': [(radius[0] + central[0], radius[1] + central[1], radius[2] + central[2]),
                   (radius[0] + central[0], radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], radius[1] + central[1], radius[2] + central[2])],
            '下面': [(radius[0] + central[0], -radius[1] + central[1], radius[2] + central[2]),
                   (radius[0] + central[0], -radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], -radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], -radius[1] + central[1], radius[2] + central[2])],
            '左面': [(-radius[0] + central[0], radius[1] + central[1], radius[2] + central[2]),
                   (-radius[0] + central[0], radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], -radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], -radius[1] + central[1], radius[2] + central[2])],
            '右面': [(radius[0] + central[0], radius[1] + central[1], radius[2] + central[2]),
                   (radius[0] + central[0], radius[1] + central[1], -radius[2] + central[2]),
                   (radius[0] + central[0], -radius[1] + central[1], -radius[2] + central[2]),
                   (radius[0] + central[0], -radius[1] + central[1], radius[2] + central[2])],
            '前面': [(radius[0] + central[0], radius[1] + central[1], radius[2] + central[2]),
                   (radius[0] + central[0], -radius[1] + central[1], radius[2] + central[2]),
                   (-radius[0] + central[0], -radius[1] + central[1], radius[2] + central[2]),
                   (-radius[0] + central[0], radius[1] + central[1], radius[2] + central[2])],
            '后面': [(radius[0] + central[0], radius[1] + central[1], -radius[2] + central[2]),
                   (radius[0] + central[0], -radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], -radius[1] + central[1], -radius[2] + central[2]),
                   (-radius[0] + central[0], radius[1] + central[1], -radius[2] + central[2])]
        }
        super(Cube, self).__init__(gl)
        self.faces = {
            "color": self.color,
            "normal": [self.get_normal(self.dot_set['上面']), self.get_normal(self.dot_set['下面']),
                       self.get_normal(self.dot_set['左面']), self.get_normal(self.dot_set['右面']),
                       self.get_normal(self.dot_set['前面']), self.get_normal(self.dot_set['后面'])],
            "faces": [self.dot_set['上面'], self.dot_set['下面'], self.dot_set['左面'],
                      self.dot_set['右面'], self.dot_set['前面'], self.dot_set['后面']]
        }


class LightSphere(SolidObject):
    def __init__(self, gl, radius=1000, central=(0, 0, 0), color=(0.7, 0.7, 0.7, 1)):
        self.radius = radius
        self.central = central
        self.color = color
        self._faces = []
        n = 10
        # 绕Z轴旋转
        for i in range(2 * n):
            face__ = []
            for j in range(2 * n):
                face__.append((
                    self.central[0] + self.radius * math.cos(i * math.pi / n) * math.sin(j * math.pi / n),
                    self.central[1] + self.radius * math.sin(i * math.pi / n) * math.sin(j * math.pi / n),
                    self.central[2] + self.radius * math.cos(j * math.pi / n)
                ))
            self._faces.append(face__)
        # 绕Y轴旋转
        for i in range(n):
            face__ = []
            for j in range(n):
                face__.append((
                    self.central[0] + self.radius * math.cos(i * math.pi / n) * math.sin(j * math.pi / n),
                    self.central[1] + self.radius * math.sin(i * math.pi / n),
                    self.central[2] + self.radius * math.cos(i * math.pi / n) * math.cos(j * math.pi / n)
                ))
            self._faces.append(face__)
        # 绕X轴旋转
        for i in range(2 * n):
            face__ = []
            for j in range(2 * n):
                face__.append((
                    self.central[0] + self.radius * math.cos(i * math.pi / n),
                    self.central[1] + self.radius * math.sin(i * math.pi / n) * math.sin(j * math.pi / n),
                    self.central[2] + self.radius * math.sin(i * math.pi / n) * math.cos(j * math.pi / n)
                ))
            self._faces.append(face__)
        super(LightSphere, self).__init__(gl)
        self.faces = {
            "color": self.color,
            "normal": [QVector3D(0, 1, 0) for _ in range(len(self._faces))],
            "faces": self._faces
        }

    def draw(self, gl, material, theme_color):
        gl.glLoadName(id(self) % 4294967296)
        super(LightSphere, self).draw(gl, material, theme_color)


class AdHull(ReadPTB, SolidObject):
    def __init__(self, path):
        ReadPTB.__init__(self, path)
        SolidObject.__init__(self, None)
        self.path = path
        self.obj = self.result['adHull']
        self.ShipName = self.obj.ShipName
        self.Position = self.obj.Position
        self.Dock = self.obj.Dock
        self.Rail = self.obj.Rail
        self.WaterLineHeight = self.obj.WaterLineHeight
        self.HullColor = self.obj.HullColor
        self.WaterLineColor = self.obj.WaterLineColor
        self.Slices = self.obj.Slices
        self.SlicesPoints = self.obj.SlicesPoints
        self.SlicesPoints_half = {}
        for key, value in self.SlicesPoints.items():
            # 切半，只保留左半边
            self.SlicesPoints_half[key] = value[:len(value) // 2]

        # SlicePoints 键值对是：分段名称 和 节点集合，其中节点先从前到后遍历左边再从前到后遍历右边，方向一致。
        self.lines = {}
        self.deck_dots = []
        self.height = 0
        self.get_deck_dots()  # 给self.deck_dots赋值
        self.faces = {
            "color": [0.5, 0.5, 0.5, 1],
            "normal": [],
            "faces": []
        }
        for i in range(len(self.SlicesPoints_half) - 1):  # 给self.faces赋值
            mode = "normal" if i < len(self.SlicesPoints_half) // 2 else "back"
            for t in self.obj.get_plot_triangles(
                    list(self.SlicesPoints_half.values())[i],
                    list(self.SlicesPoints_half.values())[i + 1],
                    mode=mode
            ):
                self.faces["faces"].append(t)
        self.center = self.get_center()  # 给self.center赋值
        self.faces["normal"] = []
        for face_ in self.faces["faces"]:
            self.faces["normal"].append(get_normal(*face_, self.center))  # 给self.faces["normal"]赋值

    def get_deck_dots(self):
        """
        根据self.SlicesPoints中的点集，生成self.lines中的线段集合
        """
        slice_num = len(self.SlicesPoints)
        # 生成线段
        for i in range(slice_num):
            node_set = list(self.SlicesPoints.values())[i]
            slice_node_num = len(node_set) // 2
            # 翻转node_set后一半的顺序
            node_set_transposed = node_set[:slice_node_num] + node_set[slice_node_num:][::-1]
            # 生成甲板
            self.deck_dots.append(node_set_transposed[-1])
            self.deck_dots.append(node_set_transposed[0])

    def draw(self, gl, material="钢铁", theme_color=None):
        gl.glLoadName(id(self) % 4294967296)
        super(AdHull, self).draw(gl, "钢铁", theme_color)
        self.draw_deck(gl, theme_color)  # 绘制甲板
        # self.draw_water_line(gl, theme_color)  # 绘制水线

    def draw_water_line(self, gl, theme_color=None):
        water_line = self.obj.get_xz_from_y(self.WaterLineHeight * self.height / 3)
        # 现在water_line只有左侧点，需要补充右侧点
        new = []
        for i in range(len(water_line)):
            new.append((water_line[i][0], water_line[i][1]))
            new.append((-water_line[i][0], water_line[i][1]))
        # 现在water_line只有x和z，需要补充y
        for i in range(len(new)):
            new[i] = (new[i][0], self.WaterLineHeight * self.height / 3, new[i][1])
        # 绘制水线
        gl.glLineWidth(1)
        gl.glColor3f(0.5, 0.5, 0.5)
        mt = "水线"
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[mt][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[mt][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[mt][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[mt][3])
        gl.glBegin(gl.GL_QUAD_STRIP)
        for dot in new:
            gl.glVertex3f(*dot)
        gl.glEnd()

    def draw_deck(self, gl, theme_color=None):
        gl.glLineWidth(1)
        gl.glColor3f(0.5, 0.5, 0.5)
        mt = "甲板"
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[mt][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[mt][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[mt][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[mt][3])
        gl.glNormal3f(0, 1, 0)
        gl.glBegin(gl.GL_QUAD_STRIP)
        for dot in self.deck_dots:
            gl.glVertex3f(*dot)
        gl.glEnd()

    def get_max_slices_node_num_and_height(self):
        """
        获取所有分段中节点数最多的分段的节点数
        """
        max_num = 0
        lowest_y = 0
        highest_y = 0
        for name, node_set in self.SlicesPoints.items():
            if len(node_set) > max_num:
                max_num = len(node_set)
            for node in node_set:
                if node[1] < lowest_y:
                    lowest_y = node[1]
                if node[1] > highest_y:
                    highest_y = node[1]
        return max_num, highest_y - lowest_y

    @staticmethod
    def transposePTB2NA(SlicesPoints):
        # PTB的前后是x，上下是y，左右是z，NA的前后是z，上下是y，左右是x
        for slice_name in SlicesPoints:
            for i in range(len(SlicesPoints[slice_name])):
                SlicesPoints[slice_name][i] = (SlicesPoints[slice_name][i][2],
                                               SlicesPoints[slice_name][i][1],
                                               SlicesPoints[slice_name][i][0])
        return SlicesPoints


class NAHull(ReadNA, SolidObject):
    def __init__(self, path=False, data=None, show_statu_func=None):
        """
        NAHull一定要在用户选完颜色之后调用，因为需要根据颜色来初始化DrawMap。
        注意，self.DrawMap不会在ReadNA和SolidObject中初始化，会在其他地方初始化。
        在初始化后会调用get_ys_and_zs()和get_layers()方法，而不是在self.__init__()中调用
        :param path:
        :param data:
        """
        # 判断show_statu_func是函数还是qsignal，
        try:
            self.show_statu_func = show_statu_func.emit
        except AttributeError:
            self.show_statu_func = show_statu_func
        self.DrawMap = {}  # 绘图数据，键值对是：颜色 和 零件对象集合
        ReadNA.__init__(self, path, data, self.show_statu_func)  # 注意，DrawMap不会在ReadNA或SolidObject中初始化
        SolidObject.__init__(self, None)
        self.DrawMap = self.ColorPartsMap.copy()
        self.xzLayers = []  # 所有xz截面
        self.xyLayers = []  # 所有xy截面
        self.leftViews = []  # 中间yz截面

    def get_layers(self):
        self.get_xz_layers()
        self.get_xy_layers()
        self.get_left_views()

    def get_xz_layers(self):
        total_y_num = len(self.partRelationMap.xzDotsLayerMap)
        i = 0
        for y, parts in self.partRelationMap.xzDotsLayerMap.items():
            i += 1
            if i % 4567 == 0:
                self.show_statu_func(f"正在生成xz截面第{i}/{total_y_num}层", "process")
            if len(parts) < 4:
                continue
            self.xzLayers.append(NaHullXZLayer(self, y, parts))

    def get_xy_layers(self):
        total_z_num = len(self.partRelationMap.xyDotsLayerMap)
        i = 0
        for z, parts in self.partRelationMap.xyDotsLayerMap.items():
            i += 1
            if i % 4567 == 0:
                self.show_statu_func(f"正在生成xy截面第{i}/{total_z_num}层", "process")
            if len(parts) < 3:
                continue
            self.xyLayers.append(NaHullXYLayer(self, z, parts))

    def get_left_views(self):
        # TODO: 生成左视图
        pass

    @staticmethod
    def toJson(data):
        # 将ColorPartMap转换为字典形式，以便于json序列化
        result = {}
        for color, part_set in data.items():
            result[color] = []
            for part in part_set:
                result[color].append(part.to_dict())
        return result

    @staticmethod
    def draw_color(gl, theme_color, material, color, part_set):
        # 16进制颜色转换为RGBA
        if theme_color[material][1] == (0.35, 0.35, 0.35, 1.0):  # 说明是白天模式
            _rate = 600
            color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, 1
        else:  # 说明是黑夜模式
            _rate = 600
            color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, 1
            # 减去一定的值
            difference = 0.08
            color_ = (color_[0] - difference, color_[1] - difference, color_[2] - difference, 1)
            # 如果小于0，就等于0
            color_ = (color_[0] if color_[0] > 0 else 0,
                      color_[1] if color_[1] > 0 else 0,
                      color_[2] if color_[2] > 0 else 0,
                      1)
        light_color_ = color_[0] * 0.9 + 0.3, color_[1] * 0.9 + 0.3, color_[2] * 0.9 + 0.3, 1
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, color_)
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, light_color_)
        gl.glColor4f(*color_)
        for part in part_set:
            gl.glLoadName(id(part) % 4294967296)
            # 获取part的地址
            part_address = id(part)
            try:
                for draw_method, faces_dots in part.plot_faces.items():
                    # draw_method是字符串，需要转换为OpenGL的常量
                    for face in faces_dots:
                        gl.glBegin(eval(f"gl.{draw_method}"))
                        if len(face) == 3 or len(face) == 4:
                            normal = get_normal(face[0], face[1], face[2])
                        elif len(face) > 12:
                            normal = get_normal(face[0], face[6], face[12])
                        else:
                            continue
                        gl.glNormal3f(normal.x(), normal.y(), normal.z())
                        for dot in face:
                            gl.glVertex3f(dot[0], dot[1], dot[2])
                        gl.glEnd()
            except AttributeError as e:
                pass

    def draw(self, gl, material="钢铁", theme_color=None):
        gl.glLoadName(id(self) % 4294967296)
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[material][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[material][3])
        # 绘制面
        for color, part_set in self.DrawMap.items():
            # t = Thread(target=self.draw_color, args=(gl, theme_color, material, color, part_set))
            # t.start()
            self.draw_color(gl, theme_color, material, color, part_set)


class NaHullXZLayer(SolidObject):
    def __init__(self, na_hull, y, y_parts):
        """
        :param na_hull: 暂时没用
        :param y:
        :param y_parts:
        """
        SolidObject.__init__(self, None)
        self.na_hull = na_hull
        self.y = y
        self.y_parts = y_parts
        self.PlotAvailable = True  # 当只含有一个零件时，不绘制
        # 在na_hull中找到所有y值为y的零件和点
        self.index = []  # 所有点在原来的Part.plot_all_dots中的索引，用来判断是否是含曲面零件的曲面中间点连线，是则不显示。
        self.PartsDotsMap = self.get_partsDotsMap()  # 键值对：Part对象 和 该对象中y=self.y的点集合
        self.Pos_list = self.get_pos_list()  # 所有面的点集合

    def get_partsDotsMap(self):
        result = {}
        for part in self.y_parts:
            if type(part) != AdjustableHull:
                continue
            for i in range(len(part.plot_all_dots)):
                dot = list(part.plot_all_dots[i])
                # if -0.0005 < dot[1] - self.y < 0.0005:
                if dot[1] == self.y:
                    if len(part.plot_all_dots) == 48:  # 为带曲面的零件
                        self.index.append(i) if i not in self.index else None
                    if part not in result:
                        result[part] = [dot]
                    if dot not in result[part]:
                        result[part].append(dot)
        if len(result) <= 2:  # 如果只有一两个零件，就不绘制
            self.PlotAvailable = False
            return {}
        if len(self.index) == 4 and self.index[0] not in [0, 24]:  # 曲面的中间点
            self.PlotAvailable = False
            return {}
        # 对result中的点集合进行排序：逆时针排序
        for part, dots in result.items():
            center = [part.Pos[0], self.y, part.Pos[2]]
            dots.sort(key=lambda x: math.atan2(x[2] - center[2], x[0] - center[0]))
        return result

    def get_pos_list(self):
        result = []
        for dot_sets in self.PartsDotsMap.values():
            center = np.array([0., 0., 0.])
            for dot in dot_sets:
                result.append(dot)
                center += np.array(dot)
            center /= len(dot_sets)
            result.append(center)
        return result

    def draw(self, gl, material="半透明", theme_color=None):
        gl.glLoadName(id(self) % 4294967296)
        if not self.PlotAvailable:
            return
        # 绘制面
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[material][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[material][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[material][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[material][3])
        for part, dots in self.PartsDotsMap.items():
            gl.glNormal3f(0, 1, 0)
            gl.glBegin(gl.GL_POLYGON)
            for dot in dots[::-1]:
                gl.glVertex3f(*dot)
            gl.glEnd()
            gl.glNormal3f(0, -1, 0)
            gl.glBegin(gl.GL_POLYGON)
            for dot in dots:
                gl.glVertex3f(*dot)
            gl.glEnd()


class NaHullXYLayer(SolidObject):
    def __init__(self, na_hull, z, z_parts):
        """
        :param na_hull: 暂时没用
        :param z:
        :param z_parts:
        """
        SolidObject.__init__(self, None)
        self.na_hull = na_hull
        self.z = z
        self.z_parts = z_parts
        self.PlotAvailable = True  # 当只含有一个零件时，不绘制
        # 在na_hull中找到所有z值为z的零件和点
        self.index = []  # 所有点在原来的Part.plot_all_dots中的索引，用来判断是否是含曲面零件的曲面中间点连线，是则不显示。
        self.PartsDotsMap = self.get_partsDotsMap()  # 键值对：Part对象 和 该对象中z=self.z的点集合
        self.Pos_list = self.get_pos_list()  # 所有面的点集合

    def get_partsDotsMap(self):
        result = {}
        for part in self.z_parts:
            if type(part) != AdjustableHull:
                continue
            for i in range(len(part.plot_all_dots)):
                dot = list(part.plot_all_dots[i])
                # if -0.0005 < dot[1] - self.y < 0.0005:
                if dot[2] == self.z:
                    if len(part.plot_all_dots) == 48:  # 为带曲面的零件
                        self.index.append(i) if i not in self.index else None
                    if part not in result:
                        result[part] = [dot]
                    if dot not in result[part]:
                        result[part].append(dot)
        if len(result) <= 2:  # 如果只有一两个零件，就不绘制
            self.PlotAvailable = False
            return {}
        if len(self.index) == 4 and self.index[0] not in [0, 24]:  # 曲面的中间点
            self.PlotAvailable = False
            return {}
        # 对result中的点集合进行排序：逆时针排序
        for part, dots in result.items():
            center = [part.Pos[0], part.Pos[1], self.z]
            dots.sort(key=lambda x: math.atan2(x[1] - center[1], x[0] - center[0]))
        return result

    def get_pos_list(self):
        result = []
        for dot_sets in self.PartsDotsMap.values():
            center = np.array([0., 0., 0.])
            for dot in dot_sets:
                result.append(dot)
                center += np.array(dot)
            center /= len(dot_sets)
            result.append(center)
        return result

    def draw(self, gl, material="半透明", theme_color=None):
        gl.glLoadName(id(self) % 4294967296)
        if not self.PlotAvailable:
            return
        # 绘制面
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[material][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[material][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[material][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[material][3])
        for part, dots in self.PartsDotsMap.items():
            gl.glNormal3f(0, 0, 1)
            gl.glBegin(gl.GL_POLYGON)
            for dot in dots[::-1]:
                gl.glVertex3f(*dot)
            gl.glEnd()
            gl.glNormal3f(0, 0, -1)
            gl.glBegin(gl.GL_POLYGON)
            for dot in dots:
                gl.glVertex3f(*dot)
            gl.glEnd()


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
        dx = dx * 2 * self.sensitivity["旋转"]
        dy = dy * 2 * self.sensitivity["旋转"]
        _rate = self.distance / 1000
        left = QVector3D.crossProduct(self.angle, self.up).normalized()
        up = QVector3D.crossProduct(left, self.angle).normalized()
        self.pos += up * dy * _rate - left * dx * _rate
        self.angle = self.calculate_angle()
        # 如果到顶或者到底，就不再旋转
        if self.angle.y() > 0.99 and dy > 0:
            return
        if self.angle.y() < -0.99 and dy < 0:
            return

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
