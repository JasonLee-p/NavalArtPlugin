"""

"""
# 系统库
import os.path
import sys
import webbrowser
# 第三方库
from PyQt5 import _QOpenGLFunctions_2_0  # 这个库必须导入，否则打包后会报错
from PyQt5.QtGui import QMouseEvent, QCursor, QKeySequence
from PyQt5.QtWidgets import QApplication, QFileDialog, QGridLayout, QTextEdit, QShortcut

# 本地库
from NA_design_reader import Part
from path_utils import find_ptb_path
from GUI.QtGui import *
from GUI.dialogs import NewProjectDialog, ColorDialog, ThemeDialog, SensitiveDialog
from OpenGLWindow import OpenGLWin, OpenGLWin2
from PTB_design_reader import AdvancedHull
from OpenGL_objs import *
from project_file import ConfigFile
from project_file import ProjectFile as PF
from right_element_view import Mod1SinglePart


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
        # 重置NavalArt的Part的ShipsAllParts
        Part.ShipsAllParts = []

    @staticmethod
    def load_project(path) -> 'CurrentProject':
        prj = PF.load_project(path)
        if prj is None:
            return None
        # 重置NavalArt的Part的ShipsAllParts
        Part.ShipsAllParts = []
        # 修改配置文件的ProjectsFolder和Projects
        Config.ProjectsFolder = os.path.dirname(path)
        Config.Projects[prj.Name] = path
        # 重置NavalArt的Part的ShipsAllParts
        Part.ShipsAllParts = []
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
            na_hull.get_ys_and_zs()  # 给na_hull.ys和na_hull.zs赋值
            na_hull.get_layers()  # 给na_hull.xzLayers和na_hull.xyLayers赋值
            Handler.hull_design_tab.show_iron_obj(na_hull)  # 显示船体设计
            CurrentPrj = Handler.CurrentProjectData["Object"]
            show_state(f"{path}读取成功", 'success')  # 显示状态
        except FileNotFoundError:
            show_state(f"未找到配置中的{path}", "error")  # 显示状态
            # 删除配置中的该项目
            del Config.Projects[Handler.CurrentProjectData["Name"]]
            Config.save_config()  # 保存配置文件


class MainWin(MainWindow):
    def __init__(self, parent=None):
        MainWindow.__init__(self, parent)


class GLWin(OpenGLWin):
    def __init__(self, parent=None, various_mode=False):
        OpenGLWin.__init__(self, parent, various_mode)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            Handler.right_widget.update_tab1()
        elif event.button() == Qt.RightButton and Handler.right_widget.ActiveTab == "船体设计":
            if Handler.hull_design_tab.ThreeDFrame.rotate_start == Handler.hull_design_tab.ThreeDFrame.lastPos:
                Handler.hull_design_tab.menu.exec_(QCursor.pos())


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
        self.right_widget = RightTabWidget()
        self.window.down_splitter.addWidget(self.right_widget)
        # 给标签页添加信号
        self.MainTabWidget.currentChanged.connect(self.tab_changed)
        # 计算屏幕宽度5/6
        self.window.down_splitter.setSizes([self.window.width(), 1])
        self.window.showMaximized()

    def tab_changed(self):
        """
        更新right_widget的ActiveTab
        """
        # 在tab_map的键里寻找当前标签页的名称
        for tab_name in self.tab_map:
            if self.tab_map[tab_name] == self.MainTabWidget.currentWidget():
                self.right_widget.ActiveTab = tab_name
                if self.right_widget.ActiveTab != "船体设计":
                    # 隐藏right_widget.tab1_current_widget
                    self.right_widget.tab1_current_widget.hide()
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
            file_dialog = QFileDialog(self.window, "选择工程", Config.ProjectsFolder)
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
        Handler.hull_design_tab.zx_layer_obj.clear()
        Handler.hull_design_tab.yx_layer_obj.clear()
        Handler.hull_design_tab.left_view_obj.clear()
        # 读取成功，开始绘制
        na_hull = NAHull(data=Handler.CurrentProjectData["Object"].NAPartsData)  # 通过读取的船体设计文件，新建NaHull对象
        na_hull.DrawMap = na_hull.ColorPartsMap  # 设置绘制图层
        na_hull.get_ys_and_zs()  # 给na_hull.ys和na_hull.zs赋值
        na_hull.get_layers()  # 给na_hull.xzLayers和na_hull.xyLayers赋值
        Handler.hull_design_tab.show_iron_obj(na_hull)  # 显示船体设计
        CurrentPrj = Handler.CurrentProjectData["Object"]
        show_state(f"{file_path}读取成功", 'success')  # 显示状态
        # 更新配置文件（把该条目改到字典的最后一项）
        del Config.Projects[Handler.CurrentProjectData["Name"]]
        Config.Projects[Handler.CurrentProjectData["Name"]] = Handler.CurrentProjectData["Path"]
        Config.save_config()  # 保存配置文件

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
        theme_dialog = ThemeDialog(config=Config, show_state_func=show_state, parent=self.window)
        theme_dialog.exec_()

    def set_sensitivity(self, event):
        sensitive_dialog = SensitiveDialog(config=Config, camera=Camera, parent=self.window)
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


