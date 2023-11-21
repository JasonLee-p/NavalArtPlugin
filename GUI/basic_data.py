# -*- coding: utf-8 -*-
"""
GUI基础参数
"""
from base64 import b64decode

import ujson
from PySide2.QtGui import QFont

from path_utils import DESKTOP_PATH, CONFIG_PATH

try:
    YAHEI = [QFont("Microsoft YaHei", size) if size else None for size in range(5, 101)]
    HEI = [QFont("SimHei", size) if size else None for size in range(5, 101)]
    # 加粗
    BOLD_YAHEI = [QFont("Microsoft YaHei", size, weight=QFont.Bold) if size else None for size in range(5, 101)]
    BOLD_HEI = [QFont("SimHei", size, weight=QFont.Bold) if size else None for size in range(5, 101)]
    # 斜体
    ITALIC_YAHEI = [QFont("Microsoft YaHei", size, italic=True) if size else None for size in range(5, 101)]
    ITALIC_HEI = [QFont("SimHei", size, italic=True) if size else None for size in range(5, 101)]
    # 加粗斜体
    BOLD_ITALIC_YAHEI = [QFont("Microsoft YaHei", size, weight=QFont.Bold, italic=True) if size else None for size in range(5, 101)]
    BOLD_ITALIC_HEI = [QFont("SimHei", size, weight=QFont.Bold, italic=True) if size else None for size in range(5, 101)]
except Exception as e:
    print(e)


# 主要颜色
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_data = ujson.load(f)
    Theme = config_data['Config']['Theme']
    ProjectFolder = config_data['ProjectsFolder']
except (FileNotFoundError, KeyError, AttributeError):
    Theme = 'Night'
    ProjectFolder = DESKTOP_PATH

# 其他基础色
GRAY = '#808080'
WHITE = '#FFFFFF'
BLACK = '#000000'
RED = '#FF0000'
GREEN = '#00FF00'
BLUE = '#0000FF'
YELLOW = '#FFFF00'
ORANGE = '#FFA500'
PURPLE = '#800080'
PINK = '#FFC0CB'
BROWN = '#A52A2A'
CYAN = '#00FFFF'
GOLD = '#FFD700'
LIGHTER_RED = '#F76677'
LIGHTER_GREEN = '#6DDF6D'
LIGHTER_BLUE = '#6D9DDF'
DARKER_RED = '#C00010'
DARKER_GREEN = '#00C000'
DARKER_BLUE = '#0010C0'

# 根据主题选择颜色，图片
if Theme == 'Day':
    from theme_config_color.day_color import *
    from UI_design.ImgPng_day import close, add, choose, minimize, maximize, maximize_exit, add_y, add_z, tip, ICO
elif Theme == 'Night':
    from theme_config_color.night_color import *
    from UI_design.ImgPng_night import close, add, choose, minimize, maximize, maximize_exit, add_y, add_z, tip, ICO


BYTES_CLOSE = b64decode(close)
BYTES_ADD = b64decode(add)
BYTES_CHOOSE = b64decode(choose)
BYTES_MINIMIZE = b64decode(minimize)
BYTES_MAXIMIZE = b64decode(maximize)
BYTES_MAXIMIZE_EXIT = b64decode(maximize_exit)
BYTES_ADD_Y = b64decode(add_y)
BYTES_ADD_Z = b64decode(add_z)
BYTES_TIP = b64decode(tip)
BYTES_ICO = b64decode(ICO)
