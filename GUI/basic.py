# -*- coding: utf-8 -*-
"""
将会被多次使用的基础类
"""
# 内置库
import ctypes
import json
import os
from typing import List
from abc import abstractmethod
from base64 import b64decode

# 第三方库
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QRect, QPoint
from PyQt5.QtGui import (QIcon, QPixmap, QImage, QColor, QFont, QPainter, QPainterPath, QLinearGradient,
                         QPolygon, QIntValidator)
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QMessageBox, QDialog, QToolBar, QSizePolicy
from PyQt5.QtWidgets import QLineEdit, QComboBox, QSlider, QPushButton
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
# 本地库
from path_utils import find_na_root_path

# 读取配置文件中的主题信息
_path = os.path.join(find_na_root_path(), 'plugin_config.json')
try:
    with open(_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    Theme = data['Config']['Theme']
    ProjectFolder = data['ProjectsFolder']
except (FileNotFoundError, KeyError, AttributeError):
    Theme = 'Night'
    ProjectFolder = os.path.join(os.path.expanduser("~"), 'Desktop')

# 根据主题选择颜色，图片
if Theme == 'Day':
    from theme_config_color.day_color import *
    from UI_design.ImgPng_day import close
elif Theme == 'Night':
    from theme_config_color.night_color import *
    from UI_design.ImgPng_night import close

# 常量
WHITE = 'white'
GOLD = 'gold'
GRAY = '#808080'
YAHEI = '微软雅黑'
LOCAL_ADDRESS = os.path.dirname(os.path.abspath(__file__))
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 设置高分辨率
ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 125  # 获取缩放比例
user32 = ctypes.windll.user32
WinWid = user32.GetSystemMetrics(0)  # 获取分辨率
WinHei = user32.GetSystemMetrics(1)  # 获取分辨率
RATE = WinWid / 1920
_FONT_SCL = True
if _FONT_SCL:
    FONT_7 = QFont(YAHEI, 7 / ScaleFactor)  # 设置字体
    FONT_8 = QFont(YAHEI, 8 / ScaleFactor)  # 设置字体
    FONT_9 = QFont(YAHEI, 9 / ScaleFactor)  # 设置字体
    FONT_10 = QFont(YAHEI, 10 / ScaleFactor)  # 设置字体
    FONT_11 = QFont(YAHEI, 11 / ScaleFactor)  # 设置字体
    FONT_12 = QFont(YAHEI, 12 / ScaleFactor)  # 设置字体
    FONT_13 = QFont(YAHEI, 13 / ScaleFactor)  # 设置字体
    FONT_14 = QFont(YAHEI, 14 / ScaleFactor)  # 设置字体
    FONT_15 = QFont(YAHEI, 15 / ScaleFactor)  # 设置字体
    FONT_16 = QFont(YAHEI, 16 / ScaleFactor)  # 设置字体
    FONT_17 = QFont(YAHEI, 17 / ScaleFactor)  # 设置字体
    FONT_18 = QFont(YAHEI, 18 / ScaleFactor)  # 设置字体
    FONT_19 = QFont(YAHEI, 19 / ScaleFactor)  # 设置字体
    FONT_20 = QFont(YAHEI, 20 / ScaleFactor)  # 设置字体
    FONT_21 = QFont(YAHEI, 21 / ScaleFactor)  # 设置字体
    FONT_22 = QFont(YAHEI, 22 / ScaleFactor)  # 设置字体
else:
    FONT_7 = QFont(YAHEI, 7)
    FONT_8 = QFont(YAHEI, 8)
    FONT_9 = QFont(YAHEI, 9)
    FONT_10 = QFont(YAHEI, 10)
    FONT_11 = QFont(YAHEI, 11)
    FONT_12 = QFont(YAHEI, 12)
    FONT_13 = QFont(YAHEI, 13)
    FONT_14 = QFont(YAHEI, 14)
    FONT_15 = QFont(YAHEI, 15)
    FONT_16 = QFont(YAHEI, 16)
    FONT_17 = QFont(YAHEI, 17)
    FONT_18 = QFont(YAHEI, 18)
    FONT_19 = QFont(YAHEI, 19)
    FONT_20 = QFont(YAHEI, 20)
    FONT_21 = QFont(YAHEI, 21)
    FONT_22 = QFont(YAHEI, 22)


def getFG_fromBG(bg: QColor):
    # 如果红绿蓝三色的平均值小于128，那么前景色为白色，否则为黑色
    if (bg.red() + bg.green() + bg.blue()) / 3 < 128:
        return QColor(255, 255, 255)
    else:
        return QColor(0, 0, 0)


def front_completion(txt, length, add_char):
    """
    用于在字符串前补全字符
    :param txt: 原字符串
    :param length: 补全后的长度
    :param add_char: 用于补全的字符
    :return: 补全后的字符串
    """
    if len(txt) < length:
        return add_char * (length - len(txt)) + txt
    else:
        return txt


def set_buttons(
        buttons, sizes, font=FONT_9, border=0, border_color=FG_COLOR0,
        border_radius=10, padding=0, bg=(BG_COLOR1, BG_COLOR3, BG_COLOR2, BG_COLOR3),
        fg=FG_COLOR0
):
    """
    设置按钮样式
    :param buttons: 按钮列表
    :param sizes:
    :param font: QFont对象
    :param border: 边框宽度
    :param border_color: 边框颜色
    :param border_radius: 边框圆角
    :param padding: 内边距
    :param bg: 按钮背景颜色
    :param fg: 按钮字体颜色
    :return:
    """
    buttons = list(buttons)
    if isinstance(border_radius, int):
        border_radius = (border_radius, border_radius, border_radius, border_radius)
    if type(sizes[0]) in [int, None]:
        sizes = [sizes] * len(buttons)
    if border != 0:
        border_text = f"{border}px solid {border_color}"
    else:
        border_text = "none"
    if isinstance(padding, int):
        padding = (padding, padding, padding, padding)
    if isinstance(bg, str):
        bg = (bg, bg, bg, bg)
    if isinstance(fg, str):
        fg = (fg, fg, fg, fg)
    for button in buttons:
        if sizes[buttons.index(button)][0] is None:
            # 宽度拉伸
            button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            button.setFixedHeight(sizes[buttons.index(button)][1])
        elif sizes[buttons.index(button)][1] is None:
            # 高度拉伸
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Maximum)
            button.setFixedWidth(sizes[buttons.index(button)][0])
        else:
            button.setFixedSize(*sizes[buttons.index(button)])
        button.setFont(font)
        button.setStyleSheet(f"""
            QPushButton{{
                background-color:{bg[0]};
                color:{fg[0]};
                border-top-left-radius: {border_radius[0]}px;
                border-top-right-radius: {border_radius[1]}px;
                border-bottom-right-radius: {border_radius[2]}px;
                border-bottom-left-radius: {border_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
            QPushButton:hover{{
                background-color:{bg[1]};
                color:{fg[1]};
                border-top-left-radius: {border_radius[0]}px;
                border-top-right-radius: {border_radius[1]}px;
                border-bottom-right-radius: {border_radius[2]}px;
                border-bottom-left-radius: {border_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
            QPushButton::pressed{{
                background-color:{bg[2]};
                color:{fg[2]};
                border-top-left-radius: {border_radius[0]}px;
                border-top-right-radius: {border_radius[1]}px;
                border-bottom-right-radius: {border_radius[2]}px;
                border-bottom-left-radius: {border_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
            QPushButton::focus{{
                background-color:{bg[3]};
                color:{fg[3]};
                border-top-left-radius: {border_radius[0]}px;
                border-top-right-radius: {border_radius[1]}px;
                border-bottom-right-radius: {border_radius[2]}px;
                border-bottom-left-radius: {border_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
        """)


