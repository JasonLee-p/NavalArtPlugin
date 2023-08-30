"""

"""
# 系统库
import sys
import webbrowser
# 第三方库
from PyQt5 import _QOpenGLFunctions_2_0  # 用于解决打包时的bug
from PyQt5.QtWidgets import QApplication, QFileDialog, QToolBar, QGridLayout, QSpinBox, QCheckBox, QSizePolicy

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


def front_completion(txt, length, add_char):
    """
    用于在字符串前补全字符
    :param txt: 原字符串
    :param length: 补全后的长度
    :param add_char: 用于补全的字符
    :return: 补全后的字符串
    """
    if len(txt) < length:
        return add_char * (length - len(txt)) + txt
    else:
        return txt


def getFG_fromBG(bg: QColor):
    # 如果红绿蓝三色的平均值小于128，那么前景色为白色，否则为黑色
    if (bg.red() + bg.green() + bg.blue()) / 3 < 128:
        return QColor(255, 255, 255)
    else:
        return QColor(0, 0, 0)


def show_state(txt, msg_type='process'):
    """
    显示状态栏信息
    :param txt:
    :param msg_type:
    :return:
    """
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
                "操作灵敏度": self.set_sensitivity,
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
            "预览NA船体": self.read_na_hull_tab,
            "预览PTB船壳": self.read_adhull_tab,
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

    def set_sensitivity(self, event):
        sensitive_dialog = SensitiveDialog(parent=self.window)
        sensitive_dialog.exec_()

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
        self.ThreeDFrame = OpenGLWin(Config.Sensitivity)
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
        self.environment_obj = self.ThreeDFrame.environment_obj
        self.all_3d_obj = self.ThreeDFrame.all_3d_obj

    def add_layer(self):
        ...

    def choose_mode(self):
        if self.down_tool_bar.actions()[0].isChecked():
            self.ThreeDFrame.mode = OpenGLWin.Selectable
        else:
            self.ThreeDFrame.mode = OpenGLWin.UnSelectable

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
        # 设置可以选中
        choose_action.setCheckable(True)
        choose_action.setChecked(True)
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
            for mt, objs in self.all_3d_obj.items():
                objs.clear()
            show_state(f"正在读取{self.PTBDesignPath}...", 'process')
            self.show_add_hull(adhull)
            show_state(f"{self.PTBDesignPath}读取成功", 'success')
        else:
            _txt = "该设计不含进阶船体外壳，请重新选择哦"
            MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
            self.convertAdhull_button_pressed()
            return

    def show_add_hull(self, adhull_obj: AdHull):
        self.all_3d_obj["钢铁"].append(adhull_obj)
        # 更新ThreeDFrame的paintGL
        self.update_3d_obj()

    def update_3d_obj(self):
        self.environment_obj = self.environment_obj
        self.ThreeDFrame.all_3d_obj = self.all_3d_obj

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
        self.ThreeDFrame = OpenGLWin(Config.Sensitivity)
        self.down_layout = QHBoxLayout()
        self.down_tool_bar = QToolBar()
        self.init_layout()
        self.open_button = QPushButton("打开")
        self.init_open_button()
        self.up_layout.addStretch()
        # -----------------------------------------------------------------------------------操作区
        self.camera = self.ThreeDFrame.camera
        self.environment_obj = self.ThreeDFrame.environment_obj
        self.all_3d_obj = self.ThreeDFrame.all_3d_obj

    def choose_mode(self):
        if self.down_tool_bar.actions()[0].isChecked():
            self.ThreeDFrame.mode = OpenGLWin.Selectable
        else:
            self.ThreeDFrame.mode = OpenGLWin.UnSelectable

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
        # 设置可以选中
        choose_action.setCheckable(True)
        choose_action.setChecked(True)
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
            for mt, objs in self.all_3d_obj.items():
                objs.clear()
            show_state(f"正在读取{self.PTBDesignPath}...", 'process')
            self.show_add_hull(adhull)
            show_state(f"{self.PTBDesignPath}读取成功", 'success')
        else:
            _txt = "该设计不含进阶船体外壳，请重新选择哦"
            MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
            self.convertAdhull_button_pressed()
            return

    def show_add_hull(self, adhull_obj: AdvancedHull):
        self.all_3d_obj["钢铁"].append(adhull_obj)
        # 更新ThreeDFrame的paintGL
        self.update_3d_obj()

    def update_3d_obj(self):
        self.environment_obj = self.environment_obj
        self.ThreeDFrame.all_3d_obj = self.all_3d_obj

    # ==============================================================================================


