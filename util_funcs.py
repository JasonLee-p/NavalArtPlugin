"""
工具函数
"""

import ctypes


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