def set_button_style(button, size: tuple, font=FONT_9, style="普通", active_color=BG_COLOR3, icon=None):
    """
    设置按钮样式
    :param button: QPushButton对象
    :param size: Tuple[int, int]，按钮大小
    :param font: QFont对象
    :param style: "普通"或"圆角边框"
    :param active_color: 鼠标悬停时的颜色
    :param icon: QIcon对象
    :return:
    """
    button.setFixedSize(*size)
    if style == "普通":
        button.setStyleSheet(f"""
            QPushButton{{
                background-color:{BG_COLOR1};
                color:{FG_COLOR0};
                border-radius: 0px;
                border: 0px;
            }}
            QPushButton:hover{{
                background-color:{active_color};
                color:{FG_COLOR0};
                border-radius: 0px;
                border: 0px;
            }}
            QPushButton:pressed{{
                background-color:{active_color};
                color:{FG_COLOR0};
                border-radius: 0px;
                border: 0px;
            }}          
        """)
    elif style == "圆角边框":
        button.setStyleSheet(f"""
            QPushButton{{
                background-color:{BG_COLOR1};
                color:{FG_COLOR0};
                border-radius: 10px;
                border: 0px;
            }}
            QPushButton:hover{{
                background-color:{active_color};
                color:{FG_COLOR0};
                border-radius: 10px;
                border: 0px;
            }}
            QPushButton:pressed{{
                background-color:{active_color};
                color:{FG_COLOR0};
                border-radius: 10px;
                border: 0px;
            }}          
        """)
    button.setFont(font)
    if icon:
        button.setIcon(icon)
        button.setIconSize(QSize(*size))


def set_top_button_style(button: QPushButton, width=50):
    """
    设置标签页内顶部的按钮样式
    :param button: QPushButton对象
    :param width: int，按钮宽度
    :return:
    """
    # 设置样式
    set_buttons([button], sizes=(width, 30), font=FONT_8, border=0, border_radius=0, padding=0)


def set_tool_bar_style(tool_bar: QToolBar):
    """
    设置工具栏样式
    :param tool_bar: QToolBar对象
    :return:
    """
    tool_bar.setStyleSheet(f"background-color: {BG_COLOR0};")
    tool_bar.setOrientation(Qt.Vertical)
    tool_bar.setToolButtonStyle(Qt.ToolButtonIconOnly)  # 不显示文本
    tool_bar.setContentsMargins(0, 0, 0, 0)
    # 按钮样式
    tool_bar.setIconSize(QSize(26, 26))
    tool_bar.setFixedWidth(40)
    tool_bar.setMovable(True)
    tool_bar.setFloatable(True)
    tool_bar.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)


