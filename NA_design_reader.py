"""
读取NA设计文件的模块
"""
import xml.etree.ElementTree as ET
from typing import Union

import numpy as np
from quaternion import quaternion
from GUI.QtGui import ProgressBarWindow

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


def show_statu():
    return


def rotate_axis(rotated_axis, axis, angle):
    # 将轴向量和要旋转的向量归一化
    axis = axis / np.linalg.norm(axis)
    rotated_axis = rotated_axis / np.linalg.norm(rotated_axis)

    # 计算旋转后的向量
    cos_theta = np.cos(angle)
    sin_theta = np.sin(angle)
    cross_product = np.cross(axis, rotated_axis)
    dot_product = np.dot(axis, rotated_axis)

    rotated = (rotated_axis * cos_theta +
               cross_product * sin_theta +
               axis * dot_product * (1 - cos_theta))

    return rotated


def rotate(dot_dict, rot):
    """
    对点集进行欧拉角旋转

    :param dot_dict: 字典，值是零件的各个点的坐标，格式为 {'point1': [x1, y1, z1], 'point2': [x2, y2, z2], ...}
    :param rot: 角度值，三个值分别为x,y,z轴的旋转角度，单位为度
    :return: 旋转后的点集，格式与输入点集相同，但是返回np.array类型的值
    """
    # 将角度转换为弧度
    rot = np.deg2rad(rot)
    # 获取旋转矩阵
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(rot[0]), -np.sin(rot[0])],
                   [0, np.sin(rot[0]), np.cos(rot[0])]])

    Ry = np.array([[np.cos(rot[1]), 0, np.sin(rot[1])],
                   [0, 1, 0],
                   [-np.sin(rot[1]), 0, np.cos(rot[1])]])

    Rz = np.array([[np.cos(rot[2]), -np.sin(rot[2]), 0],
                   [np.sin(rot[2]), np.cos(rot[2]), 0],
                   [0, 0, 1]])

    # 遍历点集进行旋转
    rotated_dot_dict = {}
    for key, point in dot_dict.items():
        # 转换为NumPy数组
        point_np = np.array(point)
        # 进行旋转
        rotated_point = Rx.dot(Ry).dot(Rz).dot(point_np)
        # 将结果保存到字典中
        rotated_dot_dict[key] = rotated_point
    return rotated_dot_dict


def rotate_quaternion2(dot_dict, rot):
    """
    对点集进行四元数旋转

    :param dot_dict: 字典，值是零件的各个点的坐标，格式为 {'pointset1': [[x1, y1, z1], [x2, y2, z2], ...], 'pointset2': [[x1, y1, z1], [x2, y2, z2], ...], ...}

    :param rot: 角度值，三个值分别为x,y,z轴的旋转角度，单位为度
    :return: 旋转后的点集，格式与输入点集相同，但值为np.array类型
    """
    # 转换为弧度
    rot = np.radians(rot)
    # 计算旋转矩阵
    rot_x = np.array([[1, 0, 0],
                      [0, np.cos(rot[0]), -np.sin(rot[0])],
                      [0, np.sin(rot[0]), np.cos(rot[0])]])

    rot_y = np.array([[np.cos(rot[1]), 0, np.sin(rot[1])],
                      [0, 1, 0],
                      [-np.sin(rot[1]), 0, np.cos(rot[1])]])

    rot_z = np.array([[np.cos(rot[2]), -np.sin(rot[2]), 0],
                      [np.sin(rot[2]), np.cos(rot[2]), 0],
                      [0, 0, 1]])

    # 合并旋转矩阵
    rotation_matrix = rot_z.dot(rot_y).dot(rot_x)

    # 遍历点集进行旋转
    rotated_dot_dict = {}
    for key, pointset in dot_dict.items():
        # 转换为NumPy数组
        pointset_np = np.array(pointset)
        # 进行旋转
        rotated_pointset = np.dot(pointset_np, rotation_matrix.T)
        # 将结果保存到字典中
        rotated_dot_dict[key] = rotated_pointset

    return rotated_dot_dict


