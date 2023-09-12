import xml.etree.ElementTree as ET
import numpy as np
from quaternion import quaternion

"""
文件格式：
<root>
  <ship author="XXXXXXXXX" description="description" hornType="1" hornPitch="0.9475011" tracerCol="E53D4FFF">
    <part id="0">
      <data length="4.5" height="1" frontWidth="0.2" backWidth="0.5" frontSpread="0.05" backSpread="0.2" upCurve="0" downCurve="1" heightScale="1" heightOffset="0" />
      <position x="0" y="0" z="114.75" />
      <rotation x="0" y="0" z="0" />
      <scale x="1" y="1" z="1" />
      <color hex="975740" />
      <armor value="5" />
    </part>
    <part id="190">
      <position x="0" y="-8.526513E-14" z="117.0312" />
      <rotation x="90" y="0" z="0" />
      <scale x="0.03333336" y="0.03333367" z="0.1666679" />
      <color hex="975740" />
      <armor value="5" />
    </part>
  </root>
"""


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

    def __init__(self, Id, pos, rot, scale, color, armor):
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
            self, Id, pos, rot, scale, color, armor,
            length, height, frontWidth, backWidth, frontSpread, backSpread, upCurve, downCurve, heightScale,
            heightOffset):
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
        Part.__init__(self, Id, pos, rot, scale, color, armor)
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
        self.all_dots = []
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
            self.all_dots = [
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
            self.all_dots = front_set + back_set
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

    def __init__(self, Id, pos, rot, scale, color, armor, manual_control, elevator):
        super().__init__(Id, pos, rot, scale, color, armor)
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
    def __init__(self, filepath=False, data=None):
        """

        :param filepath:
        :param data: 字典，键是颜色的十六进制表示，值是零件的列表，但是尚未实例化，是字典形式的数据
        """
        self.Parts = []
        if filepath is False:
            # 实例化data中的零件
            self.ColorPartsMap = {}
            for color, parts in data.items():
                for part in parts:
                    if part["Typ"] == "Part":
                        obj = Part(
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
        else:  # 读取文件
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
            self._all_parts = self.root.findall('ship/part')
            self.Weapons = MainWeapon.All
            self.AdjustableHulls = AdjustableHull.All
            self.ColorPartsMap = {}
            for part in self.root.findall('ship/part'):
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
                        _id, _pos, _rot, _scl, _col, _amr,
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
                    obj = MainWeapon(_id, _pos, _rot, _scl, _col, _amr,
                                     manual_control, elevatorH)
                # 最后添加到普通零件
                else:
                    obj = Part(_id, _pos, _rot, _scl, _col, _amr)
                # 添加颜色
                _color = f"#{part.find('color').attrib['hex']}"
                if _color not in self.ColorPartsMap.keys():
                    self.ColorPartsMap[_color] = []
                self.ColorPartsMap[_color].append(obj)
                self.Parts.append(obj)