class ReadNAHullTab(QWidget):
    def __init__(self, parent=None):
        self.AddImg = QIcon(QPixmap.fromImage(QImage.fromData(ADD_)))
        self.ChooseImg = QIcon(QPixmap.fromImage(QImage.fromData(CHOOSE_)))
        self.NAPath = NAPath
        self.NADesignPath = ''
        super().__init__(parent)
        # -----------------------------------------------------------------------------------GUI设置
        # 设置全局字体
        self.Font = QFont('微软雅黑', 8)
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = OpenGLWin(Config.Sensitivity)
        self.down_layout = QHBoxLayout()
        self.down_tool_bar = QToolBar()
        self.init_layout()
        self.open_button = QPushButton("打开")
        self.init_open_button()
        self.up_layout.addStretch()
        # -----------------------------------------------------------------------------------操作区
        self.camera = self.ThreeDFrame.camera
        self.environment_obj = self.ThreeDFrame.environment_obj
        self.all_3d_obj = self.ThreeDFrame.all_3d_obj

    def choose_mode(self):
        # 切换3d界面的选择模式
        if self.down_tool_bar.actions()[0].isChecked():
            self.ThreeDFrame.mode = OpenGLWin.Selectable
        else:
            self.ThreeDFrame.mode = OpenGLWin.UnSelectable

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
        # 设置可以选中
        choose_action.setCheckable(True)
        choose_action.setChecked(True)
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
        file_dialog = QFileDialog(self, "选择图纸", self.NAPath)
        file_dialog.setNameFilter("na files (*.na)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        except IndexError:
            return
        self.NADesignPath = file_path
        try:
            na_hull = NAHull(file_path)
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开，请关闭后重试"
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        show_state(f"正在读取{self.NADesignPath}...", 'process')
        show_state(f"{self.NADesignPath}读取成功", 'success')
        # 检测颜色种类，弹出对话框，选择颜色
        color_dialog = ColorDialog(self, na_hull)
        color_dialog.exec_()
        self.show_na_hull(na_hull)

    def show_na_hull(self, na_hull_obj):
        self.all_3d_obj["钢铁"].append(na_hull_obj)
        # 更新ThreeDFrame的paintGL
        self.update_3d_obj()

    def update_3d_obj(self):
        self.environment_obj = self.environment_obj
        self.ThreeDFrame.all_3d_obj = self.all_3d_obj

    # ==============================================================================================


class ArmorDesignTab(QWidget):
    ...


class ThemeDialog(BasicDialog):
    def __init__(self, parent, title="设置主题", size=QSize(300, 200)):
        self.center_layout = QGridLayout()
        self.cb0 = QPushButton("")
        self.cb1 = QPushButton("")
        self.cb2 = QPushButton("")
        self.button_group = CircleSelectButtonGroup(
            [self.cb0, self.cb1, self.cb2],
            parent=self,
            half_size=7
        )
        self.lb0 = MyLabel("白天", font=QFont("微软雅黑", 10))
        self.lb1 = MyLabel("夜晚", font=QFont("微软雅黑", 10))
        self.lb2 = MyLabel("自定义", font=QFont("微软雅黑", 10))
        self.center_layout.addWidget(self.cb0, 0, 0)
        self.center_layout.addWidget(self.cb1, 1, 0)
        self.center_layout.addWidget(self.cb2, 2, 0)
        self.center_layout.addWidget(self.lb0, 0, 1)
        self.center_layout.addWidget(self.lb1, 1, 1)
        self.center_layout.addWidget(self.lb2, 2, 1)
        super().__init__(parent, title, size, self.center_layout)
        self.set_widget()

    def set_widget(self):
        self.center_layout.setSpacing(8)
        self.center_layout.setContentsMargins(30, 20, 30, 0)

    def ensure(self):
        super().ensure()
        if self.button_group.selected_bt_index == 0:
            Config.Config["Theme"] = "Day"
        elif self.button_group.selected_bt_index == 1:
            Config.Config["Theme"] = "Night"
        elif self.button_group.selected_bt_index == 2:
            # 提示自定义功能未开放
            MyMessageBox().information(self, "提示", "自定义功能未开放", MyMessageBox.Ok)
            return
        # 提示保存成功，建议重启程序
        show_state("主题保存成功，建议重启程序", "success")
        Config.save_config()  # 保存配置


class SensitiveDialog(BasicDialog):
    def __init__(self, parent, title="设置灵敏度", size=QSize(300, 200)):
        self.center_layout = QGridLayout()
        self.lb0 = MyLabel("缩放灵敏度", font=QFont("微软雅黑", 10))
        self.lb1 = MyLabel("旋转灵敏度", font=QFont("微软雅黑", 10))
        self.lb2 = MyLabel("平移灵敏度", font=QFont("微软雅黑", 10))
        # 滑动条
        self.sld0 = QSlider(Qt.Horizontal)
        self.sld1 = QSlider(Qt.Horizontal)
        self.sld2 = QSlider(Qt.Horizontal)
        self.sld0.setMinimum(0)
        self.sld0.setMaximum(100)
        self.sld1.setMinimum(0)
        self.sld1.setMaximum(100)
        self.sld2.setMinimum(0)
        self.sld2.setMaximum(100)
        self.sld0.setValue(int(100 * Config.Sensitivity["缩放"]))
        self.sld1.setValue(int(100 * Config.Sensitivity["旋转"]))
        self.sld2.setValue(int(100 * Config.Sensitivity["平移"]))
        self.center_layout.addWidget(self.lb0, 0, 0)
        self.center_layout.addWidget(self.lb1, 1, 0)
        self.center_layout.addWidget(self.lb2, 2, 0)
        self.center_layout.addWidget(self.sld0, 0, 1)
        self.center_layout.addWidget(self.sld1, 1, 1)
        self.center_layout.addWidget(self.sld2, 2, 1)
        self.result = [Config.Sensitivity["缩放"], Config.Sensitivity["旋转"], Config.Sensitivity["平移"]]
        for i in range(3):
            self.result[i] = self.result[i] * 100
        # 绑定事件
        self.sld0.valueChanged.connect(self.value_changed0)
        self.sld1.valueChanged.connect(self.value_changed1)
        self.sld2.valueChanged.connect(self.value_changed2)
        super().__init__(parent, title, size, self.center_layout)
        self.set_widget()

    def value_changed0(self):
        self.result[0] = self.sld0.value()

    def value_changed1(self):
        self.result[1] = self.sld1.value()

    def value_changed2(self):
        self.result[2] = self.sld2.value()

    def set_widget(self):
        self.center_layout.setSpacing(8)
        self.center_layout.setContentsMargins(30, 20, 30, 0)

    def ensure(self):
        super().ensure()
        Config.Sensitivity["缩放"] = self.result[0] * 0.01
        Config.Sensitivity["旋转"] = self.result[1] * 0.01
        Config.Sensitivity["平移"] = self.result[2] * 0.01
        Config.save_config()
        for c in Camera.all_cameras:
            c.Sensitivity = Config.Sensitivity


class ColorDialog(BasicDialog):
    def __init__(self, parent, na_hull):
        self.title = "选择：该设计中 船体独有的颜色"
        self.na_hull = na_hull
        self.color_parts_map = self.na_hull.ColorPartsMap
        self.color_num = len(self.color_parts_map)
        self.color_partNum_map = {}
        for color, parts in self.color_parts_map.items():
            self.color_partNum_map[color] = len(parts)
        # 把颜色按照数量排序
        self.color_partNum_map = dict(sorted(self.color_partNum_map.items(), key=lambda x: x[1], reverse=True))
        self.color_choose_map = {}
        # 生成颜色选择按钮（显示出该颜色，并且在色块上显示出该颜色对应的部件数量，下方是勾选框，用于选择是否显示该颜色）
        self.center_layout = QGridLayout()
        for color, num in self.color_partNum_map.items():
            index_ = list(self.color_partNum_map.keys()).index(color)
            bg_ = QColor(color)
            fg_ = getFG_fromBG(bg_)
            # 色块
            color_block = QLabel(str(num))
            color_block.setFixedSize(55, 45)
            color_block.setAlignment(Qt.AlignCenter)
            color_block.setStyleSheet(f"background-color: {bg_.name()};color: {fg_.name()};"
                                      f"border-radius: 5px;"
                                      f"border: 1px solid {bg_.name()};"
                                      f"font: 12pt '微软雅黑';")
            # 16进制色名
            color_name = QLabel(color)
            color_name.setAlignment(Qt.AlignCenter)
            color_name.setStyleSheet(f"color: {FG_COLOR0};"
                                     f"font: 7pt '微软雅黑';")
            # RGB色名
            rgb_widget = QWidget()
            rgb_layout = QVBoxLayout()
            rgb_widget.setLayout(rgb_layout)
            red = QLabel(f"R {front_completion(str(bg_.red()), 3, '0')}")
            green = QLabel(f"G {front_completion(str(bg_.green()), 3, '0')}")
            blue = QLabel(f"B {front_completion(str(bg_.blue()), 3, '0')}")
            red.setAlignment(Qt.AlignCenter)
            green.setAlignment(Qt.AlignCenter)
            blue.setAlignment(Qt.AlignCenter)
            red.setStyleSheet(f"color: red;font: 7pt '微软雅黑';")
            green.setStyleSheet(f"color: green;font: 7pt '微软雅黑';")
            blue.setStyleSheet(f"color: blue;font: 7pt '微软雅黑';")
            rgb_layout.addWidget(red)
            rgb_layout.addWidget(green)
            rgb_layout.addWidget(blue)
            rgb_layout.setSpacing(2)
            # 选择框
            choose_box = QCheckBox()
            choose_box.setFixedSize(20, 20)
            self.color_choose_map[color] = choose_box
            # 添加到布局
            self.center_layout.addWidget(color_block, 0, index_)
            self.center_layout.addWidget(color_name, 1, index_)
            self.center_layout.addWidget(rgb_widget, 2, index_)
            self.center_layout.addWidget(choose_box, 3, index_, alignment=Qt.AlignCenter)
            # 把其他部件的左键也绑定choose_box修改事件
            color_block.mousePressEvent = lambda event, cb=choose_box: self.color_block_pressed(event, cb)
            color_name.mousePressEvent = lambda event, cb=choose_box: self.color_block_pressed(event, cb)
            rgb_widget.mousePressEvent = lambda event, cb=choose_box: self.color_block_pressed(event, cb)
        super().__init__(parent, self.title, QSize(self.color_num * 90, 350), self.center_layout)
        self.set_widget()

    @staticmethod
    def color_block_pressed(event, choose_box):
        if event.button() == Qt.LeftButton:
            choose_box.setChecked(not choose_box.isChecked())

    def set_widget(self):
        # 上下间距
        self.center_layout.setSpacing(8)
        self.center_layout.setContentsMargins(50, 50, 50, 0)

    def ensure(self):
        draw_map = {}
        for color, choose_box in self.color_choose_map.items():
            if choose_box.isChecked():
                draw_map[color] = self.color_parts_map[color]
        self.na_hull.DrawMap = draw_map
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
    Projects = Config.Projects
    # 初始化界面和事件处理器
    QApp = QApplication(sys.argv)
    QtWindow = MainWindow(Config)
    Handler = MainHandler(QtWindow)
    QtWindow.show()  # 显示被隐藏的窗口
    # 保存配置
    Config.save_config()
    # 主循环
    sys.exit(QApp.exec_())
