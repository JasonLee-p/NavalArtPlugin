"""
读取NA设计文件的模块
"""
import copy
import time
import xml.etree.ElementTree as ET
from typing import Union, List, Dict, Callable

import numpy as np
from quaternion import quaternion
from util_funcs import CONST, VECTOR_RELATION_MAP, rotate_quaternion, get_normal, fit_bezier

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

RotateOrder = CONST.ROTATE_ORDER


def get_rot_relation(rot: list, rot_: list) -> Union[str, None]:
    """
    求rot_关于rot的关系：
    x+为左，y+为上，z+为前
    左转90度：'l'
    右转90度：'r'
    抬头90度：'u'
    低头90度：'d'
    关于x轴对称（上下颠倒，前后颠倒）：'x'
    关于y轴对称（前后颠倒，左右颠倒）：'y'
    关于z轴对称（左右颠倒，上下颠倒）：'z'
    关于关于原点中心对称（左右颠倒，上下颠倒，前后颠倒）：'o'
    其他：None
    :param rot: 第一个旋转角度的列表 [rx, ry, rz]
    :param rot_: 第二个旋转角度的列表 [rx_, ry_, rz_]
    :return: 字符串，表示两个旋转之间的关系，如 'l'、'r'、'u'、'd'、'x'、'y'、'z'、'o'、None
    """
    rot = list(rot)
    rot_ = list(rot_)
    if rot_ == rot:
        return 'same'
    elif rot_ == [(rot[0] + 180) % 360., rot[1], rot[2]]:
        return 'x'
    elif rot_ == [rot[0], (rot[1] + 180) % 360., rot[2]]:
        return 'y'
    elif rot_ == [rot[0], rot[1], (rot[2] + 180) % 360]:
        return 'z'
    elif rot_ == [(rot[0] + 180) % 360, (rot[1] + 180) % 360, rot[2]]:
        return 'o'
    elif rot_ == [rot[0], (rot[1] + 90) % 360, rot[2]]:
        return 'l'
    elif rot_ == [rot[0], (rot[1] - 90) % 360, rot[2]]:
        return 'r'
    elif rot_ == [(rot[0] - 90) % 360, rot[1], rot[2]]:
        return 'u'
    elif rot_ == [(rot[0] + 90) % 360, rot[1], rot[2]]:
        return 'd'
    else:
        return None


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


def get_raw_direction(parts):
    """
    判断方向（哪一个坐标值相同）
    :param parts:
    :return:
    """
    xs = set([part.Pos[0] for part in parts])
    ys = set([part.Pos[1] for part in parts])
    zs = set([part.Pos[2] for part in parts])
    direction = None
    if len(zs) > 1 and len(ys) == 1 and len(xs) == 1:
        direction = CONST.FRONT_BACK
    elif len(ys) > 1 and len(zs) == 1 and len(xs) == 1:
        direction = CONST.UP_DOWN
    elif len(xs) > 1 and len(zs) == 1 and len(ys) == 1:
        direction = CONST.LEFT_RIGHT
    return direction


