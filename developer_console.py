# -*- coding: utf-8 -*-
"""
开发者控制台
"""
import sys
import ctypes
import traceback
from base64 import b64decode
from io import StringIO

from PyQt5.QtGui import QFontMetrics, QFont

from GUI.basic import close
from GUI import *
from ship_reader import NAPart

python_keyWords_list = ['fromkeys', 'break', 'global', 'zip', 'del', 'min', 'complex', 'lambda', '__reversed__',
                        'sorted', '__new__', 'range', 'assert', 'id', 'map', 'coerce', '__ge__', '__str__', 'slice',
                        'staticmethod', 'as', 'max', 'super', 'reversed', 'globals', 'reduce', 'getattr', 'bin',
                        'intern', 'pass', 'None', '__delitem__', '__getitem__', '__init_subclass__', 'property', 'try',
                        'int', 'class', 'basestring', '__dir__', 'and', '__reduce_ex__', 'is', 'issubclass', 'iter',
                        'delattr', 'setattr', 'exec', 'float', 'unicode', 'with', 'filter', 'help', 'async', 'continue',
                        '__setattr__', 'ord', 'round', '__gt__', 'in', 'all', 'not', 'keys', 'from', 'object',
                        '__sizeof__', 'clear', '__getattribute__', 'finally', 'abs', 'vars', 'raise', 'open', 'long',
                        'next', '__delattr__', 'update', 'for', 'classmethod', '__le__', 'True', 'dir', 'any', 'unichr',
                        'or', 'nonlocal', 'ascii', 'except', 'tuple', 'popitem', 'values', 'yield', 'reload', '__len__',
                        'len', 'get', 'await', '__class__', 'cmp', 'bool', '__subclasshook__', 'format', 'if',
                        'enumerate', '__eq__', 'execfile', 'list', 'else', 'return', 'items', 'False', 'copy', 'sum',
                        '__contains__', 'print', 'xrange', '__ne__', 'hash', 'repr', 'def', 'input', 'hex',
                        'setdefault', 'locals', 'callable', 'apply', 'pop', 'hasattr', 'compile', 'file', 'divmod',
                        '__lt__', 'chr', 'isinstance', '__init__', '__iter__', 'str', 'frozenset', 'type', 'oct',
                        'dict', 'pow', '__reduce__', 'set', '__repr__', 'raw_input', '__setitem__', 'while', 'import',
                        '__hash__', 'eval', 'buffer', '__format__', 'elif', '__doc__']

python_keyWords_list = list(set(python_keyWords_list))


def open_developer_console(Handler, ProjectHandler):
    """
    打开开发者控制台
    :return:
    """
    DeveloperConsole(Handler, ProjectHandler).show()


def get_keyboard_layout_name():
    # 获取当前输入法名称
    klid = ctypes.windll.user32.GetKeyboardLayout(0)
    buffer_size = 9
    buffer = ctypes.create_unicode_buffer(buffer_size)
    ctypes.windll.user32.GetKeyboardLayoutNameW(buffer)
    return buffer.value


