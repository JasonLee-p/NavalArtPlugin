# -*- coding: utf-8 -*-
"""
GUI基础参数
"""
import os
from base64 import b64decode

import ujson
from PySide2.QtGui import QFont

from path_utils import find_na_root_path

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
_path = os.path.join(find_na_root_path(), 'plugin_config.json')
try:
    with open(_path, 'r', encoding='utf-8') as f:
        config_data = ujson.load(f)
    Theme = config_data['Config']['Theme']
    ProjectFolder = config_data['ProjectsFolder']
except (FileNotFoundError, KeyError, AttributeError):
    Theme = 'Night'
    ProjectFolder = os.path.join(os.path.expanduser("~"), 'Desktop')

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
