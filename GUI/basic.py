# -*- coding: utf-8 -*-
"""
将会被多次使用的基础类
"""
# 内置库
import ctypes
import json
import os
from abc import abstractmethod
# 第三方库
from typing import List

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QImage, QColor, QFont, QPalette
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QMessageBox, QDialog, QToolBar
from PyQt5.QtWidgets import QLineEdit, QComboBox, QSlider, QPushButton
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from base64 import b64decode
# 本地库
from path_utils import find_na_root_path

# 读取配置文件中的主题信息
_path = os.path.join(find_na_root_path(), 'plugin_config.json')
try:
    with open(_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    Theme = data['Config']['Theme']
    ProjectFolder = data['ProjectsFolder']
except:
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
FONT_7 = QFont(YAHEI, 7)  # 设置字体
FONT_8 = QFont(YAHEI, 8)  # 设置字体
FONT_9 = QFont(YAHEI, 9)  # 设置字体
FONT_10 = QFont(YAHEI, 10)  # 设置字体
FONT_11 = QFont(YAHEI, 11)  # 设置字体
FONT_12 = QFont(YAHEI, 12)  # 设置字体
FONT_13 = QFont(YAHEI, 13)  # 设置字体
FONT_14 = QFont(YAHEI, 14)  # 设置字体
FONT_15 = QFont(YAHEI, 15)  # 设置字体
FONT_16 = QFont(YAHEI, 16)  # 设置字体
FONT_17 = QFont(YAHEI, 17)  # 设置字体
FONT_18 = QFont(YAHEI, 18)  # 设置字体
FONT_19 = QFont(YAHEI, 19)  # 设置字体
FONT_20 = QFont(YAHEI, 20)  # 设置字体
FONT_21 = QFont(YAHEI, 21)  # 设置字体
FONT_22 = QFont(YAHEI, 22)  # 设置字体
LOCAL_ADDRESS = os.path.dirname(os.path.abspath(__file__))
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 设置高分辨率
user32 = ctypes.windll.user32
WinWid = user32.GetSystemMetrics(0)  # 获取分辨率
WinHei = user32.GetSystemMetrics(1)  # 获取分辨率
RATE = WinWid / 1920


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


def set_button_style(button, size: tuple, font=FONT_14, style="普通", active_color='gray', icon=None):
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
        button.setStyleSheet(f'QPushButton{{border:none;color:{FG_COLOR0};font-size:14px;'
                             f'color:{FG_COLOR0};'
                             f'font-family:{YAHEI};}}'
                             f'QPushButton:hover{{background-color:{active_color};}}')
    elif style == "圆角边框":
        button.setStyleSheet(f'QPushButton{{border-radius:5px;border:1px solid gray;color:{FG_COLOR0};'
                             f'color:{FG_COLOR0};'
                             f'font-size:14px;font-family:{YAHEI};}}'
                             f'QPushButton:hover{{background-color:{active_color};}}')
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
    button.setFont(QFont('微软雅黑', 8))
    # 设置样式：圆角、背景色、边框
    button.setStyleSheet(
        f"QPushButton{{background-color: {BG_COLOR0};"
        f"color: {FG_COLOR0};"
        f"border-radius: 0px;"
        f"border: 1px solid {BG_COLOR0};}}"
        # 鼠标悬停样式
        f"QPushButton:hover{{background-color: {BG_COLOR3};"
        f"color: {FG_COLOR0};"
        f"border-radius: 0px;"
        f"border: 1px solid {BG_COLOR3};}}"
        # 鼠标按下样式
        f"QPushButton:pressed{{background-color: {BG_COLOR2};"
        f"color: {FG_COLOR0};"
        f"border-radius: 0px;"
        f"border: 1px solid {BG_COLOR2};}}"
    )
    # 设置大小
    button.setFixedSize(width, 30)


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


class MyMessageBox(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            # 设置以自己为父的QMessageBox的样式
            f"QMessageBox{{background-color: {BG_COLOR1};"
            f"color: {FG_COLOR0};"
            f"border: 1px solid {FG_COLOR2};"
            f"border-radius: 5px;}}"
            # 设置QMessageBox的按钮样式
            f"QMessageBox QPushButton{{background-color: {BG_COLOR1};"
            f"color: {FG_COLOR0};"
            f"border: 1px solid {FG_COLOR2};"
            f"border-radius: 5px;}}"
            f"QMessageBox QPushButton:hover{{background-color: {BG_COLOR3};"
            f"color: {FG_COLOR0};"
            f"border: 1px solid {FG_COLOR2};"
            f"border-radius: 5px;}}"
            # 设置QMessageBox的输入框样式
            f"QMessageBox QLineEdit{{background-color: {BG_COLOR1};"
            f"color: {FG_COLOR0};"
            f"border: 1px solid {FG_COLOR2};"
            f"border-radius: 5px;}}"
            # 设置QMessageBox的输入框样式
            f"QMessageBox QComboBox{{background-color: {BG_COLOR1};"
            f"color: {FG_COLOR0};"
            f"border: 1px solid {FG_COLOR2};"
            f"border-radius: 5px;}}"
        )
        # 设置按钮
        self.setStandardButtons(QMessageBox.Yes)
        self.button(QMessageBox.Yes).setCursor(Qt.PointingHandCursor)


class MyLabel(QLabel):
    def __init__(self, text, font=QFont("微软雅黑", 9), color=FG_COLOR0, side=Qt.AlignLeft | Qt.AlignVCenter):
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
        self.setStyleSheet(
            f"QSlider::groove:horizontal{{background-color:{BG_COLOR2};"  # 滑块背景颜色
            "border-radius:4px;"
            "height:10px;"
            "margin:1px 1px;}}"
            f"QSlider::handle:horizontal{{background-color:{BG_COLOR3};"  # 滑块颜色
            "border-radius:4px;"
            "width:10px;"
            "margin:-10px 0px -10px 0px;}}"
            f"QSlider::add-page:horizontal{{background-color:{BG_COLOR3};"  # 滑块右边颜色
            "border-radius:4px;"
            "height:10px;}}"
            f"QSlider::sub-page:horizontal{{background-color:{BG_COLOR3};"  # 滑块左边颜色
            "border-radius:4px;"
            "height:10px;}}"
        )
        # 在滑块上显示当前值
        self.valueLabel = QLabel(str(self.value()))
        self.valueLabel.setAttribute(Qt.WA_TranslucentBackground)
        self.valueLabel.setStyleSheet(f"color:{FG_COLOR0};")
        self.valueLabel.setFont(QFont("微软雅黑", 8))
        self.valueLabel.setFixedSize(50, 20)
        self.valueLabel.setParent(self)
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
        self.setFixedSize(half_size * 2, half_size * 2)
        self.setStyleSheet(
            f"border-radius: {half_size}px; background-color: {color}; border: 1px solid {FG_COLOR0};")
        # 事件
        self.setCheckable(True)
        self.setChecked(init_statu)
        self.clicked.connect(self.change_color)

    def change_color(self):
        if self.isChecked():
            self.setChecked(True)
            self.setStyleSheet(
                f"border-radius: {self.half_size}px; background-color: {self.check_color};")
        else:
            self.setChecked(False)
            self.setStyleSheet(
                f"border-radius: {self.half_size}px; background-color: {self.color}; border: 1px solid {FG_COLOR0};")


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
            button.setFixedSize(half_size * 2, half_size * 2)
            button.setStyleSheet(
                f"border-radius: {half_size}px; background-color: {color}; border: 1px solid {FG_COLOR0};")
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
    def __init__(self, widget_list: List[QWidget], parent, original_style_sheet, selected_style_sheet):
        """
        给非按钮控件添加选中效果
        :param widget_list:
        :param parent:
        :param original_style_sheet:
        :param selected_style_sheet:
        """
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
                 resizable=False, hide_bottom=False):
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
        self.setWindowTitle(title)
        self.title = title
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedSize(size)
        self.topH = 35
        self.TitleFont = QFont("微软雅黑", 10)
        self.ContentFont = QFont("微软雅黑", 15)
        # 设置边框阴影
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setBlurRadius(15)
        self.setGraphicsEffect(self.shadow)
        if isinstance(border_radius, int):
            self.setStyleSheet(f"background-color:{BG_COLOR1}; border-radius:{border_radius}px;")
        elif isinstance(border_radius, tuple):
            self.setStyleSheet(f"background-color:{BG_COLOR1};"
                               f"border-top-left-radius:{border_radius[0]}px;"
                               f"border-top-right-radius:{border_radius[1]}px;"
                               f"border-bottom-left-radius:{border_radius[2]}px;"
                               f"border-bottom-right-radius:{border_radius[3]}px;")
        else:
            self.setStyleSheet(f"background-color:{BG_COLOR1}; border-radius:10px;")
        # 设置主题
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
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
            # 分割线
            spl2 = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
            spl2.setStyleSheet(f"background-color:{BG_COLOR0};")
            self.main_layout.addWidget(spl2, alignment=Qt.AlignTop)
            # 底部（按钮）
            self.bottom_layout = QHBoxLayout()
            self.cancel_button = QPushButton('取消')
            self.ensure_button = QPushButton('确定')
            self.add_bottom_bar()
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
        self.close_button.setFixedSize(self.topH + 10, self.topH)
        self.close_button.setIcon(self.close_bg)
        self.close_button.setIconSize(QSize(20, 20))
        self.close_button.setStyleSheet('QPushButton{border:none;}'
                                        'QPushButton:hover{background-color:red;}')
        self.close_button.clicked.connect(self.close)
        self.top_layout.addWidget(self.close_button, alignment=Qt.AlignRight)

    def init_center_layout(self):
        self.main_layout.addLayout(self._center_layout, stretch=1)

    def add_bottom_bar(self):
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setSpacing(0)
        self.main_layout.addLayout(self.bottom_layout)
        self.bottom_layout.addStretch(1)
        self.bottom_layout.addWidget(self.cancel_button)
        self.bottom_layout.addWidget(self.ensure_button)
        # 按钮样式
        self.cancel_button.setFixedSize(80, 30)
        self.ensure_button.setFixedSize(80, 30)
        set_button_style(self.cancel_button, size=(80, 30), active_color="#F76677")  # "#F76677"
        set_button_style(self.ensure_button, size=(80, 30), active_color="#6DDF6D")  # "#6DDF6D"
        self.cancel_button.clicked.connect(self.close)
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


class ShortCutWidget(QWidget):
    def __init__(self):
        _font = QFont('微软雅黑', 8)
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
            MyLabel("快捷键：", QFont('微软雅黑', 9), color=GRAY, side=Qt.AlignTop | Qt.AlignHCenter), 0, 0, 1, total_row
        )
        for i in range(len(self.shortcut_labels)):
            _l = i % 4 + 1
            _r = i // 4
            self.layout.addWidget(self.shortcut_labels[i], _l, _r)
