# -*- coding: utf-8 -*-
"""
右侧的元素编辑界面
Mod表示模式，1表示全视图模式，2表示水平截面模式，3表示竖直截面模式，4表示左视图模式

"""
import time
from typing import Union, List

from GUI import *
from ship_reader import NAPart, AdjustableHull
from state_history import push_global_statu, push_operation
from util_funcs import not_implemented, CONST
from operation import *


def show_buttons(buttons: List[QPushButton]):
    for bt in buttons:
        bt.show()


def hide_buttons(buttons: List[QPushButton]):
    for bt in buttons:
        bt.hide()


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
    current = None  # 当前正在编辑的对象

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
        self.lb1 = MyLabel("零件高级变换", FONT_10, side=Qt.AlignCenter)
        self.lb2 = MyLabel("添加零件", FONT_10, side=Qt.AlignCenter)
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
        self.transform_layout = QGridLayout()
        self.add_layout = QGridLayout()
        # 变换类操作按钮
        self.rotate_button = QPushButton()
        self.scl_norm_button = QPushButton()
        self.forecastle_button = QPushButton()
        self.poop_button = QPushButton()
        self.transform_buttons = [self.rotate_button, self.scl_norm_button,
                                  self.forecastle_button, self.poop_button]
        # 添加类操作按钮（包括前后细分，上下细分，向前添加层，向后添加层，向上添加层，向下添加层）
        self.add_z_button = QPushButton()
        self.add_y_button = QPushButton()
        self.add_front_part_button = QPushButton()
        self.add_front_layer_button = QPushButton()
        self.add_back_part_button = QPushButton()
        self.add_back_layer_button = QPushButton()
        self.add_up_part_button = QPushButton()
        self.add_up_layer_button = QPushButton()
        self.add_down_part_button = QPushButton()
        self.add_down_layer_button = QPushButton()
        self.add_buttons = [self.add_z_button, self.add_y_button,
                            self.add_front_part_button, self.add_front_layer_button,
                            self.add_back_part_button, self.add_back_layer_button,
                            self.add_up_part_button, self.add_up_layer_button,
                            self.add_down_part_button, self.add_down_layer_button]
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
                    lineEdit.textChanged.connect(self.lineEditChanged)
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
        self.layout.addWidget(self.lb1, len(self.content) + 1, 0, 1, 4)
        # 变换零件
        self.layout.addLayout(self.transform_layout, len(self.content) + 2, 0, 1, 4)
        self.transform_layout.setSpacing(7)
        self.transform_layout.setContentsMargins(0, 0, 0, 0)
        hide_buttons(self.transform_buttons)
        # 添加分割线
        line = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        self.layout.addWidget(line, len(self.content) + 3, 0, 1, 4)
        # 下一个标题
        self.layout.addWidget(self.lb2, len(self.content) + 4, 0, 1, 4)
        # 添加零件
        self.layout.addLayout(self.add_layout, len(self.content) + 5, 0, 1, 4)
        self.add_layout.setSpacing(7)
        self.add_layout.setContentsMargins(0, 0, 0, 0)
        hide_buttons(self.add_buttons)
        self.init_buttons()

    def init_buttons(self):
        # 设置按钮样式
        style = str(f"QPushButton{{background-color: {BG_COLOR1};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:hover{{background-color: {BG_COLOR2};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}"
                    f"QPushButton:pressed{{background-color: {BG_COLOR3};color: {FG_COLOR0};"
                    f"border: 1px solid {FG_COLOR2};border-radius: 5px;}}")
        for i in range(len(self.transform_buttons)):
            self.transform_buttons[i].setStyleSheet(style)
            self.transform_buttons[i].setLayout(QHBoxLayout())
            self.transform_buttons[i].layout().setSpacing(0)
            self.transform_buttons[i].layout().setContentsMargins(3, 3, 3, 3)
            self.transform_buttons[i].setFixedSize(90, 50)
            self.transform_layout.addWidget(self.transform_buttons[i], 2 * (i // 2), i % 2)
        for i in range(len(self.add_buttons)):
            self.add_buttons[i].setStyleSheet(style)
            self.add_buttons[i].setLayout(QHBoxLayout())
            self.add_buttons[i].layout().setSpacing(0)
            self.add_buttons[i].layout().setContentsMargins(3, 3, 3, 3)
            self.add_buttons[i].setFixedSize(90, 50)
            self.add_layout.addWidget(self.add_buttons[i], 2 * (i // 2), i % 2)
        # 按钮内添加控件
        self.rotate_button.layout().addWidget(MyLabel("不变形旋转", FONT_9, side=Qt.AlignCenter))
        self.scl_norm_button.layout().addWidget(MyLabel("缩放归一化", FONT_9, side=Qt.AlignCenter))
        self.forecastle_button.layout().addWidget(MyLabel("舰艏上扬体", FONT_9, side=Qt.AlignCenter))
        self.poop_button.layout().addWidget(MyLabel("舰艉上扬体", FONT_9, side=Qt.AlignCenter))
        self.add_z_button.layout().addWidget(self.add_z_label)
        self.add_y_button.layout().addWidget(self.add_y_label)
        self.add_z_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_y_button.layout().addWidget(MyLabel("细分", FONT_9, side=Qt.AlignCenter))
        self.add_front_part_button.layout().addWidget(MyLabel("向前加零件", FONT_9, side=Qt.AlignCenter))
        self.add_back_part_button.layout().addWidget(MyLabel("向后加零件", FONT_9, side=Qt.AlignCenter))
        self.add_up_part_button.layout().addWidget(MyLabel("向上加零件", FONT_9, side=Qt.AlignCenter))
        self.add_down_part_button.layout().addWidget(MyLabel("向下加零件", FONT_9, side=Qt.AlignCenter))
        self.add_front_layer_button.layout().addWidget(MyLabel("向前添加层", FONT_9, side=Qt.AlignCenter))
        self.add_back_layer_button.layout().addWidget(MyLabel("向后添加层", FONT_9, side=Qt.AlignCenter))
        self.add_up_layer_button.layout().addWidget(MyLabel("向上添加层", FONT_9, side=Qt.AlignCenter))
        self.add_down_layer_button.layout().addWidget(MyLabel("向下添加层", FONT_9, side=Qt.AlignCenter))
        # 绑定按钮事件
        self.rotate_button.clicked.connect(self.rotate)
        self.scl_norm_button.clicked.connect(self.scl_norm)
        self.forecastle_button.clicked.connect(self.forecastle)
        self.poop_button.clicked.connect(self.poop)
        self.add_z_button.clicked.connect(self.add_z)
        self.add_y_button.clicked.connect(self.add_y)
        self.add_front_part_button.clicked.connect(lambda event: self.add_layer_(CONST.FRONT, single=True))
        self.add_back_part_button.clicked.connect(lambda event: self.add_layer_(CONST.BACK, single=True))
        self.add_up_part_button.clicked.connect(lambda event: self.add_layer_(CONST.UP, single=True))
        self.add_down_part_button.clicked.connect(lambda event: self.add_layer_(CONST.DOWN, single=True))
        self.add_front_layer_button.clicked.connect(lambda event: self.add_layer_(CONST.FRONT))
        self.add_back_layer_button.clicked.connect(lambda event: self.add_layer_(CONST.BACK))
        self.add_up_layer_button.clicked.connect(lambda event: self.add_layer_(CONST.UP))
        self.add_down_layer_button.clicked.connect(lambda event: self.add_layer_(CONST.DOWN))
        # 绑定鼠标悬浮在子标题事件（显示buttons隐藏其他buttons）
        self.lb1.enterEvent = self.change_showed_buttons
        self.lb2.enterEvent = self.change_showed_buttons

    def change_showed_buttons(self, event=None):
        if self.lb1.underMouse():
            self.lb1.setStyleSheet(f"color: {FG_COLOR0};")
            self.lb2.setStyleSheet(f"color: {GRAY};")
            show_buttons(self.transform_buttons)
            hide_buttons(self.add_buttons)
        elif self.lb2.underMouse():
            self.lb1.setStyleSheet(f"color: {GRAY};")
            self.lb2.setStyleSheet(f"color: {FG_COLOR0};")
            show_buttons(self.add_buttons)
            hide_buttons(self.transform_buttons)

    @not_implemented
    def rotate(self, event=None):
        pass

    @not_implemented
    def scl_norm(self, event=None):
        pass

    @not_implemented
    def forecastle(self, event=None):
        pass

    @not_implemented
    def poop(self, event=None):
        pass

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

    def add_layer_(self, direction, single=False):
        relation_map = self.selected_obj.allParts_relationMap.basicMap
        if (
                self.selected_obj in relation_map and
                direction in relation_map[self.selected_obj] and
                relation_map[self.selected_obj][direction] != {}
        ):
            glWin = self.selected_obj.glWin
            _next = list(relation_map[self.selected_obj][direction].keys())[0]
            if not isinstance(_next, AdjustableHull):
                return
            glWin.selected_gl_objects[glWin.show_3d_obj_mode] = [_next]
            self.selected_obj = _next
            self.update_context(self.selected_obj)
            glWin.paintGL()
            glWin.update()
        else:  # 没有零件，添加零件
            self.hide()
            AddLayerOperation(direction, [self.selected_obj], single=single)

    def update_context(self, selected_obj):
        """
        只根据对象修改值，不产生新的操作
        :param selected_obj:
        :return:
        """
        self.selected_obj = selected_obj
        if selected_obj is None:
            self.hide()
            return
        self.allow_update_obj_when_editing = False  # 防止修改输入框的时候修改对象
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

    def mouse_wheel(self, event) -> Union[SinglePartOperation, None]:
        """
        鼠标滚轮事件，修改当前输入框的值
        :param event:
        :return:
        """
        # 通过鼠标位置检测当前输入框
        active_textEdit = None
        pos = self.mapFromGlobal(QCursor.pos())
        for key in self.content:
            if key not in ["类型", "旋转"]:
                for textEdit in self.content[key]["QLineEdit"]:
                    if textEdit.geometry().contains(pos):
                        active_textEdit = textEdit
                        break
                if active_textEdit:
                    break
        if active_textEdit is None:
            return None
        step = self.wheel_change_value_map[active_textEdit]
        # 获取输入框的值
        if event.angleDelta().y() < 0:
            step = - step
        if step == 0:
            return None
        # 修改值
        else:
            step_type = type(step)
            new_value = step + step_type(active_textEdit.text())
            # 修改输入框的值
            if step_type == int:
                active_textEdit.setText(str(new_value))
            elif step_type == float:
                if (active_textEdit in [
                    self.content["坐标"]["QLineEdit"][0],
                    self.content["坐标"]["QLineEdit"][1],
                    self.content["坐标"]["QLineEdit"][2]]
                        and self.selected_obj in self.selected_obj.allParts_relationMap.basicMap
                        and self.selected_obj.allParts_relationMap.basicMap[self.selected_obj] != {}):
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
                        relation_map = self.selected_obj.allParts_relationMap
                        relation_map.del_part(self.selected_obj)
                elif active_textEdit in [self.content["上弧度"]["QLineEdit"][0],
                                         self.content["下弧度"]["QLineEdit"][0]] \
                        and (new_value < 0 or new_value > 1):
                    # 弧度值不在0-1之间，直接不修改
                    return
                active_textEdit.setText(str(round(new_value, 3)))
                if not self.circle_bt.isChecked():  # 扩散随着宽度变换
                    if active_textEdit == self.content["前宽度"]["QLineEdit"][0]:
                        txt = self.content["前扩散"]["QLineEdit"][0].text()
                        self.content["前扩散"]["QLineEdit"][0].setText(str(round(float(txt) - step, 3)))
                    elif active_textEdit == self.content["后宽度"]["QLineEdit"][0]:
                        txt = self.content["后扩散"]["QLineEdit"][0].text()
                        self.content["后扩散"]["QLineEdit"][0].setText(str(round(float(txt) - step, 3)))

    def lineEditChanged(self, event=None):
        """
        输入框值改变时，修改对象的值，并且将操作压入操作栈
        :return:
        """
        if not self.allow_update_obj_when_editing:
            return False
        self.allow_update_obj_when_editing = False
        self.change_part_attrs()
        self.allow_update_obj_when_editing = True

    @push_operation
    def change_part_attrs(self):
        changed = [[
            self.content["坐标"]["QLineEdit"][0].text(), self.content["坐标"]["QLineEdit"][1].text(),
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
        # spo = SinglePartOperation(self, event, self.selected_obj, 0, None, bool(self.circle_bt.isChecked()),
        #                           Mod1SinglePartEditing.current, original_data=original_data, change_data=changed)
        spo = SinglePartOperation(self, self.selected_obj, changed)
        return spo



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
        glWin.repaintGL()
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
        glWin.repaintGL()
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
        AddLayerOperation(direction, self.selected_objs)


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
        glWin.repaintGL()
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
        glWin.repaintGL()
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
        AddLayerOperation(direction, self.selected_objs)


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
