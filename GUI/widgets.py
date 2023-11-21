# -*- coding: utf-8 -*-
"""
主要窗口
"""
from GUI.basic_data import *
from GUI.basic_widgets import *


class MainWindow(Window):
    def __init__(self):
        super().__init__(None, title='NavalArt Hull Editor', ico_bites=BYTES_ICO, size=(1200, 800), resizable=True,
                         show_maximize=True)

    def init_top_widget(self):
        self.top_widget.setFixedHeight(self.topH)
        self.top_widget.setStyleSheet(f"""
            QWidget{{
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
        self.center_widget.setStyleSheet(f"""
            QWidget{{
                background-color: {self.bg};
                color: {self.fg};
            }}
        """)

    def resetTheme(self, theme_data):
        ...
