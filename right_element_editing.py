# -*- coding: utf-8 -*-
"""
右侧元素编辑
"""
from typing import Union

from PyQt5.QtGui import QDoubleValidator

from GUI import *
from ship_reader import NAPart, AdjustableHull


class Mod1SinglePartEditing(QWidget):
    def __init__(self):
        """
        全视图模式，单零件元素检视器
        """
        super().__init__()
        self.selected_obj = Union[NAPart, AdjustableHull, None]
        self.allow_update_obj_when_editing = True
        self.content = {
            "类型": MyLabel("未选择物体", FONT_10, side=Qt.AlignCenter),
            "坐标": {"value": [0, 0, 0], "QLineEdit": [QLineEdit(), QLineEdit(), QLineEdit()]},
            "装甲": {"value": [0], "QLineEdit": [QLineEdit()]},
            # 可调节零件模型信息
            "原长度": {"value": [0], "QLineEdit": [QLineEdit()]},
            "原高度": {"value": [0], "QLineEdit": [QLineEdit()]},
            "前宽度": {"value": [0], "QLineEdit": [QLineEdit()]},
            "后宽度": {"value": [0], "QLineEdit": [QLineEdit()]},
            "前扩散": {"value": [0], "QLineEdit": [QLineEdit()]},
            "后扩散": {"value": [0], "QLineEdit": [QLineEdit()]},
            "上弧度": {"value": [0], "QLineEdit": [QLineEdit()]},
            "下弧度": {"value": [0], "QLineEdit": [QLineEdit()]},
            "高缩放": {"value": [0], "QLineEdit": [QLineEdit()]},
            "高偏移": {"value": [0], "QLineEdit": [QLineEdit()]}
        }
        self.wheel_change_value_map = {
            self.content["坐标"]["QLineEdit"][0]: float(0.1), self.content["坐标"]["QLineEdit"][1]: float(0.1), self.content["坐标"]["QLineEdit"][2]: float(0.1),
            self.content["装甲"]["QLineEdit"][0]: int(1),
            self.content["原长度"]["QLineEdit"][0]: float(0.1), self.content["原高度"]["QLineEdit"][0]: float(0.1),
            self.content["前宽度"]["QLineEdit"][0]: float(0.1), self.content["后宽度"]["QLineEdit"][0]: float(0.1),
            self.content["前扩散"]["QLineEdit"][0]: float(0.1), self.content["后扩散"]["QLineEdit"][0]: float(0.1),
            self.content["上弧度"]["QLineEdit"][0]: float(0.1), self.content["下弧度"]["QLineEdit"][0]: float(0.1),
            self.content["高缩放"]["QLineEdit"][0]: float(0.1), self.content["高偏移"]["QLineEdit"][0]: float(0.1)
        }
        # grid
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.init_layout()
        # 绑定滚轮事件
        self.wheelEvent = self.mouse_wheel

    def init_layout(self):
        self.layout.setSpacing(7)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # 按照tab1_content0的内容，添加控件
        # 只添加类型的结果，并且放大一个字号占据所有列
        self.layout.addWidget(self.content["类型"], 0, 0, 1, 4)
        # 添加其他的控件
        text_font = FONT_9
        for i, key_ in enumerate(self.content):
            if key_ != "类型":
                # 添加标签
                label = MyLabel(key_, text_font, side=Qt.AlignTop | Qt.AlignVCenter)
                label.setFixedSize(70, 25)
                self.layout.addWidget(label, i, 0)
                # 添加输入框，并设置样式
                for j, lineEdit in enumerate(self.content[key_]["QLineEdit"]):
                    lineEdit.setFont(text_font)
                    lineEdit.setFixedWidth(60)
                    lineEdit.setFixedHeight(25)
                    lineEdit.setStyleSheet(f"background-color: {BG_COLOR1};color: {FG_COLOR0};"
                                           f"border: 1px solid {FG_COLOR2};border-radius: 5px;")
                    self.layout.addWidget(lineEdit, i, j + 1)
                    # 如果为旋转，则不可编辑
                    if key_ == "旋转":
                        lineEdit.setReadOnly(True)
                        continue
                    # 只允许输入和显示数字，小数点，负号
                    # TODO: 未完成
                    # 解绑鼠标滚轮事件
                    lineEdit.wheelEvent = lambda event: None
                    # 绑定值修改信号
                    lineEdit.textChanged.connect(self.update_obj_when_editing)
                    # # 添加撤回快捷键
                    # undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), lineEdit)
                    # undo_shortcut.activated.connect(lineEdit.undo)
                    # # 添加重做快捷键
                    # redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), lineEdit)
                    # redo_shortcut.activated.connect(lineEdit.redo)

    def mouse_wheel(self, event):
        # 通过鼠标位置检测当前输入框
        active_textEdit = None
        pos = self.mapFromGlobal(QCursor.pos())
        for key in self.content:
            if key not in ["类型", "旋转"]:
                for textEdit in self.content[key]["QLineEdit"]:
                    if textEdit.geometry().contains(pos):
                        active_textEdit = textEdit
                        break
        if active_textEdit is None:
            return
        step = self.wheel_change_value_map[active_textEdit]
        step_type = type(step)
        # 获取输入框的值
        value = step_type(active_textEdit.text())
        if event.angleDelta().y() < 0:
            step = - step  # 滚轮向下滚动，值减小
        value += step
        # 修改输入框的值
        if step_type == int:
            active_textEdit.setText(str(value))
        elif step_type == float:
            if active_textEdit in [self.content["坐标"]["QLineEdit"][0], self.content["坐标"]["QLineEdit"][1],
                                   self.content["坐标"]["QLineEdit"][2]] and \
                    self.selected_obj.allParts_relationMap.basicMap[self.selected_obj]:
                # 如果该零件的关系图为空，则不警告，因为没有关系图，所以不会解除关系
                # 如果pos_diff不为零，警告用户，单独更改零件的位置会将本零件在零件关系图中解除所有关系
                reply = QMessageBox.warning(None, "警告", "更改单个零件的位置，会解除与其他所有零件的方位关系！\n"
                                                        "我们非常不建议您这么做！\n"
                                                        "是否继续？",
                                            QMessageBox.Yes | QMessageBox.No | QMessageBox.Help)
                if reply == QMessageBox.No:
                    return
                elif reply == QMessageBox.Help:
                    # TODO: 弹出帮助窗口
                    return
                elif reply == QMessageBox.Yes:
                    # 解除关系
                    relation_map = self.selected_obj.allParts_relationMap
                    relation_map.del_part(self.selected_obj)
            elif active_textEdit in [self.content["上弧度"]["QLineEdit"][0], self.content["下弧度"]["QLineEdit"][0]] \
                    and (value < 0 or value > 1):
                # 弧度值不在0-1之间，直接不修改
                return
            active_textEdit.setText(str(round(value, 3)))
            if active_textEdit == self.content["前宽度"]["QLineEdit"][0]:
                txt = self.content["前扩散"]["QLineEdit"][0].text()
                self.content["前扩散"]["QLineEdit"][0].setText(str(round(float(txt) - step, 3)))
            elif active_textEdit == self.content["后宽度"]["QLineEdit"][0]:
                txt = self.content["后扩散"]["QLineEdit"][0].text()
                self.content["后扩散"]["QLineEdit"][0].setText(str(round(float(txt) - step, 3)))
        update_success = self.update_obj_when_editing()

    def update_obj_when_editing(self):
        if not self.allow_update_obj_when_editing:
            return False
        # 当值被修改，更新被绘制对象的值
        changed = self.selected_obj.change_attrs(
            [self.content["坐标"]["QLineEdit"][0].text(), self.content["坐标"]["QLineEdit"][1].text(), self.content["坐标"]["QLineEdit"][2].text()],
            self.content["装甲"]["QLineEdit"][0].text(),
            self.content["原长度"]["QLineEdit"][0].text(),
            self.content["原高度"]["QLineEdit"][0].text(),
            self.content["前宽度"]["QLineEdit"][0].text(),
            self.content["后宽度"]["QLineEdit"][0].text(),
            self.content["前扩散"]["QLineEdit"][0].text(),
            self.content["后扩散"]["QLineEdit"][0].text(),
            self.content["上弧度"]["QLineEdit"][0].text(),
            self.content["下弧度"]["QLineEdit"][0].text(),
            self.content["高缩放"]["QLineEdit"][0].text(),
            self.content["高偏移"]["QLineEdit"][0].text(),
            update=True
        )
        return changed  # bool

    def update_context(self, selected_obj):
        self.selected_obj = selected_obj
        self.allow_update_obj_when_editing = False
        # 更新内容
        obj_type_text = "可调节船体" if selected_obj.Id == "0" else "其他零件"
        self.content["类型"].setText(obj_type_text)
        for i in range(3):
            self.content["坐标"]["QLineEdit"][i].setText(str(round(selected_obj.Pos[i], 3)))
        self.content["装甲"]["QLineEdit"][0].setText(str(round(selected_obj.Amr, 3)))
        if obj_type_text == "可调节船体":
            # 更新可调节零件模型信息
            self.content["原长度"]["QLineEdit"][0].setText(str(round(selected_obj.Len, 3)))
            self.content["原高度"]["QLineEdit"][0].setText(str(round(selected_obj.Hei, 3)))
            self.content["前宽度"]["QLineEdit"][0].setText(str(round(selected_obj.FWid, 3)))
            self.content["后宽度"]["QLineEdit"][0].setText(str(round(selected_obj.BWid, 3)))
            self.content["前扩散"]["QLineEdit"][0].setText(str(round(selected_obj.FSpr, 3)))
            self.content["后扩散"]["QLineEdit"][0].setText(str(round(selected_obj.BSpr, 3)))
            self.content["上弧度"]["QLineEdit"][0].setText(str(round(selected_obj.UCur, 3)))
            self.content["下弧度"]["QLineEdit"][0].setText(str(round(selected_obj.DCur, 3)))
            self.content["高缩放"]["QLineEdit"][0].setText(str(round(selected_obj.HScl, 3)))
            self.content["高偏移"]["QLineEdit"][0].setText(str(round(selected_obj.HOff, 3)))
        self.allow_update_obj_when_editing = True


class Mod2SingleLayerEditing(QWidget):
    def __init__(self):
        """
        水平截面视图模式，单层元素编辑窗
        """
        super().__init__()
