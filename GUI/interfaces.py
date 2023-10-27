# -*- coding: utf-8 -*-
"""
主界面
"""
# 第三方库
from PySide2.QtWidgets import QSplitter, QMenu, QAction, QTabWidget
# 本地库
from .basic import *

if Theme == "Day":
    from UI_design.ImgPng_day import ICO, add, choose, minimize, maximize, maximize_exit, add_y, add_z
elif Theme == "Night":
    from UI_design.ImgPng_night import ICO, add, choose, minimize, maximize, maximize_exit, add_y, add_z

# 图标
ICO_ = b64decode(ICO)
ADD_ = b64decode(add)
CHOOSE_ = b64decode(choose)
ADD_Y = b64decode(add_y)
ADD_Z = b64decode(add_z)


class MainWindow(QWidget):
    def __init__(self, config):
        # 获取配置文件
        self.Config = config
        # 设置窗口属性
        self.topH = 35
        self.three_button_size = 25
        self.logo_size = 25
        # 读取图片
        self.ICO = QIcon(QPixmap.fromImage(QImage.fromData(ICO_)))  # 把图片编码转换成QIcon
        self.minimize_bg = b64decode(minimize)
        self.minimize_bg = QIcon(QPixmap.fromImage(QImage.fromData(self.minimize_bg)))
        self.maximize_bg = b64decode(maximize)
        self.maximize_bg = QIcon(QPixmap.fromImage(QImage.fromData(self.maximize_bg)))
        self.maximize_exit_bg = b64decode(maximize_exit)
        self.maximize_exit_bg = QIcon(QPixmap.fromImage(QImage.fromData(self.maximize_exit_bg)))
        self.close_bg = b64decode(close)
        self.close_bg = QIcon(QPixmap.fromImage(QImage.fromData(self.close_bg)))
        super().__init__(parent=None)
        self.hide()
        # 设置窗口属性
        self.setWindowTitle('NavalArt Plugin')
        self.setWindowIcon(self.ICO)
        self.set_style()
        self.setWindowFlags(Qt.FramelessWindowHint)  # 隐藏标题栏
        self.setMinimumSize(0.7 * WinWid, 0.7 * WinHei)
        self.setMaximumSize(WinWid, WinHei)
        # 添加布局器
        self.MainLayout = QVBoxLayout()  # 主布局器
        self.MainLayout.setContentsMargins(0, 0, 0, 0)
        self.MainLayout.setSpacing(0)
        self.top_layout = QHBoxLayout()  # top布局器
        self.logo = QLabel()  # logo
        self.menu_layout = QHBoxLayout()  # 菜单布局器
        self.three_button_layout = QHBoxLayout()  # 三个按钮布局器
        self.down_splitter = QSplitter(Qt.Horizontal)  # 下方布局器
        self.state_widget = QWidget()
        self.state_layout = QHBoxLayout()
        self.statu_label = MyLabel(" ", color="gray")
        self.setLayout(self.MainLayout)
        # 添加控件
        self.MainLayout.addLayout(self.top_layout)
        spl = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        spl.setStyleSheet(f"background-color:{BG_COLOR0};")
        self.MainLayout.addWidget(spl, alignment=Qt.AlignTop)
        self.MainLayout.addWidget(self.down_splitter, 1)  # 添加下方布局器
        spl = QFrame(self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken)
        spl.setStyleSheet(f"background-color:{BG_COLOR0};")
        self.MainLayout.addWidget(spl, alignment=Qt.AlignTop)
        self.MainLayout.addWidget(self.state_widget)  # 添加状态栏
        # 初始化TabWidget
        self.MainTabWidget = MainTabWidget()
        # 按钮初始化
        self.minimize_button = QPushButton()
        self.maximize_button = QPushButton()
        self.close_button = QPushButton()
        # 给top_layout的区域添加鼠标拖动功能
        self.m_flag = False
        self.m_Position = None
        self.drag = None  # 初始化拖动条

    def set_style(self):
        self.setStyleSheet(
            f"background-color: {BG_COLOR1};"
            f"color: {FG_COLOR0};"
        )

    def add_top_bar(self, menu_map):
        # 添加图片
        self.logo.setPixmap(self.ICO.pixmap(QSize(self.logo_size, self.logo_size)))
        self.logo.setFixedSize(55, self.topH)
        self.logo.setAlignment(Qt.AlignCenter)

        # 自定义菜单栏
        for menu_name in menu_map:
            menu_button = QPushButton(menu_name)
            menu_button.setFixedSize(55 * RATE, self.topH)
            menu_button.setStyleSheet(f"""
                QPushButton{{
                    background-color:{BG_COLOR1};
                    color:{FG_COLOR0};
                    border-radius: 0px;
                    border: 0px;
                    padding: 0px;
                }}
                QPushButton:hover{{
                    background-color:{BG_COLOR3};
                    color:{FG_COLOR0};
                    border-radius: 0px;
                    border: 0px;
                    padding: 0px;
                }}
                QPushButton::menu-indicator{{
                    image:none;
                }}
            """)
            menu_button.setFont(FONT_11)
            menu_button.setMenu(self.init_sub_menu(menu_name, menu_map))
            self.menu_layout.addWidget(menu_button, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # 最小化按钮
        self.set_button_style(self.minimize_button, self.minimize_bg, self.three_button_size, 'white', 'gray')
        self.minimize_button.clicked.connect(self.showMinimized)
        # 最大化按钮
        self.set_button_style(self.maximize_button, self.maximize_bg, self.three_button_size, 'white', 'gray')
        self.maximize_button.clicked.connect(self.showMaximized)
        # 关闭按钮
        self.set_button_style(self.close_button, self.close_bg, self.three_button_size, 'white', 'red')
        # 在main文件MainHandler中绑定关闭事件
        # 添加拖动条，控制窗口位置
        self.drag = self.add_drag_bar()
        # 添加按钮到子布局器
        self.three_button_layout.addWidget(self.minimize_button)
        self.three_button_layout.addWidget(self.maximize_button)
        self.three_button_layout.addWidget(self.close_button)

    def add_drag_bar(self):
        # 添加拖动条，控制窗口大小
        drag_widget = QWidget()
        # 设置宽度最大化
        drag_widget.setFixedWidth(10000)
        # drag_widget.setFixedSize(5, 5)
        drag_widget.setStyleSheet("background-color: rgba(0,0,0,0)")
        drag_widget.mouseMoveEvent = self.mouseMoveEvent
        drag_widget.mousePressEvent = self.mousePressEvent
        drag_widget.mouseReleaseEvent = self.mouseReleaseEvent
        self.MainLayout.addWidget(drag_widget, alignment=Qt.AlignBottom | Qt.AlignRight)
        return drag_widget

    def init_sub_menu(self, menu_name, menu_map):
        menu = QMenu()
        menu.setStyleSheet(
            f"QMenu{{background-color:{BG_COLOR1};color:{FG_COLOR0};border:1px solid {FG_COLOR2};}}"
            f"QMenu::item{{padding:3px 28px 3px 20px;}}"
            f"QMenu::item:selected{{background-color:{BG_COLOR3};color:{FG_COLOR0};}}"
            f"QMenu::separator{{height:1px;background-color:{FG_COLOR2};margin-left:14px;margin-right:7px;}}"
        )
        for sub_menu_name in menu_map[menu_name]:
            if isinstance(menu_map[menu_name][sub_menu_name], dict):
                # 添加子菜单
                sub_menu = menu.addMenu(sub_menu_name)
                for sub_sub_menu_name in menu_map[menu_name][sub_menu_name]:
                    sub_sub_menu = QAction(sub_sub_menu_name, self)
                    sub_sub_menu.triggered.connect(menu_map[menu_name][sub_menu_name][sub_sub_menu_name])
                    sub_menu.addAction(sub_sub_menu)
            else:
                sub_menu = QAction(sub_menu_name, self)
                sub_menu.triggered.connect(menu_map[menu_name][sub_menu_name])
                menu.addAction(sub_menu)
            # else:
            #     # 添加子菜单
            #     sub_menu = menu.addMenu(sub_menu_name)
            #     for sub_sub_menu_name in menu_map[menu_name][sub_menu_name]:
            #         sub_sub_menu = QAction(sub_sub_menu_name, self)
            #         sub_sub_menu.triggered.connect(menu_map[menu_name][sub_menu_name][sub_sub_menu_name])
            #         sub_menu.addAction(sub_sub_menu)
        return menu

    def set_button_style(self, button, icon, icon_size, color, hover_color):
        button.setFixedSize(55, self.topH)
        button.setIcon(icon)
        button.setIconSize(QSize(icon_size, icon_size))
        button.setStyleSheet(f'QPushButton{{border:none;color:{color};}}'
                             f'QPushButton:hover{{background-color:{hover_color};}}')

    def init_state_widget(self):
        self.state_widget.setLayout(self.state_layout)
        self.state_layout.addWidget(self.statu_label)
        self.statu_label.setFixedHeight(20)
        self.statu_label.setText("初始化编辑器完成")

    def init_down_splitter(self):
        self.down_splitter.setHandleWidth(1)  # 设置分割条的宽度
        self.down_splitter.setStyleSheet(  # 设置分割条的样式
            "QSplitter::handle{background-color:gray;}"
            "QSplitter::handle:hover{background-color:darkgray;}"
            "QSplitter::handle:pressed{background-color:lightgray;}")

    def showMaximized(self):
        # 检查是否已经最大化
        if self.isMaximized():
            self.showNormal()
            self.maximize_button.setIcon(self.maximize_exit_bg)
        else:
            super().showMaximized()
            self.maximize_button.setIcon(self.maximize_bg)

    def mousePressEvent(self, event):
        # 鼠标按下时，记录当前位置，若在标题栏内且非最大化，则允许拖动
        if event.button() == Qt.LeftButton and event.y() < self.topH and self.isMaximized() is False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()
            event.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        # 拖动窗口时，鼠标释放后停止拖动
        self.m_flag = False if self.m_flag else self.m_flag

    def mouseMoveEvent(self, QMouseEvent):
        # 当鼠标在标题栏按下且非最大化时，移动窗口
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)
            QMouseEvent.accept()


class MainTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # 设置标签页
        self.setDocumentMode(True)
        self.setTabPosition(QTabWidget.North)
        self.setMovable(True)
        # 设置标签栏向下对齐
        self.setStyleSheet(
            f"QTabBar::tab{{background-color:{BG_COLOR0};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-width:30ex;"
            f"border-top:0px solid {FG_COLOR2};"
            f"border-bottom:1px solid {FG_COLOR2};}}"
            # 设置选中标签栏样式
            f"QTabBar::tab:selected{{background-color:{BG_COLOR3};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-width:30ex;"
            f"border-top:0px solid {FG_COLOR2};"
            f"border-bottom:1px solid {FG_COLOR2};}}"
            # 设置鼠标悬停标签栏样式
            f"QTabBar::tab:hover{{background-color:{BG_COLOR0};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-width:30ex;"
            f"border-top:0px solid {FG_COLOR2};"
            f"border-bottom:1px solid {FG_COLOR1};}}"
        )
