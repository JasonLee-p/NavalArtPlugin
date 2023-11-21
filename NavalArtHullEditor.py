# -*- coding: utf-8 -*-
"""
主程序入口
"""
import sys

from GUI import *
from OpenGLShader import *
from ship_reader import *
from funcs_utils import *
from path_utils import *


def main():
    # 初始化界面和事件处理器
    QApp = QApplication(sys.argv)
    # 设置图标
    QApp.setWindowIcon(QIcon(QPixmap.fromImage(QImage.fromData(BYTES_ICO))))
    QApp.setStyleSheet(f"""
                QWidget{{
                    background-color:{BG_COLOR1};
                    color:{FG_COLOR0};
                }}
                QPushButton{{
                    background-color:{BG_COLOR1};
                    color:{FG_COLOR0};
                    border-radius: 5px;
                    border: 1px solid {FG_COLOR0};
                    padding-left: 15px;
                    padding-right: 15px;
                    padding-top: 5px;
                    padding-bottom: 5px;
                }}
                QPushButton:hover{{
                    background-color:{BG_COLOR3};
                    color:{FG_COLOR0};
                    border-radius: 5px;
                    border: 1px solid {FG_COLOR0};
                    padding-left: 15px;
                    padding-right: 15px;
                    padding-top: 5px;
                    padding-bottom: 5px;
                }}
                QPushButton:pressed{{
                    background-color:{BG_COLOR2};
                    color:{FG_COLOR0};
                    border-radius: 5px;
                    border: 1px solid {FG_COLOR0};
                    padding-left: 15px;
                    padding-right: 15px;
                    padding-top: 5px;
                    padding-bottom: 5px;
                }}
                // 右键菜单栏按钮样式
                QMenu::item:selected{{
                    background-color: {BG_COLOR3};
                    color: {FG_COLOR0};
                    border-radius: 5px;
                }}
                QMenu::item:disabled{{
                    background-color: {BG_COLOR1};
                    color: {GRAY};
                    border-radius: 5px;
                }}
            """)
    main_window = MainWindow()
    QApp.exec_()


if __name__ == '__main__':
    main()
