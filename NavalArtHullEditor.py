# -*- coding: utf-8 -*-
"""
主程序入口
"""
import sys
from functools import partial
import traceback

try:
    from funcs_utils import *
    from GUI import *
except Exception as e:
    traceback.print_exc()
    print(f"[ERROR] {e}")
    input(f"[INFO] Press any key to exit...")
    sys.exit(1)


def main():
    main_window = MainWindow()


def handle_exception(parent, exc_type, exc_value, exc_traceback):
    traceback_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    color_print(f"""[ERROR] {exc_type}:\n{traceback_text}""", "red")
    input(f"[INFO] Press any key to exit...")
    sys.exit(1)  # 退出程序


if __name__ == '__main__':
    # 设置 OpenGL 版本
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    # 初始化界面和事件处理器
    QApp = QApplication(sys.argv)  # 初始化应用程序
    QApp.setWindowIcon(QIcon(QPixmap.fromImage(ICO_IMAGE)))  # 设置窗口图标
    sys.excepthook = partial(handle_exception, QApp)  # 设置异常处理器
    # 运行业务逻辑
    main()
    # 退出程序
    sys.exit(QApp.exec_())
