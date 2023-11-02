# -*- coding: utf-8 -*-
"""
部件操作
"""
# 系统库
import copy
from typing import List, Literal, Union

from PyQt5.QtWidgets import QLineEdit
# 包内文件
from .basic import Operation
# 其他本地库
from GUI import QMessageBox
from ship_reader import NAPart, AdjustableHull
from GL_plot import TempAdHull
from util_funcs import CONST, get_part_world_dirs
from right_widgets.right_operation_editing import AddLayerEditing


class SinglePartOperation(Operation):
    def __init__(self, event, step, active_textEdit, circle_bt_isChecked: bool, singlePart_e, original_data=None,
                 change_data=None):
        super().__init__()
        self.name = "单零件编辑"
        self.active_textEdit = active_textEdit
        self.singlePart_e = singlePart_e
        self.original_data = original_data
        self.data = change_data
        if not self.data:
            self.event = event
            self.step = step
            self.step_type = type(self.step)
            self.origin_value = self.step_type(self.active_textEdit.text())
            self.new_value = self.origin_value + self.step
            self.circle_bt_isChecked: bool = circle_bt_isChecked

    def execute(self):
        singlePart_e = self.singlePart_e
        if self.data:
            singlePart_e.selected_obj.change_attrs(*self.data, update=True)
            singlePart_e.selected_obj.update_selectedList = True
            singlePart_e.selected_obj.glWin.paintGL()
            singlePart_e.selected_obj.update_selectedList = False
            return
        # 修改输入框的值
        if self.step_type == int:
            self.active_textEdit.setText(str(self.new_value))
        elif self.step_type == float:
            if (self.active_textEdit in [
                singlePart_e.content["坐标"]["QLineEdit"][0],
                singlePart_e.content["坐标"]["QLineEdit"][1],
                singlePart_e.content["坐标"]["QLineEdit"][2]]
                    and singlePart_e.selected_obj in singlePart_e.selected_obj.allParts_relationMap.basicMap
                    and singlePart_e.selected_obj.allParts_relationMap.basicMap[singlePart_e.selected_obj] != {}
            ):
                # 如果该零件的关系图为空，则不警告，因为没有关系图，所以不会解除关系
                # 如果pos_diff不为零，警告用户，单独更改零件的位置会将本零件在零件关系图中解除所有关系
                reply = QMessageBox.warning(
                    None, "警告",
                    f"""更改单个零件的位置，会解除与其他所有零件的方位关系！\n我们非常不建议您这么做！\n是否继续？""",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Help
                )
                if reply == QMessageBox.No:
                    return
                elif reply == QMessageBox.Help:
                    # TODO: 弹出帮助窗口
                    return
                elif reply == QMessageBox.Yes:
                    # 解除关系
                    relation_map = singlePart_e.selected_obj.allParts_relationMap
                    relation_map.del_part(singlePart_e.selected_obj)
            elif self.active_textEdit in [singlePart_e.content["上弧度"]["QLineEdit"][0],
                                          singlePart_e.content["下弧度"]["QLineEdit"][0]] \
                    and (self.new_value < 0 or self.new_value > 1):
                # 弧度值不在0-1之间，直接不修改
                return
            self.active_textEdit.setText(str(round(self.new_value, 3)))
            if not self.circle_bt_isChecked:  # 扩散随着宽度变换
                if self.active_textEdit == singlePart_e.content["前宽度"]["QLineEdit"][0]:
                    txt = singlePart_e.content["前扩散"]["QLineEdit"][0].text()
                    singlePart_e.content["前扩散"]["QLineEdit"][0].setText(str(round(float(txt) - self.step, 3)))
                elif self.active_textEdit == singlePart_e.content["后宽度"]["QLineEdit"][0]:
                    txt = singlePart_e.content["后扩散"]["QLineEdit"][0].text()
                    singlePart_e.content["后扩散"]["QLineEdit"][0].setText(str(round(float(txt) - self.step, 3)))
        update_success = singlePart_e.update_obj_when_editing()

    def undo(self):
        singlePart_e = self.singlePart_e
        if self.data:
            singlePart_e.selected_obj.change_attrs(*self.original_data, update=True)
            singlePart_e.selected_obj.update_selectedList = True
            singlePart_e.selected_obj.glWin.paintGL()
            singlePart_e.selected_obj.update_selectedList = False
            return
        step_type = type(self.step)
        # 修改输入框的值
        if step_type == int:
            self.active_textEdit.setText(str(self.origin_value))
        elif step_type == float:
            self.active_textEdit.setText(str(round(self.origin_value, 3)))
            if not self.circle_bt_isChecked:  # 扩散随着宽度变换
                if self.active_textEdit == singlePart_e.content["前宽度"]["QLineEdit"][0]:
                    txt = singlePart_e.content["前扩散"]["QLineEdit"][0].text()
                    singlePart_e.content["前扩散"]["QLineEdit"][0].setText(str(round(float(txt) + self.step, 3)))
                elif self.active_textEdit == singlePart_e.content["后宽度"]["QLineEdit"][0]:
                    txt = singlePart_e.content["后扩散"]["QLineEdit"][0].text()
                    singlePart_e.content["后扩散"]["QLineEdit"][0].setText(str(round(float(txt) + self.step, 3)))
        update_success = singlePart_e.update_obj_when_editing()

    def redo(self):
        self.execute()