class NAPartNode:
    id_map = {}
    all_dots = []  # 不储存对象，储存所有点的坐标列表

    def __init__(self, pos: list):
        self.pos = pos
        self.glWin = None
        self.near_parts = {  # 八个卦限
            CONST.FRONT_UP_LEFT: [],
            CONST.FRONT_UP_RIGHT: [],
            CONST.FRONT_DOWN_LEFT: [],
            CONST.FRONT_DOWN_RIGHT: [],
            CONST.BACK_UP_LEFT: [],
            CONST.BACK_UP_RIGHT: [],
            CONST.BACK_DOWN_LEFT: [],
            CONST.BACK_DOWN_RIGHT: [],
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
        if read_na:
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

    def __deepcopy__(self, memo):
        return self

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
            heightScale, heightOffset,
            _from_temp_data=False, _back_down_y=None, _back_up_y=None, _front_down_y=None, _front_up_y=None,
            _operation_dot_nodes=None, _plot_all_dots=None, _vertex_coordinates=None, _plot_lines=None,
            _plot_faces=None,
    ):
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

    def __deepcopy__(self, memo):
        return self

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
            dots[key] = dots[key].copy() + self.Pos  # 平移
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
                    for i in range(len(face)):
                        face[i] = face[i].copy() + self.Pos
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
            "1": [self.vertex_coordinates["front_up_left"].copy(), self.vertex_coordinates["front_up_right"].copy(),
                  self.vertex_coordinates["front_down_right"].copy(), self.vertex_coordinates["front_down_left"].copy(),
                  self.vertex_coordinates["front_up_left"].copy(), self.vertex_coordinates["back_up_left"].copy(),
                  self.vertex_coordinates["back_up_right"].copy(), self.vertex_coordinates["front_up_right"].copy()],
            "2": [self.vertex_coordinates["front_down_left"].copy(), self.vertex_coordinates["back_down_left"].copy(),
                  self.vertex_coordinates["back_down_right"].copy(),
                  self.vertex_coordinates["front_down_right"].copy()],
            "3": [self.vertex_coordinates["back_up_left"].copy(), self.vertex_coordinates["back_down_left"].copy()],
            "4": [self.vertex_coordinates["back_up_right"].copy(), self.vertex_coordinates["back_down_right"].copy()]
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

    def change_attrs(self, position=None, armor=None,
                     length=None, height=None, frontWidth=None, backWidth=None, frontSpread=None, backSpread=None,
                     upCurve=None, downCurve=None, heightScale=None, heightOffset=None,
                     update=False):
        # ==============================================================================更新零件的各个属性
        position = self.Pos if position is None else position
        armor = self.Amr if armor is None else armor
        length = self.Len if length is None else length
        height = self.Hei if height is None else height
        frontWidth = self.FWid if frontWidth is None else frontWidth
        backWidth = self.BWid if backWidth is None else backWidth
        frontSpread = self.FSpr if frontSpread is None else frontSpread
        backSpread = self.BSpr if backSpread is None else backSpread
        upCurve = self.UCur if upCurve is None else upCurve
        downCurve = self.DCur if downCurve is None else downCurve
        heightScale = self.HScl if heightScale is None else heightScale
        heightOffset = self.HOff if heightOffset is None else heightOffset

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
            self.redrawGL()
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
        for direction in [CONST.FRONT, CONST.BACK, CONST.LEFT, CONST.RIGHT, CONST.UP, CONST.DOWN]:
            if relation_map[direction] == {}:  # 该方向没有零件，跳过
                continue
            # 零件移动的情况（目前仅考虑所有零件x=0的情况）
            if direction in (CONST.FRONT, CONST.BACK  # 只有y轴变化
                             ) and pos_diff[1] != 0 and pos_diff[0] == pos_diff[2] == 0:
                for part in relation_map[direction].keys():
                    part.change_attrs(
                        (part.Pos[0], part.Pos[1] + pos_diff[1], part.Pos[2]), part.Amr,
                        part.Len, part.Hei, part.FWid, part.BWid, part.FSpr,
                        part.BSpr, part.UCur, part.DCur, part.HScl,
                        part.HOff)
            if direction in (CONST.LEFT, CONST.RIGHT  # 只有x轴变化
                             ) and pos_diff[0] != 0 and pos_diff[1] == pos_diff[2] == 0:
                pass
            if direction in (CONST.UP, CONST.DOWN  # 只有z轴变化
                             ) and pos_diff[2] != 0 and pos_diff[0] == pos_diff[1] == 0:
                for part in relation_map[direction].keys():
                    part.change_attrs(
                        (part.Pos[0], part.Pos[1], part.Pos[2] + pos_diff[2]), part.Amr,
                        part.Len, part.Hei, part.FWid, part.BWid, part.FSpr,
                        part.BSpr, part.UCur, part.DCur, part.HScl,
                        part.HOff)
            # 改变高度的情况
            if direction in (CONST.FRONT, CONST.BACK) and height_diff != 0:
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

    def get_data_in_coordinate(self, other_part: Union[NAPart, None] = None):
        """
        将零件的前后左右上下节点信息转化到世界坐标或其他零件的坐标系中
        例如一个零件在绕y轴旋转180度后，其左前下节点变为右后下节点
        :return: 例如：当零件没有旋转的时候（z+为前）：
        dict = {
        "FLU": self.FWid + self.FSpr, "FRU": self.FWid + self.FSpr, "FLD": self.FWid, "FRD": self.FWid,
        "BLU": self.BWid + self.BSpr, "BRU": self.BWid + self.BSpr, "BLD": self.BWid, "BRD": self.BWid,
        "H": self.Hei
        }
        """
        # 获取零件的旋转关系
        if other_part:
            rotation_relation = get_rot_relation(other_part.Rot, self.Rot)
        else:
            rotation_relation = get_rot_relation([0, 0, 0], self.Rot)

        # 根据旋转关系计算节点信息在世界坐标系中的位置
        if rotation_relation == 'same':
            # 零件没有旋转，直接返回初始节点信息
            part_data = {
                "FLU": self.FWid + self.FSpr, "FRU": self.FWid + self.FSpr, "FLD": self.FWid, "FRD": self.FWid,
                "BLU": self.BWid + self.BSpr, "BRU": self.BWid + self.BSpr, "BLD": self.BWid, "BRD": self.BWid,
                "BH": self.Hei, "FH": self.Hei * self.HScl, "H": self.Hei,
                "L": self.Len
            }
        elif rotation_relation == 'x':
            # 零件绕x轴旋转180度（前后上下颠倒）
            part_data = {
                "FLU": self.BWid, "FRU": self.BWid, "FLD": self.BWid + self.BSpr, "FRD": self.BWid + self.BSpr,
                "BLU": self.FWid, "BRU": self.FWid, "BLD": self.FWid + self.FSpr, "BRD": self.FWid + self.FSpr,
                "BH": self.Hei * self.HScl, "FH": self.Hei, "H": self.Hei,
                "L": self.Len
            }

        elif rotation_relation == 'y':
            # 零件绕y轴旋转180度（前后左右颠倒）
            part_data = {
                "FLU": self.BWid + self.BSpr, "FRU": self.BWid + self.BSpr, "FLD": self.BWid, "FRD": self.BWid,
                "BLU": self.FWid + self.FSpr, "BRU": self.FWid + self.FSpr, "BLD": self.FWid, "BRD": self.FWid,
                "BH": self.Hei * self.HScl, "FH": self.Hei, "H": self.Hei,
                "L": self.Len
            }
        elif rotation_relation == 'z':
            # 零件绕z轴旋转180度（上下左右颠倒）
            part_data = {
                "FLU": self.FWid, "FRU": self.FWid, "FLD": self.FWid + self.FSpr, "FRD": self.FWid + self.FSpr,
                "BLU": self.BWid, "BRU": self.BWid, "BLD": self.BWid + self.BSpr, "BRD": self.BWid + self.BSpr,
                "BH": self.Hei, "FH": self.Hei * self.HScl, "H": self.Hei,
                "L": self.Len
            }
        elif rotation_relation == 'o':
            # 零件绕原点中心对称（左右颠倒，上下颠倒，前后颠倒）
            part_data = {
                "FLU": self.FWid, "FRU": self.FWid, "FLD": self.FWid + self.FSpr, "FRD": self.FWid + self.FSpr,
                "BLU": self.BWid, "BRU": self.BWid, "BLD": self.BWid + self.BSpr, "BRD": self.BWid + self.BSpr,
                "BH": self.Hei * self.HScl, "FH": self.Hei, "H": self.Hei,
                "L": self.Len
            }
        elif rotation_relation == 'u':
            # 零件向上抬头90度（y+为上）
            part_data = {
                "FLU": self.FWid, "FRU": self.FWid, "FLD": self.BWid, "FRD": self.BWid,
                "BLU": self.FWid + self.FSpr, "BRU": self.FWid + self.FSpr, "BLD": self.BWid + self.BSpr,
                "BRD": self.BWid + self.BSpr,
                "BH": self.Len, "FH": self.Len, "H": self.Len,
                "L": self.Hei
            }
        elif rotation_relation == 'd':
            # 零件低头90度（y-为下）
            part_data = {
                "FLU": self.BWid + self.BSpr, "FRU": self.BWid + self.BSpr, "FLD": self.FWid + self.FSpr,
                "FRD": self.FWid + self.FSpr,
                "BLU": self.BWid, "BRU": self.BWid, "BLD": self.FWid, "BRD": self.FWid,
                "BH": self.Len, "FH": self.Len, "H": self.Len,
                "L": self.Hei
            }
        elif rotation_relation == 'l':
            # 零件左转90度（x+为左）
            part_data = {
                "FLU": self.Len, "FRU": self.Len, "FLD": self.Len, "FRD": self.Len,
                "BLU": self.Len, "BRU": self.Len, "BLD": self.Len, "BRD": self.Len,
                "BH": self.Hei, "FH": self.Hei, "H": self.Hei,
                "L": self.Len
            }
        elif rotation_relation == 'r':
            # 零件右转90度（y+为右）
            part_data = {
                "FLU": self.Len, "FRU": self.Len, "FLD": self.Len, "FRD": self.Len,
                "BLU": self.Len, "BRU": self.Len, "BLD": self.Len, "BRD": self.Len,
                "BH": self.Hei, "FH": self.Hei, "H": self.Hei,
                "L": self.Len
            }
        else:
            # 其他情况，暂时不处理
            part_data = None
        return part_data

    def only_self_add_z(self, smooth=False):
        """
        操作单零件
        对零件进行z细分，平均分为前后两部分（注意，是零件坐标系的z轴）
        :param smooth: 是否根据前后零件对中间层进行平滑
        :return:
        """
        FP, BP = self.add_z_without_relation(smooth=smooth)
        if FP is None or BP is None:
            return None, None
        # 添加到关系图
        if self.Rot[0] % 90 == 0 and self.Rot[1] % 90 == 0 and self.Rot[2] % 90 == 0:
            self.allParts_relationMap.replace([FP, BP], self)
            # self.allParts_relationMap.replace_2(FP, BP, self, None)
        # 重新渲染
        self.glWin.repaintGL()
        return FP, BP

    def only_self_add_y(self, smooth=False):
        """
        操作单零件
        对零件进行z细分，平均分为前后两部分（注意，是零件坐标系的z轴）
        :param smooth: 是否根据前后零件对中间层进行平滑
        :return:
        """
        UP, DP = self.add_y_without_relation(smooth=smooth)
        if UP is None or DP is None:
            return None, None
        # 添加到关系图
        if self.Rot[0] % 90 == 0 and self.Rot[1] % 90 == 0 and self.Rot[2] % 90 == 0:
            self.allParts_relationMap.replace([UP, DP], self)
            # self.allParts_relationMap.replace_2(UP, DP, self, None)
        # 重新渲染
        self.glWin.repaintGL()

    def add_z_without_relation(self, smooth=False):
        """
        不操作关系图，用于多零件操作或单零件操作的关系图操作前
        :param smooth:
        :return:
        """
        if self.HOff != 0:  # 暂时不支持有高度偏移的零件进行z细分
            return None, None
        front_vector = np.array([0., 0., 1.])
        front_vector = rotate_quaternion(front_vector, self.Rot)
        # 寻找前后左右上下的零件
        if self in self.allParts_relationMap.basicMap.keys() and tuple(front_vector) in VECTOR_RELATION_MAP.keys():
            # 转置关系映射
            relation_map = self.allParts_relationMap.basicMap[self]
            front_parts = list(relation_map[VECTOR_RELATION_MAP[tuple(front_vector)]["Larger"]].keys())
            back_parts = list(relation_map[VECTOR_RELATION_MAP[tuple(front_vector)]["Smaller"]].keys())
        else:
            front_parts = []
            back_parts = []
        # 得到前后零件
        front_part: Union[None, AdjustableHull] = None
        back_part: Union[None, AdjustableHull] = None
        f_data: Union[None, dict] = None
        b_data: Union[None, dict] = None
        if front_parts:
            for p in front_parts:
                v1 = np.array(p.Pos) - np.array(self.Pos)
                # 对后零件进行关于本零件的转置
                f_data = p.get_data_in_coordinate(self)
                if not f_data:
                    continue
                v2 = front_vector * self.Scl[2] * (self.Len / 2 + f_data["L"] / 2)
                if np.linalg.norm(v1 - v2) < 0.001 and self.FWid * self.Scl[0] == f_data["BLD"] * p.Scl[0]:
                    # 如果前后相接且宽度相接
                    front_part = p
                    break
        if back_parts:
            for p in back_parts:
                v1 = np.array(self.Pos) - np.array(p.Pos)
                # 对后零件进行关于本零件的转置
                b_data = p.get_data_in_coordinate(self)
                if not b_data:
                    continue
                v2 = front_vector * self.Scl[2] * (self.Len / 2 + b_data["L"] / 2)
                if np.linalg.norm(v1 - v2) < 0.001 and self.BWid * self.Scl[0] == b_data["FLD"] * p.Scl[0]:
                    # 如果前后相接且宽度相接
                    back_part = p
                    break
        # 计算中间层的宽度变化率
        if smooth and (front_part or back_part):
            # 计算中间层的宽度变化率，上宽度变化率，高度变化率
            self_wid_spr_ratio = (self.FWid - self.BWid) * self.Scl[0] / (self.Len * self.Scl[2])
            self_uw_spr_ratio = (self.FWid + self.FSpr - self.BWid - self.BSpr) * self.Scl[0] / (self.Len * self.Scl[2])
            self_hei_scl_ratio = (self.Hei * self.HScl - self.Hei) / (self.Len * self.Scl[2])
            if front_part:
                front_wid_spr_ratio = (f_data["FLD"] - f_data["BLD"]) * front_part.Scl[0] / (
                        f_data["L"] * front_part.Scl[2])
                front_uw_spr_ratio = (f_data["FLU"] - f_data["BLU"]) * front_part.Scl[0] / (
                        f_data["L"] * front_part.Scl[2])
                front_hei_scl_ratio = (f_data["FH"] - f_data["BH"]) * front_part.Scl[1] / (
                        f_data["L"] * front_part.Scl[2])
            if back_part:
                back_wid_spr_ratio = (b_data["FLD"] - b_data["BLD"]) * back_part.Scl[0] / (
                        b_data["L"] * back_part.Scl[2])
                back_uw_spr_ratio = (b_data["FLU"] - b_data["BLU"]) * back_part.Scl[0] / (
                        b_data["L"] * back_part.Scl[2])
                back_hei_scl_ratio = (b_data["FH"] - b_data["BH"]) * back_part.Scl[1] / (
                        b_data["L"] * back_part.Scl[2])
            # 处理前后零件缺失的情况（添加默认值）
            if front_part and not back_part:
                # 给back_part的比率赋值为前零件-2*(前零件-中零件)
                # noinspection PyUnboundLocalVariable
                back_wid_spr_ratio = front_wid_spr_ratio - 2 * (front_wid_spr_ratio - self_wid_spr_ratio)
                # noinspection PyUnboundLocalVariable
                back_uw_spr_ratio = front_uw_spr_ratio - 2 * (front_uw_spr_ratio - self_uw_spr_ratio)
                # noinspection PyUnboundLocalVariable
                back_hei_scl_ratio = front_hei_scl_ratio - 2 * (front_hei_scl_ratio - self_hei_scl_ratio)
            elif not front_part and back_part:
                # 给front_part的比率赋值为后零件-2*(后零件-中零件)
                # noinspection PyUnboundLocalVariable
                front_wid_spr_ratio = back_wid_spr_ratio - 2 * (back_wid_spr_ratio - self_wid_spr_ratio)
                # noinspection PyUnboundLocalVariable
                front_uw_spr_ratio = back_uw_spr_ratio - 2 * (back_uw_spr_ratio - self_uw_spr_ratio)
                # noinspection PyUnboundLocalVariable
                front_hei_scl_ratio = back_hei_scl_ratio - 2 * (back_hei_scl_ratio - self_hei_scl_ratio)
            # 用贝塞尔曲线拟合
            wid_ratios = fit_bezier(front_wid_spr_ratio, back_wid_spr_ratio,
                                    self.Len * self.Scl[2], (self.FWid - self.BWid) * self.Scl[0], 2)
            uw_ratios = fit_bezier(front_uw_spr_ratio, back_uw_spr_ratio,
                                   self.Len * self.Scl[2],
                                   (self.FWid + self.FSpr - self.BWid - self.BSpr) * self.Scl[0], 2)
            hei_ratios = fit_bezier(front_hei_scl_ratio, back_hei_scl_ratio,
                                    self.Len * self.Scl[2], (self.Hei * self.HScl - self.Hei) * self.Scl[1], 2)
            B_wid_spr_ratio = wid_ratios[1]
            B_uw_spr_ratio = uw_ratios[1]
            B_hei_scl_ratio = hei_ratios[1]
            # 计算前后零件的数值：
            mid_width = self.BWid + B_wid_spr_ratio * self.Len * self.Scl[2] * 0.5
            mid_uwidth = self.BWid + self.BSpr + B_uw_spr_ratio * self.Len * self.Scl[2] * 0.5
            mid_height = self.Hei + B_hei_scl_ratio * self.Len * self.Scl[2] * 0.5
        else:  # 不进行平滑处理的情况
            mid_width = (self.FWid + self.BWid) / 2
            mid_uwidth = (self.FWid + self.FSpr + self.BWid + self.BSpr) / 2
            mid_height = (self.Hei * self.HScl + self.Hei) / 2
        # 处理异常值
        if mid_width < 0:
            mid_width = 0
        if mid_uwidth < 0:
            mid_uwidth = 0
        # 求出新零件的参数
        mid_spread = mid_uwidth - mid_width
        pos_offset = front_vector * self.Len / 4 * self.Scl[2]
        F_Pos = np.array(self.Pos) + pos_offset
        B_Pos = np.array(self.Pos) - pos_offset
        F_Hei = mid_height if mid_height > 0 else 0
        F_HScl = (self.Hei * self.HScl) / mid_height
        B_Hei = self.Hei
        B_HScl = mid_height / self.Hei
        # 生成新零件对象
        if F_HScl <= 1:
            FP = AdjustableHull(
                self.read_na_obj, self.Id, F_Pos, self.Rot, self.Scl, self.Col, self.Amr,
                self.Len / 2, F_Hei, self.FWid, mid_width, self.FSpr, mid_spread, self.UCur, self.DCur, F_HScl, 0)
        else:  # 当 Hcl > 1，旋转角绕y轴旋转180度，因为在NavalArt中禁止了Hcl>1的情况，反转可以让Hcl<1
            rv_rot = [self.Rot[0], self.Rot[1] + 180, self.Rot[2]]
            fw = mid_width
            bw = self.FWid
            fs = mid_spread
            bs = self.FSpr
            hei = F_Hei * F_HScl
            h_scl = 1 / F_HScl
            FP = AdjustableHull(
                self.read_na_obj, self.Id, F_Pos, rv_rot, self.Scl, self.Col, self.Amr,
                self.Len / 2, hei, fw, bw, fs, bs, self.UCur, self.DCur, h_scl, 0)
        if B_HScl <= 1:
            BP = AdjustableHull(
                self.read_na_obj, self.Id, B_Pos, self.Rot, self.Scl, self.Col, self.Amr,
                self.Len / 2, B_Hei, mid_width, self.BWid, mid_spread, self.BSpr, self.UCur, self.DCur, B_HScl, 0)
        else:  # 当 Hcl > 1，旋转角绕y轴旋转180度，因为在NavalArt中禁止了Hcl>1的情况，反转可以让Hcl<1
            rv_rot = [self.Rot[0], self.Rot[1] + 180, self.Rot[2]]
            fw = self.BWid
            bw = mid_width
            fs = self.BSpr
            bs = mid_spread
            hei = B_Hei * B_HScl
            h_scl = 1 / B_HScl
            BP = AdjustableHull(
                self.read_na_obj, self.Id, B_Pos, rv_rot, self.Scl, self.Col, self.Amr,
                self.Len / 2, hei, fw, bw, fs, bs, self.UCur, self.DCur, h_scl, 0)
        return FP, BP

    def add_y_without_relation(self, smooth=False):
        if self.HOff != 0:  # 暂时不支持有高度偏移的零件进行z细分
            return None, None
        up_vector = np.array([0., 1., 0.])
        up_vector = rotate_quaternion(up_vector, self.Rot)
        # 寻找前后左右上下的零件
        if self in self.allParts_relationMap.basicMap.keys() and tuple(up_vector) in VECTOR_RELATION_MAP.keys():
            # 转置关系映射
            relation_map = self.allParts_relationMap.basicMap[self]
            up_parts = list(relation_map[VECTOR_RELATION_MAP[tuple(up_vector)]["Larger"]].keys())
            down_parts = list(relation_map[VECTOR_RELATION_MAP[tuple(up_vector)]["Smaller"]].keys())
        else:
            up_parts = []
            down_parts = []
        # 得到上下零件
        up_part: Union[None, AdjustableHull] = None
        down_part: Union[None, AdjustableHull] = None
        u_data: Union[None, dict] = None
        d_data: Union[None, dict] = None
        if up_parts:
            for p in up_parts:
                v1 = np.array(p.Pos) - np.array(self.Pos)
                # 对后零件进行关于本零件的转置
                u_data = p.get_data_in_coordinate(self)
                v2 = up_vector * self.Scl[1] * (self.Hei + u_data["H"]) / 2
                if np.linalg.norm(v1 - v2) < 0.001 and \
                        - 0.001 < (self.FWid + self.FSpr) * self.Scl[0] - u_data["FLD"] * p.Scl[0] < 0.001 and \
                        - 0.001 < (self.BWid + self.BSpr) * self.Scl[0] - u_data["BLD"] * p.Scl[0] < 0.001:
                    # 如果上下相接且宽度相接
                    up_part = p
                    # self.glWin.selected_gl_objects[self.glWin.show_3d_obj_mode].append(p)  # TODO: 要删除
                    break
        if down_parts:
            for p in down_parts:
                v1 = np.array(self.Pos) - np.array(p.Pos)
                # 对后零件进行关于本零件的转置
                d_data = p.get_data_in_coordinate(self)
                v2 = up_vector * self.Scl[1] * (self.Hei + d_data["H"]) / 2
                if np.linalg.norm(v1 - v2) < 0.001 and \
                        - 0.001 < self.FWid * self.Scl[0] - d_data["FLU"] * p.Scl[0] < 0.001 and \
                        - 0.001 < self.BWid * self.Scl[0] - d_data["BLU"] * p.Scl[0] < 0.001:
                    # 如果上下相接且宽度相接
                    down_part = p
                    # self.glWin.selected_gl_objects[self.glWin.show_3d_obj_mode].append(p)  # TODO: 要删除
                    break
        # 计算中间层的宽度变化率
        if smooth and (up_part or down_part):
            # 计算中间层的前宽度变化率，后宽度变化率
            self_fw_ratio = self.FSpr * self.Scl[0] / (self.Hei * self.Scl[1])
            self_bw_ratio = self.BSpr * self.Scl[0] / (self.Hei * self.Scl[1])
            if up_part:
                up_fw_ratio = (u_data["FLU"] - u_data["FLD"]) * up_part.Scl[0] / (u_data["H"] * up_part.Scl[1])
                up_bw_ratio = (u_data["BLU"] - u_data["BLD"]) * up_part.Scl[0] / (u_data["H"] * up_part.Scl[1])
            if down_part:
                down_fw_ratio = (d_data["FLU"] - d_data["FLD"]) * down_part.Scl[0] / (d_data["H"] * down_part.Scl[1])
                down_bw_ratio = (d_data["BLU"] - d_data["BLD"]) * down_part.Scl[0] / (d_data["H"] * down_part.Scl[1])
            # 处理前后零件缺失的情况（添加默认值）
            if up_part and not down_part:
                # 给down_part的比率赋值为上零件-2*(上零件-中零件)
                # noinspection PyUnboundLocalVariable
                down_fw_ratio = up_fw_ratio - 2 * (up_fw_ratio - self_fw_ratio)
                # noinspection PyUnboundLocalVariable
                down_bw_ratio = up_bw_ratio - 2 * (up_bw_ratio - self_bw_ratio)
            elif not up_part and down_part:
                # 给up_part的比率赋值为下零件-2*(下零件-中零件)
                # noinspection PyUnboundLocalVariable
                up_fw_ratio = down_fw_ratio - 2 * (down_fw_ratio - self_fw_ratio)
                # noinspection PyUnboundLocalVariable
                up_bw_ratio = down_bw_ratio - 2 * (down_bw_ratio - self_bw_ratio)
            # 用贝塞尔曲线拟合
            fw_ratios = fit_bezier(up_fw_ratio, down_fw_ratio,
                                   self.Hei * self.Scl[1], self.FSpr * self.Scl[0], 2)
            bw_ratios = fit_bezier(up_bw_ratio, down_bw_ratio,
                                   self.Hei * self.Scl[1], self.BSpr * self.Scl[0], 2)
            F_fw_ratio = fw_ratios[1]
            F_bw_ratio = bw_ratios[1]
            # 计算前后零件的数值：
            mid_fw = self.FWid + F_fw_ratio * self.Hei * self.Scl[1] * 0.5
            mid_bw = self.BWid + F_bw_ratio * self.Hei * self.Scl[1] * 0.5
        else:  # 不进行平滑处理的情况
            mid_fw = self.FWid + self.FSpr / 2
            mid_bw = self.BWid + self.BSpr / 2
        # 处理异常值
        if mid_fw < 0:
            mid_fw = 0
        if mid_bw < 0:
            mid_bw = 0
        # 求出新零件的参数
        pos_offset = up_vector * self.Hei / 4 * self.Scl[1]
        U_Pos = np.array(self.Pos) + pos_offset
        D_Pos = np.array(self.Pos) - pos_offset
        U_FSpr = self.FWid + self.FSpr - mid_fw
        U_BSpr = self.BWid + self.BSpr - mid_bw
        D_FSpr = mid_fw - self.FWid
        D_BSpr = mid_bw - self.BWid
        # 生成新零件对象
        UP = AdjustableHull(
            self.read_na_obj, self.Id, U_Pos, self.Rot, self.Scl, self.Col, self.Amr,
            self.Len, self.Hei / 2, mid_fw, mid_bw, U_FSpr, U_BSpr, self.UCur, 0, 1, 0)
        DP = AdjustableHull(
            self.read_na_obj, self.Id, D_Pos, self.Rot, self.Scl, self.Col, self.Amr,
            self.Len, self.Hei / 2, self.FWid, self.BWid, D_FSpr, D_BSpr, 0, self.DCur, 1, 0)
        # # 在数据中删除原来的零件
        # self.read_na_obj.DrawMap[f"#{self.Col}"].remove(self)
        # # 往read_na的drawMap中添加零件
        # self.read_na_obj.DrawMap[f"#{self.Col}"].append(UP)
        # self.read_na_obj.DrawMap[f"#{self.Col}"].append(DP)
        # # 更新显示的被选中的零件
        # if self.glWin:
        #     try:
        #         self.glWin.selected_gl_objects[self.glWin.show_3d_obj_mode].remove(self)
        #         self.glWin.selected_gl_objects[self.glWin.show_3d_obj_mode].append(UP)
        #         self.glWin.selected_gl_objects[self.glWin.show_3d_obj_mode].append(DP)
        #     except ValueError:
        #         # 用户选中零件后转换到了其他模式，而右侧的编辑器仍然处在原来的模式
        #         replaced = False
        #         while not replaced:
        #             for mode in self.glWin.selected_gl_objects.keys():
        #                 try:
        #                     self.glWin.selected_gl_objects[mode].remove(self)
        #                     self.glWin.selected_gl_objects[mode].append(UP)
        #                     self.glWin.selected_gl_objects[mode].append(DP)
        #                     replaced = True
        #                     break
        #                 except ValueError:
        #                     continue
        # # 从hull_design_tab_id_map（绘制所需）删除原来的零件
        # NAPart.hull_design_tab_id_map.pop(id(self) % 4294967296)
        # # 向hull_design_tab_id_map（绘制所需）添加新的零件
        # NAPart.hull_design_tab_id_map[id(UP) % 4294967296] = UP
        # NAPart.hull_design_tab_id_map[id(DP) % 4294967296] = DP
        return UP, DP

    def scale(self, ratio: list, update=False):
        super().scale(ratio)
        self.plot_all_dots = []  # 曲面变换前，位置变换后的所有点
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
        self.plot_lines = self.get_plot_lines()
        self.plot_faces = self.get_plot_faces()
        if update:
            self.redrawGL()
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
        gl.glLoadName(id(self) % 4294967296)
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

    def redrawGL(self):
        # 修改零件本身的genList状态
        self.updateList = True
        self.update_selectedList = True
        # 重新渲染
        self.glWin.repaintGL()
        # 修改零件本身的genList状态
        self.updateList = False
        self.update_selectedList = False

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
                    if i % 13 == 0:
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
            # 上方已经初始化了drawMap，不init了
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
                if i % 13 == 0:
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
    last_map = None

    def __init__(self, read_na, show_statu_func):
        """
        建立有向图，6种关系，上下左右前后，权重等于距离（按照从小到大的顺序，越近索引越小，越远索引越大）
        :param read_na:
        :param show_statu_func:
        """
        self.show_statu_func = show_statu_func
        self.Parts = read_na.Parts
        self.na_hull = read_na  # na船体对象
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
        """零件关系"""
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
        self.__temp_data = {  # 在初始化过程中用于优化的数据
            "": []
        }
        PartRelationMap.last_map = self

    @staticmethod
    def _add_basicMap_relation(part, other_part, part_relation, other_part_relation, raw_dir):
        """
        添加零件的关系
        :param part: 添加的零件
        :param other_part: 与之关系的零件
        :param part_relation: 新增零件的关系映射
        :param other_part_relation: 与之关系的零件的关系映射
        :param raw_dir: 毛方向，前后，上下，左右
        """
        if raw_dir == CONST.SAME:
            other_part_relation[CONST.SAME][part] = 0
            for _dir in (CONST.FRONT, CONST.BACK, CONST.UP, CONST.DOWN, CONST.LEFT, CONST.RIGHT):
                part_relation[_dir] = other_part_relation[_dir].copy()
            part_relation[CONST.SAME][other_part] = 0
            return
        pos_i = CONST.DIR_INDEX_MAP[raw_dir]
        sub_dirs = CONST.SUBDIR_MAP[raw_dir]
        larger_dir = sub_dirs[0]
        smaller_dir = sub_dirs[1]
        value = abs(other_part.Pos[pos_i] - part.Pos[pos_i])
        if other_part.Pos[pos_i] > part.Pos[pos_i]:  # other在part的前面
            part_relation[larger_dir][other_part] = value
            other_part_relation[smaller_dir][part] = value
        elif other_part.Pos[pos_i] < part.Pos[pos_i]:  # other在part的后面
            part_relation[smaller_dir][other_part] = value
            other_part_relation[larger_dir][part] = value
        # 将other_part的相应的方向的零件也添加到new_part的该方向零件中
        for sub_dir in sub_dirs:
            for other_part_direction, _other_part_direction_value in other_part_relation[sub_dir].items():
                value2 = abs(other_part_direction.Pos[pos_i] - part.Pos[pos_i])
                if other_part_direction.Pos[pos_i] > part.Pos[pos_i]:
                    part_relation[larger_dir][other_part_direction] = value2
                elif other_part_direction.Pos[pos_i] < part.Pos[pos_i]:
                    part_relation[smaller_dir][other_part_direction] = value2

    def add_part(self, newPart, all_parts: list = Union[list, None]):
        """
        添加零件
        :param newPart:
        :param all_parts:
        :return: 耗时（截面对象，零件关系，节点集合）
        """
        # 000000000000000000000000000000000000000000000000000000000000000000000 筛选
        if not isinstance(newPart, AdjustableHull):
            return 0., 0., 0.
        if int(newPart.Rot[0]) % 90 != 0 or int(newPart.Rot[1]) % 90 != 0 or int(newPart.Rot[2]) % 90 != 0:
            return 0., 0., 0.
        # 000000000000000000000000000000000000000000000000000000000000000000000 点集
        st = time.time()
        if isinstance(newPart, AdjustableHull):
            newPart.Pos = [round(newPart.Pos[0], 3), round(newPart.Pos[1], 3), round(newPart.Pos[2], 3)]
            for dot in newPart.operation_dot_nodes:
                # dot是np.ndarray类型
                _x = round(float(dot[0]), 3)
                _y = round(float(dot[1]), 3)
                _z = round(float(dot[2]), 3)
                if [_x, _y, _z] not in NAPartNode.all_dots:
                    node = NAPartNode([_x, _y, _z])
                    # 判断零件在节点的哪一个卦限
                    x, y, z = newPart.Pos
                    x_str = CONST.BACK if x > _x else CONST.FRONT
                    y_str = CONST.DOWN if y > _y else CONST.UP
                    z_str = CONST.LEFT if z > _z else CONST.RIGHT
                    node.near_parts[f"{x_str}_{y_str}_{z_str}"].append(newPart)
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
        # 000000000000000000000000000000000000000000000000000000000000000000000 层集
        st = time.time()
        # 初始化零件的上下左右前后零件
        newPart_relation = {CONST.FRONT: {}, CONST.BACK: {}, CONST.UP: {}, CONST.DOWN: {},
                            CONST.LEFT: {}, CONST.RIGHT: {}, CONST.SAME: {}}
        x_exist = set()  # 和新零件x相同的零件
        y_exist = set()  # 和新零件y相同的零件
        z_exist = set()  # 和新零件z相同的零件
        n_x, n_y, n_z = newPart.Pos
        if n_x not in self.yzPartsLayerMap.keys():
            self.yzPartsLayerMap[n_x] = [newPart]
        else:
            x_exist = set(self.yzPartsLayerMap[n_x])
            self.yzPartsLayerMap[n_x].append(newPart)
        if n_y not in self.xzPartsLayerMap.keys():
            self.xzPartsLayerMap[n_y] = [newPart]
        else:
            y_exist = set(self.xzPartsLayerMap[n_y])
            self.xzPartsLayerMap[n_y].append(newPart)
        if n_z not in self.xyPartsLayerMap.keys():
            self.xyPartsLayerMap[n_z] = [newPart]
        else:
            z_exist = set(self.xyPartsLayerMap[n_z])
            self.xyPartsLayerMap[n_z].append(newPart)
        layer_t = round(time.time() - st, 4)
        # 000000000000000000000000000000000000000000000000000000000000000000000 零件关系
        st = time.time()
        # 先检查是否有有位置关系的other_part，如果有，就添加到new_part的上下左右前后零件中
        # 然后新零件new_part根据other_part的关系扩充自己的关系
        if len(self.basicMap) == 0:  # 如果basicMap为空，就直接添加
            self.basicMap[newPart] = newPart_relation
            return layer_t, 0, 0
        xy_exist = x_exist & y_exist  # z轴向
        xz_exist = x_exist & z_exist  # y轴向
        yz_exist = y_exist & z_exist  # x轴向
        # xyz_exist = xy_exist | yz_exist | xz_exist
        for otherPart in xy_exist:
            others_direction_relation = self.basicMap[otherPart]
            if otherPart.Pos != newPart.Pos:
                self._add_basicMap_relation(
                    newPart, otherPart, newPart_relation, others_direction_relation, CONST.FRONT_BACK)
        for otherPart in yz_exist:
            others_direction_relation = self.basicMap[otherPart]
            if otherPart.Pos != newPart.Pos:
                self._add_basicMap_relation(
                    newPart, otherPart, newPart_relation, others_direction_relation, CONST.LEFT_RIGHT)
        for otherPart in xz_exist:
            others_direction_relation = self.basicMap[otherPart]
            if otherPart.Pos != newPart.Pos:  # 同一位置
                self._add_basicMap_relation(
                    newPart, otherPart, newPart_relation, others_direction_relation, CONST.UP_DOWN)
            else:
                self._add_basicMap_relation(
                    newPart, otherPart, newPart_relation, others_direction_relation, CONST.SAME)
        # 将new_part的关系添加到basicMap中
        self.basicMap[newPart] = newPart_relation
        relation_t = round(time.time() - st, 4)
        return layer_t, relation_t, dot_t

    def replace(self, parts: List[AdjustableHull], replaced_part):
        """
        替换零件集合，新的零件集合都有相同的某个坐标值
        :param parts:
        :param replaced_part:
        :return:
        """
        if not parts:
            return
        if replaced_part not in self.basicMap.keys():
            return
        # 判断方向（哪一个坐标值相同）
        direction = get_raw_direction(parts)
        if not direction:
            return  # 如果仍然没有判断出方向，就不替换
        # 定义一个方向映射，以便根据不同的方向进行操作
        direction_map = {
            CONST.FRONT_BACK: (CONST.FRONT, CONST.BACK),
            CONST.UP_DOWN: (CONST.UP, CONST.DOWN),
            CONST.LEFT_RIGHT: (CONST.LEFT, CONST.RIGHT)
        }
        larger_dir = direction_map[direction][0]
        smaller_dir = direction_map[direction][1]
        # 获取方向对应的坐标索引
        pos_i = CONST.DIR_INDEX_MAP[direction]
        # 按照方向值从小到大排序
        parts.sort(key=lambda _part: _part.Pos[pos_i])
        # 获取被替换零件的关系图
        replaced_relation_map = self.basicMap[replaced_part]
        # 初始化新零件的关系
        new_part_relation_maps = {}
        for i in range(len(parts)):
            new_part = parts[i]
            new_part_relation_maps[new_part] = {CONST.FRONT: {}, CONST.BACK: {},
                                                CONST.UP: {}, CONST.DOWN: {},
                                                CONST.LEFT: {}, CONST.RIGHT: {},
                                                CONST.SAME: {}}
            # 先添加新零件到各自的关系图中
            for larger_dir_p in parts[i + 1:]:
                new_part_relation_maps[new_part][larger_dir][larger_dir_p] = abs(
                    larger_dir_p.Pos[pos_i] - new_part.Pos[pos_i])
            for smaller_dir_p in parts[:i]:
                new_part_relation_maps[new_part][smaller_dir][smaller_dir_p] = abs(
                    smaller_dir_p.Pos[pos_i] - new_part.Pos[pos_i])
            # 遍历被替换零件的关系，将其关系添加到新零件的关系图中
            for l_part in replaced_relation_map[larger_dir].keys():
                new_part_relation_maps[new_part][larger_dir][l_part] = abs(
                    l_part.Pos[pos_i] - new_part.Pos[pos_i])
            for s_part in replaced_relation_map[smaller_dir].keys():
                new_part_relation_maps[new_part][smaller_dir][s_part] = abs(
                    s_part.Pos[pos_i] - new_part.Pos[pos_i])
            # 给关系零件添加关系
            # 先找到被替换零件的位置，然后在该位置插入新键值对
            for part in replaced_relation_map[smaller_dir].keys():
                # 给原零件添加关系
                self.basicMap[part][larger_dir][new_part] = abs(
                    part.Pos[pos_i] - new_part.Pos[pos_i])
            for part in replaced_relation_map[larger_dir].keys():
                # 给原零件添加关系
                self.basicMap[part][smaller_dir][new_part] = abs(
                    part.Pos[pos_i] - new_part.Pos[pos_i])
        # 删除原零件，按value排序原零件关系零件的关系
        for _dir in [CONST.FRONT, CONST.BACK, CONST.UP, CONST.DOWN, CONST.LEFT, CONST.RIGHT]:
            for part in replaced_relation_map[_dir].keys():
                op_dir = CONST.DIR_OPPOSITE_MAP[_dir]
                del self.basicMap[part][op_dir][replaced_part]
                if _dir in [larger_dir, smaller_dir]:
                    self.basicMap[part][op_dir] = dict(sorted(
                        self.basicMap[part][op_dir].items(),
                        key=lambda x: x[1]))
        # 将新零件的关系添加到basicMap中
        for new_part, new_part_relation_map in new_part_relation_maps.items():
            self.basicMap[new_part] = new_part_relation_map
        # 不删除原零件，因为可能还有其他零件与其有关系

    def undo_replace(self, parts: List[AdjustableHull], replaced_part):
        """
        撤回替换零件集合，新的零件集合都有相同的某个坐标值
        :param parts:
        :param replaced_part:  原来已经被替换的零件
        :return:
        """
        if not parts:
            return
        if replaced_part not in self.basicMap.keys():
            self.show_statu_func(f"被替换零件不在basicMap中", "warning")
        # 判断方向（哪一个坐标值相同）
        direction = get_raw_direction(parts)
        if not direction:
            return  # 如果仍然没有判断出方向，就不替换
        # 定义一个方向映射，以便根据不同的方向进行操作
        direction_map = {
            CONST.FRONT_BACK: (CONST.FRONT, CONST.BACK),
            CONST.UP_DOWN: (CONST.UP, CONST.DOWN),
            CONST.LEFT_RIGHT: (CONST.LEFT, CONST.RIGHT)
        }
        larger_dir = direction_map[direction][0]
        smaller_dir = direction_map[direction][1]
        # 获取方向对应的坐标索引
        pos_i = CONST.DIR_INDEX_MAP[direction]
        # 按照方向值从小到大排序
        parts.sort(key=lambda _part: _part.Pos[pos_i])
        # 获取被替换零件的关系图
        replaced_relation_map = self.basicMap[replaced_part]
        # 删除新零件在其关系零件中的关系
        for added_p in parts:
            for part in replaced_relation_map[larger_dir].keys():
                del self.basicMap[part][smaller_dir][added_p]
            for part in replaced_relation_map[smaller_dir].keys():
                del self.basicMap[part][larger_dir][added_p]
            # 删除新零件
            del self.basicMap[added_p]
        # 恢复原零件在其关系零件中的关系
        for direction, part_dict in self.basicMap[replaced_part].items():
            for part, value in part_dict.items():
                self.basicMap[part][CONST.DIR_OPPOSITE_MAP[direction]][replaced_part] = value
                # 按value排序
                self.basicMap[part][CONST.DIR_OPPOSITE_MAP[direction]] = dict(sorted(
                    self.basicMap[part][CONST.DIR_OPPOSITE_MAP[direction]].items(),
                    key=lambda x: x[1]))

    def add_layer(self, part_map, direction):
        """
        添加零件层
        :param part_map: 原零件：要添加的相应的新零件
        :param direction: 方向
        :return:
        """
        opposite_dir = CONST.DIR_OPPOSITE_MAP[direction]
        for org_p, new_p in part_map.items():
            pos_i = CONST.DIR_INDEX_MAP[CONST.DIR_TO_RAWDIR_MAP[direction]]
            self.basicMap[new_p] = {CONST.FRONT: {}, CONST.BACK: {}, CONST.UP: {}, CONST.DOWN: {},
                                    CONST.LEFT: {}, CONST.RIGHT: {}, CONST.SAME: {}}
            # 往原零件的该方向添加新零件
            self.basicMap[org_p][direction][new_p] = abs(
                org_p.Pos[pos_i] - new_p.Pos[pos_i])
            if len(self.basicMap[org_p][direction]) > 1:  # 如果该方向的零件数量大于1，就按照value排序
                self.basicMap[org_p][direction] = dict(sorted(
                    self.basicMap[org_p][direction].items(),
                    key=lambda x: x[1]))
            # 往新零件的相反方向添加原零件
            self.basicMap[new_p][opposite_dir][org_p] = abs(
                org_p.Pos[pos_i] - new_p.Pos[pos_i])
            # 将原零件的反方向关系表添加到新零件
            for other_p, value in self.basicMap[org_p][opposite_dir].items():
                self.basicMap[new_p][opposite_dir][other_p] = value
        # 给新零件之间添加垂直方向的关系
        for new_p in part_map.values():
            for v_dir in CONST.VERTICAL_DIR_MAP[direction]:
                raw_dir = CONST.DIR_TO_RAWDIR_MAP[v_dir]
                pos_i = CONST.DIR_INDEX_MAP[raw_dir]
                other_pos_i = [i for i in range(3) if i != pos_i]
                op0 = other_pos_i[0]
                op1 = other_pos_i[1]
                if v_dir in [CONST.FRONT, CONST.UP, CONST.LEFT]:
                    _exist = set([part for part in part_map.values() if (
                            part.Pos[pos_i] > new_p.Pos[pos_i] and
                            part.Pos[op0] == new_p.Pos[op0] and
                            part.Pos[op1] == new_p.Pos[op1]
                    )])
                else:
                    _exist = set([part for part in part_map.values() if (
                            part.Pos[pos_i] < new_p.Pos[pos_i] and
                            part.Pos[op0] == new_p.Pos[op0] and
                            part.Pos[op1] == new_p.Pos[op1]
                    )])
                for other_p in _exist:
                    self.basicMap[new_p][v_dir][other_p] = abs(
                        other_p.Pos[pos_i] - new_p.Pos[pos_i])
                # 按value排序
                self.basicMap[new_p][v_dir] = dict(sorted(
                    self.basicMap[new_p][v_dir].items(),
                    key=lambda x: x[1]))

    def undo_add_layer(self, part_map, direction):
        """
        撤回添加零件层
        :param part_map: 原零件：需要删除的新零件
        :param direction: 方向
        :return:
        """
        # 往原零件中删除新零件
        for org_p, new_p in part_map.items():
            del self.basicMap[org_p][direction][new_p]
        # 给新零件间删除所有的关系
        for new_p in part_map.values():
            self.basicMap[new_p] = {CONST.FRONT: {}, CONST.BACK: {}, CONST.UP: {}, CONST.DOWN: {},
                                    CONST.LEFT: {}, CONST.RIGHT: {}, CONST.SAME: {}}  # 清空关系

    def del_part(self, part):
        """
        删除零件
        :param part:
        :return:
        """
        PartRelationMap.last_map = self
        # 遍历自身的相关零件，将自身从其关系中删除
        for direction, other_parts in self.basicMap[part].items():
            for other_part in other_parts.keys():
                del self.basicMap[other_part][CONST.DIR_OPPOSITE_MAP[direction]][part]
        # 删除自身
        self.basicMap[part] = {CONST.FRONT: {}, CONST.BACK: {}, CONST.UP: {}, CONST.DOWN: {},
                               CONST.LEFT: {}, CONST.RIGHT: {}, CONST.SAME: {}}

    def remap(self):
        PartRelationMap.last_map = self
        # 清空所有数据
        NAPartNode.all_dots.clear()
        NAPartNode.id_map.clear()
        self.basicMap.clear()
        self.xzDotsLayerMap.clear()
        self.xyDotsLayerMap.clear()
        self.yzDotsLayerMap.clear()
        self.xzPartsLayerMap.clear()
        self.xyPartsLayerMap.clear()
        self.yzPartsLayerMap.clear()

        st = time.time()
        total_parts_num = len(NAPart.hull_design_tab_id_map)
        all_parts = [part for part in NAPart.hull_design_tab_id_map.values()]
        i = 1
        for part in NAPart.hull_design_tab_id_map.values():
            layer_t, relation_t, dot_t = self.add_part(part, all_parts)
            # 标准化（填补0）
            layer_t = str(layer_t).ljust(6, '0')
            relation_t = str(relation_t).ljust(6, '0')
            dot_t = str(dot_t).ljust(6, '0')
            if i % 3 == 0:
                process = round(i / total_parts_num * 100, 2)
                self.show_statu_func(
                    f"正在实例化第 {i} / {total_parts_num} 个零件： {process} %"
                    f"\t\t\t\t单件耗时：     截面对象  {layer_t} s     零件关系  {relation_t} s     节点集合  {dot_t} s",
                    "process")
            i += 1
        self.show_statu_func(f"零件关系图初始化完成! 耗时：{time.time() - st}s", "success")
        self.sort()
        ttt = time.time() - st
        self.show_statu_func(f"零件关系重新绑定完成! 耗时：{ttt}s", "success")
        return ttt

    def init(self, na_hull, init=True):
        """
        :param na_hull: NaHull对象
        :param init: 如果为False，这个函数则仅用于drawMap的初始化后调用，用来指示代码位置方便Debug
        :return:
        """
        PartRelationMap.last_map = self
        if not init:
            return
        self.na_hull = na_hull
        st = time.time()
        total_parts_num = sum([len(parts) for parts in self.na_hull.DrawMap.values()])
        all_parts = [part for parts in self.na_hull.DrawMap.values() for part in parts]
        i = 1
        for _color, parts in self.na_hull.DrawMap.items():
            for part in parts:
                layer_t, relation_t, dot_t = self.add_part(part, all_parts)
                # 标准化（填补0）
                layer_t = str(layer_t).ljust(6, '0')
                relation_t = str(relation_t).ljust(6, '0')
                dot_t = str(dot_t).ljust(6, '0')
                if i % 3 == 0:
                    process = round(i / total_parts_num * 100, 2)
                    self.show_statu_func(
                        f"正在实例化第 {i} / {total_parts_num} 个零件： {process} %"
                        f"\t\t\t\t单件耗时：     截面对象  {layer_t} s     零件关系  {relation_t} s     节点集合  {dot_t} s",
                        "process")
                i += 1
        self.show_statu_func(f"零件关系图初始化完成! 耗时：{time.time() - st}s", "success")
        st = time.time()
        self.sort()
        self.show_statu_func(f"零件关系图排序完成! 耗时：{time.time() - st}s", "success")

    def sort(self):
        PartRelationMap.last_map = self
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

    def get_DotsLayerMap(self):
        """
        获取DotsLayerMap的副本
        :return: xyDotsLayerMap, xzDotsLayerMap, yzDotsLayerMap
        """
        return copy.deepcopy(self.xyDotsLayerMap), copy.deepcopy(self.xzDotsLayerMap), copy.deepcopy(
            self.yzDotsLayerMap)

    def get_PartsLayerMap(self):
        """
        获取PartsLayerMap的副本
        :return: xyPartsLayerMap, xzPartsLayerMap, yzPartsLayerMap
        """
        return copy.deepcopy(self.xyPartsLayerMap), copy.deepcopy(self.xzPartsLayerMap), copy.deepcopy(
            self.yzPartsLayerMap)
