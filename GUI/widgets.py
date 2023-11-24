# -*- coding: utf-8 -*-
"""
主要窗口
"""
from GUI.basic_widgets import *
from OpenGL_plot_objs.opengl_window import GLWin


class MainWindow(Window):
    all_windows = []
    active_window = None

    def __init__(self):
        # self.center_center_widget = GLWin(proj_mode='perspective')
        self.gl_widget = QFrame()
        # 主窗口
        self.main_widget = MultiDirTabMainFrame(self.gl_widget)
        # 标签页
        self.structure_tab = MutiDirectionTab(self.main_widget, name='结构', image=STRUCTURE_IMAGE)
        self.layer_tab = MutiDirectionTab(self.main_widget, name='层级', image=LAYER_IMAGE)
        self.user_tab = MutiDirectionTab(self.main_widget, name='用户', image=USER_IMAGE)
        self.framework_tab = MutiDirectionTab(self.main_widget, name='框架', image=FRAMEWORK_IMAGE)
        # 初始化标签页
        self.init_tab_widgets()
        super().__init__(None, title='NavalArt Hull Editor', ico_bites=BYTES_ICO, size=(1200, 800), resizable=True,
                         show_maximize=True)
        self.setWindowTitle('NavalArt Hull Editor')
        MainWindow.all_windows.append(self)
        MainWindow.active_window = self
        # 状态变量池
        self.operating_prj = None

    def init_tab_widgets(self):
        # 布局
        self.main_widget.add_tab(self.structure_tab, CONST.RIGHT)
        self.main_widget.add_tab(self.layer_tab, CONST.DOWN)
        self.main_widget.add_tab(self.user_tab, CONST.RIGHT)
        self.main_widget.add_tab(self.framework_tab, CONST.LEFT)

    def init_top_widget(self):
        self.top_widget.setFixedHeight(self.topH)
        self.top_widget.setStyleSheet(f"""
            QFrame{{
                background-color: {self.bg};
                color: {self.fg};
                border-top-left-radius: {self.bd_radius[0]}px;
                border-top-right-radius: {self.bd_radius[1]}px;
            }}
        """)
        # 控件
        self.top_layout.addWidget(self.ico_label, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addWidget(self.drag_area, alignment=Qt.AlignLeft | Qt.AlignVCenter, stretch=1)
        self.top_layout.addWidget(self.minimize_button, Qt.AlignRight | Qt.AlignVCenter)
        self.top_layout.addWidget(self.maximize_button, Qt.AlignRight | Qt.AlignVCenter)
        self.top_layout.addWidget(self.close_button, Qt.AlignRight | Qt.AlignVCenter)

    def init_center_widget(self):
        super().init_center_widget()
        self.center_layout.addWidget(self.main_widget)

    def init_bottom_widget(self):
        self.bottom_widget.setFixedHeight(self.bottomH)
        self.bottom_widget.setStyleSheet(f"""
            QFrame{{
                background-color: {self.bg};
                color: {self.fg};
                border-bottom-left-radius: {self.bd_radius[0]}px;
                border-bottom-right-radius: {self.bd_radius[1]}px;
            }}
        """)
        # 控件
        self.bottom_layout.addWidget(self.status_label, Qt.AlignLeft | Qt.AlignVCenter)

    def resetTheme(self, theme_data):
        ...