class DeveloperConsole(QWidget):
    def __init__(self, Handler, ProjectHandler):
        # 设置操作变量
        self.Handler = Handler
        self.ProjectHandler = ProjectHandler
        self.DesignTab = Handler.hull_design_tab
        self.GLWidget = self.DesignTab.ThreeDFrame
        self.Selected = self.GLWidget.selected_gl_objects[self.GLWidget.show_3d_obj_mode]
        super().__init__(Handler.window)
        self.height = 500
        self.width = 700
        # 移动到中央
        self.pos = QPoint(4 * WinWid / 5, 3 * WinHei / 5)
        self.setWindowIcon(Handler.window.windowIcon())
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 保持在顶层
        # 设置窗口可缩放
        self.setFixedSize(self.width, self.height)
        self.move(self.pos - self.rect().center())
        # 控件初始化
        self.layout = QVBoxLayout()
        self.top_widget = QWidget()
        self.close_bg = b64decode(close)
        self.close_bg = QIcon(QPixmap.fromImage(QImage.fromData(self.close_bg)))
        self.close_button = QPushButton()
        self.top_layout = QHBoxLayout()
        self.drag_widget = QWidget()
        self.title_label = MyLabel("开发者控制台", font=FONT_12)
        self.console_output = OutputTextEdit(self)
        self.console_input = InputTextEdit(self)
        self.init_UI()
        self.console_input.setFocus()
        # 事件
        self.drag_pos = None
        self.dragged = False
        # 系统模拟按下shift键
        import os
        os.system("shift")

    def init_UI(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_COLOR1};
                color: {FG_COLOR0};
                border: 1px solid {FG_COLOR0};
                border-radius: 15px;
            }}
        """)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.init_top_widget()

        self.console_input.setFixedSize(self.width, 150)
        self.console_output.setFixedSize(self.width, self.height - 45 - 150 - 20)
        self.console_output.setReadOnly(True)

        self.layout.addWidget(self.top_widget, alignment=Qt.AlignTop | Qt.AlignCenter)
        self.layout.addWidget(self.console_output, alignment=Qt.AlignTop | Qt.AlignCenter, stretch=1)
        self.layout.addWidget(self.console_input, alignment=Qt.AlignTop | Qt.AlignCenter)
        self.setLayout(self.layout)

    def init_top_widget(self):
        self.top_widget.setFixedSize(self.width, 45)
        self.top_widget.setContentsMargins(0, 0, 0, 0)
        self.top_widget.setAcceptDrops(True)  # 接受拖拽
        self.top_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_COLOR1};
                color: {FG_COLOR0};
                border: 1px solid {FG_COLOR0};
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }}
        """)
        self.top_widget.setMouseTracking(True)
        self.top_widget.mousePressEvent = self.drag_pressed
        self.top_widget.mouseMoveEvent = self.drag_move
        self.top_widget.mouseReleaseEvent = self.drag_release
        self.top_layout.setSpacing(0)
        self.top_layout.setContentsMargins(1, 1, 1, 1)
        self.top_layout.addWidget(self.title_label, alignment=Qt.AlignCenter, stretch=1)
        self.close_button.setIcon(self.close_bg)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        cb_size = (40, 43)
        self.close_button.clicked.connect(self.close)
        set_buttons([self.close_button], sizes=cb_size, border_radius=14, border=0, bg=(BG_COLOR1, "#F76677", "#F76677", "#F76677"))
        self.top_layout.addWidget(self.close_button, alignment=Qt.AlignCenter)
        self.top_widget.setLayout(self.top_layout)

    def drag_pressed(self, event):
        # 获取点击点在self中的位置（event.pos()是在self.top_widget中的位置，需要做转换）
        self.drag_pos = self.top_widget.mapToParent(event.pos())
        event.accept()

    def drag_move(self, event):
        if self.drag_pos:
            self.dragged = True
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def drag_release(self, event):
        if not self.dragged:
            # 隐藏或显示
            if self.console_output.isHidden():
                self.console_output.show()
                self.console_input.show()
                self.console_input.setFocus()
            else:
                self.console_output.hide()
                self.console_input.hide()
        self.drag_pos = None
        self.dragged = False
        event.accept()


class OutputTextEdit(QTextEdit):
    def __init__(self, console):
        super().__init__()
        self.console = console
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_COLOR1};
                color: {FG_COLOR0};
                border: 1px solid {FG_COLOR0};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        self.setFont(FONT_11)
        # 设置制表符宽度
        self.setTabStopWidth(8 * QFontMetrics(FONT_11).width(' '))
        # 在输出端口输出提示信息（绿色字体）
        self.setTextColor(QColor(0, 255, 0))
        self.append("------------------------------ Command mode ------------------------------")
        self.setTextColor(QColor(FG_COLOR0))