class RightTabWidget(QTabWidget):
    def __init__(self, parent=None):
        """
        右侧工具栏
        :param parent:
        """
        super().__init__(parent)
        self.ICO = QIcon(QPixmap.fromImage(QImage.fromData(ICO_)))  # 把图片编码转换成QIcon
        self.tab1_main_layout = QVBoxLayout()
        self.tab2_main_layout = QVBoxLayout()
        # ============================================================================tab1_mod1的三种界面
        self.tab1_mod1_widget_singlePart = Mod1SinglePart()
        self.tab1_mod1_widget_verticalPartSet = QWidget()
        self.tab1_mod1_widget_horizontalPartSet = QWidget()
        self.tab1_mod1_widget_verHorPartSet = QWidget()

        self.tab1_mod1_grid_verticalPartSet = QGridLayout()
        self.tab1_mod1_grid_horizontalPartSet = QGridLayout()
        self.tab1_mod1_grid_verHorPartSet = QGridLayout()
        self.tab1_current_widget = self.tab1_mod1_widget_singlePart
        # ===========================================================================tab1_mod2的两种界面
        self.tab1_mod2_widget_singleLayer = QWidget()
        self.tab1_mod2_widget_multiLayer = QWidget()
        self.tab1_mod2_grid_singleLayer = QGridLayout()
        self.tab1_mod2_grid_multiLayer = QGridLayout()
        # GUI绑定和样式
        self.init_style()
        self.bind_widget()
        # 信号
        self.ActiveTab = "船体设计"
        # if self.ActiveTab == "船体设计":
        #     self.show_mod = Handler.hull_design_tab.ThreeDFrame.show_3d_obj_mode

    def update_tab1(self):
        ThreeDFrame = Handler.hull_design_tab.ThreeDFrame
        _len = len(ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode])
        self.tab1_current_widget.hide()  # 隐藏当前的widget

        # 当被选中物体变化的时候，更新tab1的内容
        if _len == 1:  # ================================================================== 只有一个物体
            # 获取选中的物体
            selected_obj = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
            if type(selected_obj) in (Part, AdjustableHull):
                # 更新类型
                self.tab1_mod1_widget_singlePart.show()
                self.tab1_current_widget = self.tab1_mod1_widget_singlePart
                self.tab1_mod1_widget_singlePart.update_context(selected_obj)
            elif type(selected_obj) == NaHullXZLayer:
                self.tab1_mod2_widget_singleLayer.show()  # TODO: 显示tab1_mod2_grid_singleLayer
                self.tab1_current_widget = self.tab1_mod2_widget_singleLayer
            else:
                ...
                # TODO: 其他类型的物体
        elif _len > 1:  # =================================================================== 多个物体
            _type = type(ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0])
            if _type in (Part, AdjustableHull):
                x_list = []
                z_list = []
                y_list = []
                for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode]:
                    if selected_obj is None:
                        return
                    if x_list.count(selected_obj.Pos[0]) == 0:
                        x_list.append(selected_obj.Pos[0])
                    if y_list.count(selected_obj.Pos[1]) == 0:
                        y_list.append(selected_obj.Pos[1])
                    if z_list.count(selected_obj.Pos[2]) == 0:
                        z_list.append(selected_obj.Pos[2])
                if len(set(x_list)) != 1:  # 排除零件的x坐标不相同的情况
                    return
                # 如果所有零件的z坐标都相同，那么就说明这是一组纵向排列的船体截块
                if len(set(z_list)) == 1:
                    connected = True  # 判断是否上下相连
                    # 把selected_gl_obj 按照 part_obj.Pos[1] 从小到大排序:
                    ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode].sort(key=lambda x: x.Pos[1])
                    last_part = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
                    for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][1:]:
                        last_up = last_part.Pos[1] + last_part.Hei * last_part.Scl[1] / 2
                        this_down = selected_obj.Pos[1] - selected_obj.Hei * selected_obj.Scl[1] / 2
                        if last_up < this_down:
                            connected = False
                            break
                        last_part = selected_obj
                    if connected:  # 如果相连，接下来要显示self.tab1_mod1_grid_verticalPartSet
                        self.tab1_mod1_widget_verticalPartSet.show() if self.ActiveTab == "船体设计" else None
                        self.tab1_current_widget = self.tab1_mod1_widget_verticalPartSet
                        self.show_tab1_mod1_grid_verticalPartSet()

                # 如果所有零件的x和y坐标都相同，那么就说明这是一组横向排列的船体截块
                elif len(set(y_list)) == 1:
                    connected = True  # 判断是否前后相连
                    # 把selected_gl_obj 按照 part_obj.Pos[2] 从小到大排序:
                    ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode].sort(key=lambda x: x.Pos[2])
                    last_part = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
                    for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][1:]:
                        last_front = last_part.Pos[2] + last_part.Len * last_part.Scl[2] / 2
                        this_back = selected_obj.Pos[2] - selected_obj.Len * selected_obj.Scl[2] / 2
                        if last_front != this_back:
                            connected = False
                            break
                        last_part = selected_obj
                    if connected:  # 如果相连，接下来要显示self.tab1_mod1_grid_horizontalPartSet
                        self.tab1_mod1_widget_horizontalPartSet.show() if self.ActiveTab == "船体设计" else None
                        self.tab1_current_widget = self.tab1_mod1_widget_horizontalPartSet
                        self.show_tab1_mod1_grid_horizontalPartSet()
                elif _len == len(set(y_list)) * len(set(z_list)):  # 集成块的情况：所有零件的x坐标都相同，且y坐标和z坐标构成中间不间断的矩形点阵。
                    """
                    （"x"表示零件位置，"|"表示边界，"-"表示零件的上下面相切，
                    所有等y零件的前后面相切，所有等z零件的上下面相切）
                    示例（左视简图）：
                    -----------------------------------------
                    | x |   x   |  x  |     x     |   x   |x|
                    -----------------------------------------
                    |   |       |     |           |       | |
                    | x |   x   |  x  |     x     |   x   |x|
                    |   |       |     |           |       | |
                    -----------------------------------------
                    | x |   x   |  x  |     x     |   x   |x|
                    -----------------------------------------
                    """
                    connected = True
                    # 首先判断是否满足矩形点阵
                    zy_dict = {}  # 键值对为z: [part0, part1, ...]
                    for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode]:
                        if selected_obj.Pos[2] not in zy_dict:
                            zy_dict[selected_obj.Pos[2]] = [selected_obj]
                        else:
                            zy_dict[selected_obj.Pos[2]].append(selected_obj)
                    last_y_set = set([part_obj.Pos[1] for part_obj in zy_dict[list(zy_dict.keys())[0]]])
                    for i in range(1, len(zy_dict)):
                        this_y_set = set([part_obj.Pos[1] for part_obj in zy_dict[list(zy_dict.keys())[i]]])
                        if last_y_set != this_y_set:
                            connected = False
                            break
                    # 然后计算第一层零件前后是否相连
                    if connected:
                        ...
                    # 接着计算第一竖排零件上下是否相连
                    if connected:
                        self.tab1_mod1_widget_verHorPartSet.show() if self.ActiveTab == "船体设计" else None
                        self.tab1_current_widget = self.tab1_mod1_widget_verHorPartSet
                        self.show_tab1_mod1_grid_verHorPartSet()
            elif _type == NaHullXZLayer:
                self.tab1_mod2_widget_multiLayer.show()
                self.tab1_current_widget = self.tab1_mod2_widget_multiLayer  # TODO: 显示tab1_mod2_grid_multiLayer
            else:
                ...
                # TODO: 其他类型的物体

    def show_tab1_mod1_grid_verticalPartSet(self):
        self.tab1_mod1_grid_verticalPartSet.setSpacing(7)
        self.tab1_mod1_grid_verticalPartSet.setContentsMargins(0, 0, 0, 0)
        self.tab1_mod1_grid_verticalPartSet.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # 添加title，说明当前显示的是纵向排列的船体截块
        title = MyLabel("竖直截块", QFont('微软雅黑', 10), side=Qt.AlignTop | Qt.AlignVCenter)
        title.setFixedSize(70, 25)
        self.tab1_mod1_grid_verticalPartSet.addWidget(title, 0, 0, 1, 4)

    def show_tab1_mod1_grid_horizontalPartSet(self):
        self.tab1_mod1_grid_horizontalPartSet.setSpacing(7)
        self.tab1_mod1_grid_horizontalPartSet.setContentsMargins(0, 0, 0, 0)
        self.tab1_mod1_grid_horizontalPartSet.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # 添加title，说明当前显示的是横向排列的船体截块
        title = MyLabel("水平截块", QFont('微软雅黑', 10), side=Qt.AlignTop | Qt.AlignVCenter)
        title.setFixedSize(70, 25)
        self.tab1_mod1_grid_horizontalPartSet.addWidget(title, 0, 0, 1, 4)

    def show_tab1_mod1_grid_verHorPartSet(self):
        self.tab1_mod1_grid_verHorPartSet.setSpacing(7)
        self.tab1_mod1_grid_verHorPartSet.setContentsMargins(0, 0, 0, 0)
        self.tab1_mod1_grid_verHorPartSet.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        # 添加title，说明当前显示的是集成块
        title = MyLabel("集成块", QFont('微软雅黑', 10), side=Qt.AlignTop | Qt.AlignVCenter)
        title.setFixedSize(70, 25)
        self.tab1_mod1_grid_verHorPartSet.addWidget(title, 0, 0, 1, 4)

    def tab1_grid_qte_mouse_wheel(self, event=None):
        # 寻找当前鼠标所在的输入框
        active_textEdit = None
        for key in self.tab1_content_singlePart:
            if key != "类型":
                for qte in self.tab1_content_singlePart[key]["QTextEdit"]:
                    if qte.hasFocus():
                        active_textEdit = qte
                        break
        if active_textEdit is None:
            return
        # 获取输入框的值
        value = float(active_textEdit.toPlainText())
        # 获取鼠标滚轮的滚动值
        delta = event.angleDelta().y()
        # 根据滚动值，修改输入框的值
        if delta > 0:
            value += 0.05
        else:
            value -= 0.05
        active_textEdit.setText(str(value))

    def init_style(self):
        self.setTabPosition(QTabWidget.East)
        self.setMovable(True)
        self.setDocumentMode(True)
        self.setStyleSheet(
            f"QTabBar::tab{{background-color:{BG_COLOR0};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-height:30ex;"
            f"border-right:0px solid {FG_COLOR2};"
            f"border-left:1px solid {FG_COLOR2};}}"
            # 设置选中标签栏样式
            f"QTabBar::tab:selected{{background-color:{BG_COLOR3};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-height:30ex;"
            f"border-right:0px solid {FG_COLOR2};"
            f"border-left:1px solid {FG_COLOR2};}}"
            # 设置鼠标悬停标签栏样式
            f"QTabBar::tab:hover{{background-color:{BG_COLOR3};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-height:30ex;"
            f"border-right:0px solid {FG_COLOR2};"
            f"border-left:1px solid {FG_COLOR1};}}"
        )
        # 添加标签页
        self.addTab(self.init_tab1(), "元素检视器")
        self.addTab(self.init_tab2(), "属性编辑器")
        self.setContentsMargins(0, 0, 0, 0)
        self.setTabText(0, "元素检视器")
        self.setTabText(1, "属性编辑器")
        self.setTabToolTip(0, "元素检视器")
        self.setTabToolTip(1, "属性编辑器")

    def bind_widget(self):
        # tab1_mod1
        self.tab1_mod1_widget_verticalPartSet.setLayout(self.tab1_mod1_grid_verticalPartSet)
        self.tab1_mod1_widget_horizontalPartSet.setLayout(self.tab1_mod1_grid_horizontalPartSet)
        self.tab1_mod1_widget_verHorPartSet.setLayout(self.tab1_mod1_grid_verHorPartSet)
        # tab1_mod2
        self.tab1_mod2_widget_singleLayer.setLayout(self.tab1_mod2_grid_singleLayer)
        self.tab1_mod2_widget_multiLayer.setLayout(self.tab1_mod2_grid_multiLayer)
        # 添加控件
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_singlePart)  # mod1
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_verticalPartSet)
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_horizontalPartSet)
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_verHorPartSet)
        self.tab1_main_layout.addWidget(self.tab1_mod2_widget_singleLayer)  # mod2
        self.tab1_main_layout.addWidget(self.tab1_mod2_widget_multiLayer)
        # 隐藏
        self.tab1_mod1_widget_verticalPartSet.hide()  # mod1
        self.tab1_mod1_widget_horizontalPartSet.hide()
        self.tab1_mod1_widget_verHorPartSet.hide()
        self.tab1_mod2_widget_singleLayer.hide()  # mod2
        self.tab1_mod2_widget_multiLayer.hide()
        self.tab1_main_layout.addStretch(1)

    def init_tab1(self):
        tab = QWidget()
        tab.setLayout(self.tab1_main_layout)
        # 标题
        title = MyLabel("元素检视器", QFont('微软雅黑', 11), side=Qt.AlignTop | Qt.AlignCenter)
        self.tab1_main_layout.addWidget(title, alignment=Qt.AlignTop | Qt.AlignCenter)
        # 添加分割线
        self.tab1_main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken), alignment=Qt.AlignTop)
        return tab

    def init_tab2(self):
        tab = QWidget()
        tab.setLayout(self.tab2_main_layout)
        # 标题
        title = MyLabel("属性编辑器", QFont('微软雅黑', 11), side=Qt.AlignCenter)
        self.tab2_main_layout.addWidget(title)
        return tab


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
        self.ThreeDFrame = GLWin(Config.Sensitivity, various_mode=True)
        self.down_layout = QHBoxLayout()
        self.left_tool_bar = QToolBar()
        self.init_layout()
        self.save_button = QPushButton("保存")
        self.read_from_na_button = QPushButton("从NA新建")
        self.convertAdhull_button = QPushButton("从PTB转换")
        self.init_buttons()
        self.up_layout.addStretch()
        self.menu = QMenu()
        self.init_menu()
        # -----------------------------------------------------------------------------------信号
        self.camera = self.ThreeDFrame.camera
        self.environment_obj = self.ThreeDFrame.environment_obj
        # 在不同模式下显示的物体：
        self.all_3d_obj = self.ThreeDFrame.all_3d_obj  # 普通模式
        self.zx_layer_obj = self.ThreeDFrame.zx_layer_obj  # 横剖面模式
        self.yx_layer_obj = self.ThreeDFrame.yx_layer_obj  # 纵剖面模式
        self.left_view_obj = self.ThreeDFrame.left_view_obj  # 左视图模式

    def init_menu(self):
        # 右键菜单
        self.menu.addAction(QAction("撤销 Ctrl+Z", self))
        self.menu.addAction(QAction("重做 Ctrl+Shift+Z", self))
        self.menu.addSeparator()
        self.menu.addAction(QAction("复制 Ctrl+C", self))
        self.menu.addAction(QAction("粘贴 Ctrl+V", self))
        self.menu.addSeparator()
        self.menu.addAction(QAction("删除 Delete", self))
        self.menu.addAction(QAction("添加 Ctrl+Shift+A", self))
        self.menu.addSeparator()
        self.menu.addAction(QAction("导入 I", self))
        self.menu.addAction(QAction("导出 O", self))
        # 菜单绑定函数
        self.menu.actions()[0].triggered.connect(self.undo)
        self.menu.actions()[1].triggered.connect(self.redo)
        self.menu.actions()[3].triggered.connect(self.copy)
        self.menu.actions()[4].triggered.connect(self.paste)
        self.menu.actions()[6].triggered.connect(self.delete)
        self.menu.actions()[7].triggered.connect(self.add)
        self.menu.actions()[9].triggered.connect(self.import_)
        self.menu.actions()[10].triggered.connect(self.export)
        # 快捷键绑定
        undo_ = QShortcut(QKeySequence("Ctrl+Z"), self)
        redo_ = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        copy_ = QShortcut(QKeySequence("Ctrl+C"), self)
        paste_ = QShortcut(QKeySequence("Ctrl+V"), self)
        delete_ = QShortcut(QKeySequence("Delete"), self)
        add_ = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        import_ = QShortcut(QKeySequence("I"), self)
        export_ = QShortcut(QKeySequence("O"), self)
        undo_.activated.connect(self.undo)
        redo_.activated.connect(self.redo)
        copy_.activated.connect(self.copy)
        paste_.activated.connect(self.paste)
        delete_.activated.connect(self.delete)
        add_.activated.connect(self.add)
        import_.activated.connect(self.import_)
        export_.activated.connect(self.export)

    def show_menu(self, pos):
        self.menu.exec_(QCursor.pos())

    def undo(self):
        show_state(f"撤销", 'success')

    def redo(self):
        show_state(f"重做", 'success')

    def copy(self):
        show_state(f"复制 {self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode]}", 'success')

    def paste(self):
        show_state(f"粘贴 {self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode]}", 'success')

    def delete(self):
        show_state(f"删除{self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode]}", 'success')

    def add(self):
        show_state(f"添加", 'success')

    def import_(self):
        show_state(f"导入", 'success')

    def export(self):
        show_state(f"导出", 'success')

    # ======================================================================================左工具栏函数
    def add_layer(self):
        ...

    def choose_mode(self):
        if self.left_tool_bar.actions()[0].isChecked():
            self.ThreeDFrame.operation_mode = OpenGLWin.Selectable
        else:
            self.ThreeDFrame.operation_mode = OpenGLWin.UnSelectable

    def init_style(self):
        # 设置边距
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet(f"background-color: {BG_COLOR0};")

    def init_layout(self):
        self.up_layout.setSpacing(0)
        self.up_layout.setContentsMargins(0, 0, 0, 0)
        self.down_layout.setSpacing(0)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        self.init_left_tool_bar()
        self.down_layout.addWidget(self.ThreeDFrame)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.up_layout, stretch=0)
        # 添加分割线
        self.main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))
        self.main_layout.addLayout(self.down_layout, stretch=1)
        self.setLayout(self.main_layout)

    def init_left_tool_bar(self):
        set_tool_bar_style(self.left_tool_bar)
        choose_action = QAction(self.ChooseImg, "框选", self)
        add_layer_action = QAction(self.AddImg, "添加层", self)
        choose_action.triggered.connect(self.choose_mode)
        add_layer_action.triggered.connect(self.add_layer)
        # 设置可以选中
        choose_action.setCheckable(True)
        choose_action.setChecked(True)
        self.left_tool_bar.addAction(choose_action)
        self.left_tool_bar.addAction(add_layer_action)
        # 打包工具栏
        self.down_layout.addWidget(self.left_tool_bar)

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

    @staticmethod
    def save_file():
        # 保存工程文件
        Handler.CurrentProjectData["Object"].save()
        time = Handler.CurrentProjectData["Object"].SaveTime
        show_state(f"{time} {Handler.CurrentProjectData['Path']}已保存", 'success')

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
        # 清空原来的所有对象
        for mt, objs in self.all_3d_obj.items():
            objs.clear()
        self.zx_layer_obj.clear()
        self.yx_layer_obj.clear()
        self.left_view_obj.clear()
        # 保存工程文件
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
        self.zx_layer_obj.extend(obj.xzLayers)
        # 更新ThreeDFrame的paintGL
        self.update_3d_obj()

    def update_3d_obj(self):
        # self.ThreeDFrame.environment_obj = self.environment_obj
        # self.ThreeDFrame.all_3d_obj = self.all_3d_obj
        # self.ThreeDFrame.zx_layer_obj = self.zx_layer_obj
        # self.ThreeDFrame.yx_layer_obj = self.yx_layer_obj
        # self.ThreeDFrame.left_view_obj = self.left_view_obj
        for gl_plot_obj in self.all_3d_obj["钢铁"]:  # 找到NA船壳，把所有零件添加到ThreeDFrame的ShipsAllParts
            if type(gl_plot_obj) == NAHull:
                self.ThreeDFrame.ShipsAllParts = gl_plot_obj.Parts


