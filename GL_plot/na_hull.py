"""
定义了NavalArt内物体的绘制对象
"""

import math
import numpy as np
from ship_reader.NA_design_reader import ReadNA, AdjustableHull
from .basic import SolidObject, get_normal


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
    id_map = {}

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
        NaHullXZLayer.id_map[id(self) % 4294967296] = self

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
    id_map = {}

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
        NaHullXYLayer.id_map[id(self) % 4294967296] = self

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