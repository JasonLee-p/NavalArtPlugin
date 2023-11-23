# -*- coding: utf-8 -*-
"""
对 Pyside2 中 Qt线程的封装
"""
import time
from abc import abstractmethod

from PySide2.QtCore import QThread, Signal, Slot

from funcs_utils import color_print


class BasicThread(QThread):
    """
    线程基类
    """
    show_statu_func = Signal(str, str)  # 内容, 类型
    start_signal = Signal()
    finished_signal = Signal()
    error_signal = Signal(Exception)

    pool = []

    def __init__(self, protected_vars: list = None):
        super().__init__()
        self.name = f"{self.__class__.__name__}[{len(BasicThread.pool) + 1}]"
        self.protected_vars = protected_vars
        self.is_running = False
        self.is_finished = False
        self.is_paused = False
        self.is_error = False

        self.start_signal.connect(self.start_slot)
        self.finished_signal.connect(self.finished_slot)
        self.error_signal.connect(self.error_slot)

        self.start()

    def run(self):
        """
        重写run函数
        """
        self.is_running = True
        self.start_signal.emit()
        try:
            self.main()
        except Exception as e:
            self.error_signal.emit(e)
            self.is_error = True
        self.is_running = False
        self.is_finished = True
        self.finished_signal.emit()

    @abstractmethod
    def main(self):
        """
        主函数
        """
        pass

    def start_slot(self):
        """
        开始时的槽函数
        """
        for var in self.protected_vars:
            var.lock()
        BasicThread.pool.append(self)
        color_print(f"[INFO] Thread {self.name} started.")

    def finished_slot(self):
        """
        结束时的槽函数
        """
        for var in self.protected_vars:
            var.unlock()
        BasicThread.pool.remove(self)
        color_print(f"[INFO] Thread {self.name} finished, running time: {time.time() - self.start_time:.3f}s.")

    def error_slot(self, e: Exception):
        """
        错误时的槽函数
        """
        for var in self.protected_vars:
            var.unlock()
        BasicThread.pool.remove(self)
        color_print(f"[ERROR] Thread {self.name} error: {e}")

    def pause(self):
        for var in self.protected_vars:
            var.unlock()
        self.is_paused = True
        self.is_running = False

    def resume(self):
        for var in self.protected_vars:
            var.lock()
        self.is_paused = False
        self.is_running = True

    def stop(self):
        for var in self.protected_vars:
            var.unlock()
        self.is_running = False
        self.is_paused = False
        self.is_finished = True
        self.is_error = False
        self.quit()
        self.wait()
        self.finished_signal.emit()

    def restart(self):
        for var in self.protected_vars:
            var.unlock()
        self.stop()
        self.start()

    def __del__(self):
        if self.is_running:
            self.stop()
        for var in self.protected_vars:
            try:
                var.unlock()
            except RuntimeError:
                pass
        self.quit()
        self.wait()
        self.finished_signal.emit()
