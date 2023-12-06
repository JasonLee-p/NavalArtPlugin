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


VERSION = "0.0.3.0"
TESTING = True


def init_QApp():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(QPixmap(ICO_IMAGE)))
    app.setApplicationName("NavalArt HullEditor")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("JasonLee")
    # 设置主题
    app.setStyle("Fusion")
    return app


def main():
    main_window = MainWindow()


def handle_exception(parent, exc_type, exc_value, exc_traceback):
    if TESTING:
        traceback_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        color_print(f"""[ERROR] {exc_type}:\n{traceback_text}""", "red")
        input(f"[INFO] Press any key to exit...")
        sys.exit(1)  # 退出程序
    else:
        MessageBox(f"{exc_type}:\n{exc_value}", CONST.ERROR)


if __name__ == '__main__':
    # 设置 OpenGL 版本
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    # 初始化界面和事件处理器
    QApp = init_QApp()
    sys.excepthook = partial(handle_exception, QApp)  # 设置异常处理器
    # 运行业务逻辑
    main()
    # main_win = QMainWindow()
    # main_win.setLayout(QVBoxLayout())
    # main_win.layout().addWidget(QOpenGLWidget())
    # 退出程序
    sys.exit(QApp.exec())
