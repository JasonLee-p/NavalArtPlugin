# -*- coding: utf-8 -*-
"""
部件操作
"""
# 系统库
import copy
from typing import List, Literal
# 包内文件
from .basic import Operation
# 其他本地库
from GUI import QMessageBox
from ship_reader import NAPart, AdjustableHull
from state_history import operationObj_wrapper
from util_funcs import not_implemented


class SinglePartOperation(Operation):
    def __init__(self, event, step, active_textEdit, circle_bt_isChecked: bool, singlePart_e, original_data=None, change_data=None):
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
    def __init__(self, position: Literal["front", "back", "up", "down"],
                 base_parts: List[AdjustableHull]):
        super().__init__()
        self.position = position
        self.base_parts = base_parts

        if len(self.base_parts) == 1:
            _p = self.base_parts[0]
            # 寻找该单零件垂直于添加方向的所有关系零件
            ...
            # 如果原零件不在关系图中，那么就不需要考虑关系图
            if _p not in
        else:
            self.original_parts = base_parts
            self.partRelationMap = self.base_parts[0].allParts_relationMap
        self.added_parts = []


    def execute(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    @staticmethod
    @operationObj_wrapper
    def add_front_layer(original_parts):
        return AddLayerOperation("front", original_parts)

    @staticmethod
    @operationObj_wrapper
    def add_back_layer(original_parts):
        return AddLayerOperation("back", original_parts)

    @staticmethod
    @operationObj_wrapper
    def add_up_layer(original_parts):
        return AddLayerOperation("up", original_parts)

    @staticmethod
    @operationObj_wrapper
    def add_down_layer(original_parts):
        return AddLayerOperation("down", original_parts)