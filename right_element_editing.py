# -*- coding: utf-8 -*-
"""
右侧的元素编辑界面
Mod表示模式，1表示全视图模式，2表示水平截面模式，3表示竖直截面模式，4表示左视图模式

"""
from typing import Union, List

from GUI import *
from ship_reader import NAPart, AdjustableHull
from ship_reader.NA_design_reader import PartRelationMap
from state_history import push_global_statu, push_operation
from util_funcs import not_implemented, CONST
from operation import *


class Mod1AllPartsEditing(QWidget):
    def __init__(self):
        """
        全视图模式，所有零件编辑器
        """
        # 提供y，z平移，整体缩放，重置关系图 功能
        super().__init__()
        self.title = MyLabel("所有可调节船体", FONT_10, side=Qt.AlignCenter)
        self.trans_button = QPushButton("整体平移")
        self.scale_button = QPushButton("整体缩放")
        self.remap_button = QPushButton("重新绑定零件关系")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_layout()
        self.init_button()

    def init_button(self):
        style = str(f"QPushButton{{background-color: {BG_COLOR1};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:hover{{background-color: {BG_COLOR2};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:pressed{{background-color: {BG_COLOR3};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}")
        self.trans_button.setStyleSheet(style)
        self.scale_button.setStyleSheet(style)
        self.remap_button.setStyleSheet(style)
        self.trans_button.setFixedSize(150, 30)
        self.scale_button.setFixedSize(150, 30)
        self.remap_button.setFixedSize(150, 30)
        # 信号绑定
        self.trans_button.clicked.connect(self.trans_all_parts)
        self.scale_button.clicked.connect(self.scale_all_parts)
        self.remap_button.clicked.connect(self.remap_all_parts)

    def init_layout(self):
        self.layout.setSpacing(7)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.layout.addWidget(self.title)
        self.layout.addWidget(self.trans_button)
        self.layout.addWidget(self.scale_button)
        self.layout.addWidget(self.remap_button)

    @not_implemented
    def trans_all_parts(self, event=None):
        ...

    @not_implemented
    def scale_all_parts(self, event=None):
        ...

    @staticmethod
    @push_global_statu
    def remap_all_parts(event=None):
        _p = list(NAPart.hull_design_tab_id_map.values())[0]
        i = 0
        while type(_p) != AdjustableHull and i < len(NAPart.hull_design_tab_id_map):
            i += 1
            _p = list(NAPart.hull_design_tab_id_map.values())[i]
        part_relation_map = _p.allParts_relationMap
        # 重新绑定零件关系
        part_relation_map.remap()
        # 重新绘制层
        _p.glWin.xz_layer_obj, _p.glWin.xy_layer_obj, _p.glWin.left_view_obj = _p.read_na_obj.get_layers()
        _p.glWin.paintGL()
        # 更新状态栏
        _p.read_na_obj.show_statu_func("重新绑定零件关系成功！", "success")

    def update_context(self):
        pass


