# -*- coding: utf-8 -*-
"""
右侧元素检视器的内容
"""
from GUI import *


class Mod1AllPartsView(QWidget):
    def __init__(self):
        """
        全视图模式，所有零件元素检视器
        """
        super().__init__()
        self.title = MyLabel("所有可调节船体", FONT_10, side=Qt.AlignTop | Qt.AlignVCenter)
        self.layout = QGridLayout()
        self.init_layout()

    def init_layout(self):
        self.layout.setSpacing(7)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title.setFixedSize(70, 25)
        self.layout.addWidget(self.title, 0, 0, 1, 4)


class Mod1SinglePartView(QWidget):
    def __init__(self):
        """
        全视图模式，单零件元素检视器
        """
        super().__init__()
        self.content = {
            "类型": MyLabel("未选择物体", FONT_10, side=Qt.AlignCenter),
            "坐标": {"value": [0, 0, 0], "QLineEdit": [QLineEdit(), QLineEdit(), QLineEdit()]},
            "旋转": {"value": [0, 0, 0], "QLineEdit": [QLineEdit(), QLineEdit(), QLineEdit()]},
            "缩放": {"value": [1, 1, 1], "QLineEdit": [QLineEdit(), QLineEdit(), QLineEdit()]},
            "颜色": {"value": [0.5, 0.5, 0.5], "QLineEdit": [QLineEdit(), QLineEdit(), QLineEdit()]},
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
        # grid
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.init_layout()

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
                for j, textEdit in enumerate(self.content[key_]["QLineEdit"]):
                    textEdit.setFont(text_font)
                    textEdit.setFixedWidth(60)
                    textEdit.setFixedHeight(25)
                    textEdit.setReadOnly(True)
                    textEdit.setStyleSheet(f"background-color: {BG_COLOR1};color: {FG_COLOR0};"
                                           f"border: 1px solid {FG_COLOR2};border-radius: 5px;")
                    self.layout.addWidget(textEdit, i, j + 1)

    def tab1_grid_qte_mouse_wheel(self, event=None):
        # 寻找当前鼠标所在的输入框
        active_textEdit = None
        for key in self.content:
            if key != "类型":
                for qte in self.content[key]["QLineEdit"]:
                    if qte.hasFocus():
                        active_textEdit = qte
                        break
        if active_textEdit is None:
            return
        # 获取输入框的值
        value = float(active_textEdit.toPlainText())
        # 获取鼠标滚轮的滚动值
        delta = event.angleDelta().y()
        # 根据滚动值，修改输入框的值
        if delta > 0:
            value += 0.05
        else:
            value -= 0.05
        active_textEdit.setText(str(value))

    def update_context(self, selected_obj):
        # 更新内容
        obj_type_text = "可调节船体" if selected_obj.Id == "0" else "其他零件"
        self.content["类型"].setText(obj_type_text)
        for i in range(3):
            # 修改颜色格式：从无井号16进制转换为0-255
            col_txt = selected_obj.Col[i * 2: i * 2 + 2]
            col = int(col_txt, 16)
            self.content["坐标"]["QLineEdit"][i].setText(str(selected_obj.Pos[i]))
            self.content["旋转"]["QLineEdit"][i].setText(str(selected_obj.Rot[i]))
            self.content["缩放"]["QLineEdit"][i].setText(str(selected_obj.Scl[i]))
            self.content["颜色"]["QLineEdit"][i].setText(str(col))
        self.content["装甲"]["QLineEdit"][0].setText(str(selected_obj.Amr))
        if obj_type_text == "可调节船体":
            # 更新可调节零件模型信息
            self.content["原长度"]["QLineEdit"][0].setText(str(selected_obj.Len))
            self.content["原高度"]["QLineEdit"][0].setText(str(selected_obj.Hei))
            self.content["前宽度"]["QLineEdit"][0].setText(str(selected_obj.FWid))
            self.content["后宽度"]["QLineEdit"][0].setText(str(selected_obj.BWid))
            self.content["前扩散"]["QLineEdit"][0].setText(str(selected_obj.FSpr))
            self.content["后扩散"]["QLineEdit"][0].setText(str(selected_obj.BSpr))
            self.content["上弧度"]["QLineEdit"][0].setText(str(selected_obj.UCur))
            self.content["下弧度"]["QLineEdit"][0].setText(str(selected_obj.DCur))
            self.content["高缩放"]["QLineEdit"][0].setText(str(selected_obj.HScl))
            self.content["高偏移"]["QLineEdit"][0].setText(str(selected_obj.HOff))


class Mod1VerticalPartSetView(QWidget):
    def __init__(self):
        """
        全视图模式，竖直截块元素检视器
        """
        super().__init__()
        self.title = MyLabel("竖直截块", FONT_10, side=Qt.AlignTop | Qt.AlignVCenter)
        self.layout = QGridLayout()
        self.init_layout()

    def init_layout(self):
        self.layout.setSpacing(7)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title.setFixedSize(70, 25)
        self.layout.addWidget(self.title, 0, 0, 1, 4)


class Mod1HorizontalPartSetView(QWidget):
    def __init__(self):
        """
        全视图模式，水平截块元素检视器
        """
        super().__init__()
        self.title = MyLabel("水平截块", FONT_10, side=Qt.AlignTop | Qt.AlignVCenter)
        self.layout = QGridLayout()
        self.init_layout()

    def init_layout(self):
        self.layout.setSpacing(7)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title.setFixedSize(70, 25)
        self.layout.addWidget(self.title, 0, 0, 1, 4)


class Mod1VerHorPartSetView(QWidget):
    def __init__(self):
        """
        全视图模式，集成块元素检视器
        """
        super().__init__()
        self.title = MyLabel("集成块", FONT_10, side=Qt.AlignTop | Qt.AlignVCenter)
        self.layout = QGridLayout()
        self.init_layout()

    def init_layout(self):
        self.layout.setSpacing(7)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.title.setFixedSize(70, 25)
        self.layout.addWidget(self.title, 0, 0, 1, 4)

