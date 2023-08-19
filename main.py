"""

"""
# 系统库
import sys
import webbrowser
# 第三方库
from PyQt5 import _QOpenGLFunctions_2_0  # 用于解决打包时的bug
from PyQt5.QtWidgets import QApplication, QFileDialog, QToolBar, QGridLayout

# 本地库
from path_utils import find_ptb_path
from GUI.QtGui import *
from OpenGLWindow import OpenGLWin
from PTB_design_reader import AdvancedHull
from OpenGL_objs import *
from ProjectFile import NewProjectDialog, ConfigFile, ProjectFile


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        return False


def show_state(txt, msg_type='process'):
    color_map = {
        'warning': 'orange',
        'success': f"{FG_COLOR0}",
        'process': 'gray',
        'error': f"{FG_COLOR1}",
    }
    label_ = Handler.window.statu_label
    if msg_type in color_map:
        label_.setStyleSheet(f'color: {color_map[msg_type]};')
    else:
        label_.setStyleSheet(f'color: {FG_COLOR0};')
    label_.setText(txt)


class Operation:
    # 定义可用的操作
    Select = 1
    DisSelect = 2
    ShowAdHull = 3

    # 操作历史记录
    history = []
    index = 0

    def __init__(self, operation_type, operation_data):
        """
        记录用户操作
        :param operation_type:
        :param operation_data:
        """
        self.operation_type = operation_type
        self.operation_data = operation_data
        Operation.history.append(self)


class MainHandler:
    def __init__(self, window):
        self.window = window
        self.MenuMap = {
            " 设计": {
                "打开工程": self.open_project,
                "新建工程": self.new_project,
                "导出为": self.export_file,
                "保存工程": self.save_file,
                "另存为": self.save_as_file,
            },
            " 编辑": {
                "撤销": self.undo,
                "重做": self.redo,
                "剪切": self.cut,
                "复制": self.copy,
                "粘贴": self.paste,
                "删除": self.delete,
                "全选": self.select_all
            },
            " 设置": {
                "界面主题": self.set_theme,
                "框线显示": self.set_lines,
            },
            " 视图": {
                "3D视图": self.thd_view,
                "缩小": self.zoom_out,
                "还原": self.zoom_reset,
                "全屏": self.full_screen
            },
            " 帮助": {"关于我们": self.about}
        }
        self.MainTabWidget = self.window.MainTabWidget
        self.window.add_top_bar(self.MenuMap)
        self.window.init_down_splitter()
        self.window.init_state_widget()
        self.MainLayout = self.window.MainLayout

        # 添加工作区选项卡
        self.read_adhull_tab = ReadPTBAdHullTab()
        self.read_na_hull_tab = ReadNAHullTab()
        self.hull_design_tab = HullDesignTab()
        self.armor_design_tab = ArmorDesignTab()
        self.tab_map = {
            "船体设计": self.hull_design_tab,
            "装甲设计": self.armor_design_tab,
            "预览PTB船壳": self.read_adhull_tab,
            "预览NA船体": self.read_na_hull_tab,
        }
        for tab_name in self.tab_map:
            self.MainTabWidget.addTab(self.tab_map[tab_name], tab_name)
        self.show_top_bar()

        # 添加标签页
        self.window.down_splitter.addWidget(self.MainTabWidget)
        self.right_widget = RightWidget()
        self.window.down_splitter.addWidget(self.right_widget)
        # 给标签页添加信号
        self.MainTabWidget.currentChanged.connect(self.tab_changed)
        # 计算屏幕宽度5/6
        self.window.down_splitter.setSizes([int(self.window.width() * 5 / 6), int(self.window.width() / 6)])
        self.window.showMaximized()
        # -----------------------------------------------------------------------------------------信号与槽
        self.OperationHistory = Operation.history  # 用于记录操作的列表
        self.OperationIndex = Operation.index

    def tab_changed(self):
        """
        更新right_widget的ActiveTab
        """
        # 在tab_map的键里寻找当前标签页的名称
        for tab_name in self.tab_map:
            if self.tab_map[tab_name] == self.MainTabWidget.currentWidget():
                self.right_widget.ActiveTab = tab_name
                # print(self.right_widget.ActiveTab)
                break

    def show_top_bar(self):
        self.window.top_layout.addWidget(self.window.logo, 0, Qt.AlignLeft)
        self.window.top_layout.addLayout(self.window.menu_layout)
        # self.window.top_layout.addStretch(1)
        # self.window.top_layout.addWidget(self.MainTabWidget, 0, Qt.AlignRight | Qt.AlignBottom)
        self.window.top_layout.addStretch(10)
        self.window.top_layout.addLayout(self.window.three_button_layout)
        self.window.top_layout.setContentsMargins(0, 0, 0, 0)
        self.window.top_layout.setSpacing(0)

    # ---------------------------------------------------------------------------------------------------

    def open_project(self, event):
        # 选择路径
        project_path = ''

    def new_project(self, event):
        new_project_dialog = NewProjectDialog(parent=self.window)
        new_project_dialog.exec_()

    def export_file(self, event):
        ...

    def save_file(self, event):
        ...

    def save_as_file(self, event):
        ...

    def undo(self, event):
        ...

    def redo(self, event):
        ...

    def cut(self, event):
        ...

    def copy(self, event):
        ...

    def paste(self, event):
        ...

    def delete(self, event):
        ...

    def select_all(self, event):
        ...

    def set_theme(self, event):
        theme_dialog = ThemeDialog(parent=self.window)
        theme_dialog.exec_()

    def set_lines(self, event):
        ...

    def thd_view(self, event):
        ...

    def zoom_out(self, event):
        ...

    def zoom_reset(self, event):
        ...

    def full_screen(self, event):
        ...

    @staticmethod
    def about(event):
        # 打开网页
        url = 'http://naval_plugins.e.cn.vc/'
        webbrowser.open(url)