class InputTextEdit(QTextEdit):
    def __init__(self, console):
        super().__init__()
        self.current_text_list = []
        self.hints_labels = []
        self.current_hint_index = 0
        self.console = console
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_COLOR1};
                color: {FG_COLOR0};
                border: 1px solid {FG_COLOR0};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        self.setFont(FONT_11)
        self.setTabStopWidth(8 * QFontMetrics(FONT_11).width(' '))
        # 将输入框的光标设置为竖线
        self.textCursor().insertText(' ')
        self.textCursor().deletePreviousChar()
        # 提示词显示框（带有透明背景，右侧滚动条）
        self.hints_area = QScrollArea(console.Handler.window)
        # 隐藏滚动条
        self.hints_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hints_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                color: {FG_COLOR0};
                border: 0px;
                border-radius: 5px;
            }}
            // 隐藏滚动条
            QScrollBar:vertical {{
                width: 0px;
            }}
        """)
        self.hints_area.setFixedSize(500, 200)
        self.hints_area.move(0, 0)
        self.hints_area.setFrameShape(QFrame.NoFrame)
        self.hints_area.hide()
        self.hints_widget = QWidget()
        self.hints_widget.setFixedWidth(477)
        self.hints_area.setWidget(self.hints_widget)
        # 提示词显示框的布局
        self.hints_layout = QVBoxLayout()
        self.hints_layout.setContentsMargins(5, 5, 5, 5)
        self.hints_layout.setSpacing(5)
        self.hints_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.hints_widget.setLayout(self.hints_layout)
        self.hints_widget.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                color: {FG_COLOR0};
            }}
        """)
        # 提示词的字体
        self.hints_font = QFont("Consolas", 11)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            # 如果没有shift键，则执行命令
            if not event.modifiers() & Qt.ShiftModifier:
                # 获取命令
                command = self.toPlainText()
                # 清空输入框
                self.clear()
                # 执行命令
                Command(command, self.console)
            else:
                # 如果有shift键，则换行
                self.insertPlainText('\n')
        elif event.key() == Qt.Key_Tab:
            if self.hints_labels:
                # 如果按下了Tab键，则将第一个提示词补全到输入框中
                # 从self中删除current_text_list的最后一个元素，然后添加提示词
                del_ = self.current_text_list[-1]
                # 往输入框删除
                for i in range(len(del_)):
                    self.textCursor().deletePreviousChar()
                # 往输入框添加
                self.insertPlainText(self.hints_labels[self.current_hint_index].text())
        elif event.key() == Qt.Key_Up:
            if self.hints_labels:
                # 如果按下了上箭头，则current_hint指向上一个提示词
                if self.current_hint_index > 0:
                    self.hints_labels[self.current_hint_index].setStyleSheet(f"""
                        QLabel {{
                            background-color: {BG_COLOR0};
                            color: {FG_COLOR0};
                            border: 0px;
                            border-radius: 5px;
                            padding-left: 5px;
                            padding-right: 5px;
                        }}
                    """)
                    self.current_hint_index -= 1
                    self.hints_labels[self.current_hint_index].setStyleSheet(f"""
                        QLabel {{
                            background-color: {BG_COLOR3};
                            color: {FG_COLOR0};
                            border: 0px;
                            border-radius: 5px;
                            padding-left: 5px;
                            padding-right: 5px;
                        }}
                    """)
            elif event.key() == Qt.Key_Down:
                # 如果按下了下箭头，则current_hint指向下一个提示词
                if self.current_hint_index < len(self.hints_labels) - 1:
                    self.hints_labels[self.current_hint_index].setStyleSheet(f"""
                        QLabel {{
                            background-color: {BG_COLOR0};
                            color: {FG_COLOR0};
                            border: 0px;
                            border-radius: 5px;
                            padding-left: 5px;
                            padding-right: 5px;
                        }}
                    """)
                    self.current_hint_index += 1
                    self.hints_labels[self.current_hint_index].setStyleSheet(f"""
                        QLabel {{
                            background-color: {BG_COLOR3};
                            color: {FG_COLOR0};
                            border: 0px;
                            border-radius: 5px;
                            padding-left: 5px;
                            padding-right: 5px;
                        }}
                    """)
        else:
            super().keyPressEvent(event)
        self.text_changed()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.current_hint_index = 0
            self.hints_labels = []
            self.hints_area.hide()

    def text_changed(self):
        self.current_hint_index = 0
        self.hints_labels = []
        # 检查是否需要提示
        hints = self.get_hints()
        if not hints:
            self.hints_area.hide()
            return
        # 在输入框下方显示提示词
        self.hints_area.show()
        # 清空提示词
        for i in range(self.hints_layout.count()):
            self.hints_layout.itemAt(i).widget().deleteLater()
        # 添加提示词
        for hint in hints:
            label = QLabel(hint, self)
            label.setFont(self.hints_font)
            label.setStyleSheet(f"""
                QLabel {{
                    background-color: {BG_COLOR0};
                    color: {FG_COLOR0};
                    border: 0px;
                    border-radius: 5px;
                    padding-left: 5px;
                    padding-right: 5px;
                }}
            """)
            self.hints_layout.addWidget(label, alignment=Qt.AlignLeft)
            self.hints_labels.append(label)
        self.hints_labels[0].setStyleSheet(f"""
            QLabel {{
                background-color: {BG_COLOR3};
                color: {FG_COLOR0};
                border: 0px;
                border-radius: 5px;
                padding-left: 5px;
                padding-right: 5px;
            }}
        """)
        self.current_hint_index = 0
        # 设置提示词显示框的位置
        cursor_bottom_left = self.cursorRect().bottomLeft()
        cursor_bottom_left_global = self.mapToGlobal(cursor_bottom_left)
        self.hints_area.move(cursor_bottom_left_global + QPoint(10, 14))
        # 设置滚动区域高度
        self.hints_widget.setFixedHeight(self.hints_layout.count() * 27 + 10)

    def get_hints(self):
        """
        获取提示词
        :return:
        """
        # 从最后一个字符遍历，一直到遇到标点符号或空格或换行符（除了下划线）
        text = self.toPlainText()
        if text == "":
            return []
        txt = [str('')]
        for i in range(len(text) - 1, -1, -1):
            if text[i] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_":
                txt[-1] = text[i] + txt[-1]
            elif text[i] == ".":
                txt.append(str(''))
            else:
                break
        self.current_text_list = txt
        if Command.mode == "command":
            return self.get_command_hints(txt, text)
        elif Command.mode == "python":
            return self.get_python_hints(txt, text)

    def get_command_hints(self, txt, text):
        hints = Command.hints
        # 过滤
        if len(txt) == 1:
            if text[0] == "$" and not text.startswith("$command") and not text.startswith("$python"):
                return ["command", "python"]
            result = []
            for key in hints:
                if key.startswith(str(txt[0])) and not key.startswith("_") and key != txt[0]:
                    result.append(key)
            return result
        else:
            return []

    def get_python_hints(self, txt, text):
        # 提供给exec()的全局变量
        Handler = self.console.Handler
        ProjectHandler = self.console.ProjectHandler
        DesignTab = self.console.DesignTab
        GLWidget = self.console.GLWidget
        Selected = self.console.Selected
        hints = ["Handler", "ProjectHandler", "DesignTab", "GLWidget", "Selected"]
        # 过滤
        if len(txt) == 1:
            if text[0] == "$" and not text.startswith("$command") and not text.startswith("$python"):
                return ["command", "python"]
            result = []
            for python_keyWords in python_keyWords_list:
                if python_keyWords.startswith(str(txt[0])) and not python_keyWords.startswith(
                        "_") and python_keyWords != txt[0]:
                    result.append(python_keyWords)
            for key in hints:
                if key.startswith(str(txt[0])) and not key.startswith("_") and key != txt[0]:
                    result.append(key)
            return result
        else:
            result = []
            last = txt[-1]
            second_last = txt[-2]
            attrs = []
            try:
                attrs = dir(second_last)
            except:
                pass
            for attr in attrs:
                if attr.startswith(last) and not attr.startswith("_") and attr != last:
                    result.append(attr)
            return result