def rotate_quaternion(dot_dict, rot):
    """
    对点集进行四元数旋转

    :param dot_dict: 字典，值是零件的各个点的坐标，格式为 {'point1': [x1, y1, z1], 'point2': [x2, y2, z2], ...}
    :param rot: 角度值，三个值分别为x,y,z轴的旋转角度，单位为度
    :return: 旋转后的点集，格式与输入点集相同，但值为np.array类型
    """
    # 将角度转换为弧度
    rot = np.radians(rot)

    # 计算旋转的四元数
    q_x = np.array([np.cos(rot[0] / 2), np.sin(rot[0] / 2), 0, 0])
    q_y = np.array([np.cos(rot[1] / 2), 0, np.sin(rot[1] / 2), 0])
    q_z = np.array([np.cos(rot[2] / 2), 0, 0, np.sin(rot[2] / 2)])

    # 合并三个旋转四元数
    q = quaternion(1, 0, 0, 0)
    q = q * quaternion(*q_x)
    q = q * quaternion(*q_y)
    q = q * quaternion(*q_z)

    # 遍历点集进行旋转
    rotated_dot_dict = {}
    for key, point in dot_dict.items():
        # 将点坐标转换为四元数
        point_quat = np.quaternion(0, *point)
        # 进行四元数旋转
        rotated_point_quat = q * point_quat * np.conj(q)
        # 提取旋转后的点坐标
        rotated_point = np.array([rotated_point_quat.x, rotated_point_quat.y, rotated_point_quat.z])
        # 将结果保存到字典中
        rotated_dot_dict[key] = rotated_point

    return rotated_dot_dict


class Part:
    ShipsAllParts = []

    def __init__(self, read_na, Id, pos, rot, scale, color, armor):
        self.read_na_obj = read_na
        self.allParts_relationMap = read_na.partRelationMap
        self.Id = Id
        self.Pos = pos
        self.Rot = rot
        self.Scl = scale
        self.Col = color
        self.Amr = armor
        Part.ShipsAllParts.append(self)

    def __str__(self):
        part_type = "Part"
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
            "Typ": 'Part',
            "Id": self.Id,
            "Pos": list(self.Pos),
            "Rot": list(self.Rot),
            "Scl": list(self.Scl),
            "Col": str(self.Col),
            "Amr": self.Amr,
        }