class RightWidget(QWidget):
    def __init__(self, parent=None):
        self.ActiveTab = "读取PTB船壳"
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")
        self.ICO = QIcon(QPixmap.fromImage(QImage.fromData(ICO_)))  # 把图片编码转换成QIcon
        self.logo = QLabel()
        self.layout = QVBoxLayout()
        self.top1_layout = QHBoxLayout()
        self.init_layout()

    def init_layout(self):
        # 添加图片
        # self.logo.setPixmap(QPixmap.fromImage(QImage.fromData(ICO_)))
        # self.logo.setScaledContents(True)
        # self.logo.setFixedSize(256, 256)
        # self.top1_layout.setContentsMargins(0, 0, 0, 0)
        # self.top1_layout.setSpacing(0)
        # self.layout.setContentsMargins(0, 0, 0, 0)
        # self.layout.setSpacing(0)
        # 添加布局
        # self.top1_layout.addWidget(self.logo, 0, Qt.AlignTop)
        self.layout.addLayout(self.top1_layout)
        self.setLayout(self.layout)


class HullDesignTab(QWidget):
    def __init__(self, parent=None):
        self.AddImg = QIcon(QPixmap.fromImage(QImage.fromData(ADD_)))
        self.ChooseImg = QIcon(QPixmap.fromImage(QImage.fromData(CHOOSE_)))
        self.PTBPath = PTBPath
        self.PTBDesignPath = ''
        super().__init__(parent)
        # -----------------------------------------------------------------------------------GUI设置
        # 设置全局字体
        self.Font = QFont('微软雅黑', 8)
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = OpenGLWin()
        self.down_layout = QHBoxLayout()
        self.down_tool_bar = QToolBar()
        self.init_layout()
        self.save_button = QPushButton("保存")
        self.convertAdhull_button = QPushButton("从PTB转换")
        self.init_select_button()
        self.init_convertAdhull_button()
        self.up_layout.addStretch()
        # -----------------------------------------------------------------------------------操作区
        self.camera = self.ThreeDFrame.camera
        self.solid_obj = {
            "船底": self.ThreeDFrame.solid_obj["船底"],
            "钢铁": self.ThreeDFrame.solid_obj["钢铁"],
            "甲板": self.ThreeDFrame.solid_obj["甲板"],
        }
        self.line_group_obj = self.ThreeDFrame.line_group_obj

    def add_layer(self):
        ...

    def choose_mode(self):
        # 改变第一个按钮的颜色
        self.down_tool_bar.actions()[0].setChecked(True)

    def init_style(self):
        # 设置边距
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")

    def init_layout(self):
        self.up_layout.setSpacing(0)
        self.up_layout.setContentsMargins(0, 0, 0, 0)
        self.down_layout.setSpacing(0)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        self.init_tool_bar()
        self.down_layout.addWidget(self.ThreeDFrame)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.up_layout, stretch=0)
        # 添加分割线
        self.main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))
        self.main_layout.addLayout(self.down_layout, stretch=1)
        self.setLayout(self.main_layout)

    def init_tool_bar(self):
        # 设置工具栏
        self.down_tool_bar.setStyleSheet(f"background-color: {BG_COLOR0};")
        self.down_tool_bar.setOrientation(Qt.Vertical)
        self.down_tool_bar.setToolButtonStyle(Qt.ToolButtonIconOnly)  # 不显示文本
        self.down_tool_bar.setContentsMargins(0, 0, 0, 0)
        # 按钮样式
        self.down_tool_bar.setIconSize(QSize(26, 26))
        self.down_tool_bar.setFixedWidth(40)
        self.down_tool_bar.setMovable(True)
        self.down_tool_bar.setFloatable(True)
        self.down_tool_bar.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)

        choose_action = QAction(self.ChooseImg, "框选", self)
        add_layer_action = QAction(self.AddImg, "添加层", self)
        choose_action.triggered.connect(self.choose_mode)
        add_layer_action.triggered.connect(self.add_layer)
        self.down_tool_bar.addAction(choose_action)
        self.down_tool_bar.addAction(add_layer_action)
        # 打包工具栏
        self.down_layout.addWidget(self.down_tool_bar)

    def init_select_button(self):
        self.save_button.setFont(self.Font)
        # 设置样式：圆角、背景色、边框
        self.save_button.setStyleSheet(
            f"QPushButton{{background-color: {BG_COLOR0};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR0};}}"
            # 鼠标悬停样式
            f"QPushButton:hover{{background-color: {BG_COLOR3};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR3};}}"
            # 鼠标按下样式
            f"QPushButton:pressed{{background-color: {BG_COLOR2};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR2};}}"
        )
        # 设置大小
        self.save_button.setFixedSize(50, 30)
        self.save_button.clicked.connect(self.save_file)
        self.up_layout.addWidget(self.save_button, alignment=Qt.AlignLeft)

    def init_convertAdhull_button(self):
        self.convertAdhull_button.setFont(self.Font)
        # 设置样式：圆角、背景色、边框
        self.convertAdhull_button.setStyleSheet(
            f"QPushButton{{background-color: {BG_COLOR0};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR0};}}"
            # 鼠标悬停样式
            f"QPushButton:hover{{background-color: {BG_COLOR3};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR3};}}"
            # 鼠标按下样式
            f"QPushButton:pressed{{background-color: {BG_COLOR2};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR2};}}"
        )
        # 设置大小
        self.convertAdhull_button.setFixedSize(100, 30)
        self.convertAdhull_button.clicked.connect(self.convertAdhull_button_pressed)
        self.up_layout.addWidget(self.convertAdhull_button, alignment=Qt.AlignLeft)

    def save_file(self):
        ...

    def convertAdhull_button_pressed(self):
        # 打开文件选择窗口，目录为PTB目录
        file_dialog = QFileDialog(self, "选择图纸", self.PTBPath)
        file_dialog.setNameFilter("xml files (*.xml)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        except IndexError:
            return
        self.PTBDesignPath = file_path
        try:
            adhull = AdHull(file_path)
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开，请关闭后重试"
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        if adhull.result["adHull"]:  # 如果存在进阶船壳
            # 弹出对话框，询问是否保存当前设计
            _txt = "是否保存当前设计？"
            reply = MyMessageBox().question(self, "提示", _txt, MyMessageBox.Yes | MyMessageBox.No)
            if reply == MyMessageBox.Yes:
                self.save_file()
            self.line_group_obj.clear()
            show_state(f"正在读取{self.PTBDesignPath}...", 'process')
            self.show_add_hull(adhull)
            show_state(f"{self.PTBDesignPath}读取成功", 'success')
        else:
            _txt = "该设计不含进阶船体外壳，请重新选择哦"
            MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
            self.convertAdhull_button_pressed()
            return

    def show_add_hull(self, adhull_obj: AdvancedHull):
        self.line_group_obj.append(adhull_obj)
        # 更新ThreeDFrame的paintGL
        self.update_solid_obj()

    def update_solid_obj(self):
        self.ThreeDFrame.solid_obj["钢铁"] = self.solid_obj["钢铁"]
        self.ThreeDFrame.solid_obj["甲板"] = self.solid_obj["甲板"]
        self.ThreeDFrame.solid_obj["船底"] = self.solid_obj["船底"]
        self.ThreeDFrame.line_group_obj = self.line_group_obj

    # ==============================================================================================


class ReadPTBAdHullTab(QWidget):
    def __init__(self, parent=None):
        self.AddImg = QIcon(QPixmap.fromImage(QImage.fromData(ADD_)))
        self.ChooseImg = QIcon(QPixmap.fromImage(QImage.fromData(CHOOSE_)))
        self.PTBPath = PTBPath
        self.PTBDesignPath = ''
        super().__init__(parent)
        # -----------------------------------------------------------------------------------GUI设置
        # 设置全局字体
        self.Font = QFont('微软雅黑', 8)
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = OpenGLWin()
        self.down_layout = QHBoxLayout()
        self.down_tool_bar = QToolBar()
        self.init_layout()
        self.open_button = QPushButton("打开")
        self.init_open_button()
        self.up_layout.addStretch()
        # -----------------------------------------------------------------------------------操作区
        self.camera = self.ThreeDFrame.camera
        self.solid_obj = {
            "船底": self.ThreeDFrame.solid_obj["船底"],
            "钢铁": self.ThreeDFrame.solid_obj["钢铁"],
            "甲板": self.ThreeDFrame.solid_obj["甲板"],
        }
        self.line_group_obj = self.ThreeDFrame.line_group_obj

    def choose_mode(self):
        # 改变第一个按钮的颜色
        self.down_tool_bar.actions()[0].setChecked(True)

    def init_style(self):
        # 设置边距
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")

    def init_layout(self):
        self.up_layout.setSpacing(0)
        self.up_layout.setContentsMargins(0, 0, 0, 0)
        self.down_layout.setSpacing(0)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        self.init_tool_bar()
        self.down_layout.addWidget(self.ThreeDFrame)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.up_layout, stretch=0)
        # 添加分割线
        self.main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))
        self.main_layout.addLayout(self.down_layout, stretch=1)
        self.setLayout(self.main_layout)

    def init_tool_bar(self):
        # 设置工具栏  # TODO: 重构
        self.down_tool_bar.setStyleSheet(f"background-color: {BG_COLOR0};")
        self.down_tool_bar.setOrientation(Qt.Vertical)
        self.down_tool_bar.setToolButtonStyle(Qt.ToolButtonIconOnly)  # 不显示文本
        self.down_tool_bar.setContentsMargins(0, 0, 0, 0)
        # 按钮样式
        self.down_tool_bar.setIconSize(QSize(26, 26))
        self.down_tool_bar.setFixedWidth(40)
        self.down_tool_bar.setMovable(True)
        self.down_tool_bar.setFloatable(True)
        self.down_tool_bar.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)

        choose_action = QAction(self.ChooseImg, "框选", self)
        choose_action.triggered.connect(self.choose_mode)
        self.down_tool_bar.addAction(choose_action)
        # 打包工具栏
        self.down_layout.addWidget(self.down_tool_bar)

    def init_open_button(self):
        self.open_button.setFont(self.Font)
        # 设置样式：圆角、背景色、边框
        self.open_button.setStyleSheet(
            f"QPushButton{{background-color: {BG_COLOR0};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR0};}}"
            # 鼠标悬停样式
            f"QPushButton:hover{{background-color: {BG_COLOR3};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR3};}}"
            # 鼠标按下样式
            f"QPushButton:pressed{{background-color: {BG_COLOR2};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR2};}}"
        )
        # 设置大小
        self.open_button.setFixedSize(50, 30)
        self.open_button.clicked.connect(self.convertAdhull_button_pressed)
        self.up_layout.addWidget(self.open_button, alignment=Qt.AlignLeft)

    def convertAdhull_button_pressed(self):
        # 打开文件选择窗口，目录为PTB目录
        file_dialog = QFileDialog(self, "选择图纸", self.PTBPath)
        file_dialog.setNameFilter("xml files (*.xml)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        except IndexError:
            return
        self.PTBDesignPath = file_path
        try:
            adhull = AdHull(file_path)
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开，请关闭后重试"
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        if adhull.result["adHull"]:  # 如果存在进阶船壳
            self.line_group_obj.clear()
            show_state(f"正在读取{self.PTBDesignPath}...", 'process')
            self.show_add_hull(adhull)
            show_state(f"{self.PTBDesignPath}读取成功", 'success')
        else:
            _txt = "该设计不含进阶船体外壳，请重新选择哦"
            MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
            self.convertAdhull_button_pressed()
            return

    def show_add_hull(self, adhull_obj: AdvancedHull):
        self.line_group_obj.append(adhull_obj)
        # 更新ThreeDFrame的paintGL
        self.update_solid_obj()

    def update_solid_obj(self):
        self.ThreeDFrame.solid_obj["钢铁"] = self.solid_obj["钢铁"]
        self.ThreeDFrame.solid_obj["甲板"] = self.solid_obj["甲板"]
        self.ThreeDFrame.solid_obj["船底"] = self.solid_obj["船底"]
        self.ThreeDFrame.line_group_obj = self.line_group_obj

    # ==============================================================================================


class ReadNAHullTab(QWidget):
    def __init__(self, parent=None):
        self.NAPath = NAPath
        self.NADesignPath = ''
        super().__init__(parent)
        # 设置边距
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")
        # 设置全局字体
        self.Font = QFont('微软雅黑', 8)
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.down_widget = QWidget()
        self.down_layout = QHBoxLayout()
        self.down_widget.setLayout(self.down_layout)
        self.down_tool_bar = QToolBar()
        self.init_layout()
        # 设置样式
        self.setStyleSheet(f"background-color: {BG_COLOR0};")
        # 在upWidget添加图纸选择按钮
        self.select_button = QPushButton("打开")
        self.init_select_button()

    def init_layout(self):
        self.up_layout.setSpacing(0)
        self.up_layout.setContentsMargins(0, 0, 0, 0)
        self.down_widget.setContentsMargins(0, 0, 0, 0)
        self.down_widget.setStyleSheet(f"background-color: {BG_COLOR1};")
        self.down_layout.setSpacing(0)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.up_layout)
        # 添加分割线
        self.main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))
        self.main_layout.addWidget(self.down_widget, 1)
        self.setLayout(self.main_layout)

    def init_tool_bar(self):
        # 设置工具栏
        self.down_tool_bar.setStyleSheet(f"background-color: {BG_COLOR0};")
        # 初始位置
        self.down_tool_bar.setOrientation(Qt.Vertical)
        # self.down_tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.down_tool_bar.setMovable(True)
        self.down_tool_bar.setFloatable(True)
        self.down_tool_bar.setAllowedAreas(Qt.LeftToolBarArea | Qt.RightToolBarArea)
        self.down_tool_bar.setContentsMargins(0, 0, 0, 0)
        self.down_tool_bar.setIconSize(QSize(32, 32))
        self.down_tool_bar.setFixedWidth(32)

        # 添加工具栏按钮
        self.down_tool_bar.addAction(self.select_action)
        self.down_tool_bar.addAction(self.check_dot_action)
        self.down_tool_bar.addAction(self.check_slice_action)
        # 打包工具栏
        self.down_widget.layout().addWidget(self.down_tool_bar)

    def init_select_button(self):
        self.select_button.setFont(self.Font)
        # 设置样式：圆角、背景色、边框
        self.select_button.setStyleSheet(
            f"QPushButton{{background-color: {BG_COLOR0};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR0};}}"
            # 鼠标悬停样式
            f"QPushButton:hover{{background-color: {BG_COLOR3};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR3};}}"
            # 鼠标按下样式
            f"QPushButton:pressed{{background-color: {BG_COLOR2};"
            f"color: {FG_COLOR0};"
            f"border-radius: 0px;"
            f"border: 1px solid {BG_COLOR2};}}"
        )
        # 设置大小
        self.select_button.setFixedSize(50, 30)
        self.select_button.clicked.connect(self.select_button_pressed)
        self.up_layout.addWidget(self.select_button, alignment=Qt.AlignLeft)

    def select_button_pressed(self):
        # 打开文件选择窗口，目录为PTB目录
        file_dialog = QFileDialog(self, "选择图纸", self.NAPath)
        file_dialog.setNameFilter("na files (*.na)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
            self.NADesignPath = file_path
            try:
                ...  # TODO: 读取NA文件
            except IndexError and KeyError and AttributeError:
                _txt = "该文件不是有效的船体设计文件，请重新选择哦"
                # 白色背景的提示框
                MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
                return
            ...  # TODO: 读取NA文件
        except IndexError:
            return

    def show_add_hull(self, adhull_obj: AdvancedHull):
        print(adhull_obj.SlicesPoints)

    def show_obj(self, path="J330.solid_obj"):
        ...

    # ==============================================================================================

    def select_action(self):
        ...

    def check_dot_action(self):
        ...

    def check_slice_action(self):
        ...


class ArmorDesignTab(QWidget):
    ...


class ThemeDialog(BasicDialog):
    def __init__(self, parent, title="设置主题", size=QSize(300, 200)):
        self.center_layout = QGridLayout()
        self.cb0 = CircleSelectButton(7, init_statu=True)
        self.cb1 = CircleSelectButton(7)
        self.cb2 = CircleSelectButton(7)
        self.lb0 = MyLabel("白天", font=QFont("微软雅黑", 10))
        self.lb1 = MyLabel("夜晚", font=QFont("微软雅黑", 10))
        self.lb2 = MyLabel("自定义", font=QFont("微软雅黑", 10))
        self.center_layout.addWidget(self.cb0, 0, 0)
        self.center_layout.addWidget(self.cb1, 1, 0)
        self.center_layout.addWidget(self.cb2, 2, 0)
        self.center_layout.addWidget(self.lb0, 0, 1)
        self.center_layout.addWidget(self.lb1, 1, 1)
        self.center_layout.addWidget(self.lb2, 2, 1)
        # 事件
        self.selected_button = self.cb0
        super().__init__(parent, title, size, self.center_layout)
        self.set_widget()

    def set_widget(self):
        self.center_layout.setSpacing(8)
        self.center_layout.setContentsMargins(30, 20, 30, 0)

    def ensure(self):
        super().ensure()


if __name__ == '__main__':
    """
    if is_admin():
        print("程序已获取管理员身份")
    else:
        print("程序非管理员身份启动，正在获取管理员权限")
    c = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    if c != 0:
        print("获取管理员权限成功")
        # sys.exit(0)
    else:
        print("获取管理员权限失败")
        # os.system("pause")
    """
    # 初始化路径
    PTBPath = find_ptb_path()
    NAPath = find_na_path()
    # 读取配置
    Config = ConfigFile()
    Config.load_config()
    UsingTheme = Config.UsingTheme
    # 初始化界面和事件处理器
    QApp = QApplication(sys.argv)
    QtWindow = MainWindow(Config)
    Handler = MainHandler(QtWindow)
    # 保存配置
    Config.save_config()
    # 主循环
    sys.exit(QApp.exec_())
