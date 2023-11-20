# -*- coding: utf-8 -*-
"""
基础控件
"""
from typing import Union, List, Tuple

from basic import *

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *


class TextLabel(QLabel):
    def __init__(self, text, font=YAHEI[9], color=FG_COLOR0, side=Qt.AlignLeft | Qt.AlignVCenter):
        super().__init__(text)
        self.setFont(font)
        self.setStyleSheet(f"color:{color};")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(side)


class TextButton(QPushButton):
    def __init__(
            self, parent,
            text: str = '',
            bd: Union[int, Tuple[int]] = 0,
            bd_color: Union[str, Tuple[str]] = FG_COLOR0,
            bd_radius: Union[int, Tuple[int]] = 0,
            padding: Union[int, Tuple[int]] = 0,
            bg: Union[str, Tuple[str]] = BG_COLOR0,
            fg: Union[str, Tuple[str]] = FG_COLOR0,
            font=YAHEI[10],
            __set_text: bool = True
    ):
        """
        四个状态分别为：默认，鼠标悬停，鼠标按下，获得焦点
        若选中，则同为鼠标按下状态
        若禁用，则同为默认状态
        :param parent:
        :param text:
        :param bd:
        :param bd_color:
        :param bd_radius:
        :param padding:
        :param bg:
        :param fg:
        :param font:
        """
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
        # 设置样式
        if __set_text:
            self.setText(text)
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


class ImageTextButton(TextButton):
    ImgLeft = "ImgLeft"
    ImgRight = "ImgRight"
    ImgTop = "ImgTop"
    ImgBottom = "ImgBottom"

    def __init__(
            self, parent,
            text: str = '',
            img_bytes: bytes = None,
            img_pos: str = ImgLeft,
            img_size: Union[int, Tuple[int]] = 0,
            img_transparent_bg: bool = True,
            img_bd_radius: int = 0,
            spacing: int = 5,
            bd: Union[int, Tuple[int]] = 0,
            bd_color: Union[str, Tuple[str]] = FG_COLOR0,
            bd_radius: Union[int, Tuple[int]] = 0,
            padding: Union[int, Tuple[int]] = 0,
            bg: Union[str, Tuple[str]] = BG_COLOR0,
            fg: Union[str, Tuple[str]] = FG_COLOR0,
            font=YAHEI[10],
    ):
        """
        四个状态分别为：默认，鼠标悬停，鼠标按下，获得焦点
        :param parent:
        :param text:
        :param img_bytes:
        :param img_pos:
        :param img_size:
        :param img_transparent_bg:
        :param img_bd_radius:
        :param bd:
        :param bd_color:
        :param bd_radius:
        :param padding:
        :param bg:
        :param fg:
        :param font:
        """
        # 处理参数
        if isinstance(img_size, int):
            img_width, img_height = img_size, img_size
        else:
            img_width, img_height = img_size[0], img_size[1]
        self.img_bytes = img_bytes
        self.img_label = QLabel()
        self.text_label = TextLabel(text, font, fg if isinstance(fg, str) else fg[0])
        self.init_img_label(img_width, img_height, img_transparent_bg, bg, img_bd_radius)
        self.layout = QHBoxLayout() if img_pos in [self.ImgLeft, self.ImgRight] else QVBoxLayout()
        self.widgets = [self.img_label, self.text_label] if img_pos in [self.ImgLeft, self.ImgTop] else [self.text_label, self.img_label]
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(spacing)
        self.layout.addStretch()
        self.layout.addLayout(self.layout)
        self.layout.addStretch()
        super().__init__(parent, text, bd, bd_color, bd_radius, padding, bg, fg, font, __set_text=False)

    def init_img_label(self, img_width, img_height, img_transparent_bg, bg, img_bd_radius):
        img = QPixmap(QImage.fromData(QByteArray(self.img_bytes)))
        img.scaled(img_width, img_height, Qt.KeepAspectRatio)
        rounded_img = QPixmap(img_width, img_height)
        rounded_img.fill(Qt.transparent) if img_transparent_bg else rounded_img.fill(QColor(bg[0]))
        painter = QPainter(rounded_img)
        painter.setRenderHint(QPainter.Antialiasing)
        # 创建一个椭圆路径来表示圆角
        path = QPainterPath()
        path.addRoundedRect(0, 0, img_width, img_height, img_bd_radius, img_bd_radius)
        painter.setClipPath(path)  # 设置剪裁路径
        # 在剪裁后的区域内绘制原始图像
        painter.drawPixmap(0, 0, img)
        painter.end()  # 结束绘制

        self.img_label.setPixmap(rounded_img)
        self.img_label.setFixedSize(img_width, img_height)
        self.img_label.setStyleSheet(
            f"background-color: {'transparent' if img_transparent_bg else (bg[0] if isinstance(bg, tuple) else bg)};"
            f"border-radius: {img_bd_radius}px;"
        )


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

    def get_checked_button(self):
        for button in self.buttons:
            if button.isChecked():
                return button
        return None

