# # -*- coding: utf-8 -*-
"""
基础函数和基类
"""
from abc import abstractmethod


class Operation:
    def __init__(self):
        """
        操作栈中的操作基类
        在state_history.py中，
        """
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        self.execute()
