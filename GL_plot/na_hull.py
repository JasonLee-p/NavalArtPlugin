"""
定义了NavalArt内物体的绘制对象
"""

import math
from typing import Union

import numpy as np
from PyQt5.QtCore import QThread

from ship_reader.NA_design_reader import ReadNA, AdjustableHull, NAPart, MainWeapon, PartRelationMap
from .basic import SolidObject, DotNode, get_normal


class NAHull(ReadNA, SolidObject):
    def __init__(self, path=False, data=None, show_statu_func=None, glWin=None, design_tab=False):
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
        if design_tab:
            NAPart.hull_design_tab_id_map = {}
        ReadNA.__init__(self, path, data, self.show_statu_func, glWin, design_tab)  # 注意，DrawMap不会在ReadNA或SolidObject中初始化
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
            if i % 123 == 0:
                self.show_statu_func(f"正在生成xz截面第{i}/{total_y_num}层", "process")
            if len(parts) < 4:
                continue
            self.xzLayers.append(NaHullXZLayer(self, y, parts))
        self.show_statu_func("xz截面生成完毕", "process")

    def get_xy_layers(self):
        total_z_num = len(self.partRelationMap.xyDotsLayerMap)
        i = 0
        for z, parts in self.partRelationMap.xyDotsLayerMap.items():
            i += 1
            if i % 123 == 0:
                self.show_statu_func(f"正在生成xy截面第{i}/{total_z_num}层", "process")
            if len(parts) < 3:
                continue
            self.xyLayers.append(NaHullXYLayer(self, z, parts))
        self.show_statu_func("xy截面生成完毕", "process")

    def get_left_views(self):
        # TODO: 生成左视图
        self.show_statu_func("左视图生成完毕", "process")

    @staticmethod
    def toJson(data):
        # 将ColorPartMap转换为字典形式，以便于json序列化
        result = {}
        for color, part_set in data.items():
            result[color] = []
            for part in part_set:
                result[color].append(part.to_dict())
        return result

    def draw_color(self, gl, color, part_set, transparent):
        # else:
        alpha = 1 if not transparent else 0.3
        # 16进制颜色转换为RGBA
        _rate = 255
        color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, alpha
        gl.glColor4f(*color_)
        for part in part_set:
            if type(part) != AdjustableHull:
                continue
            if not part.updateList and part.genList:
                gl.glCallList(part.genList)
                continue
            elif not part.update_transparentList and part.transparent_genList:
                gl.glCallList(part.transparent_genList)
                continue
            if transparent:
                part.transparent_genList = gl.glGenLists(1)
                gl.glNewList(part.transparent_genList, gl.GL_COMPILE_AND_EXECUTE)
            else:
                part.genList = gl.glGenLists(1)
                gl.glNewList(part.genList, gl.GL_COMPILE_AND_EXECUTE)
            gl.glLoadName(id(part) % 4294967296)
            part.glWin = self.glWin
            if type(part) != AdjustableHull:
                continue
            for draw_method, faces_dots in part.plot_faces.items():
                # draw_method是字符串，需要转换为OpenGL的常量
                for face in faces_dots:
                    gl.glDrawArrays(eval(f"gl.{draw_method}"), 0, len(face))
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

    def draw(self, gl, material="钢铁", theme_color=None, transparent=False):
        gl.glLoadName(id(self) % 4294967296)
        # total_part_num = sum([len(part_set) for part_set in self.DrawMap.values()])
        # if total_part_num > 100:  # 大于1000个零件时，多线程绘制（用QThread）
        #     # 根据颜色分线程，所有线程结束后主线程再继续
        #     threads = []
        #     for color, part_set in self.DrawMap.items():
        #         t = DrawThread(gl, self.glWin, theme_color, material, color, part_set, transparent)
        #         threads.append(t)
        #         t.start()
        #     for t in threads:
        #         t.wait()
        # else:
        # 绘制面
        for color, part_set in self.DrawMap.items():
            # t = Thread(target=self.draw_color, args=(gl, theme_color, material, color, part_set))
            # t.start()
            self.draw_color(gl, color, part_set, transparent)


class DrawThread(QThread):
    def __init__(self, gl, glWin, theme_color, material, color, part_set, transparent):
        super().__init__()
        self.gl = gl
        self.glWin = glWin
        self.theme_color = theme_color
        self.material = material
        self.color = color
        self.part_set = part_set
        self.transparent = transparent

    def run(self):
        self.draw_color(self.gl, self.theme_color, self.material, self.color, self.part_set, self.transparent)

    def draw_color(self, gl, theme_color, material, color, part_set, transparent):
        alpha = 1 if not transparent else 0.3
        # 16进制颜色转换为RGBA
        # if theme_color[material][1] == (0.35, 0.35, 0.35, 1.0):  # 说明是白天模式
        _rate = 600
        color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, alpha
        # else:  # 说明是黑夜模式
        #     _rate = 600
        #     color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, alpha
        #     # 减去一定的值
        #     difference = 0.08
        #     color_ = (color_[0] - difference, color_[1] - difference, color_[2] - difference, alpha)
        #     # 如果小于0，就等于0
        #     color_ = (color_[0] if color_[0] > 0 else 0,
        #               color_[1] if color_[1] > 0 else 0,
        #               color_[2] if color_[2] > 0 else 0,
        #               1)
        # light_color_ = color_[0] * 0.9 + 0.3, color_[1] * 0.9 + 0.3, color_[2] * 0.9 + 0.3, alpha
        gl.glColor4f(*color_)
        for part in part_set:
            gl.glLoadName(id(part) % 4294967296)
            part.glWin = self.glWin
            if "plot_faces" not in part.__dict__ and type(part) != AdjustableHull:
                continue
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
        gl.glColor4f(*theme_color[material][0])
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
        gl.glColor4f(*theme_color[material][0])
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


class NaHullLeftView:
    id_map = {}

    def __init__(self):
        NaHullLeftView.id_map[id(self) % 4294967296] = self

    def draw(self):
        ...


class NAXZLayerNode(DotNode):
    id_map = {}

    def __init__(self):
        super().__init__()
        NAXZLayerNode.id_map[id(self) % 4294967296] = self

    def draw(self):
        ...


class NAXYLayerNode(DotNode):
    id_map = {}

    def __init__(self):
        super().__init__()
        NAXYLayerNode.id_map[id(self) % 4294967296] = self

    def draw(self):
        ...


class NALeftViewNode(DotNode):
    id_map = {}

    def __init__(self):
        super().__init__()
        NALeftViewNode.id_map[id(self) % 4294967296] = self

    def draw(self):
        ...