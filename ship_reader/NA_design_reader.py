"""
读取NA设计文件的模块
"""
import time
import xml.etree.ElementTree as ET
from typing import Union, List, Dict, Callable

import numpy as np
from PyQt5.QtGui import QVector3D
from quaternion import quaternion

"""
文件格式：
<root>
  <ship author="XXXXXXXXX" description="description" hornType="1" hornPitch="0.9475011" tracerCol="E53D4FFF">
    <newPart id="0">
      <data length="4.5" height="1" frontWidth="0.2" backWidth="0.5" frontSpread="0.05" backSpread="0.2" upCurve="0" downCurve="1" heightScale="1" heightOffset="0" />
      <position x="0" y="0" z="114.75" />
      <rotation x="0" y="0" z="0" />
      <scale x="1" y="1" z="1" />
      <color hex="975740" />
      <armor value="5" />
    </newPart>
    <newPart id="190">
      <position x="0" y="-8.526513E-14" z="117.0312" />
      <rotation x="90" y="0" z="0" />
      <scale x="0.03333336" y="0.03333367" z="0.1666679" />
      <color hex="975740" />
      <armor value="5" />
    </newPart>
  </root>
"""
orders = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
RotateOrder = orders[2]


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


def rotate_quaternion(vec, rot):
    """
    对np.array类型的向量进行四元数旋转
    :param vec:
    :param rot:
    :return:
    """
    if rot == [0, 0, 0]:
        # 标准化为单位向量
        return vec / np.linalg.norm(vec)
    # 转换为弧度
    rot = np.radians(rot)
    # 计算旋转的四元数
    q_x = np.array([np.cos(rot[0] / 2), np.sin(rot[0] / 2), 0, 0])
    q_y = np.array([np.cos(rot[1] / 2), 0, np.sin(rot[1] / 2), 0])
    q_z = np.array([np.cos(rot[2] / 2), 0, 0, np.sin(rot[2] / 2)])

    # 合并三个旋转四元数
    q = quaternion(1, 0, 0, 0)
    if RotateOrder == "XYZ":
        q = q * quaternion(*q_x) * quaternion(*q_y) * quaternion(*q_z)
    elif RotateOrder == "XZY":
        q = q * quaternion(*q_x) * quaternion(*q_z) * quaternion(*q_y)
    elif RotateOrder == "YXZ":
        q = q * quaternion(*q_y) * quaternion(*q_x) * quaternion(*q_z)
    elif RotateOrder == "YZX":
        q = q * quaternion(*q_y) * quaternion(*q_z) * quaternion(*q_x)
    elif RotateOrder == "ZXY":
        q = q * quaternion(*q_z) * quaternion(*q_x) * quaternion(*q_y)
    elif RotateOrder == "ZYX":
        q = q * quaternion(*q_z) * quaternion(*q_y) * quaternion(*q_x)
    else:
        raise ValueError("Invalid RotateOrder!")

    # 进行四元数旋转
    rotated_point_quat = q * np.quaternion(0, *vec) * np.conj(q)
    # 提取旋转后的点坐标
    rotated_point = np.array([rotated_point_quat.x, rotated_point_quat.y, rotated_point_quat.z])
    # 标准化为单位向量
    rotated_point = rotated_point / np.linalg.norm(rotated_point)
    return rotated_point


def rotate_quaternion2(dot_dict, scl, rot):
    """
    对点集进行四元数旋转

    :param dot_dict: 字典，值是零件的各个点的坐标，格式为 {'pointset1': [[x1, y1, z1], [x2, y2, z2], ...], 'pointset2': [[x1, y1, z1], [x2, y2, z2], ...], ...}
    :param scl: 缩放比例，三个值分别为x,y,z轴的缩放比例
    :param rot: 角度值，三个值分别为x,y,z轴的旋转角度，单位为度
    :return: 旋转后的点集，格式与输入点集相同，但值为np.array类型
    """
    if rot == [0, 0, 0]:
        return dot_dict
    # 转换为弧度
    rot = np.radians(rot)
    # 计算旋转的四元数
    q_x = np.array([np.cos(rot[0] / 2), np.sin(rot[0] / 2), 0, 0])
    q_y = np.array([np.cos(rot[1] / 2), 0, np.sin(rot[1] / 2), 0])
    q_z = np.array([np.cos(rot[2] / 2), 0, 0, np.sin(rot[2] / 2)])

    # 合并三个旋转四元数
    q = quaternion(1, 0, 0, 0)
    if RotateOrder == "XYZ":
        q = q * quaternion(*q_x) * quaternion(*q_y) * quaternion(*q_z)
    elif RotateOrder == "XZY":
        q = q * quaternion(*q_x) * quaternion(*q_z) * quaternion(*q_y)
    elif RotateOrder == "YXZ":
        q = q * quaternion(*q_y) * quaternion(*q_x) * quaternion(*q_z)
    elif RotateOrder == "YZX":
        q = q * quaternion(*q_y) * quaternion(*q_z) * quaternion(*q_x)
    elif RotateOrder == "ZXY":
        q = q * quaternion(*q_z) * quaternion(*q_x) * quaternion(*q_y)
    elif RotateOrder == "ZYX":
        q = q * quaternion(*q_z) * quaternion(*q_y) * quaternion(*q_x)
    else:
        raise ValueError("Invalid RotateOrder!")

    # 遍历点集进行旋转
    rotated_dot_dict = {}
    for key, pointset in dot_dict.items():
        for i, point in enumerate(pointset):
            # 进行缩放
            point = np.array(point) * scl
            # 将点坐标转换为四元数
            point_quat = np.quaternion(0, *point)
            # 进行四元数旋转
            rotated_point_quat = q * point_quat * np.conj(q)
            # 提取旋转后的点坐标
            rotated_point = np.array([rotated_point_quat.x, rotated_point_quat.y, rotated_point_quat.z])
            # 将结果保存到字典中
            if i == 0:
                rotated_dot_dict[key] = [rotated_point]
            else:
                rotated_dot_dict[key].append(rotated_point)

    return rotated_dot_dict


def rotate_quaternion0(face_list, scl, rot):
    """
    对点集进行四元数旋转
    :param face_list: 列表，元素是含有多个点的列表，格式为 [[array([x1, y1, z1]), array([x2, y2, z2]), ...], [...], ...]
    :param scl:
    :param rot:
    :return:
    """
    if rot == [0, 0, 0]:
        return face_list
    # 转换为弧度
    rot = np.radians(rot)
    # 计算旋转的四元数
    q_x = np.array([np.cos(rot[0] / 2), np.sin(rot[0] / 2), 0, 0])
    q_y = np.array([np.cos(rot[1] / 2), 0, np.sin(rot[1] / 2), 0])
    q_z = np.array([np.cos(rot[2] / 2), 0, 0, np.sin(rot[2] / 2)])

    # 合并三个旋转四元数
    q = quaternion(1, 0, 0, 0)
    if RotateOrder == "XYZ":
        q = q * quaternion(*q_x) * quaternion(*q_y) * quaternion(*q_z)
    elif RotateOrder == "XZY":
        q = q * quaternion(*q_x) * quaternion(*q_z) * quaternion(*q_y)
    elif RotateOrder == "YXZ":
        q = q * quaternion(*q_y) * quaternion(*q_x) * quaternion(*q_z)
    elif RotateOrder == "YZX":
        q = q * quaternion(*q_y) * quaternion(*q_z) * quaternion(*q_x)
    elif RotateOrder == "ZXY":
        q = q * quaternion(*q_z) * quaternion(*q_x) * quaternion(*q_y)
    elif RotateOrder == "ZYX":
        q = q * quaternion(*q_z) * quaternion(*q_y) * quaternion(*q_x)
    else:
        raise ValueError("Invalid RotateOrder!")
    # 遍历点集进行旋转
    rotated_face_list = []
    for face in face_list:
        rotated_face = []
        for point in face:
            # 进行缩放
            point = np.array(point) * scl
            # 将点坐标转换为四元数
            point_quat = np.quaternion(0, *point)
            # 进行四元数旋转
            rotated_point_quat = q * point_quat * np.conj(q)
            # 提取旋转后的点坐标
            rotated_point = np.array([rotated_point_quat.x, rotated_point_quat.y, rotated_point_quat.z])
            # 将结果保存到列表中
            rotated_face.append(rotated_point)
        rotated_face_list.append(rotated_face)
    return rotated_face_list


def rotate_quaternion1(dot_dict, scl, rot):
    """
    对点集进行缩放，四元数旋转

    :param dot_dict: 字典，值是零件的各个点的坐标，格式为 {'point1': [x1, y1, z1], 'point2': [x2, y2, z2], ...}
    :param scl: 缩放比例，三个值分别为x,y,z轴的缩放比例
    :param rot: 角度值，三个值分别为x,y,z轴的旋转角度，单位为度
    :return: 旋转后的点集，格式与输入点集相同，但值为np.array类型
    """
    if rot == [0, 0, 0]:
        # 仅转换为np.array类型
        for key, point in dot_dict.items():
            dot_dict[key] = np.array(point)
        return dot_dict
    # 将角度转换为弧度
    rot = np.radians(rot)
    # 计算旋转的四元数
    q_x = np.array([np.cos(rot[0] / 2), np.sin(rot[0] / 2), 0, 0])
    q_y = np.array([np.cos(rot[1] / 2), 0, np.sin(rot[1] / 2), 0])
    q_z = np.array([np.cos(rot[2] / 2), 0, 0, np.sin(rot[2] / 2)])

    # 合并三个旋转四元数
    q = quaternion(1, 0, 0, 0)
    if RotateOrder == "XYZ":
        q = q * quaternion(*q_x) * quaternion(*q_y) * quaternion(*q_z)
    elif RotateOrder == "XZY":
        q = q * quaternion(*q_x) * quaternion(*q_z) * quaternion(*q_y)
    elif RotateOrder == "YXZ":
        q = q * quaternion(*q_y) * quaternion(*q_x) * quaternion(*q_z)
    elif RotateOrder == "YZX":
        q = q * quaternion(*q_y) * quaternion(*q_z) * quaternion(*q_x)
    elif RotateOrder == "ZXY":
        q = q * quaternion(*q_z) * quaternion(*q_x) * quaternion(*q_y)
    elif RotateOrder == "ZYX":
        q = q * quaternion(*q_z) * quaternion(*q_y) * quaternion(*q_x)
    else:
        raise ValueError("Invalid RotateOrder!")

    # 遍历点集进行缩放，旋转
    rotated_dot_dict = {}
    for key, point in dot_dict.items():
        # 进行缩放
        point = np.array(point) * scl
        # 将点坐标转换为四元数
        point_quat = np.quaternion(0, *point)
        # 进行四元数旋转
        rotated_point_quat = q * point_quat * np.conj(q)
        # 提取旋转后的点坐标
        rotated_point = np.array([rotated_point_quat.x, rotated_point_quat.y, rotated_point_quat.z])
        # 将结果保存到字典中
        rotated_dot_dict[key] = rotated_point

    return rotated_dot_dict


