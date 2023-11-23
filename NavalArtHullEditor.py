# -*- coding: utf-8 -*-
"""
主程序入口
"""
import sys
from functools import partial

from GUI import *
from OpenGLShader import *
from ship_reader import *
from funcs_utils import *
from path_utils import *


def main():
    main_window0 = MainWindow()
    main_window1 = MainWindow()


def handle_exception(parent, exc_type, exc_value, exc_traceback):
    color_print(f"""
        [ERROR] {exc_type}:\n
        {exc_value}\n
        {exc_traceback}\n
    """, "red")
    QMessageBox.critical(parent, '错误', f'{exc_type}\n{exc_value}')  # 弹出错误提示
    sys.exit(1)  # 退出程序


if __name__ == '__main__':
    # 初始化界面和事件处理器
    QApp = QApplication(sys.argv)  # 初始化应用程序
    QApp.setWindowIcon(QIcon(QPixmap.fromImage(ICO_IMAGE)))  # 设置窗口图标
    QApp.setStyleSheet(MAIN_STYLE_SHEET)  # 设置全局默认样式表
    QApp.setQuitOnLastWindowClosed(True)  # 关闭最后一个窗口时退出程序
    sys.excepthook = partial(handle_exception, QApp)  # 设置异常处理器
    # 运行业务逻辑
    main()
    # 退出程序
    sys.exit(QApp.exec_())
