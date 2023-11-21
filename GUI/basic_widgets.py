# -*- coding: utf-8 -*-
"""
基础控件
"""
from typing import Union, List, Tuple, Type

from basic_data import *

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *


class TextLabel(QLabel):
    def __init__(self, parent, text, font=YAHEI[9], color=FG_COLOR0, align=Qt.AlignLeft | Qt.AlignVCenter):
        super().__init__(parent=parent, text=text)
        self.text = text
        self.setFont(font)
        self.setStyleSheet(f"color:{color};")
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setAlignment(align)

    def set_text(self, text, color: str = None):
        self.text = text
        if color:
            self.setStyleSheet(f"color:{color};")
        self.setText(text)


class Button(QPushButton):
    def __init__(
            self, parent,
            tool_tip: str = None,
            bd: Union[int, Tuple[int, int, int, int]] = 0,
            bd_color: Union[str, Tuple[str, str, str, str]] = FG_COLOR0,
            bd_radius: Union[int, Tuple[int, int, int, int]] = 0,
            padding: Union[int, Tuple[int, int, int, int]] = 0,
            bg: Union[str, Tuple[str, str, str, str]] = BG_COLOR0,
            fg: Union[str, Tuple[str, str, str, str]] = FG_COLOR0,
            font=YAHEI[10],
            align=Qt.AlignCenter,
            size: Union[int, Tuple[int, int]] = (65, 30),
    ):
        super().__init__(parent)
        # 处理参数
        if bd != 0:
            bd_text = f"{bd}px solid {bd_color}"
        else:
            bd_text = "none"
        if isinstance(bd_radius, int):
            bd_radius = [bd_radius] * 4
        if isinstance(bg, str):
            bg = [bg] * 4
        if isinstance(fg, str):
            fg = [fg] * 4
        if isinstance(padding, int):
            padding = [padding] * 4
        self.setFont(font)
        self.setStyleSheet(f"""
                    QPushButton{{
                        background-color:{bg[0]};
                        color:{fg[0]};
                        border-top-left-radius: {bd_radius[0]}px;
                        border-top-right-radius: {bd_radius[1]}px;
                        border-bottom-right-radius: {bd_radius[2]}px;
                        border-bottom-left-radius: {bd_radius[3]}px;
                        border: {bd_text};
                        padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
                    }}
                    QPushButton:hover{{
                        background-color:{bg[1]};
                        color:{fg[1]};
                        border-top-left-radius: {bd_radius[0]}px;
                        border-top-right-radius: {bd_radius[1]}px;
                        border-bottom-right-radius: {bd_radius[2]}px;
                        border-bottom-left-radius: {bd_radius[3]}px;
                        border: {bd_text};
                        padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
                    }}
                    QPushButton::pressed{{
                        background-color:{bg[2]};
                        color:{fg[2]};
                        border-top-left-radius: {bd_radius[0]}px;
                        border-top-right-radius: {bd_radius[1]}px;
                        border-bottom-right-radius: {bd_radius[2]}px;
                        border-bottom-left-radius: {bd_radius[3]}px;
                        border: {bd_text};
                        padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
                    }}
                    QPushButton::focus{{
                        background-color:{bg[3]};
                        color:{fg[3]};
                        border-top-left-radius: {bd_radius[0]}px;
                        border-top-right-radius: {bd_radius[1]}px;
                        border-bottom-right-radius: {bd_radius[2]}px;
                        border-bottom-left-radius: {bd_radius[3]}px;
                        border: {bd_text};
                        padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
                    }}
                    QPushButton::disabled{{
                        background-color:{bg[0]};
                        color: gray;
                        border-top-left-radius: {bd_radius[0]}px;
                        border-top-right-radius: {bd_radius[1]}px;
                        border-bottom-right-radius: {bd_radius[2]}px;
                        border-bottom-left-radius: {bd_radius[3]}px;
                        border: 1px solid gray;
                        padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
                    }}
                    QPushButton::checked{{
                        background-color:{bg[2]};
                        color:{fg[2]};
                        border-top-left-radius: {bd_radius[0]}px;
                        border-top-right-radius: {bd_radius[1]}px;
                        border-bottom-right-radius: {bd_radius[2]}px;
                        border-bottom-left-radius: {bd_radius[3]}px;
                        border: {bd_text};
                        padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
                    }}
                """)
        self.setAlignment(align)
        self.setFixedSize(size[0], size[1])
        if tool_tip:
            self.setToolTip(tool_tip)
            self.setToolTipDuration(5000)


