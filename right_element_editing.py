"""
右侧元素编辑
"""
from PyQt5.QtGui import QMouseEvent, QCursor, QKeySequence
from PyQt5.QtWidgets import QApplication, QFileDialog, QGridLayout, QTextEdit, QShortcut
from GUI.QtGui import *


class Mod2SingleLayerEditing(QWidget):
    def __init__(self):
        """
        水平截面视图模式，单层元素编辑窗
        """
        super().__init__()