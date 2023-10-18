"""
工具函数
"""

import ctypes
from PyQt5.QtWidgets import QMessageBox


def not_implemented(func):
    """
    装饰未完成的功能
    :return:
    """
    def wrapper(*args, **kwargs):
        QMessageBox.information(None, "提示", "该功能暂未实现，敬请期待！", QMessageBox.Ok)
    return wrapper


def empty_func(*args, **kwargs):
    """
    空函数，用于占位
    :param args:
    :param kwargs:
    :return:
    """
    pass


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as _e:
        print(_e)
        return False
