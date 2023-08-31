import math
import xml.etree.ElementTree as ET

import numpy as np

"""
文件格式：
<root>
  <ship author="22222222222" description="description" hornType="1" hornPitch="0.9475011" tracerCol="E53D4FFF">
    <part id="0">                            # 可调节船体
      <data length="4.5" height="1" frontWidth="0.2" backWidth="0.5" frontSpread="0.05" backSpread="0.2" upCurve="0" downCurve="1" heightScale="1" heightOffset="0" />
      <position x="0" y="0" z="114.75" />
      <rotation x="0" y="0" z="0" />
      <scale x="1" y="1" z="1" />
      <color hex="975740" />
      <armor value="5" />
    </part>
    <part id="190">                         # 非可调节船体
      <position x="0" y="-8.526513E-14" z="117.0312" />
      <rotation x="90" y="0" z="0" />
      <scale x="0.03333336" y="0.03333367" z="0.1666679" />
      <color hex="975740" />
      <armor value="5" />
    </part>
  </root>
"""

Using_GL_QUADS = "GL_QUADS"
Using_GL_QUAD_STRIP = "GL_QUAD_STRIP"
Using_GL_TRIANGLES = "GL_TRIANGLES"
Using_GL_TRIANGLE_STRIP = "GL_TRIANGLE_STRIP"
Using_GL_TRIANGLE_FAN = "GL_TRIANGLE_FAN"