def get_bezier(start, s_control, back, b_control, x):
    """
    计算贝塞尔曲线上的点的坐标，用np.array类型表示
    :param start: 起点
    :param s_control: 起点控制点
    :param back: 终点
    :param b_control: 终点控制点
    :param x: 点的x坐标，x在start[0]和back[0]之间
    :return: 返回贝塞尔曲线上的点坐标
    """
    # 计算 t 值
    t = (x - start[0]) / (back[0] - start[0])

    # 贝塞尔曲线公式
    result = (1 - t)**3 * start + 3 * (1 - t)**2 * t * s_control + 3 * (1 - t) * t**2 * b_control + t**3 * back

    return np.array(result)


def fit_bezier(front_k, back_k, length, height, n, draw=False):
    # 过滤n值>=2
    if n < 2:
        raise ValueError("n must be greater than or equal to 2")

    # 计算控制点位置
    distance = length / 4
    start = np.array([0, 0])
    end = np.array([length, height])
    dir_s = np.array([1, front_k])
    dir_b = np.array([1, back_k])
    # 标准化后乘以距离
    dir_s = dir_s * distance / np.linalg.norm(dir_s)
    dir_b = dir_b * distance / np.linalg.norm(dir_b)
    start_control = start + dir_s
    end_control = end - dir_b
    if draw:
        # 在matplotlib绘制贝塞尔曲线：
        import matplotlib.pyplot as plt
        # 从0到length之间生成100个点
        t_values = np.linspace(0, length, 100)
        # 初始化存储曲线上点的空数组
        curve_points = []
        # 计算贝塞尔曲线上的点
        for t in t_values:
            point = get_bezier(start, start_control, end, end_control, t / length)
            curve_points.append(point)
        # 转换为NumPy数组以便于绘图
        curve_points = np.array(curve_points)
        # 绘制贝塞尔曲线
        plt.figure(figsize=(8, 6))
        plt.plot(curve_points[:, 0], curve_points[:, 1], label='Bezier Curve', color='blue')
        plt.scatter([start[0], start_control[0], end[0], end_control[0]],
                    [start[1], start_control[1], end[1], end_control[1]],
                    color='red', marker='o', label='Control Points')
        plt.title('Bezier Curve')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.legend()
        plt.grid(True)
        plt.show()
    # 存储斜率的列表
    slopes = []
    # 计算每段的长度
    last_point = None
    step = length / n
    # 计算每段的斜率
    for i in range(n):
        # 计算当前参数值
        x = (i + 1) * step
        # 计算贝塞尔曲线上的点坐标
        point = get_bezier(start, start_control, end, end_control, x)
        # 计算与前一个点的斜率，如果为第一个点则计算与起点的斜率
        if i == 0:
            slope = (point[1] - start[1]) / step
        else:
            slope = (point[1] - last_point[1]) / step
        # 将斜率添加到列表中
        slopes.append(slope)
        # 保存上一个点的坐标
        last_point = point

    return slopes


class NAPartNode:
    id_map = {}
    all_dots = []  # 不储存对象，储存所有点的坐标列表

    def __init__(self, pos: list):
        self.pos = pos
        self.glWin = None
        self.near_parts = {  # 八个卦限
            PartRelationMap.FRONT_UP_LEFT: [],
            PartRelationMap.FRONT_UP_RIGHT: [],
            PartRelationMap.FRONT_DOWN_LEFT: [],
            PartRelationMap.FRONT_DOWN_RIGHT: [],
            PartRelationMap.BACK_UP_LEFT: [],
            PartRelationMap.BACK_UP_RIGHT: [],
            PartRelationMap.BACK_DOWN_LEFT: [],
            PartRelationMap.BACK_DOWN_RIGHT: [],
        }
        NAPartNode.id_map[id(self) % 4294967296] = self
        NAPartNode.all_dots.append(self.pos)
        # 绘图指令集初始化
        self.genList = None
        self.updateList = False
        self.selected_genList = None
        self.update_selectedList = False

    def draw(self, gl, material="节点", theme_color=None, point_size=5):
        if self.genList and not self.updateList:
            gl.glCallList(self.genList)
            return
        self.genList = gl.glGenLists(1)
        gl.glNewList(self.genList, gl.GL_COMPILE_AND_EXECUTE)
        gl.glLoadName(id(self) % 4294967296)
        gl.glColor4f(*theme_color[material][0])
        gl.glPointSize(point_size)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex3f(*self.pos)
        gl.glEnd()
        gl.glEndList()


class XZLayerNode(NAPartNode):
    ...


class NAPart:
    ShipsAllParts = []
    id_map = {}  # 储存零件ID与零件实例的映射
    hull_design_tab_id_map = {}  # 在na_hull中清空和初始化

    def __init__(self, read_na, Id, pos, rot, scale, color, armor):
        self.glWin = None  # 用于绘制的窗口
        self.read_na_obj = read_na
        self.allParts_relationMap = read_na.partRelationMap
        self.Id = Id
        self.Pos = pos
        self.Rot = rot
        self.Scl = scale
        self.Col = color  # "#975740"
        self.Amr = armor
        NAPart.ShipsAllParts.append(self)
        NAPart.id_map[id(self) % 4294967296] = self
        # 绘图指令集初始化
        self.pre_genList = None
        self.genList = None
        self.updateList = False
        self.transparent_genList = None
        self.update_transparentList = False
        self.selected_genList = None
        self.update_selectedList = False

    def set_basic_attributes(self, armor):
        self.Amr = armor

    def delete(self):
        del NAPart.id_map[id(self) % 4294967296]

    def scale(self, ratio: list):
        self.Scl = [self.Scl[0] * ratio[0], self.Scl[1] * ratio[1], self.Scl[2] * ratio[2]]
        self.Pos = [self.Pos[0] * ratio[0], self.Pos[1] * ratio[1], self.Pos[2] * ratio[2]]

    def __str__(self):
        part_type = "NAPart"
        return str(
            f"\n\nTyp:  {part_type}\n"
            f"Id:   {self.Id}\n"
            f"Pos:  {self.Pos}\n"
            f"Rot:  {self.Rot}\n"
            f"Scl:  {self.Scl}\n"
            f"Col:  #{self.Col}\n"
            f"Amr:  {self.Amr} mm\n"
        )

    def __repr__(self):  # 用于print
        return self.__str__()

    # 定义被存为json文件的格式
    def to_dict(self):
        return {
            "Typ": 'NAPart',
            "Id": self.Id,
            "Pos": list(self.Pos),
            "Rot": list(self.Rot),
            "Scl": list(self.Scl),
            "Col": str(self.Col),
            "Amr": self.Amr,
        }


