# -*- coding: utf-8 -*-
"""
适配本程序的抽象 OpenGL窗口，用于显示模型，接收鼠标键盘事件
"""
from typing import Literal

from GUI.basic_windows import GLWidget
from .plot_objs import *


class GLWin(GLWidget):
    def __init__(self, proj_mode: Literal['ortho', 'perspective'] = 'perspective'):
        super().__init__(proj_mode=proj_mode)
        self.plot_objs["船体"] = []
        cube0 = Cube(pos=np.array([0, 0, 0]), size=np.array([10, 10, 10]))
        self.plot_objs["船体"].append(cube0)