def rotate(x, y, z, rotX, rotY, rotZ) -> np.array:
    # 将角度转换为弧度
    rotX_rad = math.radians(rotX)
    rotY_rad = math.radians(rotY)
    rotZ_rad = math.radians(rotZ)
    # 定义旋转矩阵
    rotation_matrix_x = [
        [1, 0, 0],
        [0, math.cos(rotX_rad), -math.sin(rotX_rad)],
        [0, math.sin(rotX_rad), math.cos(rotX_rad)]
    ]
    rotation_matrix_y = [
        [math.cos(rotY_rad), 0, math.sin(rotY_rad)],
        [0, 1, 0],
        [-math.sin(rotY_rad), 0, math.cos(rotY_rad)]
    ]
    rotation_matrix_z = [
        [math.cos(rotZ_rad), -math.sin(rotZ_rad), 0],
        [math.sin(rotZ_rad), math.cos(rotZ_rad), 0],
        [0, 0, 1]
    ]
    # 计算旋转后的坐标
    rotated_x = x * rotation_matrix_z[0][0] + y * rotation_matrix_z[0][1] + z * rotation_matrix_z[0][2]
    rotated_y = x * rotation_matrix_z[1][0] + y * rotation_matrix_z[1][1] + z * rotation_matrix_z[1][2]
    rotated_z = x * rotation_matrix_z[2][0] + y * rotation_matrix_z[2][1] + z * rotation_matrix_z[2][2]

    rotated_x = rotated_x * rotation_matrix_y[0][0] + rotated_y * rotation_matrix_y[0][1] + rotated_z * rotation_matrix_y[0][2]
    rotated_y = rotated_x * rotation_matrix_y[1][0] + rotated_y * rotation_matrix_y[1][1] + rotated_z * rotation_matrix_y[1][2]
    rotated_z = rotated_x * rotation_matrix_y[2][0] + rotated_y * rotation_matrix_y[2][1] + rotated_z * rotation_matrix_y[2][2]

    rotated_x = rotated_x * rotation_matrix_x[0][0] + rotated_y * rotation_matrix_x[0][1] + rotated_z * rotation_matrix_x[0][2]
    rotated_y = rotated_x * rotation_matrix_x[1][0] + rotated_y * rotation_matrix_x[1][1] + rotated_z * rotation_matrix_x[1][2]
    rotated_z = rotated_x * rotation_matrix_x[2][0] + rotated_y * rotation_matrix_x[2][1] + rotated_z * rotation_matrix_x[2][2]

    return np.array([rotated_x, rotated_y, rotated_z])


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
        part_type = self.__class__.__name__
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
        super().__init__(Id, pos, rot, scale, color, armor)
        self.Len = length
        self.Hei = height
        self.FWid = frontWidth
        self.BWid = backWidth
        self.FSpr = frontSpread
        self.BSpr = backSpread
        self.UCur = upCurve
        self.DCur = downCurve
        self.HScl = heightScale
        self.HOff = heightOffset
        AdjustableHull.All.append(self)
        self.draw_method, self.Triangles = self.get_plot_triangles()

    def get_plot_triangles(self):
        """
        :return: 绘制零件的方法，绘制零件需的三角形集
        """
        # 获取零件顶点的坐标（相对于零件中心）
        front_z = self.Len / 2  # 零件前端的z坐标
        back_z = -self.Len / 2  # 零件后端的z坐标
        front_down_y = - self.Hei / 2 * self.HScl + self.HOff
        front_down_y = - self.Hei / 2 if front_down_y < - self.Hei / 2 else front_down_y
        front_up_y = self.Hei / 2 * self.HScl + self.HOff
        front_up_y = self.Hei / 2 if front_up_y > self.Hei / 2 else front_up_y
        back_down_y = - self.Hei / 2
        back_up_y = self.Hei / 2
        front_down_x = self.FWid / 2
        back_down_x = self.BWid / 2
        front_up_x = front_down_x + self.FSpr / 2  # 扩散也要除以二分之一
        back_up_x = back_down_x + self.BSpr / 2  # 扩散也要除以二分之一
        if self.UCur == 0 and self.DCur == 0:
            # 旋转
            dots = {
                "front_up_left": rotate(front_up_x, front_up_y, front_z, *self.Rot),
                "front_up_right": rotate(-front_up_x, front_up_y, front_z, *self.Rot),
                "front_down_left": rotate(front_down_x, front_down_y, front_z, *self.Rot),
                "front_down_right": rotate(-front_down_x, front_down_y, front_z, *self.Rot),
                "back_up_left": rotate(back_up_x, back_up_y, back_z, *self.Rot),
                "back_up_right": rotate(-back_up_x, back_up_y, back_z, *self.Rot),
                "back_down_left": rotate(back_down_x, back_down_y, back_z, *self.Rot),
                "back_down_right": rotate(-back_down_x, back_down_y, back_z, *self.Rot),
            }
            for key in dots.keys():
                dots[key] *= self.Scl  # 缩放
                dots[key] += self.Pos  # 平移
            # 返回绘制方法和三角形集
            return Using_GL_QUADS, [
                [dots["front_up_left"], dots["front_up_right"], dots["front_down_right"], dots["front_down_left"]],
                [dots["back_up_left"], dots["back_up_right"], dots["back_down_right"], dots["back_down_left"]],
                [dots["front_up_left"], dots["front_up_right"], dots["back_up_right"], dots["back_up_left"]],
                [dots["front_down_left"], dots["front_down_right"], dots["back_down_right"], dots["back_down_left"]],
                [dots["front_up_left"], dots["front_down_left"], dots["back_down_left"], dots["back_up_left"]],
                [dots["front_up_right"], dots["front_down_right"], dots["back_down_right"], dots["back_up_right"]],
            ]
        else:
            # 计算中间坐标
            front_mid_y = (front_up_y + front_down_y) / 2
            if front_mid_y > front_up_y:
                front_mid_y = front_up_y
            elif front_mid_y < front_down_y:
                front_mid_y = front_down_y
            front_mid_x = (front_up_x + front_down_x) / 2

    def __str__(self):
        part_type = self.__class__.__name__
        return str(
            f"\nTyp:  {part_type}\n"
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


class MainWeapon(Part):
    All = []

    def __init__(self, Id, pos, rot, scale, color, armor, manual_control, elevator):
        super().__init__(Id, pos, rot, scale, color, armor)
        self.ManualControl = manual_control
        self.ElevatorH = elevator
        MainWeapon.All.append(self)


class ReadNA:
    def __init__(self, filepath):
        self.filename = filepath.split('\\')[-1]
        self.filepath = filepath
        self.root = ET.parse(filepath).getroot()
        self.ShipName = self.filename[:-3]
        self.Author = self.root.find('ship').attrib['author']
        self.HornType = self.root.find('ship').attrib['hornType']
        self.HornPitch = self.root.find('ship').attrib['hornPitch']
        self.TracerCol = self.root.find('ship').attrib['tracerCol']
        self._all_parts = self.root.findall('ship/part')
        self.Parts = Part.ShipsAllParts
        self.Weapons = MainWeapon.All
        self.AdjustableHulls = AdjustableHull.All
        self.ColorPartsMap = {}
        for part in self.root.findall('ship/part'):
            _id = part.attrib['id']
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
