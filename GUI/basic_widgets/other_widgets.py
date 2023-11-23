# -*- coding: utf-8 -*-
"""
其他小部件
"""
from typing import Union, Tuple, Type

from ..basic_data import *


from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *


class HorSpliter(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(2)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")


class VerSpliter(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(1)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")


class TextLabel(QLabel):
    def __init__(self, parent, text, font=YAHEI[6], color=FG_COLOR0, align=Qt.AlignLeft | Qt.AlignVCenter):
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
                 bg: Union[ThemeColor, str] = BG_COLOR0, tool_tip=None):
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


class ProgressBar(QProgressBar):
    def __init__(self, lengh, ):
        ...


class TextEdit(QLineEdit):
    def __init__(self, parent, text="", tool_tip: str = None, font=YAHEI[6]):
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
            font=YAHEI[6],
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
        if self.text() != "":
            if self.text()[0] == "0" and len(self.text()) > 1:
                self.setText(self.text()[1:])
            try:
                if self.num_range[0] <= self.num_type(self.text()) <= self.num_range[1]:
                    self.current_value = round(self.num_type(self.text()), self.rounding) if self.rounding else int(
                        self.text())
            except ValueError:
                pass
        else:
            self.current_value = 0
        self.setText(str(self.current_value))
        self.root_parent.update()
        self.textChanging = False


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
        painter.setBrush(QColor(str(FG_COLOR0)))
        painter.drawPolygon(QPolygon([
            QPoint(pos_x - 5, 0),
            QPoint(pos_x + 5, 0),
            QPoint(pos_x, 5),
        ]))

    def update(self):
        self.repaint()
        super().update()


class Splitter(QSplitter):
    def __init__(self, orientation):
        super().__init__(orientation)
        self.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {BG_COLOR0};
                width: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {BG_COLOR2};
                width: 2px;
            }}
            QSplitter::handle:pressed {{
                background-color: {BG_COLOR2};
                width: 2px;
            }}
        """)
        self.setHandleWidth(1)
