# -*- coding: utf-8 -*-
"""
定义了NavalArt内物体的绘制对象
"""
import math

import numpy as np

from ship_reader.NA_design_reader import (
    ReadNA, AdjustableHull, NAPart, NAPartNode,
    rotate_quaternion0, rotate_quaternion1, rotate_quaternion2)
from .basic import SolidObject, DotNode, get_normal, TempObj


class NAHull(ReadNA, SolidObject):
    current_in_design_tab = None
    current_in_preview_tab = None

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
            NAPartNode.id_map = {}
            NaHullXZLayer.id_map = {}
            NaHullXYLayer.id_map = {}
            NaHullLeftView.id_map = {}
            NAXZLayerNode.id_map = {}
            NAXYLayerNode.id_map = {}
            NALeftViewNode.id_map = {}
            NAPartNode.all_dots = []
        ReadNA.__init__(self, path, data, self.show_statu_func, glWin,
                        design_tab)  # 注意，DrawMap不会在ReadNA或SolidObject中初始化
        SolidObject.__init__(self, None)
        self.DrawMap = self.ColorPartsMap.copy()
        self.xzLayers = []  # 所有xz截面
        self.xyLayers = []  # 所有xy截面
        self.leftViews = []  # 中间yz截面
        # 更新current静态变量
        if design_tab:
            NAHull.current_in_design_tab = self
        else:
            NAHull.current_in_preview_tab = self

    def get_layers(self):
        # 清空id_map
        NAXZLayerNode.id_map = {}
        NAXYLayerNode.id_map = {}
        NALeftViewNode.id_map = {}
        NaHullXZLayer.id_map = {}
        NaHullXYLayer.id_map = {}
        NaHullLeftView.id_map = {}
        xz = self.get_xz_layers()
        xy = self.get_xy_layers()
        _l = self.get_left_views()
        return xz, xy, _l

    def get_xz_layers(self):
        self.xzLayers.clear()
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
        return self.xzLayers

    def get_xy_layers(self):
        self.xyLayers.clear()
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
        return self.xyLayers

    def get_left_views(self):
        self.leftViews.clear()
        # TODO: 生成左视图
        self.show_statu_func("左视图生成完毕", "process")
        return self.leftViews

    @staticmethod
    def toJson(data):
        # 将ColorPartMap转换为字典形式，以便于json序列化
        result = {}
        for color, part_set in data.items():
            result[color] = [part.to_dict() for part in part_set]
        return result

    def draw_color(self, gl, color, part_set, transparent):
        # else:
        alpha = 1 if not transparent else 0.3
        # 16进制颜色转换为RGBA
        _rate = 255
        color_ = int(color[1:3], 16) / _rate, int(color[3:5], 16) / _rate, int(color[5:7], 16) / _rate, alpha
        gl.glColor4f(*color_)
        for part in part_set:
            if not isinstance(part, AdjustableHull):
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
            if not isinstance(part, AdjustableHull):
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

    # 整体缩放
    def scale(self, ratio):
        for part_set in self.DrawMap.values():
            for part in part_set:
                part.scale(ratio)


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

    def __deepcopy__(self, memo):
        return self

    def get_partsDotsMap(self):
        result = {}
        for part in self.y_parts:
            if not isinstance(part, AdjustableHull):
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

    def __deepcopy__(self, memo):
        return self

    def get_partsDotsMap(self):
        result = {}
        for part in self.z_parts:
            if not isinstance(part, AdjustableHull):
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

    def __deepcopy__(self, memo):
        return self

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


class TempAdjustableHull(TempObj):
    def __init__(
            self, read_na, glWin, Id, pos, rot, scale, color, armor,
            length, height, frontWidth, backWidth, frontSpread, backSpread, upCurve, downCurve,
            heightScale, heightOffset,
            original_hull_data
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
        super().__init__()
        self.glWin = glWin  # 用于绘制的窗口
        self.read_na_obj = read_na
        self.original_hull_data = original_hull_data
        self.Id = Id
        self.Pos = pos
        self.Rot = rot
        self.Scl = scale
        self.Col = color  # "#975740"
        self.Amr = armor
        # ======================================================================= 初始化零件的各个参数
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
        self.glWin.paintGL()
        self.glWin.update()

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
                  self.vertex_coordinates["back_down_right"].copy(), self.vertex_coordinates["front_down_right"].copy()],
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

    def change_attrs_T(self, position=None, armor=None,
                       length=None, height=None, frontWidth=None, backWidth=None, frontSpread=None, backSpread=None,
                       upCurve=None, downCurve=None, heightScale=None, heightOffset=None,
                       update=False):
        # ==============================================================================更新零件的各个属性
        if position is None:
            position = self.Pos
        if armor is None:
            armor = self.Amr
        if length is None:
            length = self.Len
        if height is None:
            height = self.Hei
        if frontWidth is None:
            frontWidth = self.FWid
        if backWidth is None:
            backWidth = self.BWid
        if frontSpread is None:
            frontSpread = self.FSpr
        if backSpread is None:
            backSpread = self.BSpr
        if upCurve is None:
            upCurve = self.UCur
        if downCurve is None:
            downCurve = self.DCur
        if heightScale is None:
            heightScale = self.HScl
        if heightOffset is None:
            heightOffset = self.HOff
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
        self.operation_dot_nodes = []  # 位置变换后，曲面变换前的所有点
        self.plot_all_dots = []  # 曲面变换，位置变换后的所有点
        self.vertex_coordinates = self.get_initial_vertex_coordinates()
        self.plot_lines = self.get_plot_lines()
        self.plot_faces = self.get_plot_faces()
        if update:
            # 重绘
            self.glWin.paintGL()
            self.glWin.update()
        return True

    def export2AdjustableHull(self) -> AdjustableHull:
        obj = AdjustableHull(
            self.read_na_obj, self.Id, self.Pos, self.Rot, self.Scl, self.Col, self.Amr,
            self.Len, self.Hei, self.FWid, self.BWid, self.FSpr, self.BSpr, self.UCur, self.DCur,
            self.HScl, self.HOff,
            _from_temp_data=True, _back_down_y=self.back_down_y, _back_up_y=self.back_up_y,
            _front_down_y=self.front_down_y, _front_up_y=self.front_up_y,
            _operation_dot_nodes=self.operation_dot_nodes, _plot_all_dots=self.plot_all_dots,
            _vertex_coordinates=self.vertex_coordinates, _plot_lines=self.plot_lines, _plot_faces=self.plot_faces
        )
        # 添加颜色
        _color = f"#{obj.Col}"
        if _color not in self.read_na_obj.ColorPartsMap.keys():
            self.ColorPartsMap[_color] = []
        self.read_na_obj.ColorPartsMap[_color].append(obj)
        self.read_na_obj.Parts.append(obj)
        NAPart.hull_design_tab_id_map[id(obj) % 4294967296] = obj
        return obj

    def draw(self, gl, material="被选中", theme_color=None):
        # 材料设置
        gl.glColor4f(*theme_color["被选中"][0][:3], 0.5)
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