class DeleteSinglePartOperation(Operation):
    """
    删除单零件操作
    """

    def __init__(self, original_part: AdjustableHull):
        super().__init__()
        self.name = "删除零件"
        self.original_part: AdjustableHull = original_part
        self.allParts_relationMap = original_part.allParts_relationMap
        self.Col = self.original_part.Col
        self.read_na_obj = self.original_part.read_na_obj
        self.glWin = self.original_part.glWin
        self.glWinMode = copy.copy(self.glWin.show_3d_obj_mode)

    def execute(self):
        # 在数据中删除原来的零件
        try:
            self.read_na_obj.DrawMap[f"#{self.Col}"].remove(self.original_part)
        except ValueError:  # TODO:
            pass
        # 更新显示的被选中的零件
        if self.glWin:
            try:
                self.glWin.selected_gl_objects[self.glWinMode].remove(self.original_part)
            except ValueError:
                # 用户选中零件后转换到了其他模式，而右侧的编辑器仍然处在原来的模式
                replaced = False
                while not replaced:
                    for mode in self.glWin.selected_gl_objects.keys():
                        try:
                            self.glWin.selected_gl_objects[mode].remove(self.original_part)
                            self.glWinMode = mode
                            replaced = True
                            break
                        except ValueError:
                            continue
        # 从hull_design_tab_id_map（绘制所需）删除原来的零件
        NAPart.hull_design_tab_id_map.pop(id(self.original_part) % 4294967296)
        # 从关系图中删除原来的零件
        if (self.original_part.Rot[0] % 90 == 0 and self.original_part.Rot[1] % 90 == 0 and
                self.original_part.Rot[2] % 90 == 0):
            self.allParts_relationMap.del_part(self.original_part)
        # 重新渲染
        for _mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[_mode][1] = True
        self.glWin.paintGL()
        for _mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[_mode][1] = False
        self.glWin.update()

    def undo(self):
        # 在数据中恢复原来的零件
        self.read_na_obj.DrawMap[f"#{self.Col}"].append(self.original_part)
        # 更新显示的被选中的零件
        if self.glWin:
            self.glWin.selected_gl_objects[self.glWinMode] = [self.original_part]
        # 向hull_design_tab_id_map（绘制所需）添加原来的零件
        NAPart.hull_design_tab_id_map[id(self.original_part) % 4294967296] = self.original_part
        # 恢复关系图
        if (self.original_part.Rot[0] % 90 == 0 and self.original_part.Rot[1] % 90 == 0 and
                self.original_part.Rot[2] % 90 == 0):
            self.allParts_relationMap.undo_del_part(self.original_part)
        # 重新渲染
        for mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[mode][1] = True
        self.glWin.paintGL()
        for mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[mode][1] = False
        self.glWin.update()

    def redo(self):
        self.execute()