class Mod1SinglePartEditing(QWidget):
    current = None

    def __init__(self):
        """
        全视图模式，单零件编辑器
        """
        super().__init__()
        # 图标
        self.ADD_Y = QPixmap.fromImage(QImage.fromData(ADD_Y))
        self.ADD_Z = QPixmap.fromImage(QImage.fromData(ADD_Z))
        self.ADD_Y = self.ADD_Y.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ADD_Z = self.ADD_Z.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # 转化为控件
        self.add_y_label = QLabel()
        self.add_z_label = QLabel()
        self.add_y_label.setPixmap(self.ADD_Y)
        self.add_z_label.setPixmap(self.ADD_Z)
        # 选择的对象
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
            self.content["坐标"]["QLineEdit"][0]: float(0.1), self.content["坐标"]["QLineEdit"][1]: float(0.1),
            self.content["坐标"]["QLineEdit"][2]: float(0.1),
            self.content["装甲"]["QLineEdit"][0]: int(1),
            self.content["原长度"]["QLineEdit"][0]: float(0.1), self.content["原高度"]["QLineEdit"][0]: float(0.1),
            self.content["前宽度"]["QLineEdit"][0]: float(0.1), self.content["后宽度"]["QLineEdit"][0]: float(0.1),
            self.content["前扩散"]["QLineEdit"][0]: float(0.1), self.content["后扩散"]["QLineEdit"][0]: float(0.1),
            self.content["上弧度"]["QLineEdit"][0]: float(0.1), self.content["下弧度"]["QLineEdit"][0]: float(0.1),
            self.content["高缩放"]["QLineEdit"][0]: float(0.1), self.content["高偏移"]["QLineEdit"][0]: float(0.1)
        }
        # 单选框，用户选择当宽度编辑的时候相应的扩散是否修改，默认为修改。
        self.circle_bt = CircleSelectButton(7, False)
        self.keep_spread_label = MyLabel("保持扩散", FONT_9, side=Qt.AlignCenter)
        self.keep_spread_label.setFixedSize(80, 20)
        # 下方其他编辑
        self.down_layout = QGridLayout()
        # 按钮（包括前后细分，上下细分，向前添加层，向后添加层，向上添加层，向下添加层）
        self.add_z_button = QPushButton()
        self.add_y_button = QPushButton()
        self.add_front_layer_button = QPushButton()
        self.add_back_layer_button = QPushButton()
        self.add_up_layer_button = QPushButton()
        self.add_down_layer_button = QPushButton()
        self.buttons = [self.add_z_button, self.add_y_button, self.add_front_layer_button, self.add_back_layer_button,
                        self.add_up_layer_button, self.add_down_layer_button]
        # grid
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.init_layout()
        # 绑定滚轮事件
        self.wheelEvent = self.mouse_wheel
        Mod1SinglePartEditing.current = self

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
        # 添加输入框的值限制
        self.content["上弧度"]["QLineEdit"][0].setValidator(QDoubleValidator(0, 1, 3))
        self.content["下弧度"]["QLineEdit"][0].setValidator(QDoubleValidator(0, 1, 3))
        self.content["高缩放"]["QLineEdit"][0].setValidator(QDoubleValidator(0, 1, 3))
        # 第四五行右边添加单选框，圆圈在左1，文字在右
        w = QWidget()
        w.setLayout(QHBoxLayout())
        w.layout().addWidget(self.circle_bt)
        w.layout().addWidget(self.keep_spread_label)
        self.keep_spread_label.mousePressEvent = lambda event: self.circle_bt.click()
        w.mousePressEvent = lambda event: self.circle_bt.click()
        self.layout.addWidget(w, 5, 2, 2, 2)
        # 添加分割线
        line = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        self.layout.addWidget(line, len(self.content), 0, 1, 4)
        # 下一个标题
        lb2 = MyLabel("添加零件", FONT_10, side=Qt.AlignCenter)
        self.layout.addWidget(lb2, len(self.content) + 1, 0, 1, 4)
        # 添加下方其他编辑
        self.layout.addLayout(self.down_layout, len(self.content) + 2, 0, 1, 4)
        self.down_layout.setSpacing(7)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        # 设置按钮样式
        style = str(f"QPushButton{{background-color: {BG_COLOR1};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:hover{{background-color: {BG_COLOR2};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:pressed{{background-color: {BG_COLOR3};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}")
        for i in range(len(self.buttons)):
            self.buttons[i].setStyleSheet(style)
            self.buttons[i].setLayout(QHBoxLayout())
            self.buttons[i].layout().setSpacing(0)
            self.buttons[i].layout().setContentsMargins(3, 3, 3, 3)
            self.buttons[i].setFixedSize(90, 50)
            self.down_layout.addWidget(self.buttons[i], 2 * (i // 2), i % 2)
        # 按钮内添加控件
        self.add_z_button.layout().addWidget(self.add_z_label)
        self.add_y_button.layout().addWidget(self.add_y_label)
        self.add_z_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_y_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_front_layer_button.layout().addWidget(MyLabel("向前添加层", FONT_9, side=Qt.AlignCenter))
        self.add_back_layer_button.layout().addWidget(MyLabel("向后添加层", FONT_9, side=Qt.AlignCenter))
        self.add_up_layer_button.layout().addWidget(MyLabel("向上添加层", FONT_9, side=Qt.AlignCenter))
        self.add_down_layer_button.layout().addWidget(MyLabel("向下添加层", FONT_9, side=Qt.AlignCenter))
        # 绑定按钮事件
        self.add_z_button.clicked.connect(self.add_z)
        self.add_y_button.clicked.connect(self.add_y)
        self.add_front_layer_button.clicked.connect(self.add_front_layer_pressed)
        self.add_back_layer_button.clicked.connect(self.add_back_layer_pressed)
        self.add_up_layer_button.clicked.connect(self.add_up_layer_pressed)
        self.add_down_layer_button.clicked.connect(self.add_down_layer_pressed)

    @push_operation
    def add_z(self, event=None):
        cso = None
        if self.selected_obj:
            FP, BP = self.selected_obj.add_z_without_relation(smooth=True)
            if FP is None or BP is None:
                return cso
            cso = CutSinglePartOperation(self.selected_obj, [FP, BP])
            self.selected_obj = None
        # 隐藏自己
        self.hide()
        return cso

    @push_operation
    def add_y(self, event=None):
        cso = None
        if self.selected_obj:
            UP, DP = self.selected_obj.add_y_without_relation(smooth=True)
            if UP is None or DP is None:
                return cso
            cso = CutSinglePartOperation(self.selected_obj, [UP, DP])
            self.selected_obj = None
        # 隐藏自己
        self.hide()
        return cso

    def add_front_layer_pressed(self, event=None):
        self.add_layer_(CONST.FRONT)

    def add_back_layer_pressed(self, event=None):
        self.add_layer_(CONST.BACK)

    def add_up_layer_pressed(self, event=None):
        self.add_layer_(CONST.UP)

    def add_down_layer_pressed(self, event=None):
        self.add_layer_(CONST.DOWN)

    def add_layer_(self, direction):
        relation_map = self.selected_obj.allParts_relationMap.basicMap
        if relation_map[self.selected_obj][direction]:  # 已经有零件
            glWin = self.selected_obj.glWin
            _next = list(relation_map[self.selected_obj][direction].keys())[0]
            if type(_next) == NAPart:
                return
            glWin.selected_gl_objects[glWin.show_3d_obj_mode] = [_next]
            self.selected_obj = _next
            self.update_context(self.selected_obj)
            glWin.paintGL()
            glWin.update()
        else:  # 没有零件，添加零件
            self.hide()
            AddLayerOperation.add_layer(self.selected_obj, direction)

    def mouse_wheel(self, event) -> Union[SinglePartOperation, None]:
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
            self.update_(event, step, active_textEdit)

    @push_operation
    def update_(self, event, step, active_textEdit):
        spo = SinglePartOperation(event, step, active_textEdit, bool(self.circle_bt.isChecked()), Mod1SinglePartEditing.current)
        # spo.execute()
        return spo

    def update_obj_when_editing(self, event=None):
        if not self.allow_update_obj_when_editing:
            return False
        if event is None:  # 被鼠标滚轮后的调用，不存进undo_stack
            # 当值被修改，更新被绘制对象的值
            changed = self.selected_obj.change_attrs(
                [self.content["坐标"]["QLineEdit"][0].text(), self.content["坐标"]["QLineEdit"][1].text(),
                 self.content["坐标"]["QLineEdit"][2].text()],
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
        else:  # 被连接的直接修改信号的调用，存进undo_stack
            self.change_part_attrs(event)

    @push_operation
    def change_part_attrs(self, event):
        original_data = [self.selected_obj.Pos.copy(), self.selected_obj.Amr, self.selected_obj.Len,
                         self.selected_obj.Hei, self.selected_obj.FWid, self.selected_obj.BWid, self.selected_obj.FSpr,
                         self.selected_obj.BSpr, self.selected_obj.UCur, self.selected_obj.DCur, self.selected_obj.HScl,
                         self.selected_obj.HOff]
        changed = [[self.content["坐标"]["QLineEdit"][0].text(), self.content["坐标"]["QLineEdit"][1].text(),
                    self.content["坐标"]["QLineEdit"][2].text()],
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
                   self.content["高偏移"]["QLineEdit"][0].text()]
        spo = SinglePartOperation(event, 0, None, bool(self.circle_bt.isChecked()),
                                  Mod1SinglePartEditing.current, original_data=original_data, change_data=changed)
        return spo

    def update_context(self, selected_obj):
        self.selected_obj = selected_obj
        if selected_obj is None:
            self.hide()
            return
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


class Mod1VerticalPartSetEditing(QWidget):
    def __init__(self):
        """
        全视图模式，竖直截块编辑器
        """
        super().__init__()
        self.title = MyLabel("竖直截块", FONT_10, side=Qt.AlignCenter)
        # 图标
        self.ADD_Y = QPixmap.fromImage(QImage.fromData(ADD_Y))
        self.ADD_Z = QPixmap.fromImage(QImage.fromData(ADD_Z))
        self.ADD_Y = self.ADD_Y.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ADD_Z = self.ADD_Z.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # 转化为控件
        self.add_y_label = QLabel()
        self.add_z_label = QLabel()
        self.add_y_label.setPixmap(self.ADD_Y)
        self.add_z_label.setPixmap(self.ADD_Z)
        # 选择的对象
        self.selected_objs: List[AdjustableHull] = []
        self.allow_update_obj_when_editing = True
        # 下方其他编辑
        self.down_layout = QGridLayout()
        # 按钮（包括前后细分，上下细分，向前添加层，向后添加层，向上添加层，向下添加层）
        self.add_z_button = QPushButton()
        self.add_y_button = QPushButton()
        self.add_front_layer_button = QPushButton()
        self.add_back_layer_button = QPushButton()
        self.add_up_layer_button = QPushButton()
        self.add_down_layer_button = QPushButton()
        self.buttons = [self.add_z_button, self.add_y_button, self.add_front_layer_button, self.add_back_layer_button,
                        self.add_up_layer_button, self.add_down_layer_button]
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
        self.layout.addWidget(self.title, 0, 0, 1, 4)
        # 添加下方其他编辑
        self.layout.addLayout(self.down_layout, 1, 0, 1, 4)
        self.down_layout.setSpacing(7)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        # 设置按钮样式
        style = str(f"QPushButton{{background-color: {BG_COLOR1};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:hover{{background-color: {BG_COLOR2};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:pressed{{background-color: {BG_COLOR3};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}")
        for i in range(len(self.buttons)):
            self.buttons[i].setStyleSheet(style)
            self.buttons[i].setLayout(QHBoxLayout())
            self.buttons[i].layout().setSpacing(0)
            self.buttons[i].layout().setContentsMargins(3, 3, 3, 3)
            self.buttons[i].setFixedSize(90, 50)
            self.down_layout.addWidget(self.buttons[i], 2 * (i // 2), i % 2)
        # 按钮内添加控件
        self.add_z_button.layout().addWidget(self.add_z_label)
        self.add_y_button.layout().addWidget(self.add_y_label)
        self.add_z_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_y_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_front_layer_button.layout().addWidget(MyLabel("向前添加层", FONT_9, side=Qt.AlignCenter))
        self.add_back_layer_button.layout().addWidget(MyLabel("向后添加层", FONT_9, side=Qt.AlignCenter))
        self.add_up_layer_button.layout().addWidget(MyLabel("向上添加层", FONT_9, side=Qt.AlignCenter))
        self.add_down_layer_button.layout().addWidget(MyLabel("向下添加层", FONT_9, side=Qt.AlignCenter))
        # 绑定按钮事件
        self.add_z_button.clicked.connect(self.add_z)
        self.add_y_button.clicked.connect(self.add_y)
        self.add_front_layer_button.clicked.connect(self.add_front_layer)
        self.add_back_layer_button.clicked.connect(self.add_back_layer)
        self.add_up_layer_button.clicked.connect(self.add_up_layer)
        self.add_down_layer_button.clicked.connect(self.add_down_layer)

    @not_implemented
    @push_global_statu
    def add_z(self, event=None):
        return
        front_parts = []
        back_parts = []
        glWin = self.selected_objs[0].glWin
        for part in self.selected_objs:
            FP, BP = part.add_z_without_relation(smooth=True)
            if FP or BP:
                front_parts.append(FP)
                back_parts.append(BP)
        # 处理零件关系图
        relation_map = self.selected_objs[0].allParts_relationMap
        self.selected_objs = []
        # TODO: 未完成
        # 重新渲染
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = True
        glWin.paintGL()
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = False
        glWin.update()
        self.hide()

    @not_implemented
    @push_global_statu
    def add_y(self, event=None):
        return
        up_parts = []
        down_parts = []
        glWin = self.selected_objs[0].glWin
        for part in self.selected_objs:
            UP, DP = part.add_y_without_relation(smooth=True)
            if UP or DP:
                up_parts.append(UP)
                down_parts.append(DP)
        # 处理零件关系图
        relation_map = self.selected_objs[0].allParts_relationMap
        self.selected_objs = []
        # TODO: 未完成
        # 重新渲染
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = True
        glWin.paintGL()
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = False
        glWin.update()
        self.hide()

    def add_front_layer(self, event=None):
        self.add_layer_(CONST.FRONT)

    def add_back_layer(self, event=None):
        self.add_layer_(CONST.BACK)

    def add_up_layer(self, event=None):
        self.add_layer_(CONST.UP)

    def add_down_layer(self, event=None):
        self.add_layer_(CONST.DOWN)

    def add_layer_(self, direction):
        self.hide()
        AddLayerOperation.add_layer(self.selected_objs, direction)

    def mouse_wheel(self, event):
        self.wheelEvent(event)


class Mod1HorizontalPartSetEditing(QWidget):
    def __init__(self):
        """
        全视图模式，水平截块编辑器
        """
        super().__init__()
        self.title = MyLabel("水平截块", FONT_10, side=Qt.AlignCenter)
        # 图标
        self.ADD_Y = QPixmap.fromImage(QImage.fromData(ADD_Y))
        self.ADD_Z = QPixmap.fromImage(QImage.fromData(ADD_Z))
        self.ADD_Y = self.ADD_Y.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.ADD_Z = self.ADD_Z.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        # 转化为控件
        self.add_y_label = QLabel()
        self.add_z_label = QLabel()
        self.add_y_label.setPixmap(self.ADD_Y)
        self.add_z_label.setPixmap(self.ADD_Z)
        # 选择的对象
        self.selected_objs: List[AdjustableHull] = []
        self.allow_update_obj_when_editing = True
        # 下方其他编辑
        self.down_layout = QGridLayout()
        # 按钮（包括前后细分，上下细分，向前添加层，向后添加层，向上添加层，向下添加层）
        self.add_z_button = QPushButton()
        self.add_y_button = QPushButton()
        self.add_front_layer_button = QPushButton()
        self.add_back_layer_button = QPushButton()
        self.add_up_layer_button = QPushButton()
        self.add_down_layer_button = QPushButton()
        self.buttons = [self.add_z_button, self.add_y_button, self.add_front_layer_button, self.add_back_layer_button,
                        self.add_up_layer_button, self.add_down_layer_button]
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
        self.layout.addWidget(self.title, 0, 0, 1, 4)
        # 添加下方其他编辑
        self.layout.addLayout(self.down_layout, 1, 0, 1, 4)
        self.down_layout.setSpacing(7)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        # 设置按钮样式
        style = str(f"QPushButton{{background-color: {BG_COLOR1};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:hover{{background-color: {BG_COLOR2};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:pressed{{background-color: {BG_COLOR3};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}")
        for i in range(len(self.buttons)):
            self.buttons[i].setStyleSheet(style)
            self.buttons[i].setLayout(QHBoxLayout())
            self.buttons[i].layout().setSpacing(0)
            self.buttons[i].layout().setContentsMargins(3, 3, 3, 3)
            self.buttons[i].setFixedSize(90, 50)
            self.down_layout.addWidget(self.buttons[i], 2 * (i // 2), i % 2)
        # 按钮内添加控件
        self.add_z_button.layout().addWidget(self.add_z_label)
        self.add_y_button.layout().addWidget(self.add_y_label)
        self.add_z_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_y_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_front_layer_button.layout().addWidget(MyLabel("向前添加层", FONT_9, side=Qt.AlignCenter))
        self.add_back_layer_button.layout().addWidget(MyLabel("向后添加层", FONT_9, side=Qt.AlignCenter))
        self.add_up_layer_button.layout().addWidget(MyLabel("向上添加层", FONT_9, side=Qt.AlignCenter))
        self.add_down_layer_button.layout().addWidget(MyLabel("向下添加层", FONT_9, side=Qt.AlignCenter))
        # 绑定按钮事件
        self.add_z_button.clicked.connect(self.add_z)
        self.add_y_button.clicked.connect(self.add_y)
        self.add_front_layer_button.clicked.connect(self.add_front_layer)
        self.add_back_layer_button.clicked.connect(self.add_back_layer)
        self.add_up_layer_button.clicked.connect(self.add_up_layer)
        self.add_down_layer_button.clicked.connect(self.add_down_layer)

    @not_implemented
    @push_global_statu
    def add_z(self, event=None):
        return
        front_parts = []
        back_parts = []
        glWin = self.selected_objs[0].glWin
        for part in self.selected_objs:
            FP, BP = part.add_z_without_relation(smooth=True)
            if FP or BP:
                front_parts.append(FP)
                back_parts.append(BP)
        # 处理零件关系图
        relation_map = self.selected_objs[0].allParts_relationMap
        self.selected_objs = []
        # TODO: 未完成
        # 重新渲染
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = True
        glWin.paintGL()
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = False
        glWin.update()
        self.hide()

    @not_implemented
    @push_global_statu
    def add_y(self, event=None):
        return
        up_parts = []
        down_parts = []
        glWin = self.selected_objs[0].glWin
        for part in self.selected_objs:
            UP, DP = part.add_y_without_relation(smooth=True)
            if UP or DP:
                up_parts.append(UP)
                down_parts.append(DP)
        # 处理零件关系图
        relation_map = self.selected_objs[0].allParts_relationMap
        self.selected_objs = []
        # TODO: 未完成
        # 重新渲染
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = True
        glWin.paintGL()
        for mode in glWin.gl_commands.keys():
            glWin.gl_commands[mode][1] = False
        glWin.update()
        self.hide()

    def add_front_layer(self, event=None):
        self.add_layer_(CONST.FRONT)

    def add_back_layer(self, event=None):
        self.add_layer_(CONST.BACK)

    def add_up_layer(self, event=None):
        self.add_layer_(CONST.UP)

    def add_down_layer(self, event=None):
        self.add_layer_(CONST.DOWN)

    def add_layer_(self, direction):
        self.hide()
        AddLayerOperation.add_layer(self.selected_objs, direction)

    def mouse_wheel(self, event):
        self.wheelEvent(event)


class Mod1VerHorPartSetEditing(QWidget):
    def __init__(self):
        """
        全视图模式，集成块编辑器
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


class Mod2SingleLayerEditing(QWidget):
    def __init__(self):
        """
        水平截面视图模式，单层元素编辑窗
        """
        super().__init__()
