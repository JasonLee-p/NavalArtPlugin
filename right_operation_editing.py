# -*- coding: utf-8 -*-
"""
右侧的操作参数编辑界面
当触发某些操作的时候，这些控件会从隐藏状态变为显示状态
"""
from typing import Literal
from util_funcs import CONST

from GUI import *

Direction2Chinese = {CONST.FRONT: "前", CONST.BACK: "后", CONST.LEFT: "左",
                     CONST.RIGHT: "右", CONST.UP: "上", CONST.DOWN: "下",
                     "": ""}

Direction2LenWidHei = {CONST.FRONT: "长", CONST.BACK: "长", CONST.LEFT: "宽",
                       CONST.RIGHT: "宽", CONST.UP: "高", CONST.DOWN: "高",
                       "": ""}


class OperationEditing(QWidget):
    is_editing = False

    def __init__(self):
        """
        基类
        """
        super().__init__(parent=None)


class AddLayerEditing(OperationEditing):
    def __init__(self):
        """
        向某方向添加层
        """
        super().__init__()
        self.direction = ''
        self.title = MyLabel(f"向{Direction2Chinese[self.direction]}方添加层", FONT_10, side=Qt.AlignCenter)
        # 单选框，用户选择当宽度编辑的时候相应的扩散是否修改，默认为修改。
        self.circle_bt = CircleSelectButton(7, False)
        self.keep_spread_label = MyLabel("保持扩散", FONT_9, side=Qt.AlignCenter)
        self.keep_spread_label.setFixedSize(80, 20)
        # 确定按钮
        self.ensure_button = QPushButton("确定")
        set_buttons([self.ensure_button], sizes=[(110, 30)], font=FONT_8, border=1, border_color=FG_COLOR2)
        self.ensure_button.clicked.connect(self.ensure_button_clicked)
        self.content = {}
        # 分割线
        line = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        # 布局
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(7)
        self.context_widget = QWidget()
        self.context_layout = QGridLayout()
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        self.context_layout.setSpacing(7)
        self.context_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(self.layout)
        self.context_widget.setLayout(self.context_layout)
        self.layout.addWidget(self.title, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.context_widget, alignment=Qt.AlignCenter)
        self.layout.addWidget(line, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.ensure_button, alignment=Qt.AlignCenter)
        # 事件
        self.wheelEvent = self.mouse_wheel
        self.hide()

    def reset_ui(self):
        OperationEditing.is_editing = True
        text_font = FONT_9
        for i, key_ in enumerate(self.content):
            # 添加标签
            label = MyLabel(key_, text_font, side=Qt.AlignTop | Qt.AlignVCenter)
            label.setFixedSize(70, 25)
            self.context_layout.addWidget(label, i, 0)
            # 添加输入框，并设置样式
            for j, lineEdit in enumerate(self.content[key_]["QLineEdit"]):
                lineEdit.setFont(text_font)
                lineEdit.setFixedWidth(60)
                lineEdit.setFixedHeight(25)
                lineEdit.setStyleSheet(f"background-color: {BG_COLOR1};color: {FG_COLOR0};"
                                       f"border: 1px solid {FG_COLOR2};border-radius: 5px;")
                self.context_layout.addWidget(lineEdit, i, j + 1)
                lineEdit.setText(str(self.content[key_]["value"]))  # 填充值
                # 限制值的范围
                if "高度" in key_ or "长度" in key_ or "宽度" in key_:
                    lineEdit.setValidator(QDoubleValidator(0.001, 1000, 3))
                # 解绑鼠标滚轮事件
                lineEdit.wheelEvent = lambda event: None
                # # 绑定值修改信号
                # lineEdit.textChanged.connect(self.update_obj_when_editing)

    def update_direction(self, direction: Literal["front", "back", "left", "right", "top", "bottom"], content: dict):
        self.title.setText(f"向{Direction2Chinese[direction]}方添加层")
        self.direction = direction
        self.content = content
        self.reset_ui()
        self.show()
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
            key = None
            pos = self.context_widget.mapFromGlobal(QCursor.pos())
            for key_ in self.content:
                for lineEdit in self.content[key_]["QLineEdit"]:
                    if lineEdit.geometry().contains(pos):
                        active_textEdit = lineEdit
                        key = key_
                        break
                if active_textEdit:
                    break
        if active_textEdit is None:
            return None
        step = 0.1
        # 获取输入框的值
        if event.angleDelta().y() < 0:
            step = - step
        if step != 0:
            self.update_(step, key, active_textEdit)

    @staticmethod
    def update_(step, key, active_textEdit):
        # 获取输入框的值
        step_type = type(step)
        if active_textEdit.text() == "":
            active_textEdit.setText("0")
            return
        if step_type == int:
            active_textEdit.setText(str(int(active_textEdit.text()) + step))
        elif step_type == float:
            # 限制为正数
            if step < 0 and float(active_textEdit.text()) <= 0 and ("高度" in key or "长度" in key or "宽度" in key):
                active_textEdit.setText("0.0")
            else:
                active_textEdit.setText(str(round(float(active_textEdit.text()) + step, 4)))

    def ensure_button_clicked(self):
        MyMessageBox().information(self, "提示", "该功能尚未完成，敬请期待！")
        OperationEditing.is_editing = False
        self.hide()
