import xml.etree.ElementTree as ET
import numpy as np

"""
文件格式：
<root>
  <ship author="22222222222" description="description" hornType="1" hornPitch="0.9475011" tracerCol="E53D4FFF">
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


def rotate(dot_dict, rot):
    # 对整个零件的坐标进行旋转
    # 旋转矩阵
    rot_matrix = np.array([
        [np.cos(np.deg2rad(rot[2])), -np.sin(np.deg2rad(rot[2])), 0],
        [np.sin(np.deg2rad(rot[2])), np.cos(np.deg2rad(rot[2])), 0],
        [0, 0, 1]
    ]) @ np.array([
        [np.cos(np.deg2rad(rot[1])), 0, np.sin(np.deg2rad(rot[1]))],
        [0, 1, 0],
        [-np.sin(np.deg2rad(rot[1])), 0, np.cos(np.deg2rad(rot[1]))]
    ]) @ np.array([
        [1, 0, 0],
        [0, np.cos(np.deg2rad(rot[0])), -np.sin(np.deg2rad(rot[0]))],
        [0, np.sin(np.deg2rad(rot[0])), np.cos(np.deg2rad(rot[0]))]
    ])
    # 旋转
    for key in dot_dict.keys():
        dot_dict[key] = rot_matrix @ dot_dict[key]
    return dot_dict


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
        half_height_scale = self.Hei * self.HScl / 2  # 高度缩放的一半
        center_height_offset = self.HOff * self.Hei  # 高度偏移
        self.front_down_y = center_height_offset - half_height_scale  # 零件前端下端的y坐标
        self.front_up_y = center_height_offset + half_height_scale  # 零件前端上端的y坐标
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
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
        self.plot_faces = self.get_plot_faces()

    def get_plot_faces(self):
        """
        :return: 绘制零件的方法，绘制零件需的三角形集
        """
        if self.UCur == 0 and self.DCur == 0:
            # 旋转
            dots = rotate(self.vertex_coordinates, self.Rot)
            # 平移
            for key in dots.keys():
                dots[key] *= self.Scl  # 缩放
                dots[key] += self.Pos  # 平移
            result = {
                "GL_QUADS": [],
                "GL_TRIANGLES": []
            }
            faces = [
                [dots["front_up_left"], dots["front_up_right"], dots["front_down_right"], dots["front_down_left"]],
                [dots["back_up_left"], dots["back_down_left"], dots["back_down_right"], dots["back_up_right"]],
                [dots["front_up_left"], dots["back_up_left"], dots["back_up_right"], dots["front_up_right"]],
                [dots["front_down_left"], dots["front_down_right"], dots["back_down_right"], dots["back_down_left"]],
                [dots["front_up_left"], dots["front_down_left"], dots["back_down_left"], dots["back_up_left"]],
                [dots["front_up_right"], dots["back_up_right"], dots["back_down_right"], dots["front_down_right"]],
            ]
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
            # 返回绘制方法和三角形集字典
            return result
        else:
            return {"GL_QUAD_STRIP": []}  # TODO: 有曲率的零件的绘制方法

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
        try:
            self.TracerCol = self.root.find('ship').attrib['tracerCol']
        except KeyError:
            self.TracerCol = None
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
