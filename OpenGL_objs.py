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
from PyQt5.QtGui import QVector3D
# 自定义库
from NA_design_reader import ReadNA
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
    all_objects = {
        # 对象：{面集:{线集:点集}}，其中点集、线集、面集都是列表，列表中的元素是QVector3D
    }

    def __init__(self, gl):
        self.gl = gl
        self.faces = {}
        GLObject.all_objects[self] = [[], [], []]

    @abstractmethod
    def get_set(self):
        pass


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

    def get_set(self):
        GLObject.all_objects[self][0] = self.faces["faces"]

    def draw(self, gl, material, theme_color):
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
    def __init__(self, path=False, data=None):
        self.DrawMap = {}  # 绘图数据，键值对是：颜色 和 零件对象集合
        ReadNA.__init__(self, path, data)
        SolidObject.__init__(self, None)

    @staticmethod
    def toJson(data):
        # 将ColorPartMap转换为字典形式，以便于json序列化
        result = {}
        for color, part_set in data.items():
            result[color] = []
            for part in part_set:
                result[color].append(part.to_dict())
        return result

    def draw(self, gl, material="钢铁", theme_color=None):

        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[material][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[material][3])
        # 绘制面
        for color, part_set in self.DrawMap.items():
            # 16进制颜色转换为RGBA
            if theme_color[material][1] == (0.35, 0.35, 0.35, 1.0):  # 说明是白天模式
                _rate = 600
                color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, 1
            else:  # 说明是黑夜模式
                _rate = 1000
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
        rate_ = self.distance / 650
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
        _rate = self.distance / 400
        left = QVector3D.crossProduct(self.angle, self.up).normalized()
        up = QVector3D.crossProduct(left, self.angle).normalized()
        self.pos += up * dy * _rate - left * dx * _rate
        self.angle = self.calculate_angle()
        # 如果到顶或者到底，就不再旋转
        if self.angle.y() > 0.99 and dy > 0:
            return
        if self.angle.y() < -0.99 and dy < 0:
            return

    def get_world_to_camera_matrix(self):
        """
        获取世界坐标系到摄像机坐标系的变换矩阵
        """
        return self.look_at(self.pos, self.tar, self.up)

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