class TextButton(Button):
    def __init__(
            self, parent,
            text: str = '',
            tool_tip: str = None,
            bd: Union[int, Tuple[int, int, int, int]] = 0,
            bd_color: Union[str, Tuple[str, str, str, str]] = FG_COLOR0,
            bd_radius: Union[int, Tuple[int, int, int, int]] = 0,
            padding: Union[int, Tuple[int, int, int, int]] = 0,
            bg: Union[str, Tuple[str, str, str, str]] = BG_COLOR0,
            fg: Union[str, Tuple[str, str, str, str]] = FG_COLOR0,
            font=YAHEI[10],
            align=Qt.AlignCenter,
            size: Union[int, Tuple[int, int]] = (65, 30),
            __set_text: bool = True
    ):
        self.text = text
        # 设置样式
        if __set_text:
            self.setText(text)
        super().__init__(parent, tool_tip, bd, bd_color, bd_radius, padding, bg, fg, font, align, size)


class BorderRadiusImage(QLabel):
    def __init__(self, parent, img_bytes: bytes, img_size: Union[int, Tuple[int, int]], bd_radius: int = 0,
                 bg: str = BG_COLOR0, tool_tip=None):
        super().__init__(parent)
        # 处理参数
        if isinstance(img_size, int):
            self.width, self.height = img_size, img_size
        else:
            self.width, self.height = img_size[0], img_size[1]
        self.img_bytes = img_bytes
        self.bd_radius = bd_radius
        self.bg = bg

        img = QPixmap(QImage.fromData(QByteArray(self.img_bytes)))
        img.scaled(self.width, self.height, Qt.KeepAspectRatio)
        rounded_img = QPixmap(self.width, self.height)
        rounded_img.fill(Qt.transparent)
        painter = QPainter(rounded_img)
        painter.setRenderHint(QPainter.Antialiasing)
        # 创建一个椭圆路径来表示圆角
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, self.bd_radius, self.bd_radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, img)
        painter.end()
        self.setPixmap(rounded_img)
        self.setStyleSheet(
            f"background-color: {self.bg};"
            f"border-radius: {self.bd_radius}px;"
        )
        self.setFixedSize(self.width, self.height)
        if tool_tip:
            self.setToolTip(tool_tip)
            self.setToolTipDuration(5000)


class ImageButton(QPushButton):
    def __init__(self, parent, img_bytes: bytes, img_size: Union[int, Tuple[int, int]], bd_radius: int = 0, bg: str = BG_COLOR0, tool_tip=None):
        super().__init__(parent)
        # 处理参数
        if isinstance(img_size, int):
            self.width, self.height = img_size, img_size
        else:
            self.width, self.height = img_size[0], img_size[1]
        self.img_bytes = img_bytes
        self.bd_radius = bd_radius
        self.bg = bg

        img = QPixmap(QImage.fromData(QByteArray(self.img_bytes)))
        img.scaled(self.width, self.height, Qt.KeepAspectRatio)
        rounded_img = QPixmap(self.width, self.height)
        rounded_img.fill(Qt.transparent)
        painter = QPainter(rounded_img)
        painter.setRenderHint(QPainter.Antialiasing)
        # 创建一个椭圆路径来表示圆角
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, self.bd_radius, self.bd_radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, img)
        painter.end()
        self.setPixmap(rounded_img)
        self.setStyleSheet(
            f"background-color: {self.bg};"
            f"border-radius: {self.bd_radius}px;"
        )
        self.setFixedSize(self.width, self.height)
        if tool_tip:
            self.setToolTip(tool_tip)
            self.setToolTipDuration(5000)