def create_rounded_thumbnail(image_path, width, height, corner_radius):
    if isinstance(image_path, str):
        original_image = QPixmap(image_path).scaled(width, height, Qt.KeepAspectRatio)
    else:  # 是QPixmap对象
        original_image = image_path.scaled(width, height, Qt.KeepAspectRatio)
    rounded_thumbnail = QPixmap(width, height)
    rounded_thumbnail.fill(Qt.transparent)  # 设置背景透明
    painter = QPainter(rounded_thumbnail)
    painter.setRenderHint(QPainter.Antialiasing)
    # 创建一个椭圆路径来表示圆角
    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, corner_radius, corner_radius)
    painter.setClipPath(path)  # 设置剪裁路径
    # 在剪裁后的区域内绘制原始图像
    painter.drawPixmap(0, 0, original_image)
    painter.end()  # 结束绘制
    return rounded_thumbnail


class MyMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            # 设置以自己为父的QMessageBox的样式
            f"QMessageBox{{background-color: {BG_COLOR1};"
            f"color: {FG_COLOR0};"
            f"border: 1px solid {FG_COLOR2};"
            f"border-radius: 5px;}}"
        )
        # 设置按钮
        self.setStandardButtons(QMessageBox.Yes)
        self.button(QMessageBox.Yes).setCursor(Qt.PointingHandCursor)


class MyLabel(QLabel):
    def __init__(self, text, font=FONT_9, color=FG_COLOR0, side=Qt.AlignLeft | Qt.AlignVCenter):
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color:{color};")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(side)


class MyLineEdit(QLineEdit):
    def __init__(self, text="", font=FONT_9):
        super().__init__(text)
        self.setFont(font)
        self.enable()

    def enable(self):
        self.setStyleSheet(
            f"""QLineEdit{{background-color: {BG_COLOR1}; 
            color: {FG_COLOR0}; 
            border: 1px solid {FG_COLOR0}; 
            border-radius: 5px;}}"""
        )

    def disable(self):
        self.setStyleSheet(
            f"""QLineEdit{{background-color: {BG_COLOR1}; 
            color: {GRAY}; 
            border: 1px solid {GRAY}; 
            border-radius: 5px;}}"""
        )


class MyComboBox(QComboBox):
    def __init__(self, font=FONT_9):
        super().__init__()
        self.setFont(font)
        self.enable()

    def enable(self):
        self.setStyleSheet(
            f"""
            QComboBox{{
                background-color: {BG_COLOR1};
                color: {FG_COLOR0};
                border: 1px solid {FG_COLOR0};
                border-radius: 5px;
            }}
            QComboBox::drop-down{{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                background-color: {BG_COLOR0};
            }}
            QComboBox QAbstractItemView{{
                border: 1px solid {FG_COLOR0};
                border-radius: 5px;
                background-color: {BG_COLOR1};
                color: {FG_COLOR0};
                selection-background-color: {BG_COLOR3};
            }}"""
        )

    def disable(self):
        self.setStyleSheet(
            f"""
            QComboBox{{
                background-color: {BG_COLOR1};
                color: {GRAY};
                border: 1px solid {GRAY};
                border-radius: 5px;
            }}
            QComboBox::drop-down{{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                background-color: {BG_COLOR0};
            }}"""
        )