class AdjustableHull(NAPart):
    All = []

    def __init__(
            self, read_na, Id, pos, rot, scale, color, armor,
            length, height, frontWidth, backWidth, frontSpread, backSpread, upCurve, downCurve,
            heightScale, heightOffset):
        """
        :param Id: 字符串，零件ID
        :param pos: 元组，三个值分别为x,y,z轴的位置
        :param rot: 元组，三个值分别为x,y,z轴的旋转角度
        :param scale: 元组，三个值分别为x,y,z轴的缩放比例
        :param color: 字符串，颜色的十六进制表示
        :param armor: 整型，装甲厚度
        :param length: 浮点型，长度
        :param height: 浮点型，高度
        :param frontWidth: 浮点型，前宽
        :param backWidth: 浮点型，后宽
        :param frontSpread: 浮点型，前扩散
        :param backSpread: 浮点型，后扩散
        :param upCurve: 浮点型，上曲率
        :param downCurve: 浮点型，下曲率
        :param heightScale: 浮点型，前端高度缩放
        :param heightOffset: 浮点型，前端高度偏移
        """
        NAPart.__init__(self, read_na, Id, pos, rot, scale, color, armor)
        self.Len = length
        self.Hei = height
        self.FWid = frontWidth
        self.BWid = backWidth
        self.FSpr = frontSpread
        self.BSpr = backSpread
        self.UCur = upCurve
        self.DCur = downCurve
        self.HScl = heightScale  # 高度缩放
        self.HOff = heightOffset  # 高度偏移
        AdjustableHull.All.append(self)
        self._y_limit = [-self.Hei / 2, self.Hei / 2]
        # ==============================================================================初始化零件的各个坐标
        self.front_z = self.Len / 2  # 零件前端的z坐标
        self.back_z = -self.Len / 2  # 零件后端的z坐标
        self.half_height_scale = self.Hei * self.HScl / 2  # 高度缩放的一半
        self.center_height_offset = self.HOff * self.Hei  # 高度偏移
        self.front_down_y = self.center_height_offset - self.half_height_scale  # 零件前端下端的y坐标
        self.front_up_y = self.center_height_offset + self.half_height_scale  # 零件前端上端的y坐标
        if self.front_down_y < self._y_limit[0]:
            self.front_down_y = self._y_limit[0]
        elif self.front_down_y > self._y_limit[1]:
            self.front_down_y = self._y_limit[1]
        if self.front_up_y > self._y_limit[1]:
            self.front_up_y = self._y_limit[1]
        elif self.front_up_y < self._y_limit[0]:
            self.front_up_y = self._y_limit[0]
        self.back_down_y = - self.Hei / 2
        self.back_up_y = self.Hei / 2
        self.front_down_x = self.FWid / 2
        self.back_down_x = self.BWid / 2
        self.front_up_x = self.front_down_x + self.FSpr / 2  # 扩散也要除以二分之一
        self.back_up_x = self.back_down_x + self.BSpr / 2  # 扩散也要除以二分之一
        # ==============================================================================计算绘图所需的数据
        self.operation_dot_nodes = []  # 位置变换后，曲面变换前的所有点
        self.plot_all_dots = []  # 曲面变换，位置变换后的所有点
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
        self.plot_lines = self.get_plot_lines()
        self.plot_faces = self.get_plot_faces()

    def get_plot_faces(self):
        """
        :return: 绘制零件的方法，绘制零件需的三角形集
        """
        result = {
            "GL_QUADS": [],
            "GL_TRIANGLES": [],
            "GL_QUAD_STRIP": [],
            "GL_POLYGON": [],
        }
        # 缩放并旋转
        dots = rotate_quaternion1(self.vertex_coordinates, self.Scl, self.Rot)
        for key in dots.keys():
            dots[key] += self.Pos  # 平移
        faces = [
            [dots["front_up_left"], dots["front_up_right"], dots["front_down_right"], dots["front_down_left"]],
            [dots["back_up_left"], dots["back_down_left"], dots["back_down_right"], dots["back_up_right"]],
            [dots["front_up_left"], dots["back_up_left"], dots["back_up_right"], dots["front_up_right"]],
            [dots["front_down_left"], dots["front_down_right"], dots["back_down_right"], dots["back_down_left"]],
            [dots["front_up_left"], dots["front_down_left"], dots["back_down_left"], dots["back_up_left"]],
            [dots["front_up_right"], dots["back_up_right"], dots["back_down_right"], dots["front_down_right"]],
        ]
        self.operation_dot_nodes = [
            dots["front_up_left"], dots["front_up_right"], dots["front_down_right"], dots["front_down_left"],
            dots["back_up_left"], dots["back_down_left"], dots["back_down_right"], dots["back_up_right"]]
        if self.UCur < 0.005 and self.DCur <= 0.005:
            self.plot_all_dots = self.operation_dot_nodes
            # 检查同一个面内的点是否重合，重合则添加到三角绘制方法中，否则添加到四边形绘制方法中
            for face in faces:
                use_triangles = False
                added_face = None
                for i in range(3):
                    if np.array_equal(face[i], face[i + 1]):
                        # 去除重复点
                        added_face = face[:i] + face[i + 1:]
                        use_triangles = True
                        break
                if use_triangles:
                    result["GL_TRIANGLES"].append(added_face)
                else:
                    result["GL_QUADS"].append(face)
        else:  # TODO: 有曲率的零件的绘制方法
            front_part_curved_circle_dots, back_part_curved_circle_dots = self.get_initial_Curve_face_dots()
            # 翻转顺序
            reversed_b_up = back_part_curved_circle_dots["up"][::-1]
            reversed_b_down = back_part_curved_circle_dots["down"][::-1]
            # x值取反并存回原来的位置
            symmetry_f_up = [dot * np.array([-1, 1, 1]) for dot in front_part_curved_circle_dots["up"]]
            symmetry_f_down = [dot * np.array([-1, 1, 1]) for dot in front_part_curved_circle_dots["down"]]
            symmetry_b_up = [dot * np.array([-1, 1, 1]) for dot in reversed_b_up]
            symmetry_b_down = [dot * np.array([-1, 1, 1]) for dot in reversed_b_down]

            # 绘制图形集合，截面（前后）用polygon，侧面用quad_strip
            # 拼合点集
            front_set = []
            back_set = []
            # 注意front和back的点集的顺序是相反的，为了渲染的时候能够正确显示
            front_set.extend(symmetry_f_up[:-1])
            front_set.extend(symmetry_f_down[:-1])
            front_set.extend(front_part_curved_circle_dots["down"][::-1][:-1])
            front_set.extend(front_part_curved_circle_dots["up"][::-1][:-1])
            back_set.extend(back_part_curved_circle_dots["up"][:-1])
            back_set.extend(back_part_curved_circle_dots["down"][:-1])
            back_set.extend(symmetry_b_down[:-1])
            back_set.extend(symmetry_b_up[:-1])
            #   两个截面
            result["GL_POLYGON"] = [front_set, back_set]
            #   侧面
            result["GL_QUADS"] = []
            back_set = back_set[::-1]  # 翻转顺序
            back_set = [back_set[(i - 1) % len(back_set)] for i in range(len(back_set))]  # 轮转一个单位
            for i in range(23):
                result["GL_QUADS"].append([front_set[i], back_set[i], back_set[i + 1], front_set[i + 1]])
            result["GL_QUADS"].append([front_set[-1], back_set[-1], back_set[0], front_set[0]])
            # 旋转
            for method, face_set in result.items():
                result[method] = rotate_quaternion0(face_set, self.Scl, self.Rot)
                # 缩放和平移
                for face in result[method]:
                    for dot in face:
                        dot += self.Pos
            self.plot_all_dots = result["GL_POLYGON"][0] + result["GL_POLYGON"][1]
        return result

    def get_initial_Curve_face_dots(self):
        """
        获取扭曲后的零件圆形弧面的基础点集，从圆形（r=1）开始，然后进行高度缩放，底部缩放，顶部缩放，
        底部到顶部的缩放变换是线性的，也就是梯形内接变形圆
        :return:
        """
        # 单位圆的点集，12个左侧点，先忽略右侧点
        # 当Curve为0时，就是square_dots，其与circle_dots做差，令circle_dots加上差值乘以Curve就是最终的点集
        square_dots = {"up": [
            np.array([0, 1]),
            np.array([np.tan(np.deg2rad(15)), 1]),
            np.array([np.tan(np.deg2rad(30)), 1]),
            np.array([1, 1]),
            np.array([1, np.tan(np.deg2rad(30))]),
            np.array([1, np.tan(np.deg2rad(15))]),
            np.array([1, 0]),
        ], "down": [
            np.array([1, 0]),
            np.array([1, -np.tan(np.deg2rad(15))]),
            np.array([1, -np.tan(np.deg2rad(30))]),
            np.array([1, -1]),
            np.array([np.tan(np.deg2rad(30)), -1]),
            np.array([np.tan(np.deg2rad(15)), -1]),
            np.array([0, -1]),
        ]}
        Front_part_curved_circle_dots = {"up": [], "down": []}
        Back_part_curved_circle_dots = {"up": [], "down": []}
        for i in range(7):  # 从上到下，一共7个点，也就是从(0, 1, self.front_z)到(1, 0, self.front_z)
            angle = np.deg2rad(15 * i)
            circle_up = np.array([np.sin(angle), np.cos(angle)])
            circle_down = np.array([np.cos(angle), - np.sin(angle)])
            Front_part_curved_circle_dots["up"].append(
                np.append(circle_up + (square_dots["up"][i] - circle_up) * (1 - self.UCur), self.front_z))
            Front_part_curved_circle_dots["down"].append(
                np.append(circle_down + (square_dots["down"][i] - circle_down) * (1 - self.DCur), self.front_z))
            Back_part_curved_circle_dots["up"].append(
                np.append(circle_up + (square_dots["up"][i] - circle_up) * (1 - self.UCur), self.back_z))
            Back_part_curved_circle_dots["down"].append(
                np.append(circle_down + (square_dots["down"][i] - circle_down) * (1 - self.DCur), self.back_z))
            # 进行横向缩放
            Front_part_curved_circle_dots["up"][i][0] *= self.get_horizontal_scale(
                Front_part_curved_circle_dots["up"][i][1], True)
            Front_part_curved_circle_dots["down"][i][0] *= self.get_horizontal_scale(
                Front_part_curved_circle_dots["down"][i][1], True)
            Back_part_curved_circle_dots["up"][i][0] *= self.get_horizontal_scale(
                Back_part_curved_circle_dots["up"][i][1], False)
            Back_part_curved_circle_dots["down"][i][0] *= self.get_horizontal_scale(
                Back_part_curved_circle_dots["down"][i][1], False)
            # 进行y高度缩放
            Front_part_curved_circle_dots["up"][i][1] *= self.half_height_scale
            Front_part_curved_circle_dots["down"][i][1] *= self.half_height_scale
            Back_part_curved_circle_dots["up"][i][1] *= self.Hei / 2
            Back_part_curved_circle_dots["down"][i][1] *= self.Hei / 2
            # 进行y高度偏移
            Front_part_curved_circle_dots["up"][i][1] += self.center_height_offset
            Front_part_curved_circle_dots["down"][i][1] += self.center_height_offset
            # 进行y值限制
            if Front_part_curved_circle_dots["up"][i][1] > self._y_limit[1]:
                Front_part_curved_circle_dots["up"][i][1] = self._y_limit[1]
            elif Front_part_curved_circle_dots["up"][i][1] < self._y_limit[0]:
                Front_part_curved_circle_dots["up"][i][1] = self._y_limit[0]
            if Front_part_curved_circle_dots["down"][i][1] > self._y_limit[1]:
                Front_part_curved_circle_dots["down"][i][1] = self._y_limit[1]
            elif Front_part_curved_circle_dots["down"][i][1] < self._y_limit[0]:
                Front_part_curved_circle_dots["down"][i][1] = self._y_limit[0]
        return Front_part_curved_circle_dots, Back_part_curved_circle_dots

    def get_horizontal_scale(self, y, front=True):
        if front:
            return ((self.front_up_x - self.front_down_x) * y + (self.front_up_x + self.front_down_x)) / 2
        else:
            return ((self.back_up_x - self.back_down_x) * y + (self.back_up_x + self.back_down_x)) / 2

    def get_plot_lines(self):
        result = {
            "1": [self.vertex_coordinates["front_up_left"], self.vertex_coordinates["front_up_right"],
                  self.vertex_coordinates["front_down_right"], self.vertex_coordinates["front_down_left"],
                  self.vertex_coordinates["front_up_left"], self.vertex_coordinates["back_up_left"],
                  self.vertex_coordinates["back_up_right"], self.vertex_coordinates["front_up_right"]],
            "2": [self.vertex_coordinates["front_down_left"], self.vertex_coordinates["back_down_left"],
                  self.vertex_coordinates["back_down_right"], self.vertex_coordinates["front_down_right"]],
            "3": [self.vertex_coordinates["back_up_left"], self.vertex_coordinates["back_down_left"]],
            "4": [self.vertex_coordinates["back_up_right"], self.vertex_coordinates["back_down_right"]]
        }
        # 进行旋转，平移，缩放
        result = rotate_quaternion2(result, self.Scl, self.Rot)
        for key in result.keys():
            for i in range(len(result[key])):
                result[key][i] += self.Pos

        return result

    def get_initial_vertex_coordinates(self):
        return {
            "front_up_left": np.array([self.front_up_x, self.front_up_y, self.front_z]),
            "front_up_right": np.array([-self.front_up_x, self.front_up_y, self.front_z]),
            "front_down_left": np.array([self.front_down_x, self.front_down_y, self.front_z]),
            "front_down_right": np.array([-self.front_down_x, self.front_down_y, self.front_z]),
            "back_up_left": np.array([self.back_up_x, self.back_up_y, self.back_z]),
            "back_up_right": np.array([-self.back_up_x, self.back_up_y, self.back_z]),
            "back_down_left": np.array([self.back_down_x, self.back_down_y, self.back_z]),
            "back_down_right": np.array([-self.back_down_x, self.back_down_y, self.back_z]),
        }

    def change_attrs(self, position, armor,
                     length, height, frontWidth, backWidth, frontSpread, backSpread,
                     upCurve, downCurve, heightScale, heightOffset,
                     update=False):
        # ==============================================================================更新零件的各个属性
        try:
            self.Pos = [round(float(i), 3) for i in position]
            self.Amr = int(armor)
            self.Len = float(length)
            self.Hei = float(height)
            self.FWid = float(frontWidth)
            self.BWid = float(backWidth)
            self.FSpr = float(frontSpread)
            self.BSpr = float(backSpread)
            self.UCur = float(upCurve)
            self.DCur = float(downCurve)
            self.HScl = float(heightScale)  # 高度缩放
            self.HOff = float(heightOffset)  # 高度偏移
            self._y_limit = [-self.Hei / 2, self.Hei / 2]
        except ValueError:
            return False
        # ==============================================================================初始化零件的各个坐标
        self.front_z = self.Len / 2  # 零件前端的z坐标
        self.back_z = -self.Len / 2  # 零件后端的z坐标
        self.half_height_scale = self.Hei * self.HScl / 2  # 高度缩放的一半
        self.center_height_offset = self.HOff * self.Hei  # 高度偏移
        self.front_down_y = self.center_height_offset - self.half_height_scale  # 零件前端下端的y坐标
        self.front_up_y = self.center_height_offset + self.half_height_scale  # 零件前端上端的y坐标
        if self.front_down_y < self._y_limit[0]:
            self.front_down_y = self._y_limit[0]
        elif self.front_down_y > self._y_limit[1]:
            self.front_down_y = self._y_limit[1]
        if self.front_up_y > self._y_limit[1]:
            self.front_up_y = self._y_limit[1]
        elif self.front_up_y < self._y_limit[0]:
            self.front_up_y = self._y_limit[0]
        self.back_down_y = - self.Hei / 2
        self.back_up_y = self.Hei / 2
        self.front_down_x = self.FWid / 2
        self.back_down_x = self.BWid / 2
        self.front_up_x = self.front_down_x + self.FSpr / 2  # 扩散也要除以二分之一
        self.back_up_x = self.back_down_x + self.BSpr / 2  # 扩散也要除以二分之一
        # ==============================================================================计算绘图所需的数据
        self.plot_all_dots = []  # 曲面变换前，位置变换后的所有点
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
        self.plot_lines = self.get_plot_lines()
        self.plot_faces = self.get_plot_faces()
        if update:
            # 修改glWin的genList状态
            for mode in self.glWin.gl_commands.keys():
                self.glWin.gl_commands[mode][1] = True
            self.glWin.update_selected_list = True
            self.glWin.list_id_selected = None
            # 修改零件本身的genList状态
            self.updateList = True
            self.update_selectedList = True
            self.glWin.paintGL()
            self.glWin.update()
            # 修改glWin的genList状态
            for mode in self.glWin.gl_commands.keys():
                self.glWin.gl_commands[mode][1] = False
            self.glWin.update_selected_list = False
            # 修改零件本身的genList状态
            self.updateList = False
            self.update_selectedList = False
        return True

    def change_attrs_with_relative_parts(self, position, armor,
                                         length, height, frontWidth, backWidth, frontSpread, backSpread,
                                         upCurve, downCurve, heightScale, heightOffset,
                                         with_vertical_change=True, with_horizontal_change=True):
        original_position = self.Pos
        original_height = self.Hei
        original_front_width = self.FWid
        original_back_width = self.BWid
        original_front_spread = self.FSpr
        original_back_spread = self.BSpr
        original_up_curve = self.UCur
        original_down_curve = self.DCur
        original_height_scale = self.HScl
        original_height_offset = self.HOff
        # 计算差值
        pos_diff = np.array([float(i) for i in position]) - np.array(original_position)
        height_diff = float(height) - original_height
        front_down_width_diff = float(frontWidth) - original_front_width
        front_up_width_diff = float(frontSpread) - original_front_spread + front_down_width_diff
        back_down_width_diff = float(backWidth) - original_back_width
        back_up_width_diff = float(backSpread) - original_back_spread + back_down_width_diff
        up_curve_diff = float(upCurve) - original_up_curve
        down_curve_diff = float(downCurve) - original_down_curve
        height_scale_diff = float(heightScale) - original_height_scale
        height_offset_diff = float(heightOffset) - original_height_offset
        # 更新零件的属性
        self.change_attrs(position, armor,
                          length, height, frontWidth, backWidth, frontSpread, backSpread,
                          upCurve, downCurve, heightScale, heightOffset)
        front_part, back_part, left_part, right_part, up_part, down_part = None, None, None, None, None, None
        front_parts, back_parts, left_parts, right_parts, up_parts, down_parts = [], [], [], [], [], []
        # 对前后左右的可能需要修改的对象进行同步修改
        relation_map = self.allParts_relationMap.basicMap[self]
        # 对方向关系映射进行遍历
        for direction in [PartRelationMap.FRONT, PartRelationMap.BACK, PartRelationMap.LEFT, PartRelationMap.RIGHT,
                          PartRelationMap.UP, PartRelationMap.DOWN]:
            if relation_map[direction] == {}:  # 该方向没有零件，跳过
                continue
            # 零件移动的情况（目前仅考虑所有零件x=0的情况）
            if direction in (PartRelationMap.FRONT, PartRelationMap.BACK  # 只有y轴变化
                             ) and pos_diff[1] != 0 and pos_diff[0] == pos_diff[2] == 0:
                for part in relation_map[direction].keys():
                    part.change_attrs(
                        (part.Pos[0], part.Pos[1] + pos_diff[1], part.Pos[2]), part.Amr,
                        part.Len, part.Hei, part.FWid, part.BWid, part.FSpr,
                        part.BSpr, part.UCur, part.DCur, part.HScl,
                        part.HOff)
            if direction in (PartRelationMap.LEFT, PartRelationMap.RIGHT  # 只有x轴变化
                             ) and pos_diff[0] != 0 and pos_diff[1] == pos_diff[2] == 0:
                pass
            if direction in (PartRelationMap.UP, PartRelationMap.DOWN  # 只有z轴变化
                             ) and pos_diff[2] != 0 and pos_diff[0] == pos_diff[1] == 0:
                for part in relation_map[direction].keys():
                    part.change_attrs(
                        (part.Pos[0], part.Pos[1], part.Pos[2] + pos_diff[2]), part.Amr,
                        part.Len, part.Hei, part.FWid, part.BWid, part.FSpr,
                        part.BSpr, part.UCur, part.DCur, part.HScl,
                        part.HOff)
            # 改变高度的情况
            if direction in (PartRelationMap.FRONT, PartRelationMap.BACK) and height_diff != 0:
                if tuple(self.Pos) in ((0, 0, 0), (0, 180, 0)):
                    for part in relation_map[direction].keys():
                        if tuple(part.Pos) in ((0, 0, 0), (0, 180, 0)):
                            part.change_attrs(
                                part.Pos, part.Amr,
                                part.Len, part.Hei + height_diff, part.FWid, part.BWid, part.FSpr,
                                part.BSpr, part.UCur, part.DCur, part.HScl,
                                part.HOff)

            # 改变宽度的情况（需要判断当前零件角度）
            if tuple(self.Pos) == (0, 0, 0):
                t_front_up_width_diff = front_up_width_diff
                t_front_down_width_diff = front_down_width_diff
                t_back_up_width_diff = back_up_width_diff
                t_back_down_width_diff = back_down_width_diff
            elif tuple(self.Pos) == (0, 180, 0):
                t_front_up_width_diff = back_up_width_diff
                t_front_down_width_diff = back_down_width_diff
                t_back_up_width_diff = front_up_width_diff
                t_back_down_width_diff = front_down_width_diff
            elif tuple(self.Pos) == (0, 90, 0):
                # TODO: 旋转90度的情况
                pass
            elif tuple(self.Pos) == (0, 270, 0):
                # TODO: 旋转270度的情况
                pass

            # 修正完方向后，开始进行宽度变化

            # if (front_down_width_diff and tuple(self.Rot) == (0, 0, 0)) or (
            #         back_down_width_diff and tuple(self.Rot) == (0, 180, 0)):  # 零件前底部宽度变化
            #     t_front_down_width_diff = front_down_width_diff if tuple(self.Rot) == (0, 0, 0) else back_down_width_diff
            #     # if direction == PartRelationMap.UP:
            #     #     # 上方零件前方底部宽度变化，扩散反向变化以保持前方顶部宽度不变
            #     #     up_part = list(relation_map[direction].keys())[0]
            #     #     if tuple(up_part.Rot) == (0, 0, 0):
            #     #         up_part.change_attrs(
            #     #             up_part.Pos, up_part.Amr, up_part.Len, up_part.Hei,
            #     #             up_part.FWid + front_up_width_diff, up_part.BWid,
            #     #             up_part.FSpr - front_down_width_diff, up_part.BSpr,
            #     #             up_part.UCur, up_part.DCur, up_part.HScl, up_part.HOff)
            #     #     # 上前方零件的后底部宽度随着本零件的前上宽度变化而变化，后扩散反向变化以保持后顶部宽度不变
            #     #     up_front_part = list(self.allParts_relationMap.basicMap[up_part][PartRelationMap.FRONT].keys())[0]
            #     #     if tuple(up_front_part.Rot) == (0, 0, 0):
            #     #         up_front_part.change_attrs(
            #     #             up_front_part.Pos, up_front_part.Amr, up_front_part.Len, up_front_part.Hei,
            #     #             up_front_part.FWid, up_front_part.BWid + front_up_width_diff,
            #     #             up_front_part.FSpr, up_front_part.BSpr - front_down_width_diff,
            #     #             up_front_part.UCur, up_front_part.DCur, up_front_part.HScl, up_front_part.HOff)
            #     if direction == PartRelationMap.DOWN and with_vertical_change:
            #         # 下方零件仅随着零件宽度改变而改变扩散
            #         down_part = list(relation_map[direction].keys())[0]
            #         if tuple(down_part.Rot) == (0, 0, 0):
            #             down_part.change_attrs(
            #                 down_part.Pos, down_part.Amr, down_part.Len, down_part.Hei,
            #                 down_part.FWid, down_part.BWid,
            #                 down_part.FSpr + t_front_down_width_diff, down_part.BSpr,
            #                 down_part.UCur, down_part.DCur, down_part.HScl, down_part.HOff)
            #         if tuple(down_part.Rot) == (0, 180, 0):  # 前后反转
            #             down_part.change_attrs(
            #                 down_part.Pos, down_part.Amr, down_part.Len, down_part.Hei,
            #                 down_part.FWid, down_part.BWid,
            #                 down_part.FSpr, down_part.BSpr + t_front_down_width_diff,
            #                 down_part.UCur, down_part.DCur, down_part.HScl, down_part.HOff)
            #         # 下前方零件的后顶部宽度（扩散）随着本零件的前下宽度变化而变化
            #         if with_horizontal_change:
            #             down_front_part = list(self.allParts_relationMap.basicMap[down_part][PartRelationMap.FRONT].keys())[0]
            #             if tuple(down_front_part.Rot) == (0, 0, 0):
            #                 down_front_part.change_attrs(
            #                     down_front_part.Pos, down_front_part.Amr, down_front_part.Len, down_front_part.Hei,
            #                     down_front_part.FWid, down_front_part.BWid,
            #                     down_front_part.FSpr, down_front_part.BSpr + t_front_down_width_diff,
            #                     down_front_part.UCur, down_front_part.DCur, down_front_part.HScl, down_front_part.HOff)
            #     elif direction == PartRelationMap.FRONT and with_horizontal_change:
            #         # 前方零件的后方和本零件的前方同步变化
            #         front_part = list(relation_map[direction].keys())[0]
            #         if tuple(front_part.Rot) == (0, 0, 0):
            #             front_part.change_attrs(
            #                 front_part.Pos, front_part.Amr, front_part.Len, front_part.Hei,
            #                 front_part.FWid, front_part.BWid + t_front_down_width_diff,
            #                 front_part.FSpr, front_part.BSpr - t_front_down_width_diff,
            #                 front_part.UCur, front_part.DCur, front_part.HScl, front_part.HOff)
            self.glWin.update()

    def add_z(self, smooth=False):
        """
        对零件进行z细分，平均分为前后两部分
        :param smooth: 是否根据前后零件对中间层进行平滑
        :return:
        """
        if self.HOff != 0:  # 暂时不支持有高度偏移的零件进行z细分
            return
        front_vector = np.array([0, 0, 1])
        # 以0,0,1方向为前方，开始以self.Rot旋转
        front_vector = rotate_quaternion(front_vector, self.Rot)
        if self in self.allParts_relationMap.basicMap.keys():
            # 寻找前后左右上下的零件
            front_parts = list(self.allParts_relationMap.basicMap[self][PartRelationMap.FRONT].keys())
            back_parts = list(self.allParts_relationMap.basicMap[self][PartRelationMap.BACK].keys())
            left_parts = list(self.allParts_relationMap.basicMap[self][PartRelationMap.LEFT].keys())
            right_parts = list(self.allParts_relationMap.basicMap[self][PartRelationMap.RIGHT].keys())
            up_parts = list(self.allParts_relationMap.basicMap[self][PartRelationMap.UP].keys())
            down_parts = list(self.allParts_relationMap.basicMap[self][PartRelationMap.DOWN].keys())
            # 根据旋转角求出位置的偏移（往向量的方向移动1/4Len乘以缩放比例）
            if front_vector.all() == np.array([0, 0, 1]).all():
                front_parts, back_parts = front_parts, back_parts
            elif front_vector.all() == np.array([0, 0, -1]).all():
                front_parts, back_parts = back_parts, front_parts
            elif front_vector.all() == np.array([1, 0, 0]).all():
                front_parts, back_parts = left_parts, right_parts
            elif front_vector.all() == np.array([-1, 0, 0]).all():
                front_parts, back_parts = right_parts, left_parts
            elif front_vector.all() == np.array([0, 1, 0]).all():
                front_parts, back_parts = up_parts, down_parts
            elif front_vector.all() == np.array([0, -1, 0]).all():
                front_parts, back_parts = down_parts, up_parts
            else:
                front_parts, back_parts = [], []
        else:
            front_parts, back_parts = [], []
        # 得到前后零件
        front_part = None
        back_part = None
        if front_parts:
            for p in front_parts:
                v1 = np.array(p.Pos) - np.array(self.Pos)
                v2 = front_vector * self.Scl[2] * (self.Len / 2 + p.Len / 2)
                if np.linalg.norm(v1 - v2) < 0.001:
                    # 如果前后相接：
                    front_part = p
                    break
        if back_parts:
            for p in back_parts:
                v1 = np.array(self.Pos) - np.array(p.Pos)
                v2 = front_vector * self.Scl[2] * (self.Len / 2 + p.Len / 2)
                if np.linalg.norm(v1 - v2) < 0.001:
                    # 如果前后相接：
                    back_part = p
                    break
        if smooth and (front_part or back_part):
            # 计算中间层的宽度变化率
            self_wid_spr_ratio = (self.FWid - self.BWid) * self.Scl[0] / (self.Len * self.Scl[2])
            # 计算中间层的扩散变化率
            self_spr_spr_ratio = (self.FSpr - self.BSpr) * self.Scl[0] / (self.Len * self.Scl[2])
            # 计算中间层的高度变化率
            self_hei_scl_ratio = (self.Hei * self.HScl - self.Hei) / (self.Len * self.Scl[2])
            if front_part:
                # 前零件的宽度变化率
                front_wid_spr_ratio = (front_part.FWid - front_part.BWid) * front_part.Scl[0] / (front_part.Len * front_part.Scl[2])
                # 前零件的扩散变化率
                front_spr_spr_ratio = (front_part.FSpr - front_part.BSpr) * front_part.Scl[0] / (front_part.Len * front_part.Scl[2])
                # 前零件的高度变化率
                front_hei_scl_ratio = (front_part.Hei * front_part.HScl - front_part.Hei) / (front_part.Len * front_part.Scl[2])
            if back_part:
                # 后零件的宽度变化率
                back_wid_spr_ratio = (back_part.FWid - back_part.BWid) * back_part.Scl[0] / (back_part.Len * back_part.Scl[2])
                # 后零件的扩散变化率
                back_spr_spr_ratio = (back_part.FSpr - back_part.BSpr) * back_part.Scl[0] / (back_part.Len * back_part.Scl[2])
                # 后零件的高度变化率
                back_hei_scl_ratio = (back_part.Hei * back_part.HScl - back_part.Hei) / (back_part.Len * back_part.Scl[2])
            if front_part and not back_part:
                # 给back_part的比率赋值为前零件-2*(前零件-中零件)
                back_wid_spr_ratio = front_wid_spr_ratio + 2 * (front_wid_spr_ratio - self_wid_spr_ratio)
                back_spr_spr_ratio = front_spr_spr_ratio + 2 * (front_spr_spr_ratio - self_spr_spr_ratio)
                back_hei_scl_ratio = front_hei_scl_ratio + 2 * (front_hei_scl_ratio - self_hei_scl_ratio)
            elif not front_part and back_part:
                # 给front_part的比率赋值为后零件-2*(后零件-中零件)
                front_wid_spr_ratio = back_wid_spr_ratio + 2 * (back_wid_spr_ratio - self_wid_spr_ratio)
                front_spr_spr_ratio = back_spr_spr_ratio + 2 * (back_spr_spr_ratio - self_spr_spr_ratio)
                front_hei_scl_ratio = back_hei_scl_ratio + 2 * (back_hei_scl_ratio - self_hei_scl_ratio)
            # 计算中间层分为两段后前后分别的比率
            # 用贝塞尔曲线拟合
            wid_ratios = fit_bezier(
                front_wid_spr_ratio, back_wid_spr_ratio,
                self.Len * self.Scl[2], (self.FWid - self.BWid) * self.Scl[0], 2)
            spr_ratios = fit_bezier(
                front_spr_spr_ratio, back_spr_spr_ratio,
                self.Len * self.Scl[2], (self.FSpr - self.BSpr) * self.Scl[0], 2)
            hei_ratios = fit_bezier(
                front_hei_scl_ratio, back_hei_scl_ratio,
                self.Len * self.Scl[2], (self.Hei * self.HScl - self.Hei) * self.Scl[1], 2)
            B_wid_spr_ratio = wid_ratios[1]
            B_spr_spr_ratio = spr_ratios[1]
            B_hei_scl_ratio = hei_ratios[1]
            # 计算前后零件的数值：
            mid_width = self.BWid + B_wid_spr_ratio * self.Len * self.Scl[2] * 0.5
            mid_spread = self.BSpr + B_spr_spr_ratio * self.Len * self.Scl[2] * 0.5
            mid_height = self.Hei + B_hei_scl_ratio * self.Len * self.Scl[2] * 0.5
        else:  # 不平滑的情况
            mid_width = (self.FWid + self.BWid) / 2
            mid_spread = (self.FSpr + self.BSpr) / 2
            mid_height = (self.Hei * self.HScl + self.Hei) / 2
        pos_offset = front_vector * self.Len / 4 * self.Scl[2]
        F_Pos = np.array(self.Pos) + pos_offset
        B_Pos = np.array(self.Pos) - pos_offset
        F_Hei = mid_height
        F_HScl = (self.Hei * self.HScl) / mid_height
        B_Hei = self.Hei
        B_HScl = mid_height / self.Hei

        FP = AdjustableHull(
            self.read_na_obj, self.Id, F_Pos, self.Rot, self.Scl, self.Col, self.Amr,
            self.Len / 2, F_Hei, self.FWid, mid_width, self.FSpr, mid_spread, self.UCur, self.DCur, F_HScl, 0)
        BP = AdjustableHull(
            self.read_na_obj, self.Id, B_Pos, self.Rot, self.Scl, self.Col, self.Amr,
            self.Len / 2, B_Hei, mid_width, self.BWid, mid_spread, self.BSpr, self.UCur, self.DCur, B_HScl, 0)
        # 删除原来的零件
        self.read_na_obj.DrawMap[f"#{self.Col}"].remove(self)
        # 往read_na的drawMap中添加零件
        self.read_na_obj.DrawMap[f"#{self.Col}"].append(FP)
        self.read_na_obj.DrawMap[f"#{self.Col}"].append(BP)
        if self.Rot[0] % 90 == 0 and self.Rot[1] % 90 == 0 and self.Rot[2] % 90 == 0:
            # 添加关系图
            self.allParts_relationMap.replace(FP, BP, self, None)
        # 删除原来的零件
        NAPart.id_map.pop(id(self) % 4294967296)
        NAPart.hull_design_tab_id_map.pop(id(self) % 4294967296)
        # 添加新的零件
        NAPart.hull_design_tab_id_map[id(FP) % 4294967296] = FP
        NAPart.hull_design_tab_id_map[id(BP) % 4294967296] = BP
        self.glWin.selected_gl_objects[self.glWin.show_3d_obj_mode] = [FP, BP]
        for mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[mode][1] = True
        self.glWin.paintGL()
        for mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[mode][1] = False
        self.glWin.update()

    def scale(self, ratio: list, update=False):
        super().scale(ratio)
        self.plot_all_dots = []  # 曲面变换前，位置变换后的所有点
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
        self.plot_lines = self.get_plot_lines()
        self.plot_faces = self.get_plot_faces()
        if update:
            # 修改glWin的genList状态
            for mode in self.glWin.gl_commands.keys():
                self.glWin.gl_commands[mode][1] = True
            self.glWin.update_selected_list = True
            self.glWin.list_id_selected = None
            # 修改零件本身的genList状态
            self.updateList = True
            self.update_selectedList = True
            self.glWin.paintGL()
            self.glWin.update()
            # 修改glWin的genList状态
            for mode in self.glWin.gl_commands.keys():
                self.glWin.gl_commands[mode][1] = False
            self.glWin.update_selected_list = False
            # 修改零件本身的genList状态
            self.updateList = False
            self.update_selectedList = False
        return True

    def __str__(self):
        part_type = str(self.__class__.__name__)
        return str(
            f"\nTyp:  {part_type}\t"
            f"Id:   {self.Id}\n"
            f"Pos:  {self.Pos}\t"
            f"Rot:  {self.Rot}\t"
            f"Scl:  {self.Scl}\t"
            f"Col:  #{self.Col}\t"
            f"Amr:  {self.Amr} mm\n"
            f"Len:  {self.Len} m\t"
            f"Hei:  {self.Hei} m\t"
            f"FWid: {self.FWid} m\t"
            f"BWid: {self.BWid} m\t"
            f"FSpr: {self.FSpr} m\t"
            f"BSpr: {self.BSpr} m\t"
            f"UCur: {self.UCur}  \t"
            f"DCur: {self.DCur}  \t"
            f"HScl: {self.HScl}  \t"
            f"HOff: {self.HOff} m\n"
        )

    # 定义被存为json文件的格式
    def to_dict(self):
        return {
            "Typ": 'AdjustableHull',
            "Id": self.Id,
            "Pos": list(self.Pos),
            "Rot": list(self.Rot),
            "Scl": list(self.Scl),
            "Col": str(self.Col),
            "Amr": self.Amr,
            "Len": self.Len,
            "Hei": self.Hei,
            "FWid": self.FWid,
            "BWid": self.BWid,
            "FSpr": self.FSpr,
            "BSpr": self.BSpr,
            "UCur": self.UCur,
            "DCur": self.DCur,
            "HScl": self.HScl,
            "HOff": self.HOff,
        }

    def draw_pre(self, gl):
        alpha = 1
        color = "#" + self.Col
        # 16进制颜色转换为RGBA
        _rate = 255
        color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, alpha
        gl.glColor4f(*color_)
        if self.pre_genList:
            gl.glCallList(self.pre_genList)
            return
        self.pre_genList = gl.glGenLists(1)
        gl.glNewList(self.pre_genList, gl.GL_COMPILE_AND_EXECUTE)
        try:
            self.plot_faces = self.plot_faces
        except AttributeError:
            return
        for draw_method, faces_dots in self.plot_faces.items():
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
        gl.glEndList()

    def draw(self, gl, transparent=False):
        gl.glLoadName(id(self) % 4294967296)
        alpha = 1 if transparent is False else 0.3
        color = "#" + self.Col
        # 16进制颜色转换为RGBA
        _rate = 255
        color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, alpha
        gl.glColor4f(*color_)
        if self.genList and self.updateList is False:
            gl.glCallList(self.genList)
            return
        self.genList = gl.glGenLists(1)
        gl.glNewList(self.genList, gl.GL_COMPILE_AND_EXECUTE)

        try:
            self.plot_faces = self.plot_faces
        except AttributeError:
            return
        for draw_method, faces_dots in self.plot_faces.items():
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
        gl.glEndList()

    def draw_selected(self, gl, theme_color):
        # 材料设置
        gl.glColor4f(*theme_color["被选中"][0])
        if self.selected_genList and self.update_selectedList is False:
            gl.glCallList(self.selected_genList)
            return
        self.selected_genList = gl.glGenLists(1)
        gl.glNewList(self.selected_genList, gl.GL_COMPILE_AND_EXECUTE)
        for draw_method, faces_dots in self.plot_faces.items():
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
        gl.glColor4f(*theme_color["橙色"][0])
        gl.glLineWidth(3)
        for _line_name, line in self.plot_lines.items():
            # 首尾不相连
            gl.glBegin(gl.GL_LINE_STRIP)
            for dot in line:
                gl.glVertex3f(dot[0], dot[1], dot[2])
            gl.glEnd()
        gl.glEndList()