class CutSinglePartOperation(Operation):
    """
    分割零件，用于细分单零件操作
    """

    def __init__(self, original_part, new_parts: List[AdjustableHull]):
        super().__init__()
        self.name = "分割零件"
        self.original_part: AdjustableHull = original_part
        self.allParts_relationMap = original_part.allParts_relationMap
        self.Col = self.original_part.Col
        self.read_na_obj = self.original_part.read_na_obj
        self.glWin = self.original_part.glWin
        self.glWinMode = copy.copy(self.glWin.show_3d_obj_mode)
        self.new_parts: List[AdjustableHull] = new_parts

    def execute(self):
        P1, P2 = self.new_parts[0], self.new_parts[1]
        # 在数据中删除原来的零件
        try:
            self.read_na_obj.DrawMap[f"#{self.Col}"].remove(self.original_part)
        except ValueError:  # TODO:
            pass
        # 往read_na的drawMap中添加零件
        self.read_na_obj.DrawMap[f"#{self.Col}"].append(P1)
        self.read_na_obj.DrawMap[f"#{self.Col}"].append(P2)
        # 更新显示的被选中的零件
        if self.glWin:
            try:
                self.glWin.selected_gl_objects[self.glWinMode].remove(self.original_part)
                self.glWin.selected_gl_objects[self.glWinMode].append(P1)
                self.glWin.selected_gl_objects[self.glWinMode].append(P2)
            except ValueError:
                # 用户选中零件后转换到了其他模式，而右侧的编辑器仍然处在原来的模式
                replaced = False
                while not replaced:
                    for mode in self.glWin.selected_gl_objects.keys():
                        try:
                            self.glWin.selected_gl_objects[mode].remove(self.original_part)
                            self.glWin.selected_gl_objects[mode].append(P1)
                            self.glWin.selected_gl_objects[mode].append(P2)
                            self.glWinMode = mode
                            replaced = True
                            break
                        except ValueError:
                            continue
        # 从hull_design_tab_id_map（绘制所需）删除原来的零件
        NAPart.hull_design_tab_id_map.pop(id(self.original_part) % 4294967296)
        # 向hull_design_tab_id_map（绘制所需）添加新的零件
        NAPart.hull_design_tab_id_map[id(P1) % 4294967296] = P1
        NAPart.hull_design_tab_id_map[id(P2) % 4294967296] = P2
        # 添加到关系图
        if (self.original_part.Rot[0] % 90 == 0 and self.original_part.Rot[1] % 90 == 0 and
                self.original_part.Rot[2] % 90 == 0):
            self.allParts_relationMap.replace([P1, P2], self.original_part)
            # self.allParts_relationMap.replace_2(P1, P2, self.original_part, None)
        # 重新渲染
        for _mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[_mode][1] = True
        self.glWin.paintGL()
        for _mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[_mode][1] = False
        self.glWin.update()

    def undo(self):
        P1, P2 = self.new_parts[0], self.new_parts[1]
        # 在数据中恢复原来的零件
        self.read_na_obj.DrawMap[f"#{self.Col}"].append(self.original_part)
        # 往read_na的drawMap中添加零件
        self.read_na_obj.DrawMap[f"#{self.Col}"].remove(P1)
        self.read_na_obj.DrawMap[f"#{self.Col}"].remove(P2)
        # 更新显示的被选中的零件
        if self.glWin:
            self.glWin.selected_gl_objects[self.glWinMode] = [self.original_part]

        # 向hull_design_tab_id_map（绘制所需）删除新的零件
        NAPart.hull_design_tab_id_map.pop(id(P1) % 4294967296)
        NAPart.hull_design_tab_id_map.pop(id(P2) % 4294967296)
        # 从hull_design_tab_id_map（绘制所需）恢复原来的零件
        NAPart.hull_design_tab_id_map[id(self.original_part) % 4294967296] = self.original_part
        # 恢复关系图
        if (self.original_part.Rot[0] % 90 == 0 and self.original_part.Rot[1] % 90 == 0 and
                self.original_part.Rot[2] % 90 == 0):
            self.allParts_relationMap.undo_replace([P1, P2], self.original_part)
            # self.allParts_relationMap.back_replace_2(P1, P2, self.original_part, None)
        # 重新渲染
        for mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[mode][1] = True
        self.glWin.paintGL()
        for mode in self.glWin.gl_commands.keys():
            self.glWin.gl_commands[mode][1] = False
        self.glWin.update()

    def redo(self):
        self.execute()


