# -*- coding: utf-8 -*-
"""
适配本程序的抽象 OpenGL窗口，用于显示模型，接收鼠标键盘事件
"""
from typing import Literal

from GUI.basic_windows import GLWindow


class GLWin(GLWindow):
    def __init__(self, proj_mode: Literal['ortho', 'perspective'] = 'perspective'):
        super().__init__(proj_mode)