class Command:
    mode = "command"
    hints = ["del", "delete", "rot", "rotate", "remap", "reload"]
    import numpy as np
    import matplotlib.pyplot as plt

    def __init__(self, string, console):
        self.console = console
        self.global_namespace = {
            "NAPart": NAPart,
            "Handler": self.console.Handler,
            "ProjectHandler": self.console.ProjectHandler,
            "DesignTab": self.console.DesignTab,
            "GLWidget": self.console.GLWidget,
            "Selected": self.console.GLWidget.selected_gl_objects[self.console.GLWidget.show_3d_obj_mode],
            # 可调用的库
            "np": self.np,
            "plt": self.plt,
        }
        self.output = console.console_output
        # 对命令重定向输出到控制台
        self.output_buffer = StringIO()
        sys.stdout = self.output_buffer
        sys.stderr = self.output_buffer
        # 执行python命令
        self.execute(string)

    def execute(self, string):
        if string.startswith("$command"):
            Command.mode = "command"
            # 在输出端口输出提示信息（绿色字体）
            self.output.setTextColor(QColor(0, 255, 0))
            self.output.append("------------------------------ Command mode ------------------------------")
            self.output.setTextColor(QColor(FG_COLOR0))
            return
        elif string.startswith("$python"):
            Command.mode = "python"
            # 在输出端口输出提示信息（绿色字体）
            self.output.setTextColor(QColor(0, 255, 0))
            self.output.append("-------------------------------- Python mode --------------------------------")
            self.output.setTextColor(QColor(FG_COLOR0))
            return
        elif Command.mode == "command":
            try:
                self.console.console_output.setTextColor(QColor("#00FF00"))
                self.console.console_output.append(f">>> {string}")
                self.console.console_output.setTextColor(QColor(FG_COLOR0))
                # 执行命令
                self.execute_command(string)
                # 获取输出
                output = self.output_buffer.getvalue()
                # 清空输出缓冲区
                self.output_buffer.truncate(0)
                # 输出到控制台
                self.output.append(output)
            except Exception as e:
                # 获取异常的详细信息，包括行号
                print(f"Error: {e}")
                # 获取输出
                output = self.output_buffer.getvalue()
                # 清空输出缓冲区
                self.output_buffer.truncate(0)
                # 输出到控制台（使用红色字体）
                self.output.setTextColor(QColor(255, 0, 0))
                self.output.append(output)
                self.output.setTextColor(QColor(FG_COLOR0))
            # 恢复输出
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        elif Command.mode == "python":
            try:
                self.console.console_output.setTextColor(QColor("#00FF00"))
                self.console.console_output.append(f">>> {string}")
                self.console.console_output.setTextColor(QColor(FG_COLOR0))
                exec(string, self.global_namespace)
                # 获取输出
                output = self.output_buffer.getvalue()
                # 清空输出缓冲区
                self.output_buffer.truncate(0)
                # 输出到控制台
                self.output.append(output)
            except Exception as e:
                # 获取异常的详细信息，包括行号
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback_info = traceback.extract_tb(exc_traceback)
                error_line = traceback_info[-1][1]  # 获取错误的行号
                print(f"Error in line {error_line}: {e}")
                # 获取输出
                output = self.output_buffer.getvalue()
                # 清空输出缓冲区
                self.output_buffer.truncate(0)
                # 输出到控制台（使用红色字体）
                self.output.setTextColor(QColor(255, 0, 0))
                self.output.append(output)
                self.output.setTextColor(QColor(FG_COLOR0))
            # 恢复输出
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    def execute_command(self, command):
        if command.startswith("del") or command.startswith("delete"):
            self.delete_part()
        elif command.startswith("rot") or command.startswith("rotate"):
            self.rotate_part(command)
        elif command == "remap":
            _p = list(NAPart.hull_design_tab_id_map.values())[0]
            ttt = _p.allParts_relationMap.remap()
            self.output.append(f"Remap: run {ttt} times.")
        elif command == "reload":
            self.console.Handler.reload()
        else:
            raise Exception("Invalid command.")

    def delete_part(self):
        """
        删除零件
        :return:
        """
        if len(self.console.Selected) == 0:
            raise Exception("No part selected.")
        elif len(self.console.Selected) == 1:
            self.console.GLWidget.selected_gl_objects[self.console.GLWidget.show_3d_obj_mode] = []
            NAPart.hull_design_tab_id_map.pop(id(self.console.Selected[0]) % 4294967296)
            if self.console.ProjectHandler.current.na_hull is not None:
                for col, parts in self.console.ProjectHandler.current.na_hull.DrawMap.items():
                    if self.console.Selected[0] in parts:
                        parts.remove(self.console.Selected[0])
                        break
            self.output.append(f"Part at {self.console.Selected[0].Pos} deleted.")
        else:
            drawMap = self.console.ProjectHandler.current.na_hull.DrawMap
            self.console.GLWidget.selected_gl_objects[self.console.GLWidget.show_3d_obj_mode] = []
            for part in self.console.Selected:
                if self.console.ProjectHandler.current.na_hull is not None:
                    for col, parts in drawMap.items():
                        if part in parts:
                            parts.remove(part)
                            break
                self.output.append(f"Part at {part.Pos} deleted.")
                NAPart.hull_design_tab_id_map.pop(id(part) % 4294967296)

    def rotate_part(self, command):
        """
        旋转零件
        :param command:
        :return:
        """
        if " " not in command:
            raise Exception("Invalid command.")
        elif len(self.console.Selected) == 0:
            raise Exception("No part selected.")
        elif len(self.console.Selected) > 1:
            raise Exception("More than one part selected.")
        command = str(command.split(" ")[1])
        part = self.console.Selected[0]
        try:
            _angle = float(command[1:])
            if command[0] == "u":
                # 绕x轴旋转
                part.Rot = [part.Rot[0] + _angle, part.Rot[1], part.Rot[2]]
            elif command[0] == "d":
                part.Rot = [part.Rot[0] - _angle, part.Rot[1], part.Rot[2]]
            elif command[0] == "l":
                part.Rot = [part.Rot[0], part.Rot[1] + _angle, part.Rot[2]]
            elif command[0] == "r":
                part.Rot = [part.Rot[0], part.Rot[1] - _angle, part.Rot[2]]
            elif command[0] == "x":
                part.Rot = [part.Rot[0] + _angle, part.Rot[1], part.Rot[2]]
            elif command[0] == "y":
                part.Rot = [part.Rot[0], part.Rot[1] + _angle, part.Rot[2]]
            elif command[0] == "z":
                part.Rot = [part.Rot[0], part.Rot[1], part.Rot[2] + _angle]
            self.output.append(f"Part at {part.Pos} rotated to {part.Rot}.")
            # 更新绘制
            part.change_attrs(update=True)
        except ValueError as e:
            raise Exception(f"Invalid angle: {e}")