class AdjustableHull(Part):
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
        Part.__init__(self, read_na, Id, pos, rot, scale, color, armor)
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
        self.front_mid_y = (self.front_up_y + self.front_down_y) / 2  # 初始化中间坐标
        self.back_mid_y = (self.back_up_y + self.back_down_y) / 2  # 初始化中间坐标
        self.front_mid_x = (self.front_up_x + self.front_down_x) / 2
        self.back_mid_x = (self.back_up_x + self.back_down_x) / 2
        # 计算中间坐标
        if self.front_mid_y > self.front_up_y:
            self.front_mid_y = self.front_up_y
        elif self.front_mid_y < self.front_down_y:
            self.front_mid_y = self.front_down_y
        if self.back_mid_y > self.back_up_y:
            self.back_mid_y = self.back_up_y
        elif self.back_mid_y < self.back_down_y:
            self.back_mid_y = self.back_down_y
        # ==============================================================================计算绘图所需的数据
        self.plot_all_dots = []  # 曲面变换前，位置变换后的所有点
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
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
        if self.UCur == 0 and self.DCur == 0:
            # 旋转
            dots = rotate_quaternion(self.vertex_coordinates, self.Rot)
            for key in dots.keys():
                dots[key] *= self.Scl  # 缩放
                dots[key] += self.Pos  # 平移
            faces = [
                [dots["front_up_left"], dots["front_up_right"], dots["front_down_right"], dots["front_down_left"]],
                [dots["back_up_left"], dots["back_down_left"], dots["back_down_right"], dots["back_up_right"]],
                [dots["front_up_left"], dots["back_up_left"], dots["back_up_right"], dots["front_up_right"]],
                [dots["front_down_left"], dots["front_down_right"], dots["back_down_right"], dots["back_down_left"]],
                [dots["front_up_left"], dots["front_down_left"], dots["back_down_left"], dots["back_up_left"]],
                [dots["front_up_right"], dots["back_up_right"], dots["back_down_right"], dots["front_down_right"]],
            ]
            self.plot_all_dots = [
                dots["front_up_left"], dots["front_up_right"], dots["front_down_right"], dots["front_down_left"],
                dots["back_up_left"], dots["back_down_left"], dots["back_down_right"], dots["back_up_right"]]
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
            # 旋转
            front_part_curved_circle_dots = rotate_quaternion2(front_part_curved_circle_dots, self.Rot)
            back_part_curved_circle_dots = rotate_quaternion2(back_part_curved_circle_dots, self.Rot)
            # 缩放和平移
            for dot_set in front_part_curved_circle_dots.values():
                for dot in dot_set:
                    dot *= self.Scl
                    dot += self.Pos
            for dot_set in back_part_curved_circle_dots.values():
                for dot in dot_set:
                    dot *= self.Scl
                    dot += self.Pos
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
            self.plot_all_dots = front_set + back_set
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

    def __str__(self):
        part_type = str(self.__class__.__name__)
        return str(
            f"\nTyp:  {part_type}\n"
            f"Id:   {self.Id}\n"
            f"Pos:  {self.Pos}\n"
            f"Rot:  {self.Rot}\n"
            f"Scl:  {self.Scl}\n"
            f"Col:  #{self.Col}\n"
            f"Amr:  {self.Amr} mm\n"
            f"Len:  {self.Len} m\n"
            f"Hei:  {self.Hei} m\n"
            f"FWid: {self.FWid} m\n"
            f"BWid: {self.BWid} m\n"
            f"FSpr: {self.FSpr} m\n"
            f"BSpr: {self.BSpr} m\n"
            f"UCur: {self.UCur} m\n"
            f"DCur: {self.DCur} m\n"
            f"HScl: {self.HScl} m\n"
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


class MainWeapon(Part):
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
    def __init__(self, filepath: Union[str, bool] = False, data=None, show_statu_func=None):
        """

        :param filepath:
        :param data: 字典，键是颜色的十六进制表示，值是零件的列表，但是尚未实例化，是字典形式的数据
        :param show_statu_func:
        """
        self.show_statu_func = show_statu_func
        self.Parts = []
        self.partRelationMap = PartRelationMap(self, self.show_statu_func)  # 零件关系图，包含零件的上下左右前后关系
        if filepath is False:
            # ===================================================================== 实例化data中的零件
            self.ColorPartsMap = {}
            total_parts_num = sum([len(parts) for parts in data.values()])
            i = 0
            for color, parts in data.items():
                for part in parts:
                    if i % 123 == 0:
                        process = round(i / total_parts_num * 100, 2)
                        self.show_statu_func(f"正在实例化第{i}个零件，进度：{process} %", "process")
                    i += 1
                    if part["Typ"] == "Part":
                        obj = Part(
                            self,
                            part["Id"],
                            tuple(part["Pos"]), tuple(part["Rot"]), tuple(part["Scl"]),
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
                            scale=tuple(part["Scl"]),
                            color=str(part["Col"]),
                            armor=int(part["Amr"]),
                            manual_control=manual_control,
                            elevator=elevator
                        )
                    elif part["Typ"] == "AdjustableHull":
                        obj = AdjustableHull(
                            self,
                            part["Id"],
                            tuple(part["Pos"]), tuple(part["Rot"]), tuple(part["Scl"]),
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
                    # 初始化零件关系图
                    self.partRelationMap.add_part(obj)
            self.partRelationMap.sort()
            self.partRelationMap.init(drawMap=None, init=False)  # 上方已经初始化了drawMap。
        else:  # =========================================================================== 读取na文件
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
                if i % 123 == 0:
                    process = round(i / part_num * 100, 2)
                    self.show_statu_func(f"正在读取第{i}个零件，进度：{process} %", "process")
                _id = str(part.attrib['id'])
                _pos = part.find('position').attrib
                _rot = part.find('rotation').attrib
                _scl = part.find('scale').attrib
                _pos = (float(_pos['x']), float(_pos['y']), float(_pos['z']))
                _rot = (float(_rot['x']), float(_rot['y']), float(_rot['z']))
                _scl = (float(_scl['x']), float(_scl['y']), float(_scl['z']))
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
                        manual_control = part.find('turret').attrib['manualControl'] = None
                    try:
                        elevatorH = part.find('turret').attrib['evevator']
                    except KeyError:
                        elevatorH = part.find('turret').attrib['evevator'] = None
                    obj = MainWeapon(self, _id, _pos, _rot, _scl, _col, _amr,
                                     manual_control, elevatorH)
                # 最后添加到普通零件
                else:
                    obj = Part(self, _id, _pos, _rot, _scl, _col, _amr)
                # 添加颜色
                _color = f"#{part.find('color').attrib['hex']}"
                if _color not in self.ColorPartsMap.keys():
                    self.ColorPartsMap[_color] = []
                self.ColorPartsMap[_color].append(obj)
                # print("正在读取文件：", self.filename)
                # print(self.ColorPartsMap)
                self.Parts.append(obj)
                # 注意，这里没有对partRelationMap进行初始化，因为这里只是读取零件，还没有选颜色，所以要等到用户选颜色之后才能初始化
        self.show_statu_func("零件读取完成!", "success")
        # 至此已经初始化的公有属性：
        # self.filename *
        # self.filepath *
        # self.ShipName
        # self.Author
        # self.HornType
        # self.HornPitch
        # self.TracerCol
        # self.Parts  # 所有零件的列表
        # self.Weapons  # 所有武器的列表
        # self.AdjustableHulls  # 所有可调节船体的列表
        # self.ColorPartsMap  # 用于绘制的颜色-零件映射表
        # self.show_statu_func  # 进度条
        # self.partRelationMap  # 零件关系图，包含零件的上下左右前后关系


class PartRelationMap:
    FRONT = "front"
    BACK = "back"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    SAME = "same"

    FRONT_BACK = "front_back"
    UP_DOWN = "up_down"
    LEFT_RIGHT = "left_right"

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
            # Part: {PartRelationMap.FRONT: {FrontPart0: FrontValue0, ...},
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
        :return:
        """
        # 点集
        if type(newPart) == AdjustableHull:
            for dot in newPart.plot_all_dots:
                _x = float(dot[0])
                _y = float(dot[1])
                _z = float(dot[2])
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
        # 初始化零件的上下左右前后零件
        newPart_relation = {self.FRONT: {}, self.BACK: {},
                            self.UP: {}, self.DOWN: {},
                            self.LEFT: {}, self.RIGHT: {},
                            self.SAME: {}}
        # 零件集
        x_exist = []
        y_exist = []
        z_exist = []
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

        # 先检查是否有有位置关系的other_part，如果有，就添加到new_part的上下左右前后零件中
        # 然后新零件new_part根据other_part的关系扩充自己的关系
        if len(self.basicMap) == 0:  # 如果basicMap为空，就直接添加
            self.basicMap[newPart] = newPart_relation
            return
        # if newPart.Pos[0] not in self.xzPartsLayerMap.keys():  # 如果xzLayerMap中没有该层，就添加
        xy_exist = set(x_exist) & set(y_exist)
        xz_exist = set(x_exist) & set(z_exist)
        yz_exist = set(y_exist) & set(z_exist)
        for otherPart, others_direction_relation in self.basicMap.items():
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
        del self.basicMap[part]

    def init(self, drawMap, init=True):
        """
        :param drawMap: NaHull的绘图字典，键值对为：{颜色：[零件1，零件2，...]}
        :param init: 如果为False，这个函数则仅用于drawMap的初始化后调用，用来指示代码位置方便Debug
        :return:
        """
        if not init:
            return
        # st = time.time()
        total_parts_num = sum([len(parts) for parts in drawMap.values()])
        i = 1
        for _color, parts in drawMap.items():
            for part in parts:
                if i % 123 == 0:
                    process = round(i / total_parts_num * 100, 2)
                    self.show_statu_func(f"正在初始化第{i}个零件，进度：{process} %", "process")
                    # print(f"正在初始化零件关系图第{i}个零件，进度：{i / total_parts_num * 100}%")
                i += 1
                self.add_part(part)
        self.show_statu_func("零件关系图初始化完成!", "success")
        # print(f"零件关系图零件添加完成，耗时：{time.time() - st}秒")
        # st = time.time()
        self.sort()
        # print(f"零件关系图零件排序完成，耗时：{time.time() - st}秒")

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
                if i % 4567 == 0:
                    process = round(i / total_parts_num * 100, 2)
                    self.show_statu_func(f"正在排序第{i}个零件，进度：{process} %", "process")
                i += 1
                part_relation[direction] = dict(sorted(others_direction_relation.items(), key=lambda item: item[1]))
