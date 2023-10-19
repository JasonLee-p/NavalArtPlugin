# -*- coding: utf-8 -*-
"""
部件操作
"""
# 系统库
import copy
from typing import List, Literal, Union
# 包内文件
from .basic import Operation
# 其他本地库
from GUI import QMessageBox
from ship_reader import NAPart, AdjustableHull
from state_history import push_operation
from util_funcs import CONST, not_implemented, get_part_world_dirs
from right_operation_editing import AddLayerEditing


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
            if self.active_textEdit in [singlePart_e.content["坐标"]["QLineEdit"][0],
                                        singlePart_e.content["坐标"]["QLineEdit"][1],
                                        singlePart_e.content["坐标"]["QLineEdit"][2]] and \
                    singlePart_e.selected_obj.allParts_relationMap.basicMap[singlePart_e.selected_obj]:
                # 如果该零件的关系图为空，则不警告，因为没有关系图，所以不会解除关系
                # 如果pos_diff不为零，警告用户，单独更改零件的位置会将本零件在零件关系图中解除所有关系
                reply = QMessageBox.warning(None, "警告", str("更改单个零件的位置，会解除与其他所有零件的方位关系！\n"
                                                              "我们非常不建议您这么做！\n"
                                                              "是否继续？"),
                                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Help)
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
        self.read_na_obj.DrawMap[f"#{self.Col}"].remove(self.original_part)
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
        if self.original_part.Rot[0] % 90 == 0 and self.original_part.Rot[1] % 90 == 0 and self.original_part.Rot[
            2] % 90 == 0:
            self.allParts_relationMap.replace_2(P1, P2, self.original_part, None)
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
        if self.original_part.Rot[0] % 90 == 0 and self.original_part.Rot[1] % 90 == 0 and self.original_part.Rot[
            2] % 90 == 0:
            self.allParts_relationMap.back_replace_2(P1, P2, self.original_part, None)
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
                 base_parts: List[AdjustableHull]):
        """

        :param direction: 添加方向（全局坐标系）
        :param base_parts: 被选中的零件
        """
        # 初始化右侧编辑器
        if not AddLayerOperation.right_frame:
            AddLayerOperation.right_frame = AddLayerEditing()
        super().__init__()
        self.add_direction = direction  # 全局坐标系
        self.transformed_position_map = get_part_world_dirs(base_parts[0].Rot)  # 获取零件的全局坐标系方向
        self.base_parts = base_parts
        self.partRelationMap = None
        self.original_parts_data = {}  # 零件在世界坐标系中的数据
        if len(self.base_parts) == 1:
            _p = self.base_parts[0]
            # 如果原零件不在关系图中，那么就不需要考虑关系图
            if _p not in _p.allParts_relationMap.basicMap.keys():
                self._original_parts = base_parts
            else:  # 寻找该单零件垂直于添加方向的所有关系零件:
                self.partRelationMap = self.base_parts[0].allParts_relationMap
                self.find_original_parts(_p)
        else:
            self.partRelationMap = self.base_parts[0].allParts_relationMap
            self._original_parts = base_parts
        self.get_data_in_world_coordinate()
        # 初始化需要添加的零件
        self.added_parts = self.generate_added_parts(self.original_parts_data, self.add_direction)

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
            self.original_parts_data[part] = _data

    @staticmethod
    def generate_added_parts(original_parts_data, add_direction):
        """
        生成需要添加的零件
        :param original_parts_data: 源零件的数据
        :param add_direction: 添加方向（全局坐标系）
        :return:
        """
        # 打开右侧编辑器
        result: List[AdjustableHull] = []
        for part, data in original_parts_data.items():
            ...
        return result

    def execute(self):
        pass

    def undo(self):
        pass

    def redo(self):
        self.execute()

    @staticmethod
    @not_implemented
    @push_operation
    def add_layer(original_parts, direction):
        """
        将操作推入操作栈
        :param original_parts:
        :param direction:
        :return:
        """
        AddLayerOperation.right_frame.update_direction(direction)
        AddLayerOperation.right_frame.show()
        return AddLayerOperation(direction, original_parts)