class MaximizeButton(Button):
    def __init__(self, parent, size, bd_radius):
        super().__init__(parent, "最大化", 0, BG_COLOR0,
                         bd_radius, 0,
                         (BG_COLOR1, "#F76677", "#F76677", "#F76677"), FG_COLOR0, YAHEI[9], Qt.AlignCenter, size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("最大化")
        self.setToolTipDuration(5000)


class MinimizeButton(QPushButton):
    def __init__(self, parent, size, bd_radius):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"background-color: {BG_COLOR0};"
            f"border-radius: {bd_radius}px;"
        )
        self.setIcon(QIcon(QPixmap(QImage.fromData(QByteArray(BYTES_MINIMIZE)))))
        self.setFixedSize(size, size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("最小化")
        self.setToolTipDuration(5000)


class CloseButton(QPushButton):
    def __init__(self, parent, size, bd_radius):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"background-color: {BG_COLOR0};"
            f"border-radius: {bd_radius}px;"
        )
        self.setIcon(QIcon(QPixmap(QImage.fromData(QByteArray(BYTES_CLOSE)))))
        self.setFixedSize(size, size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("关闭")
        self.setToolTipDuration(5000)


class CancelButton(QPushButton):
    def __init__(self, parent, size, bd_radius):
        super().__init__(parent=parent, text="取消")
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"background-color: {LIGHTER_RED};"
            f"border-radius: {bd_radius}px;"
        )
        self.setFixedSize(size, size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("取消")
        self.setToolTipDuration(5000)


class EnsureButton(QPushButton):
    def __init__(self, parent, size, bd_radius):
        super().__init__(parent=parent, text="确定")
        self.setFixedSize(size, size)
        self.setStyleSheet(
            f"background-color: {LIGHTER_GREEN};"
            f"border-radius: {bd_radius}px;"
        )
        self.setFixedSize(size, size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("确定")
        self.setToolTipDuration(5000)


class ImageTextButton(TextButton):
    ImgLeft = "ImgLeft"
    ImgRight = "ImgRight"
    ImgTop = "ImgTop"
    ImgBottom = "ImgBottom"

    def __init__(
            self, parent,
            text: str = '',
            tool_tip: str = None,
            img_bytes: bytes = None,
            img_pos: str = ImgLeft,
            img_size: Union[int, Tuple[int, int]] = 0,
            img_bd_radius: int = 0,
            spacing: int = 5,
            bd: Union[int, Tuple[int, int, int, int]] = 0,
            bd_color: Union[str, Tuple[str, str, str, str]] = FG_COLOR0,
            bd_radius: Union[int, Tuple[int, int, int, int]] = 0,
            padding: Union[int, Tuple[int, int, int, int]] = 0,
            bg: Union[str, Tuple[str, str, str, str]] = BG_COLOR0,
            fg: Union[str, Tuple[str, str, str, str]] = FG_COLOR0,
            font=YAHEI[10],
            align=Qt.AlignCenter,
            size: Union[int, Tuple[int, int]] = (65, 30),
    ):
        """
        四个状态分别为：默认，鼠标悬停，鼠标按下，获得焦点
        :param parent:
        :param text:
        :param img_bytes:
        :param img_pos:
        :param img_size:
        :param img_bd_radius:
        :param bd:
        :param bd_color:
        :param bd_radius:
        :param padding:
        :param bg:
        :param fg:
        :param font:
        """
        self.text_label = TextLabel(text, font, fg if isinstance(fg, str) else fg[0])
        self.img_label = BorderRadiusImage(parent, img_bytes, img_size, img_bd_radius,
                                           bg if isinstance(bg, str) else bg[0])
        self.layout = QHBoxLayout() if img_pos in [self.ImgLeft, self.ImgRight] else QVBoxLayout()
        self.widgets = [self.img_label, self.text_label] if img_pos in [self.ImgLeft, self.ImgTop] else [
            self.text_label, self.img_label]
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(spacing)
        self.layout.addStretch()
        self.layout.addLayout(self.layout)
        self.layout.addStretch()
        super().__init__(parent, text, tool_tip, bd, bd_color, bd_radius, padding, bg, fg, font, align, size, __set_text=False)


class ButtonGroup:
    def __init__(self, buttons: List[QPushButton], default_index: int = 0):
        """
        按钮组，只能有一个按钮被选中
        :param buttons:
        :param default_index:
        """
        self.buttons = buttons
        for button in buttons:
            button.setCheckable(True)
            button.clicked.connect(lambda: self.button_clicked(button))
        buttons[default_index].setChecked(True)

    def button_clicked(self, clicked_button):
        for button in self.buttons:
            if button != clicked_button:
                button.setChecked(False)
        clicked_button.setChecked(True)

    @property
    def checked_button(self):
        for button in self.buttons:
            if button.isChecked():
                return button
        return None


class TextEdit(QTextEdit):
    def __init__(self, parent, text="", tool_tip: str = None, font=YAHEI[9]):
        super().__init__(parent)
        self.setFont(font)
        self.setText(text)
        self.setStyleSheet(f"""
            QLineEdit{{
                background-color: {BG_COLOR1}; 
                color: {FG_COLOR0}; 
                border: 1px solid {FG_COLOR0}; 
                border-radius: 5px;
            }}
            QLineEdit:hover{{
                background-color: {BG_COLOR2}; 
                color: {FG_COLOR0}; 
                border: 1px solid {FG_COLOR0}; 
                border-radius: 5px;
            }}
            QLineEdit::disabled{{
                background-color: {BG_COLOR1}; 
                color: gray; 
                border: 1px solid gray; 
                border-radius: 5px;
            }}
            QLineEdit::focus{{
                background-color: {BG_COLOR2}; 
                color: {FG_COLOR0}; 
                border: 1px solid {FG_COLOR0}; 
                border-radius: 5px;
            }}  
        """)
        if tool_tip:
            self.setToolTip(tool_tip)
            self.setToolTipDuration(5000)


class NumberEdit(TextEdit):
    def __init__(
            self, parent, root_parent,
            size: Tuple[int, int] = (100, 30),
            num_type: Type[int] = int, num_range: tuple = (-100000, 100000),
            rounding: int = 0,
            default_value: int = 0,
            step: Union[int, float] = int(1),
            font=YAHEI[9],
            tool_tip: str = None
    ):
        super().__init__(parent, str(default_value), tool_tip, font)
        self.root_parent = root_parent
        self.num_type = num_type
        self.num_range = num_range
        self.rounding = None if self.num_type == int else rounding
        self.default_value = default_value
        self.current_value = round(self.num_type(default_value), self.rounding) if self.rounding else int(default_value)
        self.step = step
        # 设置属性
        self.setFixedSize(size[0], size[1])
        self.setAlignment(Qt.AlignCenter)
        if self.num_type == int:
            self.setValidator(QIntValidator(self.num_range[0], self.num_range[1]))
        else:
            self.setValidator(QDoubleValidator(self.num_range[0], self.num_range[1], self.rounding))
        # 解绑滚轮事件，将来绑定到父控件上。这样做能够让控件在unfocus状态也能够响应滚轮事件进行值修改；
        self.wheelEvent = lambda event: None
        # 绑定值改变事件
        self.textChanging = False  # 防止递归
        self.textChanged.connect(self.text_changed)

    def text_changed(self):
        if self.textChanging:
            return
        self.textChanging = True
        try:
            if self.num_range[0] <= self.num_type(self.toPlainText()) <= self.num_range[1]:
                self.current_value = self.num_type(self.toPlainText())
            else:
                self.setText(str(self.current_value))
        except ValueError:
            self.setText(str(self.current_value))
        self.textChanging = False


class Window(QWidget):
    def __init__(
            self, parent, title: str, ico_bites: bytes, ico_size: int = 26, topH: int = 35, bottomH: int = 35,
            size: Tuple[int, int] = (800, 600), show_maximize: bool = True, resizable: bool = True,
            ensure_bt_fill: bool = False,
            font=YAHEI[9], bg: str = BG_COLOR1, fg: str = FG_COLOR0, bd_radius: Union[int, Tuple[int, int, int, int]] = 0,
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setFixedSize(size[0], size[1])
        self.font = font
        self.bg = bg
        self.fg = fg
        self.bd_radius = bd_radius
        self.topH = topH
        self.bottomH = bottomH
        self.btWid = 55
        self.resizable = resizable
        self.show_maximize = show_maximize
        self.title = title
        self.ico_bites = ico_bites
        self.ico_size = ico_size
        # 初始化控件
        self.top_widget = QWidget(self)
        self.center_widget = QWidget(self)
        self.bottom_widget = QWidget(self)
        self.top_layout = QHBoxLayout(self.top_widget)
        self.center_layout = QHBoxLayout(self.center_widget)
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.ico_label = BorderRadiusImage(self.top_widget, self.ico_bites, self.ico_size, 0, self.bg)
        self.close_button = CloseButton(self, self.btWid, self.bd_radius)
        self.cancel_button = CancelButton(self, self.btWid, self.bd_radius)
        self.ensure_button = EnsureButton(self, self.btWid, self.bd_radius)
        self.maximize_button = MaximizeButton(self, self.btWid, self.bd_radius)
        self.minimize_button = MinimizeButton(self, self.btWid, self.bd_radius)
        self.title_label = TextLabel(self, self.title, YAHEI[12], self.fg)