class ArmorDesignTab(QWidget):
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
        self.ThreeDFrame = OpenGLWin2(Config.Sensitivity)
        self.down_layout = QHBoxLayout()
        self.down_tool_bar = QToolBar()
        self.init_layout()
        self.open_button = QPushButton("打开")
        # self.init_open_button()
        self.up_layout.addStretch()
        # -----------------------------------------------------------------------------------操作区
        self.camera = self.ThreeDFrame.camera

    def init_layout(self):
        self.up_layout.setSpacing(0)
        self.up_layout.setContentsMargins(0, 0, 0, 0)
        self.down_layout.setSpacing(0)
        self.down_layout.setContentsMargins(0, 0, 0, 0)
        # self.init_tool_bar()
        self.down_layout.addWidget(self.ThreeDFrame)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.up_layout, stretch=0)
        # 添加分割线
        self.main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken))
        self.main_layout.addLayout(self.down_layout, stretch=1)
        self.setLayout(self.main_layout)


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
            self.ThreeDFrame.operation_mode = OpenGLWin.Selectable
        else:
            self.ThreeDFrame.operation_mode = OpenGLWin.UnSelectable

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
        self.ThreeDFrame.environment_obj = self.environment_obj
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
        self.ThreeDFrame = GLWin(Config.Sensitivity)
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
            self.ThreeDFrame.operation_mode = OpenGLWin.Selectable
        else:
            self.ThreeDFrame.operation_mode = OpenGLWin.UnSelectable

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
        self.ThreeDFrame.environment_obj = self.environment_obj
        self.ThreeDFrame.all_3d_obj = self.all_3d_obj
        for gl_plot_obj in self.all_3d_obj["钢铁"]:
            if type(gl_plot_obj) == NAHull:
                self.ThreeDFrame.ShipsAllParts = gl_plot_obj.Parts


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
    QtWindow = MainWin(Config)
    Handler = MainHandler(QtWindow)
    if Config.Projects != {}:
        CurrentProject.init_project_from_config()
    else:
        CurrentPrj = None
    QtWindow.show()  # 显示被隐藏的窗口
    # 主循环
    sys.exit(QApp.exec_())
