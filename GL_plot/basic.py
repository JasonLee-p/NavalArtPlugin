"""
基础的GL绘制对象，包括基类，环境的绘制对象（光球，网格线，大面，小面），基础3D对象（线，面）
"""

import math
from PyQt5.QtGui import QVector3D


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
