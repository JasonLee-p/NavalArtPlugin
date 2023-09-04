"""

"""
# 系统库
import os.path
import sys
import webbrowser
# 第三方库
from PyQt5 import _QOpenGLFunctions_2_0  # 用于解决打包时的bug
from PyQt5.QtWidgets import QApplication, QFileDialog, QGridLayout, QCheckBox

# 本地库
from path_utils import find_ptb_path, find_na_root_path
from GUI.QtGui import *
from OpenGLWindow import OpenGLWin
from PTB_design_reader import AdvancedHull
from OpenGL_objs import *
from ProjectFile import NewProjectDialog, ConfigFile
from ProjectFile import ProjectFile as PF


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(e)
        return False


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


class CurrentProject(PF):
    def __init__(self, name, path, original_na_file_path,
                 na_parts_data=None, operations=None, mode='空白', code='', save_time=''):
        PF.__init__(self, name, path, original_na_file_path,
                    na_parts_data, operations, mode, code, save_time)
        """
        修改配置文件对象Config，格式为：
        {
            'Config': self.Config,
            'ConfigProjects': self.ConfigProjects,
            'ProjectsFolder': self.ProjectsFolder
        }
        """
        Config.ProjectsFolder = os.path.dirname(self.Path)
        Config.Projects[self.Name] = self.Path

    @staticmethod
    def load_project(path) -> 'CurrentProject':
        prj = PF.load_project(path)
        return prj

    @staticmethod
    def init_project_from_config():
        global CurrentPrj
        path = list(Config.Projects.values())[-1]  # 获取最后一个项目的路径
        show_state(f"正在读取{path}...", 'process')  # 显示状态

        obj = CurrentProject.load_project(path)  # 读取项目文件
        if obj is None:
            return  # 如果读取失败，直接返回
        try:
            Handler.CurrentProjectData["Path"] = path  # 设置当前项目路径
            Handler.CurrentProjectData["Name"] = list(Config.Projects.keys())[-1]  # 设置当前项目名称
            Handler.CurrentProjectData["Object"] = obj
            Handler.CurrentProjectData["OriginalFilePath"] = Handler.CurrentProjectData["Object"].OriginalFilePath
            Handler.CurrentProjectData["PartsData"] = Handler.CurrentProjectData["Object"].NAPartsData
            # 读取成功，开始绘制
            na_hull = NAHull(data=Handler.CurrentProjectData["Object"].NAPartsData)  # 通过读取的船体设计文件，新建NaHull对象
            na_hull.DrawMap = na_hull.ColorPartsMap  # 设置绘制图层
            Handler.hull_design_tab.show_iron_obj(na_hull)  # 显示船体设计
            CurrentPrj = Handler.CurrentProjectData["Object"]
            show_state(f"{path}读取成功", 'success')  # 显示状态
        except FileNotFoundError:
            show_state(f"未找到配置中的{path}", "error")  # 显示状态
            # 删除配置中的该项目
            del Config.Projects[Handler.CurrentProjectData["Name"]]
            Config.save_config()  # 保存配置文件


