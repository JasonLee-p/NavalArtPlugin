# -*- coding: utf-8 -*-
"""
窗口基类
"""
from abc import abstractmethod

from GUI.basic_widgets import Window


class BasicRootWindow(Window):
    def __init__(self, parent=None, border_radius=10, title=None, size=(400, 300), center_layout=None,
                 resizable=False, hide_top=False, hide_bottom=False, ensure_bt_fill=False):
        ...

    @abstractmethod
    def ensure(self):
        self.close()

    @abstractmethod
    def cancel(self):
        self.close()

    def close(self):
        super().close()
        if self._generate_self_parent:
            self._parent.close()