class MainWeapon(NAPart):
    All = []

    def __init__(self, read_na, Id, pos, rot, scale, color, armor, manual_control, elevator):
        super().__init__(read_na, Id, pos, rot, scale, color, armor)
        self.ManualControl = manual_control
        self.ElevatorH = elevator
        MainWeapon.All.append(self)

    # 定义被存为json文件的格式
    def to_dict(self):
        return {
            "Typ": 'MainWeapon',
            "Id": self.Id,
            "Pos": list(self.Pos),
            "Rot": list(self.Rot),
            "Scl": list(self.Scl),
            "Col": str(self.Col),
            "Amr": self.Amr,
            "ManualControl": self.ManualControl,
            "ElevatorH": self.ElevatorH,
        }


class ReadNA:
    NaPathMode = "folder_path"
    NaDataMode = "data"

    def __init__(self, filepath: Union[str, bool] = False, data=None, show_statu_func=None, glWin=None,
                 design_tab=False):
        """

        :param filepath:
        :param data: 字典，键是颜色的十六进制表示，值是零件的列表，但是尚未实例化，是字典形式的数据
        :param show_statu_func:
        """
        self.glWin = glWin  # 用于绘制的窗口

        self.filename: str  # 文件名
        self.filepath: str  # 文件路径
        self.ShipName: str  # 船名
        self.Author: str  # 作者
        self.HornType: str  # 喇叭类型
        self.HornPitch: str  # 喇叭音高
        self.TracerCol: str  # 弹道颜色
        self.Parts: List[NAPart]  # 所有零件的列表
        self.Weapons: List[MainWeapon]  # 所有武器的列表
        self.AdjustableHulls: List[AdjustableHull]  # 所有可调节船体的列表
        self.ColorPartsMap: Dict[str, List[NAPart]]  # 用于绘制的颜色-零件映射表
        self.show_statu_func: Callable  # 用于显示状态的函数
        self.partRelationMap: PartRelationMap  # 零件关系图，包含零件的上下左右前后关系
        # 赋值
        self.show_statu_func = show_statu_func
        self.Parts = []
        self.partRelationMap = PartRelationMap(self, self.show_statu_func)  # 零件关系图，包含零件的上下左右前后关系
        if filepath is False:
            total_layer_time = 0
            total_relation_time = 0
            total_dot_time = 0
            self.Mode = ReadNA.NaDataMode
            # ===================================================================== 实例化data中的零件
            self.ColorPartsMap = {}
            total_parts_num = sum([len(parts) for parts in data.values()])
            i = 0
            st = time.time()
            self.show_statu_func(f"正在实例化零件，进度：0 %", "process")
            for color, parts in data.items():
                for part in parts:
                    if part["Typ"] == "NAPart" or part["Typ"] == "Part":  # TODO: Part名称已经被弃用
                        obj = NAPart(
                            self,
                            part["Id"],
                            tuple(part["Pos"]), tuple(part["Rot"]), tuple(abs(i) for i in part["Scl"]),
                            str(part["Col"]), int(part["Amr"])
                        )
                    elif part["Typ"] == "MainWeapon":
                        try:
                            manual_control = part["ManualControl"]
                        except KeyError:
                            manual_control = part["ManualControl"] = None
                        try:
                            elevator = float(part["ElevatorH"])
                        except:
                            elevator = part["ElevatorH"] = None
                        obj = MainWeapon(
                            read_na=self,
                            Id=part["Id"],
                            pos=tuple(part["Pos"]),
                            rot=tuple(part["Rot"]),
                            scale=tuple(abs(i) for i in part["Scl"]),
                            color=str(part["Col"]),
                            armor=int(part["Amr"]),
                            manual_control=manual_control,
                            elevator=elevator
                        )
                    elif part["Typ"] == AdjustableHull.__name__:
                        obj = AdjustableHull(
                            self,
                            part["Id"],
                            tuple(part["Pos"]), tuple([round(i, 3) for i in part["Rot"]]),
                            tuple(abs(i) for i in part["Scl"]),
                            str(part["Col"]), int(part["Amr"]),
                            float(part["Len"]), float(part["Hei"]),
                            float(part["FWid"]), float(part["BWid"]),
                            float(part["FSpr"]), float(part["BSpr"]),
                            float(part["UCur"]), float(part["DCur"]),
                            float(part["HScl"]), float(part["HOff"])
                        )
                    else:
                        raise ValueError(f"未知的零件类型：{part['Typ']}")
                    # 添加颜色
                    _color = f"#{part['Col']}"
                    if _color not in self.ColorPartsMap.keys():
                        self.ColorPartsMap[_color] = []
                    self.ColorPartsMap[_color].append(obj)
                    self.Parts.append(obj)
                    if design_tab:
                        NAPart.hull_design_tab_id_map[id(obj) % 4294967296] = obj
                    # 初始化零件关系图
                    layer_t, relation_t, dot_t = self.partRelationMap.add_part(obj)
                    total_layer_time += layer_t
                    total_relation_time += relation_t
                    total_dot_time += dot_t
                    average_layer_time = round(total_layer_time / (i + 1), 4)
                    average_relation_time = round(total_relation_time / (i + 1), 4)
                    average_dot_time = round(total_dot_time / (i + 1), 4)
                    # 标准化（填补0）
                    layer_t = str(layer_t).ljust(6, '0')
                    relation_t = str(relation_t).ljust(6, '0')
                    dot_t = str(dot_t).ljust(6, '0')
                    average_layer_time = str(average_layer_time).ljust(6, '0')
                    average_relation_time = str(average_relation_time).ljust(6, '0')
                    average_dot_time = str(average_dot_time).ljust(6, '0')
                    if i % 3 == 0:
                        process = round(i / total_parts_num * 100, 2)
                        self.show_statu_func(
                            f"正在实例化第 {i} / {total_parts_num} 个零件： {process} %"
                            f"\t\t\t\t单件耗时：     截面对象  {layer_t} s     零件关系  {relation_t} s     节点集合  {dot_t} s"
                            f"\t\t平均耗时：     截面对象  {average_layer_time} s     零件关系  {average_relation_time} s     节点集合  {average_dot_time} s",
                            "process")
                    if self.glWin and self.glWin.initialized and i % (total_parts_num / 400) == 0:
                        self.glWin.paintGL()
                    i += 1
            self.show_statu_func(f"零件实例化完成，耗时：{round(time.time() - st, 2)} s", "success")
            self.partRelationMap.sort()
            self.partRelationMap.init(drawMap=None, init=False)  # 上方已经初始化了drawMap。
        else:  # =========================================================================== 读取na文件
            self.Mode = ReadNA.NaPathMode
            self.filename = filepath.split('\\')[-1]
            self.filepath = filepath
            try:
                self.root = ET.parse(filepath).getroot()
            except ET.ParseError:
                print("警告：该文件已损坏")
            self.ShipName = self.filename[:-3]
            self.Author = self.root.find('ship').attrib['author']
            self.HornType = self.root.find('ship').attrib['hornType']
            self.HornPitch = self.root.find('ship').attrib['hornPitch']
            try:
                self.TracerCol = self.root.find('ship').attrib['tracerCol']
            except KeyError:
                self.TracerCol = None
            self._xml_all_parts = self.root.findall('ship/part')
            # print(self._xml_all_parts)
            self.Weapons = MainWeapon.All
            self.AdjustableHulls = AdjustableHull.All
            self.ColorPartsMap = {}
            part_num = len(self._xml_all_parts)
            for i, part in enumerate(self._xml_all_parts):
                if i % 3 == 0:
                    process = round(i / part_num * 100, 2)
                    self.show_statu_func(f"正在读取第{i}个零件，进度：{process} %", "process")
                _id = str(part.attrib['id'])
                _pos = part.find('position').attrib
                _rot = part.find('rotation').attrib
                _scl = part.find('scale').attrib
                _pos = (float(_pos['x']), float(_pos['y']), float(_pos['z']))
                _rot = (round(float(_rot['x']), 3), round(float(_rot['y']), 3), round(float(_rot['z']), 3))
                _scl = (float(_scl['x']), float(_scl['y']), float(_scl['z']))
                _scl = tuple(abs(i) for i in _scl)
                _col = str(part.find('color').attrib['hex'])
                _amr = int(part.find('armor').attrib['value'])
                # 如果ID为0，就添加到可调节船体
                if _id == '0':
                    _data = part.find('data').attrib
                    obj = AdjustableHull(
                        self, _id, _pos, _rot, _scl, _col, _amr,
                        float(_data['length']), float(_data['height']),
                        float(_data['frontWidth']), float(_data['backWidth']),
                        float(_data['frontSpread']), float(_data['backSpread']),
                        float(_data['upCurve']), float(_data['downCurve']),
                        float(_data['heightScale']), float(_data['heightOffset'])
                    )
                # 如果有turret，就添加到主武器
                elif part.find('turret') is not None:
                    try:
                        manual_control = part.find('turret').attrib['manualControl']
                    except KeyError:
                        manual_control = None
                    try:
                        elevatorH = part.find('turret').attrib['evevator']
                    except KeyError:
                        elevatorH = None
                    obj = MainWeapon(self, _id, _pos, _rot, _scl, _col, _amr,
                                     manual_control, elevatorH)
                # 最后添加到普通零件
                else:
                    obj = NAPart(self, _id, _pos, _rot, _scl, _col, _amr)
                # 添加颜色
                _color = f"#{part.find('color').attrib['hex']}"
                if _color not in self.ColorPartsMap.keys():
                    self.ColorPartsMap[_color] = []
                self.ColorPartsMap[_color].append(obj)
                # print("正在读取文件：", self.filename)
                # print(self.ColorPartsMap)
                self.Parts.append(obj)
                if design_tab:
                    NAPart.hull_design_tab_id_map[id(obj) % 4294967296] = obj
                # 注意，这里没有对partRelationMap进行初始化，因为这里只是读取零件，还没有选颜色，所以要等到用户选颜色之后才能初始化
        self.show_statu_func("零件读取完成!", "success")


