# -*- coding: utf-8 -*-
"""
适配本程序的抽象 OpenGL窗口，用于显示模型，接收鼠标键盘事件
"""
from .basic_windows import GLWindow


class GLWin(GLWindow):
    def __str__(self):
        ...