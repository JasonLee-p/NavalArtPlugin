# -*- coding: utf-8 -*-
"""
基础控件
"""
from abc import abstractmethod
from typing import Union, List, Tuple, Type

from .basic_data import *

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *


def _set_buttons(
        buttons, sizes, font=YAHEI[9], border=0, bd_color=FG_COLOR0,
        bd_radius=10, padding=0, bg=(BG_COLOR1, BG_COLOR3, BG_COLOR2, BG_COLOR3),
        fg=FG_COLOR0
):
    """
    设置按钮样式
    :param buttons: 按钮列表
    :param sizes:
    :param font: QFont对象
    :param border: 边框宽度
    :param bd_color: 边框颜色
    :param bd_radius: 边框圆角
    :param padding: 内边距
    :param bg: 按钮背景颜色
    :param fg: 按钮字体颜色
    :return:
    """
    buttons = list(buttons)
    if isinstance(bd_radius, int):
        bd_radius = (bd_radius, bd_radius, bd_radius, bd_radius)
    if type(sizes[0]) in [int, None]:
        sizes = [sizes] * len(buttons)
    if border != 0:
        border_text = f"{border}px solid {bd_color}"
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
                border-top-left-radius: {bd_radius[0]}px;
                border-top-right-radius: {bd_radius[1]}px;
                border-bottom-right-radius: {bd_radius[2]}px;
                border-bottom-left-radius: {bd_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
            QPushButton:hover{{
                background-color:{bg[1]};
                color:{fg[1]};
                border-top-left-radius: {bd_radius[0]}px;
                border-top-right-radius: {bd_radius[1]}px;
                border-bottom-right-radius: {bd_radius[2]}px;
                border-bottom-left-radius: {bd_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
            QPushButton::pressed{{
                background-color:{bg[2]};
                color:{fg[2]};
                border-top-left-radius: {bd_radius[0]}px;
                border-top-right-radius: {bd_radius[1]}px;
                border-bottom-right-radius: {bd_radius[2]}px;
                border-bottom-left-radius: {bd_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
            QPushButton::focus{{
                background-color:{bg[3]};
                color:{fg[3]};
                border-top-left-radius: {bd_radius[0]}px;
                border-top-right-radius: {bd_radius[1]}px;
                border-bottom-right-radius: {bd_radius[2]}px;
                border-bottom-left-radius: {bd_radius[3]}px;
                border: {border_text};
                padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;
            }}
        """)


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
    MAXIMIZE_EXIT_IMAGE = QImage.fromData(QByteArray(BYTES_MAXIMIZE))
    MAXIMIZE_IMAGE = QImage.fromData(QByteArray(BYTES_MAXIMIZE_EXIT))
    MINIMIZE_IMAGE = QImage.fromData(QByteArray(BYTES_MINIMIZE))
    CLOSE_IMAGE = QImage.fromData(QByteArray(BYTES_CLOSE))

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
        if isinstance(size, int):
            size = (size, size)
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


class IconLabel(QLabel):
    def __init__(self, parent, ico_bytes, title, height):
        super().__init__(parent)
        ico = QIcon(QPixmap(QImage.fromData(QByteArray(ico_bytes))))
        self.setPixmap(ico.pixmap(QSize(25, 25)))
        self.setFixedSize(55, height)
        self.setAlignment(Qt.AlignCenter)
        self.setToolTip(title)
        self.setToolTipDuration(5000)


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


class MaximizeButton(Button):
    def __init__(self, parent, size=(55, 35), bd_radius: Union[int, Tuple[int, int, int, int]] = 5):
        super().__init__(parent, None, 0, BG_COLOR0,
                         bd_radius, 0,
                         (BG_COLOR1, GRAY, GRAY, GRAY), FG_COLOR0, YAHEI[9], Qt.AlignCenter,
                         size)
        self.setIcon(QIcon(QPixmap(Button.MAXIMIZE_IMAGE)))
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        # 绑定点击事件
        self.clicked.connect(self.clicked_action)

    def clicked_action(self):
        if self.parent().isMaximized():
            self.setIcon(QIcon(QPixmap(Button.MAXIMIZE_IMAGE)))
        else:
            self.setIcon(QIcon(QPixmap(Button.MAXIMIZE_EXIT_IMAGE)))


class MinimizeButton(Button):
    def __init__(self, parent, size=(55, 35), bd_radius: Union[int, Tuple[int, int, int, int]] = 5):
        super().__init__(parent, None, 0, BG_COLOR0,
                         bd_radius, 0,
                         (BG_COLOR1, GRAY, GRAY, GRAY), FG_COLOR0, YAHEI[9], Qt.AlignCenter,
                         size)
        self.setIcon(QIcon(QPixmap(Button.MINIMIZE_IMAGE)))
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)


class CloseButton(Button):
    def __init__(self, parent, size=(55, 35), bd_radius: Union[int, Tuple[int, int, int, int]] = 5):
        super().__init__(parent, None, 0, BG_COLOR0,
                         bd_radius, 0,
                         (BG_COLOR1, LIGHTER_RED, LIGHTER_RED, LIGHTER_RED), FG_COLOR0, YAHEI[9], Qt.AlignCenter, size)
        self.setIcon(QIcon(QPixmap(Button.CLOSE_IMAGE)))
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)


class CancelButton(Button):
    def __init__(self, parent, size=(55, 35), bd_radius: Union[int, Tuple[int, int, int, int]] = 5):
        super().__init__(parent, None, 0, BG_COLOR0,
                         bd_radius, 0,
                         (BG_COLOR1, LIGHTER_RED, LIGHTER_RED, LIGHTER_RED), FG_COLOR0, YAHEI[9], Qt.AlignCenter, size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)


class EnsureButton(Button):
    def __init__(self, parent, size=(55, 35), bd_radius: Union[int, Tuple[int, int, int, int]] = 5):
        super().__init__(parent, None, 0, BG_COLOR0,
                         bd_radius, 0,
                         (BG_COLOR1, LIGHTER_GREEN, LIGHTER_GREEN, LIGHTER_GREEN), FG_COLOR0, YAHEI[9], Qt.AlignCenter,
                         size)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)


class CircleSelectButton(Button):
    def __init__(self, parent, relative_widgets: list, tool_tip, radius, color: str, check_color: str):
        super().__init__(parent, tool_tip, 0, FG_COLOR0, 1, 0, (color, check_color, check_color, check_color),
                         FG_COLOR0, YAHEI[9], Qt.AlignCenter, (radius * 2, radius * 2))
        self.setCheckable(True)
        self.setChecked(False)
        self.setCursor(Qt.PointingHandCursor)
        self.radius = radius
        self.relative_widgets = relative_widgets
        self.bind_relative_widgets()

    def bind_relative_widgets(self):
        for widget in self.relative_widgets:
            widget.clicked.connect(self.clicked)
            widget.setCursor(Qt.PointingHandCursor)


class CircleBtWithTextLabel(QPushButton):
    def __init__(self, parent, text, tool_tip, color, check_color, radius, size=(100, 30), spacing=5):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(spacing)
        self.setLayout(self.layout)
        self.text_label = TextLabel(self, text, font=YAHEI[9], color=FG_COLOR0, align=Qt.AlignLeft | Qt.AlignVCenter)
        self.__r_widgets = [self.text_label, self]
        self.circle = CircleSelectButton(self, self._r_widgets, tool_tip, radius, color, check_color)
        self.layout.addWidget(self.circle, Qt.AlignLeft | Qt.AlignVCenter)
        self.layout.addWidget(self.text_label, Qt.AlignLeft | Qt.AlignVCenter)
        self.setFixedSize(size[0], size[1])
        self.setFlat(True)


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
        super().__init__(parent, text, tool_tip, bd, bd_color, bd_radius, padding, bg, fg, font, align, size,
                         __set_text=False)


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


class HorSpliter(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(1)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")


class VerSpliter(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(1)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")


class Window(QWidget):
    def __init__(
            self, parent, title: str, ico_bites: bytes, ico_size: int = 26, topH: int = 35, bottomH: int = 35,
            size: Tuple[int, int] = (800, 600), show_maximize: bool = True, resizable: bool = True,
            font=YAHEI[9], bg: str = BG_COLOR1, fg: str = FG_COLOR0,
            bd_radius: Union[int, Tuple[int, int, int, int]] = 0,
    ):
        """
        提供带图标，顶栏，顶栏关闭按钮，底栏的窗口
        :param parent:
        :param title:
        :param ico_bites:
        :param ico_size:
        :param topH:
        :param bottomH:
        :param size:
        :param show_maximize:
        :param resizable:
        :param font:
        :param bg:
        :param fg:
        :param bd_radius:
        """
        super().__init__(parent)
        self.hide()
        # 处理参数
        if isinstance(bd_radius, int):
            bd_radius = [bd_radius] * 4
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置背景透明
        self.setFixedSize(size[0], size[1])
        self.font = font
        self.bg = bg
        self.fg = fg
        self.topH = topH
        self.bottomH = bottomH
        self.btWid = 55
        self.resizable = resizable
        self.title = title
        self.ico_size = ico_size
        self.bd_radius = bd_radius
        # 初始化控件
        self.layout = QVBoxLayout(self)
        self.top_widget = QWidget(self)
        self.center_widget = QWidget(self)
        self.bottom_widget = QWidget(self)
        self.top_layout = QHBoxLayout(self.top_widget)
        self.center_layout = QHBoxLayout(self.center_widget)
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        # 图标和基础按钮
        self.ico_label = IconLabel(None, ico_bites, self.title, topH)
        self.close_button = CloseButton(None, bd_radius=self.bd_radius)
        self.cancel_button = CancelButton(None, bd_radius=self.bd_radius)
        self.ensure_button = EnsureButton(None, bd_radius=self.bd_radius)
        self.maximize_button = MaximizeButton(None, bd_radius=self.bd_radius)
        self.minimize_button = MinimizeButton(None, bd_radius=self.bd_radius)
        # 标题
        self.title_label = TextLabel(None, self.title, YAHEI[12], self.fg)
        # 顶部拖动区域
        self.drag_area = self.init_drag_area()
        self.init_ui()
        # 显示
        if show_maximize:
            self.showMaximized()
        else:
            self.show()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget{{
                background-color: {self.bg};
                color: {self.fg};
                border-top-left-radius: {self.bd_radius[0]}px;
                border-top-right-radius: {self.bd_radius[1]}px;
                border-bottom-right-radius: {self.bd_radius[2]}px;
                border-bottom-left-radius: {self.bd_radius[3]}px;
            }}
        """)
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(HorSpliter())
        self.layout.addWidget(self.center_widget, stretch=1)
        self.layout.addWidget(HorSpliter())
        self.layout.addWidget(self.bottom_widget)
        for _layout in [self.top_layout, self.center_layout, self.bottom_layout]:
            _layout.setContentsMargins(0, 0, 0, 0)
            _layout.setSpacing(0)
        self.init_top_widget()
        self.bind_bt_funcs()

    def init_top_widget(self):
        self.top_widget.setFixedHeight(self.topH)
        self.top_widget.setStyleSheet(f"""
            QWidget{{
                background-color: {self.bg};
                color: {self.fg};
                border-top-left-radius: {self.bd_radius[0]}px;
                border-top-right-radius: {self.bd_radius[1]}px;
            }}
        """)
        # 控件
        self.top_layout.addWidget(self.ico_label, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addWidget(self.drag_area, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addWidget(self.title_label, Qt.AlignLeft | Qt.AlignVCenter)

    def init_drag_area(self):
        # 添加拖动条，控制窗口大小
        drag_widget = QWidget()
        # 设置宽度最大化
        drag_widget.setFixedWidth(10000)
        # drag_widget.setFixedSize(5, 5)
        drag_widget.setStyleSheet("background-color: rgba(0,0,0,0)")
        drag_widget.mouseMoveEvent = self.mouseMoveEvent
        drag_widget.mousePressEvent = self.mousePressEvent
        drag_widget.mouseReleaseEvent = self.mouseReleaseEvent
        self.layout.addWidget(drag_widget, alignment=Qt.AlignBottom | Qt.AlignRight)
        return drag_widget


    @abstractmethod
    def init_center_widget(self):
        pass

    def init_bottom_widget(self):
        self.bottom_widget.setFixedHeight(self.bottomH)
        self.bottom_widget.setStyleSheet(f"""
            QWidget{{
                background-color: {self.bg};
                color: {self.fg};
                border-bottom-right-radius: {self.bd_radius[2]}px;
                border-bottom-left-radius: {self.bd_radius[3]}px;
            }}
        """)
        # 控件
        self.bottom_layout.addWidget(self.cancel_button, Qt.AlignRight | Qt.AlignVCenter)
        self.bottom_layout.addWidget(self.ensure_button, Qt.AlignRight | Qt.AlignVCenter)

    def bind_bt_funcs(self):
        self.close_button.clicked.connect(self.close)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button.clicked.connect(self.showMaximized)
        self.ensure_button.clicked.connect(self.ensure)
        self.cancel_button.clicked.connect(self.cancel)

    def ensure(self):
        self.close()

    def cancel(self):
        self.close()

    def showMaximized(self):
        super().showMaximized()
        self.maximize_button.setIcon(QIcon(QPixmap(self.maximize_button.MAXIMIZE_EXIT_IMAGE)))

    def showNormal(self):
        super().showNormal()
        self.maximize_button.setIcon(QIcon(QPixmap(self.maximize_button.MAXIMIZE_IMAGE)))