class PartRelationMap:
    # 具体方位
    FRONT = "front"
    BACK = "back"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    SAME = "same"

    # 方位组合
    FRONT_BACK = "front_back"
    UP_DOWN = "up_down"
    LEFT_RIGHT = "left_right"

    # 八个卦限
    FRONT_UP_LEFT = "front_up_left"
    FRONT_UP_RIGHT = "front_up_right"
    FRONT_DOWN_LEFT = "front_down_left"
    FRONT_DOWN_RIGHT = "front_down_right"
    BACK_UP_LEFT = "back_up_left"
    BACK_UP_RIGHT = "back_up_right"
    BACK_DOWN_LEFT = "back_down_left"
    BACK_DOWN_RIGHT = "back_down_right"

    def __init__(self, read_na, show_statu_func):
        """
        建立有向图，6种关系，上下左右前后，权重等于距离（按照从小到大的顺序，越近索引越小，越远索引越大）
        :param read_na:
        :param show_statu_func:
        """
        self.show_statu_func = show_statu_func
        self.Parts = read_na.Parts
        """点平面集"""
        self.xzDotsLayerMap = {  # y: [Part0, Part1, ...]
        }  # 每一水平截面层的点，根据basicMap的前后左右关系，将点分为同一层
        self.xyDotsLayerMap = {  # z: [Part0, Part1, ...]
        }  # 每一前后截面层的点，根据basicMap的上下左右关系，将点分为同一层
        self.yzDotsLayerMap = {  # x: [Part0, Part1, ...]
        }  # 每一左右截面层的点，根据basicMap的上下前后关系，将点分为同一层
        """零件平面集"""
        self.xzPartsLayerMap = {  # y: [Part0, Part1, ...]
        }  # 每一水平截面层的零件，根据basicMap的前后左右关系，将零件分为同一层，优化basicMap添加零件的速度
        self.xyPartsLayerMap = {  # z: [Part0, Part1, ...]
        }  # 每一前后截面层的零件，根据basicMap的上下左右关系，将零件分为同一层，优化basicMap添加零件的速度
        self.yzPartsLayerMap = {  # x: [Part0, Part1, ...]
        }  # 每一左右截面层的零件，根据basicMap的上下前后关系，将零件分为同一层，优化basicMap添加零件的速度
        """零件关系图"""
        self.basicMap = {  # 以零件为基础的关系图，包含零件的上下左右前后和距离关系
            # 零件对象： {方向0：{对象0：距离0, 对象1：距离1, ...}, 方向1：{对象0：距离0, 对象1：距离1, ...}, ...}
            # NAPart: {PartRelationMap.FRONT: {FrontPart0: FrontValue0, ...},
            #        PartRelationMap.BACK: {BackPart0: BackValue0, ...},
            #        PartRelationMap.UP: {UpPart0: UpValue0, ...},
            #        PartRelationMap.DOWN: {DownPart0: DownValue0, ...},
            #        PartRelationMap.LEFT: {LeftPart0: LeftValue0, ...},
            #        PartRelationMap.RIGHT: {RightPart0: RightValue0, ...}}
            #        PartRelationMap.SAME: {SamePart0: 0, ...}}
        }  # 注意！生成完之后，会在OpenGL_objs.NaHull.getDrawMap()进行添加零件和排序，因为那个时候DrawMap才生成出来
        self.relationMap = {  # 以关系为基础的关系图，不包含距离关系，只包含映射关系
            # 方向0：{零件A：零件B, 零件C：零件D, ...}
            PartRelationMap.FRONT: {},
            PartRelationMap.UP: {},
            PartRelationMap.LEFT: {},
            PartRelationMap.SAME: {}
        }

    def opposite_direction(self, direction):
        """
        获取相反的方向
        :param direction:
        :return:
        """
        if direction == self.FRONT:
            return self.BACK
        elif direction == self.BACK:
            return self.FRONT
        elif direction == self.UP:
            return self.DOWN
        elif direction == self.DOWN:
            return self.UP
        elif direction == self.LEFT:
            return self.RIGHT
        elif direction == self.RIGHT:
            return self.LEFT
        elif direction == self.SAME:
            return self.SAME

    def _add_relation(self, part, other_part, part_relation, other_part_relation, raw_direction):
        """
        添加零件的关系
        :param part: 添加的零件
        :param other_part: 与之关系的零件
        :param part_relation: 新增零件的关系映射
        :param other_part_relation: 与之关系的零件的关系映射
        :param raw_direction: 毛方向，前后，上下，左右
        """
        if raw_direction == self.SAME:
            other_part_relation[self.SAME][part] = 0
            for relation in (self.FRONT, self.BACK, self.UP, self.DOWN, self.LEFT, self.RIGHT):
                part_relation[relation][other_part] = other_part_relation[relation][other_part]
            part_relation[self.SAME][other_part] = 0
            return
        elif raw_direction == self.FRONT_BACK:
            pos_index = 2
            other_add2_new_directions = (self.FRONT, self.BACK)
        elif raw_direction == self.UP_DOWN:
            pos_index = 1
            other_add2_new_directions = (self.UP, self.DOWN)
        elif raw_direction == self.LEFT_RIGHT:
            pos_index = 0
            other_add2_new_directions = (self.LEFT, self.RIGHT)
        else:
            raise ValueError(f"非法的方向：{raw_direction}")
        value = abs(other_part.Pos[pos_index] - part.Pos[pos_index])
        if other_part.Pos[pos_index] > part.Pos[pos_index]:  # other在part的前面
            part_relation[other_add2_new_directions[0]][other_part] = value
            other_part_relation[other_add2_new_directions[1]][part] = value
            self.relationMap[other_add2_new_directions[0]][part] = other_part
        elif other_part.Pos[pos_index] < part.Pos[pos_index]:  # other在part的后面
            part_relation[other_add2_new_directions[1]][other_part] = value
            other_part_relation[other_add2_new_directions[0]][part] = value
            self.relationMap[other_add2_new_directions[0]][other_part] = part
        # 将other_part的相应的方向的零件也添加到new_part的该方向零件中
        for raw_direction in other_add2_new_directions:
            for other_part_direction, _other_part_direction_value in other_part_relation[raw_direction].items():
                value2 = abs(other_part_direction.Pos[pos_index] - part.Pos[pos_index])
                if other_part_direction.Pos[pos_index] > part.Pos[pos_index]:
                    part_relation[other_add2_new_directions[0]][other_part_direction] = value2
                elif other_part_direction.Pos[pos_index] < part.Pos[pos_index]:
                    part_relation[other_add2_new_directions[1]][other_part_direction] = value2

    def add_part(self, newPart):
        """
        添加零件
        :param newPart:
        :return: layer_t, relation_t, dot_t
        """
        if type(newPart) != AdjustableHull:
            return 0., 0., 0.
        # 如果旋转角度不是90的倍数，就不添加
        if int(newPart.Rot[0]) % 90 != 0 or int(newPart.Rot[1]) % 90 != 0 or int(newPart.Rot[2]) % 90 != 0:
            return 0., 0., 0.
        # 点集
        st = time.time()
        if type(newPart) == AdjustableHull:
            newPart.Pos = [round(newPart.Pos[0], 3), round(newPart.Pos[1], 3), round(newPart.Pos[2], 3)]
            for dot in newPart.operation_dot_nodes:
                # dot是np.ndarray类型
                _x = round(float(dot[0]), 3)
                _y = round(float(dot[1]), 3)
                _z = round(float(dot[2]), 3)
                if [_x, _y, _z] not in NAPartNode.all_dots:
                    node = NAPartNode([_x, _y, _z])
                    # 判断零件在节点的哪一个卦限
                    if newPart.Pos[0] > _x:
                        if newPart.Pos[1] > _y:
                            if newPart.Pos[2] > _z:
                                node.near_parts[PartRelationMap.BACK_DOWN_LEFT].append(newPart)
                            else:  # newPart.Pos[2] < _z
                                node.near_parts[PartRelationMap.BACK_UP_LEFT].append(newPart)
                        else:  # newPart.Pos[1] < _y
                            if newPart.Pos[2] > _z:
                                node.near_parts[PartRelationMap.FRONT_DOWN_LEFT].append(newPart)
                            else:  # newPart.Pos[2] < _z
                                node.near_parts[PartRelationMap.FRONT_UP_LEFT].append(newPart)
                    else:  # newPart.Pos[0] < _x
                        if newPart.Pos[1] > _y:
                            if newPart.Pos[2] > _z:
                                node.near_parts[PartRelationMap.BACK_DOWN_RIGHT].append(newPart)
                            else:
                                node.near_parts[PartRelationMap.BACK_UP_RIGHT].append(newPart)
                        else:  # newPart.Pos[1] < _y
                            if newPart.Pos[2] > _z:
                                node.near_parts[PartRelationMap.FRONT_DOWN_RIGHT].append(newPart)
                            else:  # newPart.Pos[2] < _z
                                node.near_parts[PartRelationMap.FRONT_UP_RIGHT].append(newPart)
                # DotsLayerMap
                if _x not in self.yzDotsLayerMap.keys():
                    self.yzDotsLayerMap[_x] = [newPart]
                else:
                    self.yzDotsLayerMap[_x].append(newPart)
                if _y not in self.xzDotsLayerMap.keys():
                    self.xzDotsLayerMap[_y] = [newPart]
                else:
                    self.xzDotsLayerMap[_y].append(newPart)
                if _z not in self.xyDotsLayerMap.keys():
                    self.xyDotsLayerMap[_z] = [newPart]
                else:
                    self.xyDotsLayerMap[_z].append(newPart)
        dot_t = round(time.time() - st, 4)
        # 零件集
        st = time.time()
        # 初始化零件的上下左右前后零件
        newPart_relation = {self.FRONT: {}, self.BACK: {},
                            self.UP: {}, self.DOWN: {},
                            self.LEFT: {}, self.RIGHT: {},
                            self.SAME: {}}
        x_exist = []  # x相同的零件
        y_exist = []  # y相同的零件
        z_exist = []  # z相同的零件
        if newPart.Pos[0] not in self.yzPartsLayerMap.keys():
            self.yzPartsLayerMap[newPart.Pos[0]] = [newPart]
        else:
            x_exist = self.yzPartsLayerMap[newPart.Pos[0]]
            self.yzPartsLayerMap[newPart.Pos[0]].append(newPart)
        if newPart.Pos[1] not in self.xzPartsLayerMap.keys():
            self.xzPartsLayerMap[newPart.Pos[1]] = [newPart]
        else:
            y_exist = self.xzPartsLayerMap[newPart.Pos[1]]
            self.xzPartsLayerMap[newPart.Pos[1]].append(newPart)
        if newPart.Pos[2] not in self.xyPartsLayerMap.keys():
            self.xyPartsLayerMap[newPart.Pos[2]] = [newPart]
        else:
            z_exist = self.xyPartsLayerMap[newPart.Pos[2]]
            self.xyPartsLayerMap[newPart.Pos[2]].append(newPart)
        layer_t = round(time.time() - st, 4)
        st = time.time()
        # 先检查是否有有位置关系的other_part，如果有，就添加到new_part的上下左右前后零件中
        # 然后新零件new_part根据other_part的关系扩充自己的关系
        if len(self.basicMap) == 0:  # 如果basicMap为空，就直接添加
            self.basicMap[newPart] = newPart_relation
            return layer_t, 0, 0
        # if newPart.Pos[0] not in self.xzPartsLayerMap.keys():  # 如果xzLayerMap中没有该层，就添加
        xy_exist = set(x_exist) & set(y_exist)
        xz_exist = set(x_exist) & set(z_exist)
        yz_exist = set(y_exist) & set(z_exist)
        for otherPart, others_direction_relation in self.basicMap.items():
            # 遍历点集，往NAPartNode中添加点
            # xy相同，前后关系
            if otherPart in xy_exist:
                self._add_relation(newPart, otherPart, newPart_relation, others_direction_relation, self.FRONT_BACK)
            # yz相同，左右关系
            elif otherPart in yz_exist:
                self._add_relation(newPart, otherPart, newPart_relation, others_direction_relation, self.LEFT_RIGHT)
            # xz相同，上下关系
            elif otherPart in xz_exist:
                self._add_relation(newPart, otherPart, newPart_relation, others_direction_relation, self.UP_DOWN)
            elif otherPart.Pos == newPart.Pos:  # 同一位置
                self._add_relation(newPart, otherPart, newPart_relation, others_direction_relation, self.SAME)
        # 将new_part的关系添加到basicMap中
        self.basicMap[newPart] = newPart_relation
        relation_t = round(time.time() - st, 4)
        return layer_t, relation_t, dot_t

    def replace(self, part0, part1, replaced_part, direction):
        """

        :param part0: 在该方向值大的零件，注意，不是在原零件坐标系的方向，而是在世界坐标系的方向
        :param part1: 在该方向值小的零件，注意，不是在原零件坐标系的方向，而是在世界坐标系的方向
        :param replaced_part:
        :param direction:
        :return:
        """
        # if replaced_part not in self.basicMap.keys():
        #     return # 如果被替换零件不在basicMap中，就不替换
        if not direction:
            # 自行判断方向
            if part0.Pos[0] == part1.Pos[0] and part0.Pos[1] == part1.Pos[1]:
                direction = self.FRONT_BACK
                if part0.Pos[2] < part1.Pos[2]:
                    part0, part1 = part1, part0
            elif part0.Pos[0] == part1.Pos[0] and part0.Pos[2] == part1.Pos[2]:
                direction = self.UP_DOWN
                if part0.Pos[1] < part1.Pos[1]:
                    part0, part1 = part1, part0
            elif part0.Pos[1] == part1.Pos[1] and part0.Pos[2] == part1.Pos[2]:
                direction = self.LEFT_RIGHT
                if part0.Pos[0] < part1.Pos[0]:
                    part0, part1 = part1, part0
        new_map0 = {self.FRONT: {}, self.BACK: {}, self.UP: {}, self.DOWN: {}, self.LEFT: {}, self.RIGHT: {}}
        new_map1 = {self.FRONT: {}, self.BACK: {}, self.UP: {}, self.DOWN: {}, self.LEFT: {}, self.RIGHT: {}}
        # 定义一个方向映射，以便根据不同的方向进行操作
        direction_map = {
            self.FRONT_BACK: (self.FRONT, self.BACK),
            self.UP_DOWN: (self.UP, self.DOWN),
            self.LEFT_RIGHT: (self.LEFT, self.RIGHT)
        }
        dir_index_map = {
            self.FRONT_BACK: 2,
            self.UP_DOWN: 1,
            self.LEFT_RIGHT: 0
        }
        if not direction:
            return
        new_map0[direction_map[direction][1]] = {part1: abs(part1.Pos[dir_index_map[direction]] - part0.Pos[dir_index_map[direction]])}
        new_map1[direction_map[direction][0]] = {part0: abs(part1.Pos[dir_index_map[direction]] - part0.Pos[dir_index_map[direction]])}
        # 获取被替换零件的关系图
        replaced_relation_map = self.basicMap[replaced_part]
        for part in replaced_relation_map[direction_map[direction][0]].keys():
            # 给新零件添加关系
            new_map0[direction_map[direction][0]][part] = abs(part.Pos[dir_index_map[direction]] - part0.Pos[dir_index_map[direction]])
            new_map1[direction_map[direction][0]][part] = abs(part.Pos[dir_index_map[direction]] - part1.Pos[dir_index_map[direction]])
            # 给原零件添加关系
            if part in self.basicMap.keys():
                self.basicMap[part][direction_map[direction][1]][part0] = abs(
                    part.Pos[dir_index_map[direction]] - part0.Pos[dir_index_map[direction]])
                self.basicMap[part][direction_map[direction][1]][part1] = abs(
                    part.Pos[dir_index_map[direction]] - part1.Pos[dir_index_map[direction]])
            # 给原零件删除关系
            del self.basicMap[part][direction_map[direction][1]][replaced_part]
            # 给原零件重排序
            self.basicMap[part][direction_map[direction][1]] = dict(
                sorted(self.basicMap[part][direction_map[direction][1]].items(), key=lambda x: x[1]))
        for part in replaced_relation_map[direction_map[direction][1]].keys():
            # 给新零件添加关系
            new_map0[direction_map[direction][1]][part] = abs(part.Pos[dir_index_map[direction]] - part0.Pos[dir_index_map[direction]])
            new_map1[direction_map[direction][1]][part] = abs(part.Pos[dir_index_map[direction]] - part1.Pos[dir_index_map[direction]])
            # 给原零件添加关系
            self.basicMap[part][direction_map[direction][0]][part0] = abs(
                part.Pos[dir_index_map[direction]] - part0.Pos[dir_index_map[direction]])
            self.basicMap[part][direction_map[direction][0]][part1] = abs(
                part.Pos[dir_index_map[direction]] - part1.Pos[dir_index_map[direction]])
            # 给原零件删除关系
            del self.basicMap[part][direction_map[direction][0]][replaced_part]
            # 给原零件重排序
            self.basicMap[part][direction_map[direction][0]] = dict(
                sorted(self.basicMap[part][direction_map[direction][0]].items(), key=lambda x: x[1]))
        self.basicMap[part0] = new_map0
        self.basicMap[part1] = new_map1
        # 删除被替换零件
        del self.basicMap[replaced_part]

    def del_part(self, part):
        """
        删除零件
        :param part:
        :return:
        """
        # 遍历自身的相关零件，将自身从其关系中删除
        for direction, other_parts in self.basicMap[part].items():
            for other_part in other_parts.keys():
                del self.basicMap[other_part][self.opposite_direction(direction)][part]
        # 删除自身
        self.basicMap[part] = {}

    def remap(self, drawMap):
        st = time.time()
        total_parts_num = sum([len(parts) for parts in drawMap.values()])
        i = 1
        for _color, parts in drawMap.items():
            for part in parts:
                layer_t, relation_t, dot_t = self.add_part(part)
                # 标准化（填补0）
                layer_t = str(layer_t).ljust(6, '0')
                relation_t = str(relation_t).ljust(6, '0')
                dot_t = str(dot_t).ljust(6, '0')
                if i % 3 == 0:
                    process = round(i / total_parts_num * 100, 2)
                    self.show_statu_func(
                        f"正在实例化第 {i} / {total_parts_num} 个零件： {process} %"
                        f"\t\t\t\t单件耗时：     截面对象  {layer_t} s     零件关系  {relation_t} s     节点集合  {dot_t} s", "process")
                i += 1
        self.show_statu_func(f"零件关系图初始化完成! 耗时：{time.time() - st}s", "success")
        st = time.time()
        self.sort()
        self.show_statu_func(f"零件关系图排序完成! 耗时：{time.time() - st}s", "success")

    def init(self, drawMap, init=True):
        """
        :param drawMap: NaHull的绘图字典，键值对为：{颜色：[零件1，零件2，...]}
        :param init: 如果为False，这个函数则仅用于drawMap的初始化后调用，用来指示代码位置方便Debug
        :return:
        """
        if not init:
            return
        st = time.time()
        total_parts_num = sum([len(parts) for parts in drawMap.values()])
        i = 1
        for _color, parts in drawMap.items():
            for part in parts:
                layer_t, relation_t, dot_t = self.add_part(part)
                # 标准化（填补0）
                layer_t = str(layer_t).ljust(6, '0')
                relation_t = str(relation_t).ljust(6, '0')
                dot_t = str(dot_t).ljust(6, '0')
                if i % 3 == 0:
                    process = round(i / total_parts_num * 100, 2)
                    self.show_statu_func(
                        f"正在实例化第 {i} / {total_parts_num} 个零件： {process} %"
                        f"\t\t\t\t单件耗时：     截面对象  {layer_t} s     零件关系  {relation_t} s     节点集合  {dot_t} s", "process")
                i += 1
        self.show_statu_func(f"零件关系图初始化完成! 耗时：{time.time() - st}s", "success")
        st = time.time()
        self.sort()
        self.show_statu_func(f"零件关系图排序完成! 耗时：{time.time() - st}s", "success")

    def sort(self):
        self.show_statu_func("正在加载LayerMaps", "process")
        self.xzDotsLayerMap = dict(sorted(self.xzDotsLayerMap.items(), key=lambda item: item[0]))
        self.xyDotsLayerMap = dict(sorted(self.xyDotsLayerMap.items(), key=lambda item: item[0]))
        self.yzDotsLayerMap = dict(sorted(self.yzDotsLayerMap.items(), key=lambda item: item[0]))
        self.xzPartsLayerMap = dict(sorted(self.xzPartsLayerMap.items(), key=lambda item: item[0]))
        self.xyPartsLayerMap = dict(sorted(self.xyPartsLayerMap.items(), key=lambda item: item[0]))
        self.yzPartsLayerMap = dict(sorted(self.yzPartsLayerMap.items(), key=lambda item: item[0]))
        total_parts_num = sum([len(parts) for parts in self.basicMap.values()])
        i = 1
        for part, part_relation in self.basicMap.items():
            # 按照value（relation的值）对relation字典从小到大排序：
            for direction, others_direction_relation in part_relation.items():
                if i % 123 == 0:
                    process = round(i / total_parts_num * 100, 2)
                    self.show_statu_func(f"正在排序第{i}个零件，进度：{process} %", "process")
                i += 1
                part_relation[direction] = dict(sorted(others_direction_relation.items(), key=lambda item: item[1]))