class MySlider(QSlider):
    def __init__(self, value_range=(50, 1000), current_value=200.0, orientation=Qt.Horizontal):
        super().__init__(orientation)
        self.setMinimum(value_range[0])
        self.setMaximum(value_range[1])
        self.setValue(current_value)
        # 设置滑块样式
        self.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background-color: {BG_COLOR0};
                border-radius: 4px;
                height: 10px;
                margin: 1px 1px;
            }}
            QSlider::handle:horizontal {{
                background-color: {FG_COLOR0};
                border-radius: 4px;
                width: 10px;
                margin: -10px 0px -10px 0px;
            }}
            QSlider::add-page:horizontal {{
                background-color: {BG_COLOR0};
                border-radius: 4px;
                height: 10px;
            }}
            QSlider::sub-page:horizontal {{
                background-color: {BG_COLOR3};
                border-radius: 4px;
                height: 10px;
            }}
        """)
        # 在滑块上显示当前值
        self.valueLabel = QLabel(str(self.value()))
        self.valueLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.valueLabel.setStyleSheet(f"""
            QLabel{{
                background-color: transparent;
                color: {FG_COLOR0};
                border-radius: 0px;
                border: 0px solid {FG_COLOR0};
            }}
        """)
        self.valueLabel.setFont(FONT_8)
        self.valueLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.valueLabel.setFixedSize(30, 20)
        # 值变化绑定
        self.valueChanged.connect(self.valueLabel.setNum)

    # 重写鼠标滚轮
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.setValue(self.value() + 1)
        else:
            self.setValue(self.value() - 1)


class CircleSelectButton(QPushButton):
    def __init__(self, half_size, init_statu=False, color=BG_COLOR1, check_color=BG_COLOR3):
        super().__init__()
        self.half_size = half_size
        self.color = color
        self.check_color = check_color
        self.size = (half_size * 2, half_size * 2)
        set_buttons([self], sizes=self.size, border=1, border_radius=half_size, bg=color, border_color=FG_COLOR0)
        # 事件
        self.setCheckable(True)
        self.setChecked(init_statu)
        self.clicked.connect(self.change_color)

    def change_color(self):
        if self.isChecked():
            self.setChecked(True)
            set_buttons([self], sizes=self.size, border_radius=self.half_size, bg=self.check_color)
        else:
            self.setChecked(False)
            set_buttons([self], sizes=self.size, border=1, border_color=FG_COLOR0, border_radius=self.half_size,
                        bg=self.color)


class CircleSelectButtonGroup:
    """
    用于管理一组圆形选择按钮
    """

    def __init__(self, button_list: List[QPushButton], parent, half_size, color=BG_COLOR1, check_color=BG_COLOR3,
                 default_index=0):
        self.group = button_list
        self.parent = parent
        self.half_size = half_size
        self.color = color
        self.check_color = check_color
        for button in self.group:
            _size = (half_size * 2, half_size * 2)
            set_buttons([button], sizes=_size, border=1, border_radius=half_size, bg=color,
                        border_color=FG_COLOR0)
            # 事件
            button.setCheckable(True)
            button.setChecked(False)
            button.clicked.connect(self.change_color)
        self.group[0].setChecked(True)
        self.selected_bt_index = 0
        if default_index:
            self.group[default_index].setStyleSheet(
                f"border-radius: {half_size}px; background-color: {check_color};")
            self.selected_bt_index = default_index

    def change_color(self):
        self.selected_bt_index = self.group.index(self.parent.sender())
        for i, button in enumerate(self.group):
            if i == self.selected_bt_index:
                button.setChecked(True)
                button.setStyleSheet(
                    f"border-radius: {self.half_size}px; background-color: {self.check_color};")
            else:
                button.setChecked(False)
                button.setStyleSheet(
                    f"border-radius: {self.half_size}px; background-color: {self.color}; border: 1px solid {FG_COLOR0};")


class SelectWidgetGroup:
    def __init__(self, widget_list: List[QPushButton], parent, original_style_sheet, selected_style_sheet):
        """
        给非按钮控件添加选中效果
        :param widget_list:
        :param parent:
        :param original_style_sheet:
        :param selected_style_sheet:
        """
        if len(widget_list) == 0:
            raise Exception("widget_list不能为空")
        self.group = widget_list
        self.parent = parent
        self.original_style_sheet = original_style_sheet
        self.selected_style_sheet = selected_style_sheet
        for widget in self.group:
            widget.setStyleSheet(original_style_sheet)
            widget.clicked.connect(self.change_color)
        self.group[0].setStyleSheet(selected_style_sheet)
        self.selected_bt_index = 0

    def change_color(self):
        self.selected_bt_index = self.group.index(self.parent.sender())
        for i, widget in enumerate(self.group):
            if i == self.selected_bt_index:
                widget.setStyleSheet(self.selected_style_sheet)
            else:
                widget.setStyleSheet(self.original_style_sheet)


class BasicDialog(QDialog):
    def __init__(self, parent=None, border_radius=10, title=None, size=QSize(400, 300), center_layout=None,
                 resizable=False, hide_top=False, hide_bottom=False, ensure_bt_fill=False):
        self.close_bg = b64decode(close)
        self.close_bg = QIcon(QPixmap.fromImage(QImage.fromData(self.close_bg)))
        self._parent = parent
        self._generate_self_parent = False
        if not parent:
            # 此时没有其他控件，但是如果直接显示会导致圆角黑边，所以需要设置一个背景色
            self._parent = QWidget()
            # 设置透明
            self._parent.setAttribute(Qt.WA_TranslucentBackground)
            self._parent.setWindowFlags(Qt.FramelessWindowHint)
            self._parent.setFixedSize(WinWid, WinHei)
            self._parent.move((WinWid - self._parent.width()) / 2, 3 * (WinHei - self._parent.height()) / 7)
            self._parent.show()
            self._generate_self_parent = True
        super().__init__(parent=self._parent)
        self.hide()
        self.setWindowTitle(title)
        self.title = title
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(size)
        self.topH = 35
        self.TitleFont = FONT_10
        self.ContentFont = FONT_15
        # 设置边框阴影
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setBlurRadius(15)
        self.setGraphicsEffect(self.shadow)
        if isinstance(border_radius, int):
            border_command = f"border-radius:{border_radius}px;"
        elif isinstance(border_radius, tuple):
            border_command = f"""
            border-top-left-radius:{border_radius[0]}px;
            border-top-right-radius:{border_radius[1]}px;
            border-bottom-left-radius:{border_radius[2]}px;
            border-bottom-right-radius:{border_radius[3]}px;
            """
        else:
            border_command = f"border-radius:10px;"
        self.setStyleSheet(f"""
            QDialog{{
                background-color:{BG_COLOR1};
                {border_command}
            }}
        """)
        # 设置主题
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        if not hide_top:
            # 顶部栏
            self.top_layout = QHBoxLayout()
            self.close_button = QPushButton()
            self.add_top_bar()
            # 分割线
            spl = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
            spl.setStyleSheet(f"background-color:{BG_COLOR0};")
            self.main_layout.addWidget(spl, alignment=Qt.AlignTop)
        # 主体-----------------------------------------------------------------------------------------------
        self._center_layout = center_layout
        self.init_center_layout()
        self.main_layout.addStretch(1)
        if not hide_bottom:
            if not hide_top:
                # 分割线
                spl2 = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
                spl2.setStyleSheet(f"background-color:{BG_COLOR0};")
                self.main_layout.addWidget(spl2, alignment=Qt.AlignTop)
            # 底部（按钮）
            self.bottom_layout = QHBoxLayout()
            if not ensure_bt_fill:
                self.cancel_button = QPushButton('取消')
            self.ensure_button = QPushButton('确定')
            self.add_bottom_bar(ensure_bt_fill)
        # 移动到屏幕中央
        self.move((WinWid - self.width()) / 2, 3 * (WinHei - self.height()) / 7)
        # 给top_layout的区域添加鼠标拖动功能
        self.m_flag = False
        self.m_Position = None
        self.drag = None  # 初始化拖动条
        self.resizable = resizable
        if resizable:
            # 添加缩放功能，当鼠标移动到窗口边缘时，鼠标变成缩放样式
            self.drag = [False, False, False, False]  # 用于判断鼠标是否在窗口边缘
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)  # 设置窗口无边框
            self.setMouseTracking(True)  # 设置widget鼠标跟踪
            self.resize_flag = False  # 用于判断是否拉伸窗口
            self.resize_dir = None  # 用于判断拉伸窗口的方向
            self.resize_area = 5  # 用于判断鼠标是否在边缘区域
            self.resize_min_size = QSize(200, 200)
            self.resize_max_size = QSize(WinWid, WinHei)

    @abstractmethod
    def ensure(self):
        self.close()

    def close(self):
        super().close()
        if self._generate_self_parent:
            self._parent.close()

    def add_top_bar(self):
        # 布局
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(0)
        self.main_layout.addLayout(self.top_layout)
        self.top_layout.addStretch(1)
        text_label = QLabel(self.title)
        text_label.setFont(self.TitleFont)
        text_label.setStyleSheet(f"color:{FG_COLOR0};")
        self.top_layout.addWidget(text_label, alignment=Qt.AlignCenter)
        self.top_layout.addStretch(1)
        # 按钮
        cb_size = (self.topH + 10, self.topH)
        self.close_button.setIcon(self.close_bg)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        set_buttons([self.close_button], sizes=cb_size, border=0, bg=(BG_COLOR1, "#F76677", "#F76677", "#F76677"))
        self.close_button.clicked.connect(self.close)
        self.top_layout.addWidget(self.close_button, alignment=Qt.AlignRight)

    def init_center_layout(self):
        self.main_layout.addLayout(self._center_layout, stretch=1)

    def add_bottom_bar(self, ensure_bt_fill):
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setSpacing(0)
        self.main_layout.addLayout(self.bottom_layout)
        self.bottom_layout.addStretch(1)
        if not ensure_bt_fill:
            self.bottom_layout.addWidget(self.cancel_button)
            self.bottom_layout.addWidget(self.ensure_button)
            set_buttons([self.cancel_button], sizes=(80, 30), border=0, border_radius=10,
                        bg=(BG_COLOR1, "#F76677", "#F76677", BG_COLOR2))
            set_buttons([self.ensure_button], sizes=(80, 30), border=0, border_radius=10,
                        bg=(BG_COLOR1, "#6DDF6D", "#6DDF6D", BG_COLOR2))
            self.cancel_button.clicked.connect(self.close)
            self.ensure_button.clicked.connect(self.ensure)
            self.ensure_button.setFocus()
        else:
            self.bottom_layout.addWidget(self.ensure_button)
            set_buttons([self.ensure_button], sizes=(300, 35), border=0, border_radius=(0, 0, 15, 15),
                        bg=(BG_COLOR2, "#6DDF6D", "#6DDF6D", BG_COLOR2))
            self.ensure_button.setFocusPolicy(Qt.NoFocus)
            self.ensure_button.clicked.connect(self.ensure)

    def mousePressEvent(self, event):
        # 鼠标按下时，记录当前位置，若在标题栏内且非最大化，则允许拖动
        if event.button() == Qt.LeftButton and event.y() < self.topH and self.isMaximized() is False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()
            event.accept()
        elif event.button() == Qt.LeftButton and self.resizable:
            self.resize_flag = True
            self.m_Position = event.globalPos()
            _pos = event.pos()
            # 判断鼠标所在的位置是否为边缘
            if _pos.x() < self.resize_area:
                self.drag[0] = True
            if _pos.x() > self.width() - self.resize_area:
                self.drag[1] = True
            if _pos.y() < self.resize_area:
                self.drag[2] = True
            if _pos.y() > self.height() - self.resize_area:
                self.drag[3] = True
            # 判断鼠标所在的位置是否为角落
            if _pos.x() < self.resize_area and _pos.y() < self.resize_area:
                self.resize_dir = 'lt'
            elif _pos.x() < self.resize_area and _pos.y() > self.height() - self.resize_area:
                self.resize_dir = 'lb'
            elif _pos.x() > self.width() - self.resize_area and _pos.y() < self.resize_area:
                self.resize_dir = 'rt'
            elif _pos.x() > self.width() - self.resize_area and _pos.y() > self.height() - self.resize_area:
                self.resize_dir = 'rb'
            event.accept()
        self.update()

    def mouseReleaseEvent(self, QMouseEvent):
        # 拖动窗口时，鼠标释放后停止拖动
        self.m_flag = False if self.m_flag else self.m_flag
        if self.resizable:
            self.resize_flag = False if self.resize_flag else self.resize_flag
            self.drag = [False, False, False, False]
            self.resize_dir = None

    def mouseMoveEvent(self, QMouseEvent):
        # 当鼠标在标题栏按下且非最大化时，移动窗口
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)
            QMouseEvent.accept()
        if self.resizable:
            # 检查是否需要改变鼠标样式
            _pos = QMouseEvent.pos()
            if _pos.x() < self.resize_area:
                self.setCursor(Qt.SizeHorCursor)
            elif _pos.x() > self.width() - self.resize_area:
                self.setCursor(Qt.SizeHorCursor)
            elif _pos.y() < self.resize_area:
                self.setCursor(Qt.SizeVerCursor)
            elif _pos.y() > self.height() - self.resize_area:
                self.setCursor(Qt.SizeVerCursor)
            elif _pos.x() < self.resize_area and _pos.y() < self.resize_area:
                self.setCursor(Qt.SizeFDiagCursor)
            elif _pos.x() < self.resize_area and _pos.y() > self.height() - self.resize_area:
                self.setCursor(Qt.SizeBDiagCursor)
            elif _pos.x() > self.width() - self.resize_area and _pos.y() < self.resize_area:
                self.setCursor(Qt.SizeBDiagCursor)
            elif _pos.x() > self.width() - self.resize_area and _pos.y() > self.height() - self.resize_area:
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            # 检查是否需要拉伸窗口
            if self.resize_flag:
                _pos = QMouseEvent.pos()
                _dx = QMouseEvent.globalPos().x() - self.m_Position.x()
                _dy = QMouseEvent.globalPos().y() - self.m_Position.y()
                if self.resize_dir == 'lt':
                    self.setGeometry(self.x() + _dx, self.y() + _dy, self.width() - _dx, self.height() - _dy)
                elif self.resize_dir == 'lb':
                    self.setGeometry(self.x() + _dx, self.y(), self.width() - _dx, _dy)
                elif self.resize_dir == 'rt':
                    self.setGeometry(self.x(), self.y() + _dy, self.width() + _dx, self.height() - _dy)
                elif self.resize_dir == 'rb':
                    self.setGeometry(self.x(), self.y(), self.width() + _dx, self.height() + _dy)
                elif self.resize_dir == 't':
                    self.setGeometry(self.x(), self.y() + _dy, self.width(), self.height() - _dy)
                elif self.resize_dir == 'l':
                    self.setGeometry(self.x() + _dx, self.y(), self.width() - _dx, self.height())
                elif self.resize_dir == 'r':
                    self.setGeometry(self.x(), self.y(), self.width() + _dx, self.height())
                elif self.resize_dir == 'b':
                    self.setGeometry(self.x(), self.y(), self.width(), self.height() + _dy)
                self.m_Position = QMouseEvent.globalPos()
                QMouseEvent.accept()

    def _animate(self):
        animation = QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(1)
        self.show()
        animation.start()


class ShortCutWidget(QWidget):
    def __init__(self):
        _font = FONT_8
        _color = GRAY
        self.shortcut_labels = [
            MyLabel("全视图模式 1", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("横剖面模式 2", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("纵剖面模式 3", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("左视图模式 4", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("选区上移 Alt+ ↑", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("选区下移 Alt+ ↓", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("选区左移 Alt+←", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
            MyLabel("选区右移 Alt+→", _font, color=_color, side=Qt.AlignTop | Qt.AlignLeft),
        ]
        super().__init__()
        self.layout = QGridLayout()
        self.layout.setContentsMargins(15, 5, 15, 5)
        self.layout.setHorizontalSpacing(20)
        self.setLayout(self.layout)
        total_row = len(self.shortcut_labels) // 4
        self.layout.addWidget(  # 居中显示
            MyLabel("快捷键：", FONT_9, color=GRAY, side=Qt.AlignTop | Qt.AlignHCenter), 0, 0, 1, total_row
        )
        for i in range(len(self.shortcut_labels)):
            _l = i % 4 + 1
            _r = i // 4
            self.layout.addWidget(self.shortcut_labels[i], _l, _r)


class ColorSlider(QSlider):
    H = "h"
    S = "s"
    L = "l"

    def __init__(self, _type, height=30):
        super().__init__(Qt.Horizontal)
        # 设置track不可见
        self.hei = height
        self.hue_slider = None
        self.saturation_slider = None
        self.lightness_slider = None
        self.type = _type

    def init_slider(self, hue_slider, saturation_slider, lightness):
        self.hue_slider = hue_slider
        self.saturation_slider = saturation_slider
        self.lightness_slider = lightness
        if self.type == ColorSlider.H:
            self.setRange(0, 359)
            self.setValue(180)
        elif self.type == ColorSlider.S:
            self.setRange(0, 255)
            self.setValue(0)
        elif self.type == ColorSlider.L:
            self.setRange(0, 255)
            self.setValue(127)
        self.setFixedSize(400, self.hei)

    def mousePressEvent(self, event):
        # 将颜色直接设置到鼠标点击的位置
        if event.button() == Qt.LeftButton:
            value = int(event.x() / self.width() * self.maximum())
            self.setValue(value)
            self.update()

    def mouseMoveEvent(self, event):
        # 将颜色直接设置到鼠标点击的位置
        if event.buttons() == Qt.LeftButton:
            value = int(event.x() / self.width() * self.maximum())
            self.setValue(value)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = QRect(0, 5, self.width(), self.hei - 10)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        if self.type == ColorSlider.H:
            for i in range(0, 360):
                gradient.setColorAt(i / 360, QColor.fromHsl(i, 255, 127))
        elif self.type == ColorSlider.S:
            l_color = QColor.fromHsl(self.hue_slider.value(), 0, self.lightness_slider.value())
            r_color = QColor.fromHsl(self.hue_slider.value(), 255, self.lightness_slider.value())
            gradient.setColorAt(0, l_color)
            gradient.setColorAt(1, r_color)
        elif self.type == ColorSlider.L:
            for i in range(0, 256):
                gradient.setColorAt(i / 255, QColor.fromHsl(self.hue_slider.value(), self.saturation_slider.value(), i))
        painter.fillRect(rect, gradient)
        # 绘制游标
        pos_x = int(self.value() / self.maximum() * self.width())
        # 半透明矩形
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 127))
        painter.drawRect(pos_x - 6, 5, 12, self.hei - 10)
        # 绘制游标上的三角形（FG_COLOR0）
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(FG_COLOR0))
        painter.drawPolygon(QPolygon([
            QPoint(pos_x - 5, 0),
            QPoint(pos_x + 5, 0),
            QPoint(pos_x, 5),
        ]))

    def update(self):
        self.repaint()
        super().update()


class HSLColorPicker(QWidget):
    def __init__(self):
        self.current_color = QColor.fromHsl(180, 255, 127)
        self.updating = False
        super().__init__()
        self.layout = QVBoxLayout()
        self.HSL_layout = QGridLayout()
        self.layoutContentMargins = (10, 10, 10, 10)
        self.layoutVerticalSpacing = 10
        self.layoutHorizontalSpacing = 20
        self.sliderHei = 30
        self.hue_slider = ColorSlider(ColorSlider.H, self.sliderHei)
        self.hue_label = MyLabel("色相:")
        self.saturation_slider = ColorSlider(ColorSlider.S, self.sliderHei)
        self.saturation_label = MyLabel("饱和:")
        self.lightness_slider = ColorSlider(ColorSlider.L, self.sliderHei)
        self.brightness_label = MyLabel("明度:")
        self.hue_slider.init_slider(self.hue_slider, self.saturation_slider, self.lightness_slider)
        self.saturation_slider.init_slider(self.hue_slider, self.saturation_slider, self.lightness_slider)
        self.lightness_slider.init_slider(self.hue_slider, self.saturation_slider, self.lightness_slider)
        self.color_preview = QLabel()
        # 下方RBG色值显示
        self.message_layout = QHBoxLayout()
        self.RGB_layout = QGridLayout()
        self.labelR = MyLabel("R:")
        self.labelG = MyLabel("G:")
        self.labelB = MyLabel("B:")
        self.labelR_value = MyLineEdit()
        self.labelG_value = MyLineEdit()
        self.labelB_value = MyLineEdit()
        # 设置值范围
        self.labelR_value.setValidator(QIntValidator(0, 255))
        self.labelG_value.setValidator(QIntValidator(0, 255))
        self.labelB_value.setValidator(QIntValidator(0, 255))
        self.initUI()

    def initUI(self):
        self.initHSL()
        self.initMessage()
        self.setLayout(self.layout)

    def initHSL(self):
        self.HSL_layout.setContentsMargins(*self.layoutContentMargins)
        self.HSL_layout.setVerticalSpacing(self.layoutVerticalSpacing)
        self.HSL_layout.setHorizontalSpacing(self.layoutHorizontalSpacing)
        self.HSL_layout.setAlignment(Qt.AlignCenter)
        color_preview_r = 3 * self.sliderHei + 2 * self.layoutVerticalSpacing - 8
        self.color_preview.setFixedSize(color_preview_r, color_preview_r)
        self.color_preview.setStyleSheet(f"""
            QLabel{{
                border-radius: 10px;
                background-color: {BG_COLOR1};
                border: 0px solid {BG_COLOR1};
            }}
        """)
        self.update_color()

        self.hue_slider.valueChanged.connect(self.update_color)
        self.saturation_slider.valueChanged.connect(self.update_color)
        self.lightness_slider.valueChanged.connect(self.update_color)

        self.HSL_layout.addWidget(self.hue_label, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.HSL_layout.addWidget(self.hue_slider, 0, 1, alignment=Qt.AlignCenter)
        self.HSL_layout.addWidget(self.saturation_label, 1, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.HSL_layout.addWidget(self.saturation_slider, 1, 1, alignment=Qt.AlignCenter)
        self.HSL_layout.addWidget(self.brightness_label, 2, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.HSL_layout.addWidget(self.lightness_slider, 2, 1, alignment=Qt.AlignCenter)
        self.HSL_layout.addWidget(self.color_preview, 0, 2, 3, 1, alignment=Qt.AlignCenter)
        self.layout.addLayout(self.HSL_layout)

    def mousePressEvent(self, event):
        # 鼠标在控件外的时候，取色
        if event.button() == Qt.LeftButton:
            if not self.rect().contains(event.pos()):
                print("取色")
                # 获取鼠标位置的颜色
                _pos = event.globalPos()
                _color = QColor.fromRgb(QPixmap.grabWindow(QApplication.desktop().winId()).toImage().pixel(_pos))
                self.current_color = _color
                # 移动滑动条
                _h = self.current_color.hue()
                _s = self.current_color.saturation()
                _l = self.current_color.lightness()
                self.hue_slider.setValue(_h)
                self.saturation_slider.setValue(_s)
                self.lightness_slider.setValue(_l)
                # 更新RGB值
                self.labelR_value.setText(str(self.current_color.red()))
                self.labelG_value.setText(str(self.current_color.green()))
                self.labelB_value.setText(str(self.current_color.blue()))

    def initMessage(self):
        self.message_layout.setContentsMargins(0, 0, 0, 0)
        self.RGB_layout.setContentsMargins(25, 0, 25, 0)
        self.RGB_layout.setVerticalSpacing(5)
        self.RGB_layout.setHorizontalSpacing(10)
        self.RGB_layout.setAlignment(Qt.AlignCenter)
        self.labelR_value.setFixedSize(50, 30)
        self.labelG_value.setFixedSize(50, 30)
        self.labelB_value.setFixedSize(50, 30)

        self.RGB_layout.addWidget(self.labelR, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.RGB_layout.addWidget(self.labelR_value, 0, 1, alignment=Qt.AlignCenter)
        self.RGB_layout.addWidget(self.labelG, 1, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.RGB_layout.addWidget(self.labelG_value, 1, 1, alignment=Qt.AlignCenter)
        self.RGB_layout.addWidget(self.labelB, 2, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.RGB_layout.addWidget(self.labelB_value, 2, 1, alignment=Qt.AlignCenter)

        # 绑定到输入事件
        self.labelR_value.textChanged.connect(self.update_rgb_color)
        self.labelG_value.textChanged.connect(self.update_rgb_color)
        self.labelB_value.textChanged.connect(self.update_rgb_color)

        self.message_layout.addStretch(1)
        self.message_layout.addLayout(self.RGB_layout)
        self.layout.addLayout(self.message_layout)

    def update_color(self):
        if self.updating:
            return
        self.updating = True
        hue = self.hue_slider.value()
        saturation = self.saturation_slider.value()
        lightness = self.lightness_slider.value()

        self.current_color = QColor.fromHsl(hue, saturation, lightness)
        # 更新滑动条颜色
        self.hue_slider.update()
        self.saturation_slider.update()
        self.lightness_slider.update()
        # 更新RGB值
        self.labelR_value.setText(str(self.current_color.red()))
        self.labelG_value.setText(str(self.current_color.green()))
        self.labelB_value.setText(str(self.current_color.blue()))
        self.update_color_preview()
        self.updating = False

    def update_rgb_color(self):
        if self.updating:
            return
        self.updating = True
        try:
            r = int(self.labelR_value.text())
            g = int(self.labelG_value.text())
            b = int(self.labelB_value.text())
        except ValueError:
            return
        self.current_color = QColor(r, g, b)
        # 移动滑动条
        _h = self.current_color.hue()
        _s = self.current_color.saturation()
        _l = self.current_color.lightness()
        _hsl_color = QColor.fromHsl(_h, _s, _l)
        self.hue_slider.setValue(_h)
        self.saturation_slider.setValue(_s)
        self.lightness_slider.setValue(_l)
        self.update_color_preview()
        self.updating = False

    def update_color_preview(self):
        self.color_preview.setStyleSheet(f"""
            QLabel{{
                border-radius: 10px;
                background-color: {self.current_color.name()};
                border: 0px solid {BG_COLOR1};
            }}
        """)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    mainWin = QWidget()
    mainLayout = QVBoxLayout()
    mainWin.setLayout(mainLayout)
    mainWin.setWindowTitle('HSL取色器')
    mainWin.setGeometry(450, 300, 450, 300)
    mainWin.setStyleSheet(f"""
        QWidget{{
            background-color:{BG_COLOR1};
            color:{FG_COLOR0};
        }}
    """)
    mainWin.show()
    ex = HSLColorPicker()
    mainLayout.addWidget(ex)
    sys.exit(app.exec_())