class AddLayerOperation(Operation):
    right_frame: Union[AddLayerEditing, None] = None
    VERTICAL_DIR_MAP = {
        "front": ["left", "right", "up", "down"],
        "back": ["left", "right", "up", "down"],
        "up": ["left", "right", "front", "back"],
        "down": ["left", "right", "front", "back"],
        "left": ["front", "back", "up", "down"],
        "right": ["front", "back", "up", "down"],
    }

    def __init__(self, direction: Literal["front", "back", "up", "down", "left", "right"],
                 base_parts: List[AdjustableHull],
                 single: bool = False):
        """

        :param direction: 添加方向（全局坐标系）
        :param base_parts: 被选中的零件
        :param single: 是否是单零件模式
        """
        self.name = "添加层"
        # 初始化右侧编辑器
        # if not AddLayerOperation.right_frame:
        #     AddLayerOperation.right_frame = AddLayerEditing()
        super().__init__()
        self.add_direction = direction  # 全局坐标系
        self.transformed_position_map = get_part_world_dirs(base_parts[0].Rot)  # 获取零件的全局坐标系方向
        self.base_parts = base_parts
        self.partRelationMap = None
        self.original_parts_data = {}  # 零件在世界坐标系中的数据
        if len(self.base_parts) == 1 and not single:
            _p = self.base_parts[0]
            # 如果原零件不在关系图中，那么就不需要考虑关系图
            if _p not in _p.allParts_relationMap.basicMap.keys():
                self._original_parts = base_parts
            else:  # 寻找该单零件垂直于添加方向的所有关系零件:
                self.partRelationMap = self.base_parts[0].allParts_relationMap
                if _p in self.partRelationMap.basicMap and self.partRelationMap.basicMap[_p] != {}:
                    self.find_original_parts(_p)
                else:
                    self._original_parts = base_parts
        elif single:
            self.partRelationMap = self.base_parts[0].allParts_relationMap
            self._original_parts = base_parts
        else:
            self.partRelationMap = self.base_parts[0].allParts_relationMap
            self._original_parts = base_parts
        # 向被选物体中添加零件
        glWin = self.base_parts[0].glWin
        glWin.selected_gl_objects[glWin.show_3d_obj_mode] = self._original_parts.copy()
        self.get_data_in_world_coordinate()
        # 初始化需要添加的零件
        self.generate_added_parts(self.original_parts_data, self.add_direction)
        self.added_parts_dict = {}

    def find_original_parts(self, base_part):
        outer_parts = [self.base_parts[0]]
        self._original_parts = [self.base_parts[0]]

        # 此处不需要转置方向，因为需要寻找全局方向
        for _dir in self.VERTICAL_DIR_MAP[self.add_direction][:2]:
            # 此时_dir是全局左右或前后方向
            _dir_parts = self.partRelationMap.basicMap[base_part][_dir]
            if _dir_parts:
                self._original_parts.extend(_dir_parts)
                outer_parts.extend(_dir_parts)
        for _outer_p in outer_parts:
            # 此处不需要转置方向，因为需要寻找全局方向
            for _dir in self.VERTICAL_DIR_MAP[self.add_direction][2:]:
                # 此时_dir是全局上下或前后方向
                _dir_parts = self.partRelationMap.basicMap[_outer_p][_dir]
                if _dir_parts:
                    self._original_parts.extend(_dir_parts)

    def get_data_in_world_coordinate(self):
        for part in self._original_parts:
            _data = part.get_data_in_coordinate()
            if _data is not None:
                self.original_parts_data[part] = _data

    def generate_added_parts(self, original_parts_data, add_direction):
        """
        生成需要添加的零件
        :param original_parts_data: 源零件的数据
        例如：
        part_data = {
            "FLU": x0, "FRU": x1, "FLD": x2, "FRD": x3,
            "BLU": x4, "BRU": x5, "BLD": x6, "BRD": x7,
            "BH": x8, "FH": x9, "H": x10,
            "L": x11
        }
        :param add_direction: 添加方向（全局坐标系）
        :return: Dict[AdjustableHull, TempAdHull]
        """
        # 打开右侧编辑器
        result = {}
        lineEdits = {}
        if original_parts_data == {}:
            return result
        # 如果只有一个零件
        if len(original_parts_data) == 1:  # 000000000000000000000000000000000000000000 单个零件
            part = list(original_parts_data.keys())[0]
            data = original_parts_data[part]
            _glWin = part.glWin
            if add_direction == CONST.FRONT:
                # 不变信息初始化
                _Hei = data["FH"]
                _BWid = data["FLD"]
                _BSpr = data["FLU"] - data["FLD"]
                # 可变信息初始化
                _Len = data["L"]
                _FWid = max(2 * data["FLD"] - data["BLD"], 0)
                _FSpr = 2 * (data["FLU"] - data["FLD"]) - (data["BLU"] - data["BLD"])
                _Pos = [part.Pos[0], part.Pos[1], part.Pos[2] + _Len * part.Scl[2]]
                _UCur = part.UCur
                _DCur = part.DCur
                if part.Rot == [0, 0, 0]:
                    if part.HOff != 0:
                        _Pos = _Pos[0], _Pos[1] + part.HOff, _Pos[2]
                elif part.Rot == [0, 0, 180]:  # 绕z轴旋转180度
                    if part.HOff != 0:
                        _Pos = _Pos[0], _Pos[1] - part.HOff, _Pos[2]
                    _UCur = part.DCur
                    _DCur = part.UCur
                elif part.Rot == [180, 0, 0]:
                    _UCur = part.DCur
                    _DCur = part.UCur
                result[part] = TempAdHull(
                    part.read_na_obj, _glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                    _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, _UCur, _DCur,
                    1, 0,
                    original_hull_data=data
                )
                # 可编辑的信息初始化
                lineEdits = {
                    "原长度": {"value": _Len, "QLineEdit": [QLineEdit()]},
                    "前宽度": {"value": _FWid, "QLineEdit": [QLineEdit()]},
                    "前扩散": {"value": _FSpr, "QLineEdit": [QLineEdit()]},
                    "上弧度": {"value": _UCur, "QLineEdit": [QLineEdit()]},
                    "下弧度": {"value": _DCur, "QLineEdit": [QLineEdit()]},
                }
            elif add_direction == CONST.BACK:
                # 不变信息初始化
                _Hei = data["BH"]
                _FWid = data["BLD"]
                _FSpr = data["BLU"] - data["BLD"]
                # 可变信息初始化
                _Len = data["L"]
                _BWid = max(2 * data["BLD"] - data["FLD"], 0)
                _BSpr = 2 * (data["BLU"] - data["BLD"]) - (data["FLU"] - data["FLD"])
                _Pos = [part.Pos[0], part.Pos[1], part.Pos[2] - _Len * part.Scl[2]]
                _UCur = part.UCur
                _DCur = part.DCur
                if part.Rot == [0, 0, 180]:
                    _UCur = part.DCur
                    _DCur = part.UCur
                elif part.Rot == [180, 0, 0]:
                    if part.HOff != 0:
                        _Pos = _Pos[0], _Pos[1] - part.HOff, _Pos[2]
                    _UCur = part.DCur
                    _DCur = part.UCur
                elif part.Rot == [0, 180, 0]:
                    if part.HOff != 0:
                        _Pos = _Pos[0], _Pos[1] + part.HOff, _Pos[2]
                result[part] = TempAdHull(
                    part.read_na_obj, _glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                    _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, _UCur, _DCur,
                    1, 0,
                    original_hull_data=data
                )
                # 可编辑的信息初始化
                lineEdits = {
                    "原长度": {"value": _Len, "QLineEdit": [QLineEdit()]},
                    "后宽度": {"value": _BWid, "QLineEdit": [QLineEdit()]},
                    "后扩散": {"value": _BSpr, "QLineEdit": [QLineEdit()]},
                    "上弧度": {"value": _UCur, "QLineEdit": [QLineEdit()]},
                    "下弧度": {"value": _DCur, "QLineEdit": [QLineEdit()]},
                }
            elif add_direction == CONST.UP:
                # 不变信息初始化
                _Len = data["L"]
                _FWid = data["FLU"]
                _BWid = data["BLU"]
                # 可变信息初始化
                _Hei = data["H"]
                _Pos = [part.Pos[0], part.Pos[1] + _Hei * part.Scl[1], part.Pos[2]]
                _FSpr = data["FLU"] - data["FLD"]
                _BSpr = data["BLU"] - data["BLD"]
                result[part] = TempAdHull(
                    part.read_na_obj, _glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                    _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, 0, 0,
                    1, 0,
                    original_hull_data=data
                )
                lineEdits = {
                    "原高度": {"value": _Hei, "QLineEdit": [QLineEdit()]},
                    "前扩散": {"value": _FSpr, "QLineEdit": [QLineEdit()]},
                    "后扩散": {"value": _BSpr, "QLineEdit": [QLineEdit()]},
                }
                # 可编辑的信息初始化
            elif add_direction == CONST.DOWN:
                # 不变信息初始化
                _Len = data["L"]
                _FWid = 2 * data["FLD"] - data["FLU"]
                _BWid = 2 * data["BLD"] - data["BLU"]
                # 可变信息初始化
                _Hei = data["H"]
                _Pos = [part.Pos[0], part.Pos[1] - _Hei * part.Scl[1], part.Pos[2]]
                _FSpr = data["FLU"] - data["FLD"]
                _BSpr = data["BLU"] - data["BLD"]
                result[part] = TempAdHull(
                    part.read_na_obj, _glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                    _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, 0, 0,
                    1, 0,
                    original_hull_data=data
                )
                # 可编辑的信息初始化
                lineEdits = {
                    "原高度": {"value": _Hei, "QLineEdit": [QLineEdit()]},
                    "前宽度": {"value": _FWid, "QLineEdit": [QLineEdit()]},
                    "后宽度": {"value": _BWid, "QLineEdit": [QLineEdit()]},
                }
            elif add_direction == CONST.LEFT:
                return result
            elif add_direction == CONST.RIGHT:
                return result
        else:  # 0000000000000000000000000000000000000000000000000000000000000000000 多个零件
            np_datas = {}
            _first_p = list(original_parts_data.keys())[0]
            if add_direction == CONST.FRONT:
                # 可编辑的信息初始化
                lineEdits = {
                    "步进长度": {"value": original_parts_data[_first_p]["L"], "QLineEdit": [QLineEdit()]},
                    "宽度扩散": {"value": 0, "QLineEdit": [QLineEdit()]},
                }
                _z = _first_p.Pos[2] + _first_p.Scl[2] * original_parts_data[_first_p]["L"]
                for part, data in original_parts_data.items():
                    # 不变信息初始化
                    _Hei = data["FH"]
                    _BWid = data["FLD"]
                    _BSpr = data["FLU"] - data["FLD"]
                    # 可变信息初始化
                    _Len = data["L"]
                    _FWid = data["FLD"]
                    _FSpr = data["FLU"] - data["FLD"]
                    _Pos = [part.Pos[0], part.Pos[1], _z]
                    _UCur = part.UCur
                    _DCur = part.DCur
                    if part.Rot == [0, 0, 0]:
                        if part.HOff != 0:
                            _Pos = _Pos[0], _Pos[1] + part.HOff, _Pos[2]
                    elif part.Rot == [0, 0, 180]:  # 绕z轴旋转180度
                        if part.HOff != 0:
                            _Pos = _Pos[0], _Pos[1] - part.HOff, _Pos[2]
                        _UCur = part.DCur
                        _DCur = part.UCur
                    elif part.Rot == [180, 0, 0]:
                        _UCur = part.DCur
                        _DCur = part.UCur
                    result[part] = TempAdHull(
                        part.read_na_obj, part.glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                        _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, part.UCur, part.DCur,
                        1, 0,
                        original_hull_data=data
                    )
            elif add_direction == CONST.BACK:
                # 可编辑的信息初始化
                lineEdits = {
                    "步进长度": {"value": original_parts_data[_first_p]["L"], "QLineEdit": [QLineEdit()]},
                    "宽度收缩": {"value": 0, "QLineEdit": [QLineEdit()]},
                }
                for part, data in original_parts_data.items():

                    # 不变信息初始化
                    _Hei = data["BH"]
                    _FWid = data["BLD"]
                    _FSpr = data["BLU"] - data["BLD"]
                    # 可变信息初始化
                    _Len = data["L"]
                    _BWid = data["BLD"]
                    _BSpr = data["BLU"] - data["BLD"]
                    _Pos = [part.Pos[0], part.Pos[1], part.Pos[2] - _Len * part.Scl[2]]
                    _UCur = part.UCur
                    _DCur = part.DCur
                    if part.Rot == [0, 0, 180]:
                        _UCur = part.DCur
                        _DCur = part.UCur
                    elif part.Rot == [180, 0, 0]:
                        if part.HOff != 0:
                            _Pos = _Pos[0], _Pos[1] - part.HOff, _Pos[2]
                        _UCur = part.DCur
                        _DCur = part.UCur
                    elif part.Rot == [0, 180, 0]:
                        if part.HOff != 0:
                            _Pos = _Pos[0], _Pos[1] + part.HOff, _Pos[2]
                    result[part] = TempAdHull(
                        part.read_na_obj, part.glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                        _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, part.UCur, part.DCur,
                        1, 0,
                        original_hull_data=data
                    )
            elif add_direction == CONST.UP:
                # 可编辑的信息初始化
                lineEdits = {
                    "步进高度": {"value": original_parts_data[_first_p]["H"], "QLineEdit": [QLineEdit()]},
                    "步进扩散": {"value": 0, "QLineEdit": [QLineEdit()]},
                }
                for part, data in original_parts_data.items():
                    # 不变信息初始化
                    _Len = data["L"]
                    _FWid = data["FLU"]
                    _BWid = data["BLU"]
                    # 可变信息初始化
                    _Hei = data["H"]
                    _Pos = [part.Pos[0], part.Pos[1] + _Hei * part.Scl[1], part.Pos[2]]
                    _FSpr = 0
                    _BSpr = 0
                    result[part] = TempAdHull(
                        part.read_na_obj, part.glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                        _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, 0, 0,
                        1, 0,
                        original_hull_data=data
                    )
            elif add_direction == CONST.DOWN:
                # 可编辑的信息初始化
                lineEdits = {
                    "步进高度": {"value": original_parts_data[_first_p]["H"], "QLineEdit": [QLineEdit()]},
                    "步进收缩": {"value": 0, "QLineEdit": [QLineEdit()]},
                }
                for part, data in original_parts_data.items():
                    # 不变信息初始化
                    _Len = data["L"]
                    _FWid = data["FLD"]
                    _BWid = data["BLD"]
                    # 可变信息初始化
                    _Hei = data["H"]
                    _Pos = [part.Pos[0], part.Pos[1] - _Hei * part.Scl[1], part.Pos[2]]
                    _FSpr = 0
                    _BSpr = 0
                    result[part] = TempAdHull(
                        part.read_na_obj, part.glWin, part.Id, _Pos, [0, 0, 0], part.Scl, part.Col, part.Amr,
                        _Len, _Hei, _FWid, _BWid, _FSpr, _BSpr, 0, 0,
                        1, 0,
                        original_hull_data=data
                    )
            elif add_direction == CONST.LEFT:
                return result
            elif add_direction == CONST.RIGHT:
                return result
        # 更新右侧编辑器的栏目
        AddLayerOperation.right_frame.update_direction(self, add_direction, result, lineEdits)
        return result

    def execute(self):
        TempAdHull.all_objs.clear()
        glWin = self.base_parts[0].glWin
        glWin.selected_gl_objects[glWin.show_3d_obj_mode] = [add_p for add_p in self.added_parts_dict.values()]

    def undo(self):
        glWin = self.base_parts[0].glWin
        # 从DrawMap和hull_design_tab_id_map中删除添加的零件
        for add_p in self.added_parts_dict.values():
            self.base_parts[0].read_na_obj.DrawMap[f"#{add_p.Col}"].remove(add_p)
            NAPart.hull_design_tab_id_map.pop(id(add_p) % 4294967296)
        # 刷新显示
        glWin.selected_gl_objects[glWin.show_3d_obj_mode] = self.base_parts
        glWin.paintGL()
        glWin.update()

    def redo(self):
        self.execute()