class MainHandler:
    def __init__(self, window):
        # -------------------------------------------------------------------------------------信号与槽
        self.CurrentProjectData = {
            # 格式为：
            # "Object": None,
            # "Path": None,
            # "Name": None,
            # "OriginalFilePath": None,
            # "PartsData": None,
        }
        self.OperationHistory = Operation.history  # 用于记录操作的列表
        self.OperationIndex = Operation.index
        # -------------------------------------------------------------------------------------GUI设置
        self.window = window
        self.MenuMap = {
            " 设计": {
                "打开工程": self.open_project,
                "新建工程": self.new_project,
                "导出为": self.export_file,
                "保存工程": self.save_project,
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
        self.window.close_button.clicked.connect(self.close)
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
        global CurrentPrj
        # 选择路径
        if Config.ProjectsFolder == '':
            desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
            file_dialog = QFileDialog(self.window, "选择工程", desktop_path)
        else:
            file_dialog = QFileDialog(self.window, "选择工程", os.path.dirname(Config.ProjectsFolder))
        file_dialog.setNameFilter("json files (*.json)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        except IndexError:
            return
        # 修改Handler.CurrentProjectData
        obj = CurrentProject.load_project(file_path)
        if obj is None:
            return
        Handler.CurrentProjectData["Object"] = obj
        Handler.CurrentProjectData["Path"] = file_path  # 设置当前项目路径
        Handler.CurrentProjectData["Name"] = file_path.split('/')[-1].split('.')[0]  # 设置当前项目名称
        Handler.CurrentProjectData["OriginalFilePath"] = Handler.CurrentProjectData["Object"].OriginalFilePath
        Handler.CurrentProjectData["PartsData"] = Handler.CurrentProjectData["Object"].NAPartsData
        # 清空原来的所有对象，保存原来的工程文件对象
        for mt, objs in Handler.hull_design_tab.all_3d_obj.items():
            objs.clear()
        # 读取成功，开始绘制
        na_hull = NAHull(data=Handler.CurrentProjectData["Object"].NAPartsData)  # 通过读取的船体设计文件，新建NaHull对象
        na_hull.DrawMap = na_hull.ColorPartsMap  # 设置绘制图层
        Handler.hull_design_tab.show_iron_obj(na_hull)  # 显示船体设计
        CurrentPrj = Handler.CurrentProjectData["Object"]
        show_state(f"{file_path}读取成功", 'success')  # 显示状态

    def new_project(self, event=None):
        global CurrentPrj
        # 弹出对话框，获取工程名称和路径，以及其他相关信息
        new_project_dialog = NewProjectDialog(parent=self.window)
        new_project_dialog.exec_()
        # 如果确定新建工程
        if new_project_dialog.create_new_project:
            if new_project_dialog.generate_mode == 'NA':
                # 获取对话框返回的数据
                _original_na_path = new_project_dialog.OriginalNAPath
                _prj_path = new_project_dialog.ProjectPath  # name已经包含在path里了
                # 新建NAHull对象
                _na_hull = NAHull(path=_original_na_path)
                # 检测颜色种类，弹出对话框，选择颜色
                color_dialog = ColorDialog(self, _na_hull)
                color_dialog.exec_()
                self.hull_design_tab.show_iron_obj(_na_hull)
                # 生成工程文件对象
                Handler.CurrentProjectData["Path"] = _prj_path  # 设置当前项目路径
                Handler.CurrentProjectData["Name"] = _prj_path.split('/')[-1].split('.')[0]  # 设置当前项目名称
                Handler.CurrentProjectData["OriginalFilePath"] = _original_na_path
                Handler.CurrentProjectData["PartsData"] = NAHull.toJson(_na_hull.DrawMap)
                Handler.CurrentProjectData["Object"] = CurrentProject(
                    Handler.CurrentProjectData["Name"], _prj_path,
                    _original_na_path, Handler.CurrentProjectData["PartsData"],
                    operations={}, mode=PF.NA, code='', save_time=''
                )
                CurrentPrj = Handler.CurrentProjectData["Object"]
                # 保存工程文件
                Handler.CurrentProjectData["Object"].save()
                time = Handler.CurrentProjectData["Object"].SaveTime
                show_state(f"{time} {_prj_path}已保存", 'success')
                # 更新配置文件
                Config.Projects[Handler.CurrentProjectData["Name"]] = Handler.CurrentProjectData["Path"]

    def export_file(self, event):
        ...

    def save_project(self, event):
        self.CurrentProjectData["Object"].save()
        time = self.CurrentProjectData["Object"].SaveTime
        show_state(f"{time} {self.CurrentProjectData['Path']}已保存", 'success')

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

    def close(self) -> bool:
        # 重写关闭事件
        reply = QMessageBox().question(self.window, "提示", "是否退出？", MyMessageBox.Yes | MyMessageBox.No)
        if reply == QMessageBox.Yes:
            Config.save_config()  # 保存配置文件
            # 检查Handler是否有"object"属性，防止报错
            if "Object" in Handler.CurrentProjectData and Handler.CurrentProjectData["Object"] is not None:
                Handler.CurrentProjectData["Object"].save()  # 保存当前项目
                time = Handler.CurrentProjectData["Object"].SaveTime
                show_state(f"{time} {Handler.CurrentProjectData['Path']}已保存", 'success')
            self.window.close()
            return True
        else:
            return False


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
        self.NAPath = NAPath
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
        self.read_from_na_button = QPushButton("从NA新建")
        self.convertAdhull_button = QPushButton("从PTB转换")
        self.init_buttons()
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
        set_tool_bar_style(self.down_tool_bar)
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

    def init_buttons(self):
        set_top_button_style(self.save_button, 50)  # 保存按钮
        self.save_button.clicked.connect(self.save_file)
        self.up_layout.addWidget(self.save_button, alignment=Qt.AlignLeft)
        set_top_button_style(self.read_from_na_button, 100)  # 从NA读取按钮
        self.read_from_na_button.clicked.connect(self.read_from_na_button_pressed)
        self.up_layout.addWidget(self.read_from_na_button, alignment=Qt.AlignLeft)
        set_top_button_style(self.convertAdhull_button, 100)  # 从PTB转换按钮
        self.convertAdhull_button.clicked.connect(self.convertAdhull_button_pressed)
        self.up_layout.addWidget(self.convertAdhull_button, alignment=Qt.AlignLeft)

    def save_file(self):
        ...

    def read_from_na_button_pressed(self):
        # 打开文件选择窗口，目录为NavalArt目录 ===================================================
        file_dialog = QFileDialog(self, "选择图纸", self.NAPath)
        file_dialog.setNameFilter("na files (*.na)")
        file_dialog.exec_()
        try:
            _original_na_p = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        except IndexError:
            return
        try:
            _na_hull = NAHull(path=_original_na_p)
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开或不存在，请关闭后重试"
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        show_state(f"{_original_na_p}读取成功", 'success')
        # 获取用户选择的工程路径 ==========================================================================
        chosen_path = find_na_root_path() if Config.Projects == {} else os.path.dirname(Config.ProjectsFolder)
        save_dialog = QFileDialog(self, "选择工程保存路径", chosen_path)
        save_dialog.setFileMode(QFileDialog.AnyFile)
        save_dialog.setAcceptMode(QFileDialog.AcceptSave)
        save_dialog.setNameFilter("json files (*.json)")  # 仅让用户选择路径和文件名称，文件类型为json
        save_dialog.exec_()
        # 获取选择的文件路径
        try:
            _prj_path = save_dialog.selectedFiles()[0]
        except IndexError:
            return
        # 清空原来的所有对象，保存原来的工程文件对象
        for mt, objs in self.all_3d_obj.items():
            objs.clear()
        if Handler.CurrentProjectData["Object"] is not None:
            Handler.CurrentProjectData["Object"].save()
            time = Handler.CurrentProjectData["Object"].SaveTime
            show_state(f"{time} {_prj_path}已保存", 'success')
        # 检测颜色种类，弹出对话框，选择颜色
        color_dialog = ColorDialog(self, _na_hull)
        color_dialog.exec_()
        self.show_iron_obj(_na_hull)
        # 生成工程文件对象
        Handler.CurrentProjectData["Path"] = _prj_path  # 设置当前项目路径
        Handler.CurrentProjectData["Name"] = _prj_path.split('/')[-1].split('.')[0]  # 设置当前项目名称
        Handler.CurrentProjectData["OriginalFilePath"] = _prj_path
        Handler.CurrentProjectData["PartsData"] = NAHull.toJson(_na_hull.DrawMap)
        Handler.CurrentProjectData["Object"] = CurrentProject(
            Handler.CurrentProjectData["Name"], _prj_path,
            _original_na_p, Handler.CurrentProjectData["PartsData"],
            operations={}, mode=PF.NA, code='', save_time=''
        )
        # 保存工程文件
        Handler.CurrentProjectData["Object"].save()
        time = Handler.CurrentProjectData["Object"].SaveTime
        show_state(f"{time} {_prj_path}已保存", 'success')
        # 更新配置文件
        Config.Projects[Handler.CurrentProjectData["Name"]] = Handler.CurrentProjectData["Path"]

    def convertAdhull_button_pressed(self):
        """
        功能暂未实现
        :return:
        """
        MyMessageBox().information(self, "提示", "该功能暂未实现哦", MyMessageBox.Ok)
        # # 打开文件选择窗口，目录为PTB目录
        # file_dialog = QFileDialog(self, "选择图纸", self.PTBPath)
        # file_dialog.setNameFilter("xml files (*.xml)")
        # file_dialog.exec_()
        # try:
        #     file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        # except IndexError:
        #     return
        # self.PTBDesignPath = file_path
        # try:
        #     adhull = AdHull(file_path)
        # except AttributeError:
        #     _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
        #     # 白色背景的提示框
        #     MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
        #     return
        # except PermissionError:
        #     _txt = "该文件已被其他程序打开，请关闭后重试"
        #     MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
        #     return
        # if adhull.result["adHull"]:  # 如果存在进阶船壳
        #     # 弹出对话框，询问是否保存当前设计
        #     _txt = "是否保存当前设计？"
        #     reply = MyMessageBox().question(self, "提示", _txt, MyMessageBox.Yes | MyMessageBox.No)
        #     if reply == MyMessageBox.Yes:
        #         self.save_project()
        #     for mt, objs in self.all_3d_obj.items():
        #         objs.clear()
        #     show_state(f"正在读取{self.PTBDesignPath}...", 'process')
        #     self.show_iron_obj(adhull)
        #     show_state(f"{self.PTBDesignPath}读取成功", 'success')
        # else:
        #     _txt = "该设计不含进阶船体外壳，请重新选择哦"
        #     MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
        #     self.convertAdhull_button_pressed()
        #     return

    def show_iron_obj(self, obj):
        self.all_3d_obj["钢铁"].append(obj)
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
        set_top_button_style(self.open_button, 50)  # 打开按钮
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
        set_top_button_style(self.open_button, 50)  # 打开按钮
        self.open_button.clicked.connect(self.find_na_ship_button_pressed)
        self.up_layout.addWidget(self.open_button, alignment=Qt.AlignLeft)

    def find_na_ship_button_pressed(self):
        # 打开文件选择窗口，目录为NavalArt目录
        file_dialog = QFileDialog(self, "选择图纸", self.NAPath)
        file_dialog.setNameFilter("na files (*.na)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
        except IndexError:
            return
        self.NADesignPath = file_path
        try:
            na_hull = NAHull(path=file_path)
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开，请关闭后重试"
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        for mt, objs in self.all_3d_obj.items():
            objs.clear()
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
        self.center_grid_layout = QGridLayout()
        # 颜色行数
        lines = -1
        for color, num in self.color_partNum_map.items():
            index_ = list(self.color_partNum_map.keys()).index(color)
            lines += 1 if index_ % 15 == 0 else 0
            bg_ = QColor(color)
            fg_ = getFG_fromBG(bg_)
            # 色块
            color_block = QLabel(str(num))
            color_block.setFixedSize(60, 65)
            color_block.setAlignment(Qt.AlignCenter)
            color_block.setStyleSheet(f"background-color: {bg_.name()};color: {fg_.name()};"
                                      f"border-radius: 7px;"
                                      # 上边距
                                      f"margin-top: 20px;"
                                      f"font: 11pt '微软雅黑';")
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
            rgb_layout.setSpacing(0)
            # 选择框
            choose_box = QCheckBox()
            choose_box.setFixedSize(60, 16)
            # 居中
            choose_box.setStyleSheet("QCheckBox::indicator {width: 60px;height: 16px;}")
            self.color_choose_map[color] = choose_box
            # 添加到布局
            i_vertical = lines * 4
            i_horizontal = index_ % 15
            self.center_grid_layout.addWidget(color_block, i_vertical, i_horizontal, alignment=Qt.AlignCenter)
            self.center_grid_layout.addWidget(color_name, i_vertical + 1, i_horizontal, alignment=Qt.AlignCenter)
            self.center_grid_layout.addWidget(rgb_widget, i_vertical + 2, i_horizontal, alignment=Qt.AlignCenter)
            self.center_grid_layout.addWidget(choose_box, i_vertical + 3, i_horizontal, alignment=Qt.AlignCenter)

            # 把其他部件的左键也绑定choose_box修改事件
            color_block.mousePressEvent = lambda event, cb=choose_box: self.color_block_pressed(event, cb)
            color_name.mousePressEvent = lambda event, cb=choose_box: self.color_block_pressed(event, cb)
            rgb_widget.mousePressEvent = lambda event, cb=choose_box: self.color_block_pressed(event, cb)
        # 添加全选按钮
        self.all_choose_box = QCheckBox("全选")
        self.all_choose_box.setStyleSheet(f"color: {FG_COLOR0};"
                                          f"font: 11pt '微软雅黑';")
        self.all_choose_box.setFixedSize(80, 80)
        self.all_choose_box.stateChanged.connect(self.all_choose_box_state_changed)
        self.center_grid_layout.addWidget(
            self.all_choose_box, lines * 4 + 4, 0, 1, min(15, self.color_num), alignment=Qt.AlignCenter)
        # 设置布局
        if 3 < self.color_num <= 15:
            size = QSize(100 + self.color_num * 85, 380)
        elif self.color_num > 15:
            size = QSize(100 + 15 * 85, 380 + lines * 170)
        else:
            size = QSize(360, 380)
        super().__init__(parent, self.title, size, self.center_grid_layout)
        self.set_widget()

    @staticmethod
    def color_block_pressed(event, choose_box):
        if event.button() == Qt.LeftButton:
            choose_box.setChecked(not choose_box.isChecked())

    def all_choose_box_state_changed(self):
        if self.all_choose_box.isChecked():
            for color, choose_box in self.color_choose_map.items():
                choose_box.setChecked(True)
        else:
            for color, choose_box in self.color_choose_map.items():
                choose_box.setChecked(False)

    def set_widget(self):
        # 上下间距
        self.center_grid_layout.setSpacing(5)
        self.center_grid_layout.setContentsMargins(50, 30, 50, 0)
        # 居中

    def ensure(self):
        draw_map = {}
        for color, choose_box in self.color_choose_map.items():
            if choose_box.isChecked():
                draw_map[color] = self.color_parts_map[color]
        self.na_hull.DrawMap = draw_map
        if draw_map:
            super().ensure()
        else:
            MyMessageBox().information(self, "提示", "未选择任何颜色", MyMessageBox.Ok)


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
    NAPath = os.path.join(find_na_root_path(), "ShipSaves")
    # 读取配置
    Config = ConfigFile()
    # 初始化界面和事件处理器
    QApp = QApplication(sys.argv)
    QtWindow = MainWindow(Config)
    Handler = MainHandler(QtWindow)
    if Config.Projects != {}:
        CurrentProject.init_project_from_config()
    else:
        CurrentPrj = None
    QtWindow.show()  # 显示被隐藏的窗口
    # 主循环
    sys.exit(QApp.exec_())
