# -*- coding: utf-8 -*-
import os


def find_ptb_path():
    # 将PTB_path初始化为桌面位置
    PTB_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    # 从C盘开始寻找：
    # 优先在用户目录下寻找，先遍历所有账户名：
    for user in os.listdir('C:\\Users'):
        # 找到AppData/LocalLow/茕海开发组/工艺战舰Alpha
        if os.path.isdir(os.path.join('C:\\Users', user, 'AppData', 'LocalLow', '茕海开发组', '工艺战舰Alpha')):
            PTB_path = os.path.join('C:\\Users', user, 'AppData', 'LocalLow', '茕海开发组', '工艺战舰Alpha')
            break
    # 如果在用户目录下没有找到，就返回None
    return PTB_path


def find_na_ship_path():
    # 将PTB_path初始化为桌面位置
    NA_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    # 从C盘开始寻找：
    # 优先在用户目录下寻找，先遍历所有账户名：
    for user in os.listdir('C:\\Users'):
        # 找到AppData/LocalLow/RZEntertainment/NavalArt/ShipSaves
        if os.path.isdir(os.path.join(
                'C:\\Users', user, 'AppData', 'LocalLow', 'RZEntertainment', 'NavalArt', 'ShipSaves')):
            NA_path = os.path.join(
                'C:\\Users', user, 'AppData', 'LocalLow', 'RZEntertainment', 'NavalArt', 'ShipSaves')
            break
    # 如果在用户目录下没有找到，就返回None
    return NA_path


def find_na_root_path():
    # 将PTB_path初始化为桌面位置
    NA_path = os.path.join(os.path.expanduser("~"), 'Desktop')
    # 从C盘开始寻找：
    # 优先在用户目录下寻找，先遍历所有账户名：
    for user in os.listdir('C:\\Users'):
        # 找到AppData/LocalLow/RZEntertainment/NavalArt/ShipSaves
        if os.path.isdir(os.path.join(
                'C:\\Users', user, 'AppData', 'LocalLow', 'RZEntertainment', 'NavalArt')):
            NA_path = os.path.join(
                'C:\\Users', user, 'AppData', 'LocalLow', 'RZEntertainment', 'NavalArt')
            break
    # 如果在用户目录下没有找到，就返回None
    return NA_path
