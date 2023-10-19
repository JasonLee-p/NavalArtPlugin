# -*- coding: utf-8 -*-
"""
右侧的操作参数编辑界面
当触发某些操作的时候，这些控件会从隐藏状态变为显示状态
"""
from typing import Literal
from util_funcs import CONST

from GUI import *

Direction2Chinese = {CONST.FRONT: "前", CONST.BACK: "后", CONST.LEFT: "左",
                     CONST.RIGHT: "右", CONST.UP: "上", CONST.DOWN: "下"}

Direction2LenWidHei = {CONST.FRONT: "长", CONST.BACK: "长", CONST.LEFT: "宽",
                       CONST.RIGHT: "宽", CONST.UP: "高", CONST.DOWN: "高"}


class AddLayerEditing(QWidget):
    def __init__(self):
        """
        向某方向添加层
        """
        super().__init__()
        self.direction = ''
        self.title = MyLabel(f"向{Direction2Chinese[self.direction]}方添加层", FONT_10, side=Qt.AlignCenter)
        self.content = {
            f"新增{Direction2LenWidHei[self.direction]}度": {"value": 0, "QLineEdit": [QLineEdit()]},
            f"宽度增量": {"value": 0, "QLineEdit": [QLineEdit()]},
        }
        self.wheel_change_value_map = {
            self.content[f"新增{Direction2LenWidHei[self.direction]}度"]["QLineEdit"][0]: float(0.1),
            self.content[f"宽度增量"]["QLineEdit"][0]: float(0.1),
        }
        self.layout = QGridLayout()
        self.init_ui()
        self.hide()

    def init_ui(self):
        self.setLayout(self.layout)
        self.layout.setContentsMargins(15, 10, 15, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.title, 0, 0, 1, 2)
        text_font = FONT_9
        for i, key_ in enumerate(self.content):
            # 添加标签
            label = MyLabel(key_, text_font, side=Qt.AlignTop | Qt.AlignVCenter)
            label.setFixedSize(70, 25)
            self.layout.addWidget(label, i + 1, 0)
            # 添加输入框，并设置样式
            for j, lineEdit in enumerate(self.content[key_]["QLineEdit"]):
                lineEdit.setFont(text_font)
                lineEdit.setFixedWidth(60)
                lineEdit.setFixedHeight(25)
                lineEdit.setStyleSheet(f"background-color: {BG_COLOR1};color: {FG_COLOR0};"
                                       f"border: 1px solid {FG_COLOR2};border-radius: 5px;")
                self.layout.addWidget(lineEdit, i + 1, j + 1)
                # 只允许输入和显示数字，小数点，负号
                # TODO: 未完成
                # 解绑鼠标滚轮事件
                lineEdit.wheelEvent = lambda event: None
                # # 绑定值修改信号
                # lineEdit.textChanged.connect(self.update_obj_when_editing)

    def update_direction(self, direction: Literal["front", "back", "left", "right", "top", "bottom"]):
        self.title.setText(f"向{Direction2Chinese[direction]}方添加层")
        self.content[f"新增{Direction2LenWidHei[direction]}度"] = self.content.pop(f"新增{Direction2LenWidHei[self.direction]}度")
        self.wheel_change_value_map[
            self.content[f"新增{Direction2LenWidHei[direction]}度"]["QLineEdit"][0]
        ] = self.wheel_change_value_map.pop(
            self.content[f"新增{Direction2LenWidHei[self.direction]}度"]["QLineEdit"][0]
        )
        self.direction = direction
        self.update()

    def mouse_wheel(self, event):
        """
        鼠标滚轮事件
        :param event:
        :return:
        """
        if type(event) == list:  # [QTextEdit, QWheelEvent]
            # 是自己的程序在其他地方的调用，第一项就是需要修改的输入框
            active_textEdit = event[0]
            event = event[1]
        else:
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
            return None
        step = self.wheel_change_value_map[active_textEdit]
        # 获取输入框的值
        if event.angleDelta().y() < 0:
            step = - step
        if step != 0:
            self.update_(step, active_textEdit)

    @staticmethod
    def update_(step, active_textEdit):
        # 获取输入框的值
        step_type = type(step)
        if step_type == int:
            active_textEdit.setText(str(int(active_textEdit.text()) + step))
        elif step_type == float:
            active_textEdit.setText(str(float(active_textEdit.text()) + step))
