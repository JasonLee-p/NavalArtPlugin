import xml.etree.ElementTree as ET

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
