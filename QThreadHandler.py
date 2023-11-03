# -*- coding: utf-8 -*-
"""
管理QThread
"""
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from util_funcs import color_print


def handle_thread_error(func):
    thread_name_dict = {}

    def wrapper(*args, **kwargs):
        thread_class_name = args[0].__class__.__name__
        if thread_class_name not in thread_name_dict:
            thread_name_dict[thread_class_name] = 0
        try:
            thread_name_dict[thread_class_name] += 1
            color_print(f"Thread {thread_class_name}[{thread_name_dict[thread_class_name]}] started.")
            result = func(*args, **kwargs)
            color_print(f"Thread {thread_class_name}[{thread_name_dict[thread_class_name]}] finished.")
            return result
        except Exception as e:
            print(f"Error in thread {thread_class_name}[{thread_name_dict[thread_class_name]}]: {e}")

    return wrapper


class MyQThread(QThread):
    """
    QThread的子类
    """
    finished = pyqtSignal()
    error_occurred = pyqtSignal(Exception)
    print = pyqtSignal(str, str)  # 用于打印信息
    pool = []

    def __init__(self, parent=None):
        super(MyQThread, self).__init__(parent)
        self.mutex = QMutex()
        MyQThread.pool.append(self)

    def run(self):
        """
        重写run函数
        """
        ...
        # 结束的时候要将自己从线程池中移除
        MyQThread.pool.remove(self)
        self.finished.emit()
