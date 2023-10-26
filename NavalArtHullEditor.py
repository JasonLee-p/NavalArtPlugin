# -*- coding: utf-8 -*-
"""
NavalArt Hull Editor
NavalArt 船体编辑器
Author: @JasonLee
Date: 2023-9-18
"""
# 系统库
import json
import os.path
import sys
import time
import traceback
import webbrowser
from typing import Union

try:
    # 第三方库
    from OpenGL.raw.GL.VERSION.GL_1_0 import GL_PROJECTION, GL_MODELVIEW
    from PyQt5.QtCore import QPropertyAnimation

    # 本地库
    from developer_console import open_developer_console
    from connection import Connection, extract_number_from_version
    from state_history import StateHistory, push_global_statu
    from util_funcs import *
    from ship_reader import *
    from GUI import *
    from GUI.dialogs import SelectNaDialog, StartWelcomeDialog
    from GL_plot import *
    from path_utils import find_ptb_path, find_na_root_path
    from OpenGLWindow import Camera, OpenGLWin, OpenGLWin2, DesignTabGLWinMenu, reset_matrix
    from right_element_view import (
        Mod1AllPartsView, Mod1SinglePartView, Mod1VerticalPartSetView, Mod1HorizontalPartSetView,
        Mod1VerHorPartSetView)
    from right_element_editing import (
        Mod1SinglePartEditing, Mod1AllPartsEditing, Mod1VerticalPartSetEditing, Mod1HorizontalPartSetEditing,
        Mod1VerHorPartSetEditing)
    from right_operation_editing import (
        OperationEditing, AddLayerEditing)
    from project_file import ConfigFile
    from project_file import ProjectFile as PF
    from operation import AddLayerOperation

except:
    traceback.print_exc()
    input("无法正确导入库！请按回车键退出")
    sys.exit(0)

VERSION = "va0.0.2.0"


def show_state(txt, msg_type: Literal['warning', 'success', 'process', 'error'] = 'process', label=None):
    """
    显示状态栏信息
    :param txt: 状态栏信息
    :param msg_type: 状态栏信息类型
    :param label: 状态栏标签
    :return:
    """
    color_map = {
        'warning': 'orange',
        'success': f"{FG_COLOR0}",
        'process': 'gray',
        'error': f"{FG_COLOR1}",
    }
    if label is None:
        label_ = Handler.window.statu_label
    else:
        label_ = label
    if msg_type in color_map:
        label_.setStyleSheet(f'color: {color_map[msg_type]};')
    else:
        label_.setStyleSheet(f'color: {FG_COLOR0};')
    label_.setText(txt)


def check_version():
    class __CheckVersionThread(QThread):
        finished = pyqtSignal()

        def __init__(self):
            self.latest_version = None
            self.links = {}
            super().__init__()

        def run(self):
            self.latest_version, self.links = Connection.get_latest_version()
            self.finished.emit()

        def is_finished(self):
            if self.latest_version is None:
                dialog.check_update_failed()
            elif extract_number_from_version(self.latest_version) > extract_number_from_version(VERSION):
                dialog.check_update_success(self.latest_version)
            else:
                dialog.close()

    Handler.window.check_version_thread = __CheckVersionThread()
    Handler.window.check_version_thread.finished.connect(Handler.window.check_version_thread.is_finished)
    Handler.window.check_version_thread.start()

    dialog = CheckNewVersionDialog(None, VERSION)
    dialog.exec_()
    if dialog.download and len(Handler.window.check_version_thread.links) == 2:
        print("browser open")
        webbrowser.open(Handler.window.check_version_thread.links[1])
        webbrowser.open(Handler.window.check_version_thread.links[0])


# noinspection PyUnresolvedReferences
def open_project(file_path=None):
    """
    开启ProjectOpeningThread线程，读取工程
    :return:
    """
    if Handler.LoadingProject:
        MyMessageBox.information(Handler.window, "提示", "正在读取工程，请稍后再试！")
        return
    if Handler.SavingProject:
        MyMessageBox.information(Handler.window, "提示", "正在保存工程，请稍后再试！")
        return
    Handler.LoadingProject = True
    # 选择路径
    if not file_path:
        if Config.Projects == {}:  # 如果没有历史记录，打开自带文件选择框
            select_path_dialog = QFileDialog(Handler.window, "打开工程", Config.ProjectsFolder)
            select_path_dialog.setNameFilter("工程文件 (*.naprj)")
            select_path_dialog.setFileMode(QFileDialog.ExistingFile)
            select_path_dialog.exec_()
            # 判断用户是否点击确定
            if not select_path_dialog.selectedFiles():
                Handler.LoadingProject = False
                return
            file_path = select_path_dialog.selectedFiles()[0]
            del select_path_dialog
        else:
            select_prj_dialog = SelectPrjDialog(None, config_projects=Config.Projects)
            select_prj_dialog.exec_()
            file_path = select_prj_dialog.selected_project_path
            del select_prj_dialog
            if not file_path:
                Handler.LoadingProject = False
                return
    Handler.window.open_project_thread = ProjectOpeningThread(file_path)
    Handler.window.open_project_thread.update_state.connect(show_state)
    Handler.window.open_project_thread.finished.connect(after_open)
    Handler.window.open_project_thread.start()


def after_open():
    """
    读取工程文件完成后的操作
    :return:
    """
    for _l in Handler.hull_design_tab.ThreeDFrame.gl_commands.values():
        _l[1] = True
    Handler.hull_design_tab.ThreeDFrame.paintGL()
    for _l in Handler.hull_design_tab.ThreeDFrame.gl_commands.values():
        _l[1] = False
    if StateHistory.current:
        StateHistory.current.init_stack()
    Handler.LoadingProject = False


class ProjectOpeningThread(QThread):
    finished = pyqtSignal()
    update_state = pyqtSignal(str, str)  # 用于更新状态信息

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    # noinspection PyUnresolvedReferences
    def run(self):
        try:
            self.update_state.emit(f"正在读取{self.file_path}...", 'process')  # 发射更新状态信息信号
            obj = ProjectHandler.load_project(self.file_path)  # 新建工程文件对象
            if obj is None:
                self.finished.emit()
                self.update_state.emit(f"{self.file_path}读取失败", 'error')  # 发射更新状态信息信号
                return
            # 读取成功，开始绘制
            # 通过读取的船体设计文件，新建NaHull对象
            na_hull = NAHull(data=obj.NAPartsData,
                             show_statu_func=self.update_state,
                             glWin=Handler.hull_design_tab.ThreeDFrame,
                             design_tab=True)
            obj.na_hull = na_hull
            Handler.hull_design_tab.init_NaHull_partRelationMap_Layers(na_hull)  # 显示船体设计
            # 显示船体设计
            self.update_state.emit(f"{self.file_path}加载成功", 'success')  # 发射更新状态信息信号
            Handler.LoadingProject = False
            self.finished.emit()
        except Exception as _e:
            raise _e


# noinspection PyUnresolvedReferences
def new_project():
    """
    新建工程，弹出对话框，获取工程名称和路径，以及其他相关信息
    :return:
    """
    # 弹出对话框，获取工程名称和路径，以及其他相关信息
    NewProjectDialog(None, border_radius=10)
    NewProjectDialog.current.exec_()
    # 如果确定新建工程
    if NewProjectDialog.current.create_new_project:
        if NewProjectDialog.current.generate_mode == 'NA':
            if Handler.LoadingProject:
                MyMessageBox.information(Handler.window, "提示", "正在读取工程，请稍后再试！")
                return
            if Handler.SavingProject:
                MyMessageBox.information(Handler.window, "提示", "正在保存工程，请稍后再试！")
                return
            Handler.LoadingProject = True
            # 获取对话框返回的数据
            _original_na_path = NewProjectDialog.current.OriginalNAPath
            _prj_path = NewProjectDialog.current.ProjectPath  # name已经包含在path里了
            show_state(f"正在读取{_original_na_path}...", 'process')  # 发射更新状态信息信号
            # 开启线程
            Handler.window.read_na_hull_thread = ReadNAHullThread(_original_na_path)
            Handler.window.read_na_hull_thread.update_state.connect(show_state)
            Handler.window.read_na_hull_thread.finished.connect(Handler.window.read_na_hull_thread.after_read_na_hull)
            Handler.window.read_na_hull_thread.start()


class ReadNAHullThread(QThread):
    finished = pyqtSignal()
    update_state = pyqtSignal(str, str)  # 用于更新状态信息

    def __init__(self, original_na_path):
        super().__init__()
        # 通过读取的船体设计文件，新建NaHull对象
        self.original_na_path = original_na_path
        self.na_hull = None

    # noinspection PyUnresolvedReferences
    def run(self) -> None:
        self.na_hull = NAHull(path=self.original_na_path, show_statu_func=self.update_state, design_tab=True)
        self.finished.emit()

    # noinspection PyUnresolvedReferences
    def after_read_na_hull(self):
        try:
            # 检测颜色种类，弹出对话框，选择颜色
            color_dialog = ColorDialog(Handler.window, NAHull.current_in_design_tab)
            color_dialog.exec_()
            if not color_dialog.canceled:
                # 获取对话框返回的数据
                _name = NewProjectDialog.current.ProjectName
                _prj_path = NewProjectDialog.current.ProjectPath
                _original_na_path = NewProjectDialog.current.OriginalNAPath
                # 开启ProjectLoadingNewThread线程，读取工程
                Handler.window.new_project_thread = ProjectLoadingNewThread(self.na_hull, _name, _prj_path,
                                                                            _original_na_path)
                Handler.window.new_project_thread.update_state.connect(show_state)
                Handler.window.new_project_thread.finished.connect(after_new)
                Handler.window.new_project_thread.start()
        except Exception as _e:
            raise _e


def after_new():
    for _l in Handler.hull_design_tab.ThreeDFrame.gl_commands.values():
        _l[1] = True
    Handler.hull_design_tab.ThreeDFrame.paintGL()
    for _l in Handler.hull_design_tab.ThreeDFrame.gl_commands.values():
        _l[1] = False
    StateHistory.current.init_stack()
    Handler.LoadingProject = False


class ProjectLoadingNewThread(QThread):
    finished = pyqtSignal()
    update_state = pyqtSignal(str, str)

    def __init__(self, na_hull, name, path, original_na_path):
        super().__init__()
        self.na_hull = na_hull
        self.name = name
        self.path = path
        self.original_na_path = original_na_path

    # noinspection PyUnresolvedReferences
    def run(self):
        try:
            # 生成工程文件对象
            ProjectHandler(
                self.name, self.path,
                self.original_na_path, self.na_hull.DrawMap, self.na_hull,
                operations={}, mode=PF.NA, code='', save_time=''
            )
            # 读取颜色成功，开始初始化partRelationMap和Layers
            Handler.hull_design_tab.init_NaHull_partRelationMap_Layers(self.na_hull)
            # 在这里继续执行后续操作，如下所示
            self.update_state.emit(f"{self.original_na_path}读取成功", 'success')  # 发射更新状态信息信号
            Handler.LoadingProject = False
            self.finished.emit()
        except Exception as _e:
            raise _e


class ProjectHandler(PF):
    current = None

    def __init__(self, name, path, original_na_file_path,
                 na_parts_data=None, na_hull=None, operations=None, mode=PF.EMPTY, code='', save_time=''):
        self.na_hull = na_hull
        if ProjectHandler.current:  # 保存上一个工程文件，清空当前所有被绘制的对象
            show_state(f"正在保存{ProjectHandler.current.Path}...", 'process')
            # # 询问是否保存
            # if MyMessageBox.question(Handler.window, "提示", "是否保存当前工程？") == QMessageBox.Yes:
            #     ProjectHandler.current.save(ignore_loading=True)
            # 清空当前所有被绘制的对象
            time.sleep(0.1)  # TODO
            Handler.hull_design_tab.clear_all_plot_obj()
            show_state(f"{ProjectHandler.current.Path}保存成功", 'success')
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
        # 更新配置文件中的路径
        if self.Name in Config.Projects.keys():
            del Config.Projects[self.Name]
        Config.Projects[self.Name] = self.Path
        Config.ProjectsFolder = os.path.dirname(self.Path)
        Config.save_config()
        # 重置NavalArt的Part的ShipsAllParts
        NAPart.ShipsAllParts = []
        # 更新静态变量
        ProjectHandler.current = self
        self.stateHistory = StateHistory(show_state)

    @staticmethod
    def load_project(path) -> Union[None, 'ProjectHandler', 'PF']:
        """
        从文件加载工程
        :param path:
        :return:
        """
        prj = ProjectHandler.load_project_from_na(path)
        if prj is None:  # 当没有读取到工程文件时，返回None
            # 删除Config中的该条目
            try:
                del Config.Projects[os.path.basename(path).split('.')[0]]
                Config.save_config()  # 保存配置文件
            except KeyError:
                pass
            finally:
                return None
        # 重置NavalArt的Part的ShipsAllParts
        NAPart.ShipsAllParts = []
        return prj

    @staticmethod
    def load_project_from_na(path: str) -> Union[None, 'ProjectHandler']:
        """
        从工程文件加载工程
        :param path:
        :return:
        """
        # 判断是否为naprj
        if not path.endswith('.naprj'):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return None
        try:
            project_file = ProjectHandler(
                data['Name'], path, data['OriginalFilePath'], data['NAPartsData'], None, data['Operations'],
                mode=PF.LOAD,
                code=data['Code'], save_time=data['SaveTime'])
        except KeyError:
            return None
        if project_file._succeed_init:
            return project_file
        else:
            return None

    def save(self, ignore_loading=False):
        try:  # 保存
            # Handler状态操作
            if Handler.LoadingProject and not ignore_loading:
                MyMessageBox.information(Handler.window, "提示", "正在读取工程，请稍后再试！")
                return
            if Handler.SavingProject:
                MyMessageBox.information(Handler.window, "提示", "正在保存工程，请稍后再试！")
                return
            Handler.SavingProject = True
            # 截取图片
            Handler.hull_design_tab.ThreeDFrame.save_current_image(ThumbnailPath, self.Name)
            # 保存
            self.NAPartsData = NAHull.toJson(self.na_hull.DrawMap)
            super().save()
            # 更新状态栏
            _time = f"{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday} " \
                    f"{time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}"
            show_state(f"{_time} {self.Path} 已保存", 'success')
            Handler.SavingProject = False
        except Exception as _e:
            show_state(f"{self.Path} 保存失败！ {_e}", 'error')
            Handler.SavingProject = False
            return

    def save_as(self):
        """
        另存为，封装了文件对话框
        :return:
        """
        # 保存
        try:
            # Handler状态操作
            if Handler.LoadingProject:
                MyMessageBox.information(Handler.window, "提示", "正在读取工程，请稍后再试！")
                return
            if Handler.SavingProject:
                MyMessageBox.information(Handler.window, "提示", "正在保存工程，请稍后再试！")
                return
            Handler.SavingProject = True
            # 打开文件夹对话框，获取保存路径（文件夹）
            if not ProjectHandler.current:
                show_state("请先新建或打开工程", 'warning')
                return
            if Config.ProjectsFolder == '':
                desktop_path = os.path.join(os.path.expanduser("~"), 'Desktop')
                file_dialog = QFileDialog(Handler.window, "保存工程到", desktop_path)
            else:
                file_dialog = QFileDialog(Handler.window, "保存工程到", Config.ProjectsFolder)
            file_dialog.setFileMode(QFileDialog.DirectoryOnly)
            file_dialog.exec_()
            try:
                folder_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
            except IndexError:
                return
            # 保存
            self.NAPartsData = NAHull.toJson(NAHull.current_in_design_tab.DrawMap)
            super().save(folder_path)
            # 更新状态栏
            _time = f"{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday} " \
                    f"{time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}"
            show_state(f"{_time} {ProjectHandler.current.Path} 已保存", 'success')
        except Exception as _e:
            show_state(f"{ProjectHandler.current.Path} 保存失败！ {_e}", 'error')
        finally:
            Handler.SavingProject = False

    def undo(self):
        self.stateHistory.undo()

    def redo(self):
        self.stateHistory.redo()


class NewEmptyPrj(ProjectHandler):
    def __init__(self, name, path, color: QColor):
        super().__init__(name, path, None, None, None, None, mode=PF.EMPTY)
        self.stateHistory = StateHistory(show_state)
        self.na_hull = NAHull(
            show_statu_func=show_state,
            design_tab=True,
            data={color.name(): [{
                "Typ": "AdjustableHull",
                "Id": "0",
                "Pos": [0., 0., 0.], "Rot": [0., 0., 0.], "Scl": [1., 1., 1.], "Col": color.name()[1:], "Amr": 5,
                "Len": 6., "Hei": 2., "FWid": 12., "BWid": 12., "FSpr": 0., "BSpr": 0.,
                "UCur": 0., "DCur": 1., "HScl": 1., "HOff": 0.
            }]},
            glWin=Handler.hull_design_tab.ThreeDFrame,
        )


class MainWin(MainWindow):
    def __init__(self, parent=None):
        MainWindow.__init__(self, parent)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        super().keyPressEvent(event)


class GLWin(OpenGLWin):
    key_state = {
        Qt.Key_W: False, Qt.Key_S: False, Qt.Key_A: False, Qt.Key_D: False,
        Qt.Key_Q: False, Qt.Key_E: False, Qt.Key_Z: False, Qt.Key_X: False,
        Qt.Key_C: False, Qt.Key_V: False, Qt.Key_B: False, Qt.Key_N: False,
        Qt.Key_M: False, Qt.Key_J: False, Qt.Key_K: False, Qt.Key_L: False,
        Qt.Key_U: False, Qt.Key_I: False, Qt.Key_O: False, Qt.Key_P: False,
        Qt.Key_F: False, Qt.Key_G: False, Qt.Key_H: False, Qt.Key_R: False,
        Qt.Key_T: False, Qt.Key_Y: False
    }

    def __init__(self, parent=None, various_mode=False, show_statu_func=None):
        self.sub_menu_start = None  # 快捷子菜单的起始点
        self.sub_menu_end = None  # 快捷子菜单的终止点
        self.b0 = QPushButton("扩选到xy平面")
        self.b1 = QPushButton("扩选到xz平面")
        self.b2 = QPushButton("元素检视器")
        self.b3 = QPushButton("属性编辑器")
        self.b4 = QPushButton("全视图")
        self.b5 = QPushButton("横剖面")
        self.b6 = QPushButton("纵剖面")
        self.b7 = QPushButton("左视图")
        self.button_pos_map = {  # 按钮中心位置映射
            self.b0: (200, -40), self.b1: (90, -110),
            self.b2: (-75, 26), self.b3: (75, 26),
            self.b4: (-100, -20), self.b5: (45, -60),
            self.b6: (100, -20), self.b7: (-45, -60)
        }
        self.button_size_map = {
            self.b0: (110, 28), self.b1: (110, 28),
            self.b2: (90, 28), self.b3: (90, 28),
            self.b4: (60, 28), self.b5: (60, 28),
            self.b6: (60, 28), self.b7: (60, 28)
        }
        self.button_func_map = {  # 按钮功能映射
            self.b0: self.singlePart_add2xyLayer,
            self.b1: self.singlePart_add2xzLayer,
            self.b2: empty_func, self.b3: empty_func,  # 后期初始化
            self.b4: lambda x: self.set_show_3d_obj_mode(self.ShowAll),
            self.b5: lambda x: self.set_show_3d_obj_mode(self.ShowXZ),
            self.b6: lambda x: self.set_show_3d_obj_mode(self.ShowXY),
            self.b7: lambda x: self.set_show_3d_obj_mode(self.ShowLeft)
        }
        sizes = [self.button_size_map[b] for b in self.button_pos_map.keys()]
        set_buttons(self.button_pos_map.keys(), sizes=sizes, font=FONT_8, border_radius=5, fg=FG_COLOR2)
        OpenGLWin.__init__(self, parent, various_mode, show_statu_func)

    def __deepcopy__(self, memo):
        return self

    def keyPressEvent(self, event: QKeyEvent) -> None:
        for key in self.key_state.keys():
            if key == event.key():
                self.key_state[key] = True
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Alt:
            show_state("Alt快捷键指南：\t上下左右： 选区移动\t右键拖动： 快捷菜单", "warning")
        # Enter
        if event.key() == Qt.Key_Return:
            Handler.right_widget.tab2_operation_addPartLayer.ensure_button_clicked()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        for key in self.key_state.keys():
            if key == event.key():
                self.key_state[key] = False
        super().keyReleaseEvent(event)
        if event.key() == Qt.Key_Alt:
            show_state("")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            ...
        # 右键和Alt，记录快捷子菜单的起始点
        elif event.button() == Qt.RightButton:
            if event.modifiers() == Qt.AltModifier:
                # 直接利用button制作便捷环绕式菜单
                self.sub_menu_start = event.pos()
                # 绘制按钮
                for b in self.button_pos_map.keys():
                    b.setParent(self)
                    b.move(
                        self.sub_menu_start + QPoint(*self.button_pos_map[b]) - QPoint(b.width() // 2, b.height() // 2))
                    b.show()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if Qt.RightButton & event.buttons() and event.modifiers() == Qt.AltModifier and self.sub_menu_start is not None:
            self.sub_menu_end = event.pos()
            self.paintGL()
            self.update()
            # 获取当鼠标释放的时候所在的按钮区域
            pos = event.pos()
            min_dis = (pos - self.sub_menu_start).manhattanLength()
            min_b = None
            for b in self.button_pos_map.keys():
                dis = (b.geometry().center() - pos).manhattanLength()
                if dis < min_dis:
                    min_dis = dis
                    min_b = b
            if min_b is not None:
                # 按钮高亮
                for b in self.button_pos_map.keys():
                    if b == min_b:
                        set_buttons([b], sizes=[self.button_size_map[b]], font=FONT_10, border_radius=5, fg=FG_COLOR0)
                    else:
                        set_buttons([b], sizes=[self.button_size_map[b]], font=FONT_9, border_radius=5, fg=FG_COLOR2)
            else:
                _sizes = [self.button_size_map[b] for b in self.button_pos_map.keys()]
                set_buttons(self.button_pos_map.keys(), sizes=_sizes, font=FONT_9, border_radius=5, fg=FG_COLOR0)
        elif event.modifiers() != Qt.AltModifier and self.sub_menu_start is not None:
            self.lastPos = event.pos()
            self.sub_menu_start = None
            self.sub_menu_end = None
            # 按钮清除
            for b in self.button_pos_map.keys():
                b.setParent(None)
                b.hide()
            show_state("")
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            Handler.right_widget.update_tab()
        elif event.button() == Qt.RightButton and event.modifiers() == Qt.AltModifier and self.sub_menu_start is not None:
            # 获取当鼠标释放的时候所在的按钮区域
            pos = event.pos()
            # 检查离哪一个按钮最近
            min_dis = (pos - self.sub_menu_start).manhattanLength()
            min_b = None
            for b in self.button_pos_map.keys():
                dis = (b.geometry().center() - pos).manhattanLength()
                if dis < min_dis:
                    min_dis = dis
                    min_b = b
            if min_b is not None:
                if min_b in [self.b0, self.b1]:
                    self.button_func_map[min_b]()
                elif min_b == self.b2:
                    self.button_func_map[self.b2](0)
                elif min_b == self.b3:
                    self.button_func_map[self.b3](1)
                elif min_b in [self.b4, self.b5, self.b6, self.b7]:
                    self.button_func_map[min_b](0)
            # if self.show_3d_obj_mode == (self.ShowAll, self.ShowObj) \
            #         and len(self.selected_gl_objects[self.show_3d_obj_mode]) == 1:
            #     if self.b0.geometry().contains(pos):
            #         self.button_func_map[self.b0][0]()
            #     elif self.b1.geometry().contains(pos):
            #         self.button_func_map[self.b1][0]()
            # if self.b2.geometry().contains(pos):
            #     self.button_func_map[self.b2](0)
            # elif self.b3.geometry().contains(pos):
            #     self.button_func_map[self.b3](1)
            # for i in range(4, 8):
            #     b = list(self.button_pos_map.keys())[i]
            #     if b.geometry().contains(pos):
            #         self.button_func_map[b](0)
            self.sub_menu_start = None
            self.sub_menu_end = None
            # 按钮清除
            for b in self.button_pos_map.keys():
                b.setParent(None)
                b.hide()
            show_state("")
        elif event.button() == Qt.RightButton and Handler.right_widget.ActiveTab == "船体设计":
            if Handler.hull_design_tab.ThreeDFrame.rotate_start == Handler.hull_design_tab.ThreeDFrame.lastPos:
                Handler.hull_design_tab.menu.exec_(QCursor.pos())
        self.paintGL()
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.show_3d_obj_mode == (self.ShowAll, self.ShowObj) and len(
                self.selected_gl_objects[self.show_3d_obj_mode]) == 1:
            key_state = self.key_state  # Get a reference to the key_state dictionary

            if key_state[Qt.Key_L]:  # 长度
                self.editParameter("原长度", event)
            elif key_state[Qt.Key_H]:  # 高度
                self.editParameter("原高度", event)
            elif key_state[Qt.Key_F] and key_state[Qt.Key_W]:  # 前宽
                self.editParameter("前宽度", event)
            elif key_state[Qt.Key_B] and key_state[Qt.Key_W]:  # 后宽
                self.editParameter("后宽度", event)
            elif key_state[Qt.Key_F] and key_state[Qt.Key_S]:  # 前扩散
                self.editParameter("前扩散", event)
            elif key_state[Qt.Key_B] and key_state[Qt.Key_S]:  # 后扩散
                self.editParameter("后扩散", event)
            elif key_state[Qt.Key_U] and key_state[Qt.Key_C]:  # 上弧度
                self.editParameter("上弧度", event)
            elif key_state[Qt.Key_D] and key_state[Qt.Key_C]:  # 下弧度
                self.editParameter("下弧度", event)
            elif key_state[Qt.Key_H] and key_state[Qt.Key_S]:  # 高缩放
                self.editParameter("高缩放", event)
            elif key_state[Qt.Key_H] and key_state[Qt.Key_O]:  # 高偏移
                self.editParameter("高偏移", event)
            else:
                super().wheelEvent(event)
        else:
            super().wheelEvent(event)

    @staticmethod
    def editParameter(parameter_name, event):
        active_textEdit = Handler.right_widget.tab2_mod1_widget_singlePart.content[parameter_name]["QLineEdit"][0]
        Handler.right_widget.tab2_mod1_widget_singlePart.mouse_wheel([active_textEdit, event])

    @reset_matrix
    def draw_2D_objs(self):
        if self.select_start and self.select_end:
            self.draw_select_box()
        if self.sub_menu_start is not None and self.sub_menu_end is not None:
            # 画线
            self.gl2_0.glLineWidth(8)
            self.gl2_0.glEnable(self.gl2_0.GL_LIGHT1)
            self.gl2_0.glBegin(self.gl2_0.GL_LINES)
            if self.theme_color["背景"][0] == (0.9, 0.95, 1.0, 1.0):  # 白天
                self.gl2_0.glColor4f(0.9, 0.9, 0.9, 0.5)
            else:  # 黑夜
                self.gl2_0.glColor4f(1, 1, 1, 0.5)
            self.gl2_0.glVertex2f(self.sub_menu_start.x(), self.sub_menu_start.y())
            self.gl2_0.glVertex2f(self.sub_menu_end.x(), self.sub_menu_end.y())
            self.gl2_0.glEnd()
            # 画点
            self.gl2_0.glPointSize(11)
            self.gl2_0.glBegin(self.gl2_0.GL_POINTS)
            if self.theme_color["背景"][0] == (0.9, 0.95, 1.0, 1.0):  # 白天
                self.gl2_0.glColor4f(0.1, 0.1, 0.1, 0.7)
            else:
                self.gl2_0.glColor4f(0.9, 0.9, 0.9, 0.7)
            self.gl2_0.glVertex2f(self.sub_menu_start.x(), self.sub_menu_start.y())
            self.gl2_0.glVertex2f(self.sub_menu_end.x(), self.sub_menu_end.y())
            self.gl2_0.glEnd()

    def singlePart_add2xyLayer(self):
        super(GLWin, self).singlePart_add2xyLayer()
        Handler.right_widget.update_tab()

    def singlePart_add2xzLayer(self):
        super(GLWin, self).singlePart_add2xzLayer()
        Handler.right_widget.update_tab()


class MainHandler:
    def __init__(self, window):
        # -------------------------------------------------------------------------------------信号与槽
        self.LoadingProject = False
        self.SavingProject = False
        # -------------------------------------------------------------------------------------GUI设置
        self.window = window
        self.MenuMap = {
            " 设计": {
                "打开工程": self._open_project,
                "新建工程": {"从NavalArt": self.new_prj_from_na, "空白": self.new_prj_empty},
                "导出为": self.export_file,
                "保存工程": self.save,
                "另存为": self.save_as
            },
            " 编辑": {
                "全选": self.select_all
            },
            " 设置": {
                "界面主题": self.set_theme,
                "操作灵敏度": self.set_sensitivity,
                "框线显示": self.set_lines,
                "开发者控制台": self.show_console,
            },
            " 视图": {
                "切换视图": self.switch_view,
            },
            " 帮助": {
                "检查更新": check_version,
                "查看教程": user_guide,
                "关于我们": self.about
            }
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
        show_state("初始化事件管理器完成", 'process', self.window.statu_label)  # 显示状态
        # 其他设置
        self.hull_design_tab.ThreeDFrame.button_func_map[
            self.hull_design_tab.ThreeDFrame.b2] = self.right_widget.change_tab
        self.hull_design_tab.ThreeDFrame.button_func_map[
            self.hull_design_tab.ThreeDFrame.b3] = self.right_widget.change_tab

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

    @staticmethod
    def new_project(event):
        new_project()

    def new_prj_from_na(self, event):
        if self.LoadingProject:
            MyMessageBox.information(self.window, "提示", "正在读取工程，请稍后再试！")
            return
        if self.SavingProject:
            MyMessageBox.information(self.window, "提示", "正在保存工程，请稍后再试！")
            return
        # 如果用户没有安装NavalArt:
        if NAPath == os.path.join(os.path.expanduser("~"), "Desktop"):
            # 打开文件选择窗口，目录为NavalArt目录 ===================================================
            file_dialog = QFileDialog(self.window, "选择图纸", NAPath)
            file_dialog.setNameFilter("na files (*.na)")
            file_dialog.exec_()
            try:
                _original_na_p = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
            except IndexError:
                return
        else:  # 如果用户安装了NavalArt:
            file_dialog = SelectNaDialog(parent=Handler.window)
            file_dialog.exec_()
            if not file_dialog.selected_na_design:
                show_state("未选择船体设计文件", 'error')
                return
            _original_na_p = os.path.join(NAPath, f"{file_dialog.selected_na_design}.na")
        try:
            # 开启读取工程的线程
            self.LoadingProject = True
            self.window.read_na_hull_thread = ReadNAHullThread(_original_na_p)
            self.window.read_na_hull_thread.update_state.connect(show_state)
            self.window.read_na_hull_thread.finished.connect(
                lambda: self.read_na_hull_thread_finished(_original_na_p, Handler.window.read_na_hull_thread.na_hull))
            self.window.read_na_hull_thread.start()
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self.window, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开或不存在，请关闭后重试"
            MyMessageBox().information(self.window, "提示", _txt, MyMessageBox.Ok)
            return

    # noinspection PyUnresolvedReferences
    def read_na_hull_thread_finished(self, _original_na_p, _na_hull):
        try:
            show_state(f"{_original_na_p}读取成功", 'success')
            # 获取用户选择的工程路径 ==========================================================================
            chosen_path = find_na_root_path() if Config.Projects == {} else Config.ProjectsFolder
            default_name = _original_na_p.split('/')[-1].split('.')[0]
            try:
                save_dialog = QFileDialog(self.window, "选择工程保存路径", chosen_path)
                save_dialog.setFileMode(QFileDialog.AnyFile)
                save_dialog.setAcceptMode(QFileDialog.AcceptSave)
                save_dialog.setNameFilter("NavalArt Project files (*.naprj)")  # 仅让用户选择路径和文件名称，文件类型为naprj（json）
                save_dialog.selectFile(default_name)
                save_dialog.exec_()
            except Exception as _e:
                show_state(f"保存工程失败：{_e}", 'error')
                MyMessageBox().information(self.window, "提示", f"保存工程失败：{_e}", MyMessageBox.Ok)
                return
            # 获取选择的文件路径
            try:
                _prj_path = save_dialog.selectedFiles()[0]
                _name = _prj_path.split('/')[-1].split('.')[0]
            except IndexError:
                show_state(f"保存工程失败：未选择文件", 'error')
                return
            # 检测颜色种类，弹出对话框，选择颜色
            color_dialog = ColorDialog(self.window, _na_hull)
            color_dialog.exec_()
            # 生成工程文件对象
            self.window.new_project_thread = ProjectLoadingNewThread(_na_hull, _name, _prj_path, _original_na_p)
            self.window.new_project_thread.update_state.connect(show_state)
            self.window.new_project_thread.finished.connect(after_new)
            self.window.new_project_thread.start()
        except Exception as _e:
            raise _e

    def new_prj_empty(self, event):
        if self.LoadingProject:
            MyMessageBox.information(self.window, "提示", "正在读取工程，请稍后再试！")
            return
        if self.SavingProject:
            MyMessageBox.information(self.window, "提示", "正在保存工程，请稍后再试！")
            return
        # 获取用户选择的工程路径 ==========================================================================
        chosen_path = find_na_root_path() if Config.Projects == {} else Config.ProjectsFolder
        default_name = "新建工程"
        try:
            save_dialog = QFileDialog(self.window, "选择工程保存路径", chosen_path)
            save_dialog.setFileMode(QFileDialog.AnyFile)
            save_dialog.setAcceptMode(QFileDialog.AcceptSave)
            save_dialog.setNameFilter("NavalArt Project files (*.naprj)")  # 仅让用户选择路径和文件名称，文件类型为naprj（json）
            save_dialog.selectFile(default_name)
            save_dialog.exec_()
        except Exception as _e:
            show_state(f"保存工程失败：{_e}", 'error')
            MyMessageBox().information(self.window, "提示", f"保存工程失败：{_e}", MyMessageBox.Ok)
            return
        # 获取选择的文件路径
        try:
            _prj_path = save_dialog.selectedFiles()[0]
            _name = _prj_path.split('/')[-1].split('.')[0]
        except IndexError:
            show_state(f"保存工程失败：未选择文件", 'error')
            return
        # 取色
        color_dialog = ColorPicker(self.window)
        color_dialog.exec_()
        _color = color_dialog.current_color
        # 新建空白工程文件对象
        prj = NewEmptyPrj(_name, _prj_path, _color)
        na_hull = prj.na_hull
        Handler.hull_design_tab.init_NaHull_partRelationMap_Layers(na_hull)
        # 在这里继续执行后续操作，如下所示
        show_state(f"新建 {_name}", 'success')
        after_new()
        Handler.LoadingProject = False
        # 在右侧窗口显示初步调整新建工程的界面

    @staticmethod
    def _open_project(event):
        open_project()

    def export_file(self, event=None):
        if Handler.LoadingProject:
            MyMessageBox.information(self.window, "提示", "正在读取工程，请稍后再试！")
            return
        if Handler.SavingProject:
            MyMessageBox.information(self.window, "提示", "正在保存工程，请稍后再试！")
            return
        # # 打开ExportDialog
        # export_dialog = ExportDialog(parent=self.window)
        # export_dialog.exec_()
        # # 如果确定导出
        # if export_dialog.export2na:
        show_state("正在导出为NA文件...", 'process')
        choose_na_dialog = SelectNaDialog(parent=self.window, title="选择导出的目标设计")
        choose_na_dialog.exec_()
        if choose_na_dialog.selected_na_design:
            na_path = os.path.join(NAPath, f"{choose_na_dialog.selected_na_design}.na")
            self.export2Na(na_path)
            show_state(f"{ProjectHandler.current.Name}  已导出到  {na_path}", 'success')
        # elif export_dialog.export2obj:
        #     show_state("正在导出为OBJ文件...", 'process')
        #     # TODO: 导出为OBJ文件
        #     show_state(f"{ProjectHandler.current.Name}  已导出到  {path}", 'success')

    def reload(self):
        # 重新从文件加载当前
        if self.LoadingProject:
            MyMessageBox.information(self.window, "提示", "正在读取工程，请稍后再试！")
            return
        if self.SavingProject:
            MyMessageBox.information(self.window, "提示", "正在保存工程，请稍后再试！")
            return
        if not ProjectHandler.current:
            show_state("当前没有工程", 'error')
            return
        # 重新加载
        show_state("正在重新加载工程...", 'process')
        self.LoadingProject = True
        self.window.read_project_thread = ProjectOpeningThread(ProjectHandler.current.Path)
        self.window.read_project_thread.update_state.connect(show_state)
        self.window.read_project_thread.finished.connect(after_open)
        self.window.read_project_thread.start()

    def export2Na(self, na_path):
        """
        导出为NA文件
        :param na_path: NA文件路径
        :return:
        """
        # 保存
        Config.save_config()
        self.save()
        # 读取NA文件（以xml格式）
        ProjectHandler.current.save_as_na(na_path, na_path)

    @staticmethod
    def save():
        if ProjectHandler.current:
            ProjectHandler.current.save()

    @staticmethod
    def save_as():
        if ProjectHandler.current:
            ProjectHandler.current.save_as()

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
        ThreeDF = self.hull_design_tab.ThreeDFrame
        if ThreeDF.show_3d_obj_mode == (OpenGLWin.ShowAll, OpenGLWin.ShowObj):
            id_map = NAPart.hull_design_tab_id_map
        else:
            id_map = ThreeDF.selectObjOrigin_map[ThreeDF.show_3d_obj_mode].id_map
        ThreeDF.selected_gl_objects[ThreeDF.show_3d_obj_mode] = list(id_map.values())
        ThreeDF.paintGL()
        ThreeDF.update()
        show_state(f"已选中{len(ThreeDF.selected_gl_objects[ThreeDF.show_3d_obj_mode])}个对象", 'success')

    def set_theme(self, event):
        theme_dialog = ThemeDialog(config=Config, show_state_func=show_state, parent=self.window)
        theme_dialog.exec_()
        # 让用户确认是否重启程序
        reply = MyMessageBox().question(self.window, "提示", "是否重启程序？\n我们将会为您保存进度",
                                        MyMessageBox.Yes | MyMessageBox.No)
        if reply == QMessageBox.No:
            return
        # 保存配置文件
        Config.save_config()
        if ProjectHandler.current:
            ProjectHandler.current.save()
        # 获取当前运行的可执行文件的路径
        file_path = sys.argv[0]
        # 重启程序，注意，程序已经被打包为exe
        os.system(f"start {file_path}")
        sys.exit()

    def set_sensitivity(self, event):
        sensitive_dialog = SensitiveDialog(config=Config, camera=Camera, parent=self.window)
        sensitive_dialog.exec_()

    def set_lines(self, event):
        # 提示用户功能未实现
        MyMessageBox.information(self.window, "提示", "该功能暂未实现！")

    def show_console(self, event):
        if (address := get_mac_address()) is not True:  # 不是我的电脑
            # 对地址进行加密
            from hashlib import md5
            address_md5 = md5(address.encode()).hexdigest()
            text = f"""
            您没有权限访问开发者控制台！是否申请权限？
            """
            if MyMessageBox.information(self.window, "提示", text, MyMessageBox.Yes | MyMessageBox.No) == QMessageBox.Yes:
                text2 = f"""
                您的申请码为：
                {address_md5}\n
                请将申请码发送至邮箱：2593292614@qq.com
                """
                MyMessageBox.information(self.window, "提示", text2, MyMessageBox.Ok)
        else:
            open_developer_console(Handler, ProjectHandler)

    def switch_view(self, event):
        # 将hull_design_tab.ThreeDFrame的视图进行切换（透视或者正交）
        # 提示用户功能未实现
        MyMessageBox.information(self.window, "提示", "该功能暂未实现！")
        # self.hull_design_tab.ThreeDFrame.change_view_mode()

    @staticmethod
    def about(event):
        # 打开网页
        url = 'http://naval_plugins.e.cn.vc/'
        webbrowser.open(url)

    def close(self) -> bool:
        # 重写关闭事件
        if ProjectHandler.current:
            reply = MyMessageBox().question(self.window, "关闭编辑器", "是否保存当前工程？",
                                            MyMessageBox.Yes | MyMessageBox.No | MyMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                Config.save_config()  # 保存配置文件
                show_state("正在保存工程...", 'process')
                # 隐藏window
                self.window.hide()
                if ProjectHandler.current:
                    ProjectHandler.current.save()
                self.window.close()  # 关闭窗口
                sys.exit()  # 退出程序
            elif reply == QMessageBox.No:
                Config.save_config()
                self.window.close()  # 关闭窗口
                sys.exit()  # 退出程序
            else:
                return False
        else:
            Config.save_config()
            self.window.close()
            sys.exit()


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
        # ======================================================================查看模式tab1_mod1的三种界面
        self.tab1_mod1_widget_singlePart = Mod1SinglePartView()
        self.tab1_mod1_widget_verticalPartSet = Mod1VerticalPartSetView()
        self.tab1_mod1_widget_horizontalPartSet = Mod1HorizontalPartSetView()
        self.tab1_mod1_widget_verHorPartSet = Mod1VerHorPartSetView()
        self.tab1_mod1_widget_allParts = Mod1AllPartsView()
        # ===========================================================================tab1_mod2的两种界面
        self.tab1_mod2_widget_singleLayer = QWidget()
        self.tab1_mod2_widget_multiLayer = QWidget()
        self.tab1_mod2_grid_singleLayer = QGridLayout()
        self.tab1_mod2_grid_multiLayer = QGridLayout()
        # =====================================================================编辑模式tab2_mod1的三种界面
        self.tab2_mod1_widget_singlePart = Mod1SinglePartEditing()
        self.tab2_mod1_widget_verticalPartSet = Mod1VerticalPartSetEditing()
        self.tab2_mod1_widget_horizontalPartSet = Mod1HorizontalPartSetEditing()
        self.tab2_mod1_widget_verHorPartSet = Mod1VerHorPartSetEditing()
        self.tab2_mod1_widget_allParts = Mod1AllPartsEditing()
        # ===========================================================================tab2_mod2的两种界面
        self.tab2_mod2_widget_singleLayer = QWidget()
        self.tab2_mod2_widget_multiLayer = QWidget()
        self.tab2_mod2_grid_singleLayer = QGridLayout()
        self.tab2_mod2_grid_multiLayer = QGridLayout()
        # 00000000000000000000000000000000000000000000000000000000000000000000000000 操作绑定
        self.tab2_operation_addPartLayer = AddLayerEditing()
        AddLayerOperation.right_frame = self.tab2_operation_addPartLayer
        # 当前显示的widget
        self.tab1_current_widget = self.tab1_mod1_widget_allParts
        self.tab2_current_widget = self.tab2_mod1_widget_allParts
        # GUI绑定和样式
        self.init_style()
        self.bind_widget()
        # 信号
        self.ActiveTab = "船体设计"
        # if self.ActiveTab == "船体设计":
        #     self.show_mod = Handler.hull_design_tab.ThreeDFrame.show_3d_obj_mode

    def change_tab(self, tab_index):
        self.setCurrentWidget(self.widget(tab_index))
        if tab_index == 1:
            GLWin.key_state = {
                Qt.Key_A: False, Qt.Key_B: False, Qt.Key_C: False, Qt.Key_D: False, Qt.Key_E: False, Qt.Key_F: False,
                Qt.Key_G: False, Qt.Key_H: False, Qt.Key_I: False, Qt.Key_J: False, Qt.Key_K: False, Qt.Key_L: False,
                Qt.Key_M: False, Qt.Key_N: False, Qt.Key_O: False, Qt.Key_P: False, Qt.Key_Q: False, Qt.Key_R: False,
                Qt.Key_S: False, Qt.Key_T: False, Qt.Key_U: False, Qt.Key_V: False, Qt.Key_W: False, Qt.Key_X: False,
                Qt.Key_Y: False, Qt.Key_Z: False
            }

    def update_tab(self):
        if Handler.LoadingProject or Handler.SavingProject or OperationEditing.is_editing:
            return
        ThreeDFrame = Handler.hull_design_tab.ThreeDFrame
        _len = len(ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode])
        # 隐藏当前的widget
        self.tab1_current_widget.hide()
        self.tab2_current_widget.hide()
        # 禁用Handler.hull_design_tab.menu的扩展选区栏目
        Handler.hull_design_tab.menu.expand_select_area_A.setEnabled(False)
        if _len == 0:
            self.tab1_mod1_widget_allParts.show()
            self.tab2_mod1_widget_allParts.show()
            self.tab1_current_widget = self.tab1_mod1_widget_allParts
            self.tab2_current_widget = self.tab2_mod1_widget_allParts
            # self.tab1_mod1_widget_allParts.update_context()
            self.tab2_mod1_widget_allParts.update_context()
        # 当被选中物体变化的时候，更新tab的内容
        elif _len == 1:  # ================================================================== 只有一个物体
            # 获取选中的物体
            selected_obj = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
            if type(selected_obj) in (NAPart, AdjustableHull):
                # 更新显示的widget
                self.tab1_mod1_widget_singlePart.show()
                self.tab2_mod1_widget_singlePart.show()
                self.tab1_current_widget = self.tab1_mod1_widget_singlePart
                self.tab2_current_widget = self.tab2_mod1_widget_singlePart
                self.tab1_mod1_widget_singlePart.update_context(selected_obj)
                self.tab2_mod1_widget_singlePart.update_context(selected_obj)
                # 启用Handler.hull_design_tab.menu的扩展选区栏目，并绑定函数
                Handler.hull_design_tab.menu.expand_select_area_A.setEnabled(True)
                Handler.hull_design_tab.menu.connect_expand_select_area_funcs(
                    add2xzLayer_func=ThreeDFrame.singlePart_add2xzLayer,
                    add2xyLayer_func=ThreeDFrame.singlePart_add2xyLayer
                )
            elif type(selected_obj) == NaHullXZLayer:
                self.tab1_mod2_widget_singleLayer.show()  # TODO: 显示tab1_mod2_grid_singleLayer
                self.tab2_mod2_widget_singleLayer.show()  # TODO: 显示tab2_mod2_grid_singleLayer
                self.tab1_current_widget = self.tab1_mod2_widget_singleLayer
                self.tab2_current_widget = self.tab2_mod2_widget_singleLayer
            else:
                ...
                # TODO: 其他类型的物体
        elif _len > 1:  # =================================================================== 多个物体
            _type = type(ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0])
            if _type in (NAPart, AdjustableHull):  # 判断零件之间的关系
                # 判断是否全选：
                if _len == len(ThreeDFrame.selectObjOrigin_map[ThreeDFrame.show_3d_obj_mode].hull_design_tab_id_map):
                    # 全选
                    self.tab1_mod1_widget_allParts.show()
                    self.tab2_mod1_widget_allParts.show()
                    self.tab1_current_widget = self.tab1_mod1_widget_allParts
                    self.tab2_current_widget = self.tab2_mod1_widget_allParts
                    self.tab2_mod1_widget_allParts.update_context()
                    return
                selected_parts = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode]
                selected_num = len(selected_parts)
                # 随机取一个零件
                root_node_part = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
                # 获取关系图
                relation_map = root_node_part.allParts_relationMap
                if root_node_part not in relation_map.basicMap:
                    return
                root_relation_map = relation_map.basicMap[root_node_part]
                # 按顺序向前后左右搜寻零件
                dir_index_map = {
                    CONST.FRONT: 0,
                    CONST.BACK: 0,
                    CONST.LEFT: 0,
                    CONST.RIGHT: 0,
                    CONST.UP: 0,
                    CONST.DOWN: 0,
                }
                # 获取整个selected_parts的上下左右范围
                for direction, part_value_map in root_relation_map.items():
                    # part_value_map是有序的，按照value从小到大
                    for part, _value in part_value_map.items():
                        if part in selected_parts:
                            dir_index_map[direction] += 1
                        else:
                            break
                # 分别统计前后，左右，上下，如果为0正好被判定为False，用作布尔值
                front_back = dir_index_map[CONST.FRONT] + dir_index_map[CONST.BACK]
                left_right = dir_index_map[CONST.LEFT] + dir_index_map[CONST.RIGHT]
                up_down = dir_index_map[CONST.UP] + dir_index_map[CONST.DOWN]
                if not front_back:  # 纵截块
                    if not left_right:  # 竖直截块
                        if selected_num == up_down + 1:
                            # show_state("竖直截块", 'process')
                            self.tab1_mod1_widget_verticalPartSet.show()
                            self.tab2_mod1_widget_verticalPartSet.show()
                            self.tab1_current_widget = self.tab1_mod1_widget_verticalPartSet
                            self.tab2_current_widget = self.tab2_mod1_widget_verticalPartSet
                            self.tab2_mod1_widget_verticalPartSet.selected_objs = selected_parts.copy()
                    else:  # 纵截块
                        # 往左右两边遍历切换根节点，搜寻上下零件
                        for i in range(dir_index_map[CONST.LEFT]):
                            _temp_root = list(root_relation_map[CONST.LEFT].keys())[i]
                            _temp_root_relation_map = relation_map.basicMap[_temp_root]
                            _temp_root_up_map = _temp_root_relation_map[CONST.UP]
                            _temp_root_down_map = _temp_root_relation_map[CONST.DOWN]
                            for j in range(dir_index_map[CONST.UP]):
                                if list(_temp_root_up_map.keys())[j] not in selected_parts:
                                    break
                            for j in range(dir_index_map[CONST.DOWN]):
                                if list(_temp_root_down_map.keys())[j] not in selected_parts:
                                    break
                            else:
                                if selected_num == (left_right + 1) * (up_down + 1):
                                    self.tab1_mod1_widget_verHorPartSet.show()
                                    self.tab2_mod1_widget_verHorPartSet.show()
                                    self.tab1_current_widget = self.tab1_mod1_widget_verHorPartSet
                                    self.tab2_current_widget = self.tab2_mod1_widget_verHorPartSet
                                    break
                if not up_down:  # 水平截块
                    if not left_right:
                        if selected_num == front_back + 1:
                            # show_state("水平截块", 'process')
                            self.tab1_mod1_widget_horizontalPartSet.show()
                            self.tab2_mod1_widget_horizontalPartSet.show()
                            self.tab1_current_widget = self.tab1_mod1_widget_horizontalPartSet
                            self.tab2_current_widget = self.tab2_mod1_widget_horizontalPartSet
                            self.tab2_mod1_widget_horizontalPartSet.selected_objs = selected_parts.copy()
                    else:  # 水平截块
                        # 往左右两边遍历切换根节点，搜寻前后零件
                        for i in range(dir_index_map[CONST.LEFT]):
                            _temp_root = list(root_relation_map[CONST.LEFT].keys())[i]
                            _temp_root_relation_map = relation_map.basicMap[_temp_root]
                            _temp_root_front_map = _temp_root_relation_map[CONST.FRONT]
                            _temp_root_back_map = _temp_root_relation_map[CONST.BACK]
                            for j in range(dir_index_map[CONST.FRONT]):
                                if list(_temp_root_front_map.keys())[j] not in selected_parts:
                                    break
                            for j in range(dir_index_map[CONST.BACK]):
                                if list(_temp_root_back_map.keys())[j] not in selected_parts:
                                    break
                            else:
                                if selected_num == (left_right + 1) * (front_back + 1):
                                    self.tab1_mod1_widget_verHorPartSet.show()
                                    self.tab2_mod1_widget_verHorPartSet.show()
                                    self.tab1_current_widget = self.tab1_mod1_widget_verHorPartSet
                                    self.tab2_current_widget = self.tab2_mod1_widget_verHorPartSet
                                    break

                # x_list = []
                # z_list = []
                # y_list = []
                # for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode]:
                #     if selected_obj is None:
                #         return
                #     if x_list.count(selected_obj.Pos[0]) == 0:
                #         x_list.append(selected_obj.Pos[0])
                #     if y_list.count(selected_obj.Pos[1]) == 0:
                #         y_list.append(selected_obj.Pos[1])
                #     if z_list.count(selected_obj.Pos[2]) == 0:
                #         z_list.append(selected_obj.Pos[2])
                # if len(set(x_list)) != 1:  # 排除零件的x坐标不相同的情况
                #     return
                # # 如果所有零件的z坐标都相同，那么就说明这是一组纵向排列的船体截块
                # if len(set(z_list)) == 1:
                #     connected = True  # 判断是否上下相连
                #     # 把selected_gl_obj 按照 part_obj.Pos[1] 从小到大排序:
                #     ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode].sort(key=lambda x: x.Pos[1])
                #     last_part = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
                #     for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][1:]:
                #         last_up = last_part.Pos[1] + last_part.Hei * last_part.Scl[1] / 2
                #         this_down = selected_obj.Pos[1] - selected_obj.Hei * selected_obj.Scl[1] / 2
                #         if last_up < this_down:
                #             connected = False
                #             break
                #         last_part = selected_obj
                #     if connected:  # 如果相连，接下来要显示self.tab1_mod1_grid_verticalPartSet
                #         if self.ActiveTab == "船体设计":
                #             self.tab1_mod1_widget_verticalPartSet.show()
                #             self.tab2_mod1_widget_verticalPartSet.show()
                #         self.tab1_current_widget = self.tab1_mod1_widget_verticalPartSet
                #         self.tab2_current_widget = self.tab2_mod1_widget_verticalPartSet
                #         self.init_tab1_mod1_grid_verticalPartSet()
                #         self.init_tab2_mod1_grid_verticalPartSet()
                #
                # # 如果所有零件的x和y坐标都相同，那么就说明这是一组横向排列的船体截块
                # elif len(set(y_list)) == 1:
                #     connected = True  # 判断是否前后相连
                #     # 把selected_gl_obj 按照 part_obj.Pos[2] 从小到大排序:
                #     ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode].sort(key=lambda x: x.Pos[2])
                #     last_part = ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][0]
                #     for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode][1:]:
                #         last_front = last_part.Pos[2] + last_part.Len * last_part.Scl[2] / 2
                #         this_back = selected_obj.Pos[2] - selected_obj.Len * selected_obj.Scl[2] / 2
                #         if last_front != this_back:
                #             connected = False
                #             break
                #         last_part = selected_obj
                #     if connected:  # 如果相连，接下来要显示self.tab1_mod1_grid_horizontalPartSet
                #         if self.ActiveTab == "船体设计":
                #             self.tab1_mod1_widget_horizontalPartSet.show()
                #             self.tab2_mod1_widget_horizontalPartSet.show()
                #         self.tab1_current_widget = self.tab1_mod1_widget_horizontalPartSet
                #         self.tab2_current_widget = self.tab2_mod1_widget_horizontalPartSet
                #         self.init_tab1_mod1_grid_horizontalPartSet()
                #         self.init_tab2_mod1_grid_horizontalPartSet()
                # elif _len == len(set(y_list)) * len(set(z_list)):  # 集成块的情况：所有零件的x坐标都相同，且y坐标和z坐标构成中间不间断的矩形点阵。
                #     """
                #     （"x"表示零件位置，"|"表示边界，"-"表示零件的上下面相切，
                #     所有等y零件的前后面相切，所有等z零件的上下面相切）
                #     示例（左视简图）：
                #     -----------------------------------------
                #     | x |   x   |  x  |     x     |   x   |x|
                #     -----------------------------------------
                #     |   |       |     |           |       | |
                #     | x |   x   |  x  |     x     |   x   |x|
                #     |   |       |     |           |       | |
                #     -----------------------------------------
                #     | x |   x   |  x  |     x     |   x   |x|
                #     -----------------------------------------
                #     """
                #     connected = True
                #     # 首先判断是否满足矩形点阵
                #     zy_dict = {}  # 键值对为z: [part0, part1, ...]
                #     for selected_obj in ThreeDFrame.selected_gl_objects[ThreeDFrame.show_3d_obj_mode]:
                #         if selected_obj.Pos[2] not in zy_dict:
                #             zy_dict[selected_obj.Pos[2]] = [selected_obj]
                #         else:
                #             zy_dict[selected_obj.Pos[2]].append(selected_obj)
                #     last_y_set = set([part_obj.Pos[1] for part_obj in zy_dict[list(zy_dict.keys())[0]]])
                #     for i in range(1, len(zy_dict)):
                #         this_y_set = set([part_obj.Pos[1] for part_obj in zy_dict[list(zy_dict.keys())[i]]])
                #         if last_y_set != this_y_set:
                #             connected = False
                #             break
                #     # 然后计算第一层零件前后是否相连
                #     if connected:
                #         ...
                #     # 接着计算第一竖排零件上下是否相连
                #     if connected:
                #         if self.ActiveTab == "船体设计":
                #             self.tab1_mod1_widget_verHorPartSet.show()
                #             self.tab2_mod1_widget_verHorPartSet.show()
                #         self.tab1_current_widget = self.tab1_mod1_widget_verHorPartSet
                #         self.tab2_current_widget = self.tab2_mod1_widget_verHorPartSet
                #         self.init_tab1_mod1_grid_verHorPartSet()
                #         self.init_tab2_mod1_grid_verHorPartSet()
            elif _type == NaHullXZLayer:
                self.tab1_mod2_widget_multiLayer.show()
                self.tab2_mod2_widget_multiLayer.show()
                self.tab1_current_widget = self.tab1_mod2_widget_multiLayer  # TODO: 显示tab1_mod2_grid_multiLayer
                self.tab2_current_widget = self.tab2_mod2_widget_multiLayer  # TODO: 显示tab2_mod2_grid_multiLayer
            else:
                ...
                # TODO: 其他类型的物体

    def tab1_grid_qte_mouse_wheel(self, event=None):
        # 寻找当前鼠标所在的输入框
        active_textEdit = None
        for key in self.tab2_mod1_widget_singlePart:
            if key != "类型":
                for qte in self.tab2_mod1_widget_singlePart[key]["QTextEdit"]:
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
            "border-top-right-radius:8px;"
            "border-bottom-right-radius:8px;"
            f"border-right:0px solid {FG_COLOR2};"
            f"border-left:1px solid {FG_COLOR2};}}"
            # 设置选中标签栏样式
            f"QTabBar::tab:selected{{background-color:{BG_COLOR3};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-height:30ex;"
            "border-top-right-radius:8px;"
            "border-bottom-right-radius:8px;"
            f"border-right:0px solid {FG_COLOR2};"
            f"border-left:1px solid {FG_COLOR2};}}"
            # 设置鼠标悬停标签栏样式
            f"QTabBar::tab:hover{{background-color:{BG_COLOR3};"
            f"color:{FG_COLOR0};"
            "padding:4px;"
            "min-height:30ex;"
            "border-top-right-radius:0px;"
            "border-bottom-right-radius:0px;"
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
        # ===================================================================================tab1
        # tab1_mod2
        self.tab1_mod2_widget_singleLayer.setLayout(self.tab1_mod2_grid_singleLayer)
        self.tab1_mod2_widget_multiLayer.setLayout(self.tab1_mod2_grid_multiLayer)
        # 添加控件
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_singlePart)  # mod1
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_verticalPartSet)
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_horizontalPartSet)
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_verHorPartSet)
        self.tab1_main_layout.addWidget(self.tab1_mod1_widget_allParts)
        self.tab1_main_layout.addWidget(self.tab1_mod2_widget_singleLayer)  # mod2
        self.tab1_main_layout.addWidget(self.tab1_mod2_widget_multiLayer)
        # 隐藏
        self.tab1_mod1_widget_singlePart.hide()  # mod1
        self.tab1_mod1_widget_verticalPartSet.hide()
        self.tab1_mod1_widget_horizontalPartSet.hide()
        self.tab1_mod1_widget_verHorPartSet.hide()
        self.tab1_mod2_widget_singleLayer.hide()  # mod2
        self.tab1_mod2_widget_multiLayer.hide()
        # ===================================================================================tab2
        # tab2_mod2
        self.tab2_mod2_widget_singleLayer.setLayout(self.tab2_mod2_grid_singleLayer)
        self.tab2_mod2_widget_multiLayer.setLayout(self.tab2_mod2_grid_multiLayer)
        # 添加控件
        self.tab2_main_layout.addWidget(self.tab2_mod1_widget_singlePart)  # mod1
        self.tab2_main_layout.addWidget(self.tab2_mod1_widget_verticalPartSet)
        self.tab2_main_layout.addWidget(self.tab2_mod1_widget_horizontalPartSet)
        self.tab2_main_layout.addWidget(self.tab2_mod1_widget_verHorPartSet)
        self.tab2_main_layout.addWidget(self.tab2_mod1_widget_allParts)
        self.tab2_main_layout.addWidget(self.tab2_mod2_widget_singleLayer)  # mod2
        self.tab2_main_layout.addWidget(self.tab2_mod2_widget_multiLayer)
        # 00000000000000000000000000000000000000000000000000000000000000000000000 操作
        self.tab2_main_layout.addWidget(self.tab2_operation_addPartLayer)
        # 隐藏
        self.tab2_mod1_widget_singlePart.hide()  # mod1
        self.tab2_mod1_widget_verticalPartSet.hide()
        self.tab2_mod1_widget_horizontalPartSet.hide()
        self.tab2_mod1_widget_verHorPartSet.hide()
        self.tab2_mod2_widget_singleLayer.hide()  # mod2
        self.tab2_mod2_widget_multiLayer.hide()
        # 添加伸缩
        self.tab1_main_layout.addStretch(1)
        self.tab2_main_layout.addStretch(1)
        # 添加浅灰色快捷键提示
        short_cut_widget = ShortCutWidget()
        self.tab1_main_layout.addWidget(short_cut_widget, alignment=Qt.AlignLeft)

    def init_tab1(self):
        tab = QWidget()
        tab.setLayout(self.tab1_main_layout)
        # 标题
        title = MyLabel("元素检视器", FONT_10, side=Qt.AlignTop | Qt.AlignCenter)
        self.tab1_main_layout.addWidget(title, alignment=Qt.AlignTop | Qt.AlignCenter)
        # 添加分割线
        self.tab1_main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken), alignment=Qt.AlignTop)
        return tab

    def init_tab2(self):
        tab = QWidget()
        tab.setLayout(self.tab2_main_layout)
        # 标题
        title = MyLabel("属性编辑器", FONT_10, side=Qt.AlignCenter)
        self.tab2_main_layout.addWidget(title)
        # 添加分割线
        self.tab2_main_layout.addWidget(QFrame(  # top下方添加横线
            self, frameShape=QFrame.HLine, frameShadow=QFrame.Sunken), alignment=Qt.AlignTop)
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
        self.Font = FONT_8
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = GLWin(Config.Sensitivity, various_mode=True, show_statu_func=show_state)
        self.down_layout = QHBoxLayout()
        self.left_tool_bar = QToolBar()
        self.init_layout()
        self.save_button = QPushButton("保存")
        self.open_button = QPushButton("打开")
        self.read_from_na_button = QPushButton("从NA新建")
        self.convertAdhull_button = QPushButton("从PTB转换")
        self.init_buttons()
        self.up_layout.addStretch()
        self.menu = DesignTabGLWinMenu(self.ThreeDFrame)
        self.menu.connect_basic_funcs(
            self.undo, self.redo, self.delete, self.add, self.import_, self.export
        )
        self.bind_shortcut()
        # -----------------------------------------------------------------------------------信号
        self.camera = self.ThreeDFrame.camera
        self.environment_obj = self.ThreeDFrame.environment_obj
        # 在不同模式下显示的物体：
        self.all_3d_obj = self.ThreeDFrame.all_3d_obj  # 普通模式
        self.prj_all_parts = self.ThreeDFrame.prj_all_parts  # 普通模式全体零件
        self.xz_layer_obj = self.ThreeDFrame.xz_layer_obj  # 横剖面模式
        self.xy_layer_obj = self.ThreeDFrame.xy_layer_obj  # 纵剖面模式
        self.left_view_obj = self.ThreeDFrame.left_view_obj  # 左视图模式
        # 被选中的物体：
        self.selected_gl_objects = self.ThreeDFrame.selected_gl_objects  # 选中的物体

    # noinspection PyUnresolvedReferences
    def bind_shortcut(self):
        # 基础快捷键绑定
        save_ = QShortcut(QKeySequence("Ctrl+S"), self)
        save_.activated.connect(self.save)
        # 操作快捷键绑定
        expand_ = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_ = QShortcut(QKeySequence("Shift+E"), self)
        undo_ = QShortcut(QKeySequence("Ctrl+Z"), self)
        redo_ = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        copy_ = QShortcut(QKeySequence("Ctrl+C"), self)
        paste_ = QShortcut(QKeySequence("Ctrl+V"), self)
        delete_ = QShortcut(QKeySequence("Delete"), self)
        add_ = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        import_ = QShortcut(QKeySequence("I"), self)
        export_ = QShortcut(QKeySequence("O"), self)
        expand_.activated.connect(self.expand)
        edit_.activated.connect(self.edit)
        undo_.activated.connect(self.undo)
        redo_.activated.connect(self.redo)
        copy_.activated.connect(self.copy)
        paste_.activated.connect(self.paste)
        delete_.activated.connect(self.delete)
        add_.activated.connect(self.add)
        import_.activated.connect(self.import_)
        export_.activated.connect(self.export)

    @staticmethod
    def save():
        if ProjectHandler.current:
            ProjectHandler.current.save()

    @staticmethod
    def open():
        open_project()

    def expand(self):
        # 检查当前被选中的物体的数量和形式
        _len = len(self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode])
        if _len == 0:
            return

    @staticmethod
    def edit():
        show_state(f"编辑选区", 'success')
        # 右边栏切换到属性编辑器（第二个标签，索引为1）
        Handler.right_widget.setCurrentIndex(1)
        Handler.right_widget.update_tab()

    @staticmethod
    def undo():
        if ProjectHandler.current:
            ProjectHandler.current.undo()

    @staticmethod
    def redo():
        if ProjectHandler.current:
            ProjectHandler.current.redo()

    def copy(self):
        show_state(f"复制 {self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode]}", 'success')

    def paste(self):
        show_state(f"粘贴 {self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode]}", 'success')

    def delete(self):
        show_state(f"删除 {self.ThreeDFrame.selected_gl_objects[self.ThreeDFrame.show_3d_obj_mode]}", 'success')

    def add(self):
        show_state(f"添加", 'success')

    def import_(self):
        show_state(f"导入", 'success')

    @staticmethod
    def export():
        Handler.export_file()

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

    # noinspection PyUnresolvedReferences
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

    # noinspection PyUnresolvedReferences
    def init_buttons(self):
        bts = [self.save_button, self.open_button, self.read_from_na_button, self.convertAdhull_button]
        sizes = [(50, 30), (50, 30), (100, 30), (100, 30)]
        set_buttons(bts, sizes=sizes, font=FONT_8, border=0, border_radius=0, padding=0, bg=[BG_COLOR0, BG_COLOR3, BG_COLOR3, BG_COLOR1])
        for bt in bts:
            bt.setFocusPolicy(Qt.NoFocus)
            self.up_layout.addWidget(bt, alignment=Qt.AlignLeft)
        self.save_button.clicked.connect(self.save)
        self.open_button.clicked.connect(self.open)
        self.read_from_na_button.clicked.connect(self.read_from_na_button_pressed)
        self.convertAdhull_button.clicked.connect(self.convertAdhull_button_pressed)

    # noinspection PyUnresolvedReferences
    def read_from_na_button_pressed(self):
        if Handler.LoadingProject:
            MyMessageBox.information(self, "提示", "正在读取工程，请稍后再试！")
            return
        if Handler.SavingProject:
            MyMessageBox.information(self, "提示", "正在保存工程，请稍后再试！")
            return
        # 如果用户没有安装NavalArt:
        if self.NAPath == os.path.join(os.path.expanduser("~"), "Desktop"):
            # 打开文件选择窗口，目录为NavalArt目录 ===================================================
            file_dialog = QFileDialog(self, "选择图纸", self.NAPath)
            file_dialog.setNameFilter("na files (*.na)")
            file_dialog.exec_()
            try:
                _original_na_p = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
            except IndexError:
                return
        else:  # 如果用户安装了NavalArt:
            file_dialog = SelectNaDialog(parent=Handler.window)
            file_dialog.exec_()
            if not file_dialog.selected_na_design:
                show_state("未选择船体设计文件", 'error')
                return
            _original_na_p = os.path.join(self.NAPath, f"{file_dialog.selected_na_design}.na")
        try:
            # 开启读取工程的线程
            Handler.LoadingProject = True
            Handler.window.read_na_hull_thread = ReadNAHullThread(_original_na_p)
            Handler.window.read_na_hull_thread.update_state.connect(show_state)
            Handler.window.read_na_hull_thread.finished.connect(
                lambda: self.read_na_hull_thread_finished(_original_na_p, Handler.window.read_na_hull_thread.na_hull))
            Handler.window.read_na_hull_thread.start()
        except AttributeError:
            _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
            # 白色背景的提示框
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return
        except PermissionError:
            _txt = "该文件已被其他程序打开或不存在，请关闭后重试"
            MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
            return

    # noinspection PyUnresolvedReferences
    def read_na_hull_thread_finished(self, _original_na_p, _na_hull):

        def _end():
            show_state(f"未读取工程", 'process')
            Handler.LoadingProject = False
            # 清空ThreeDFrame的所有对象
            self.clear_all_plot_obj()
            NAPart.hull_design_tab_id_map = {}
            for mode in self.ThreeDFrame.gl_commands.keys():
                self.ThreeDFrame.gl_commands[mode][1] = True
            self.ThreeDFrame.paintGL()
            self.ThreeDFrame.update()
            for mode in self.ThreeDFrame.gl_commands.keys():
                self.ThreeDFrame.gl_commands[mode][1] = False
            ProjectHandler.current = None
            NAHull.current_in_design_tab = None

        try:
            show_state(f"{_original_na_p}读取成功", 'success')
            # 获取用户选择的工程路径 ==========================================================================
            chosen_path = find_na_root_path() if Config.Projects == {} else Config.ProjectsFolder
            default_name = _original_na_p.split('/')[-1].split('.')[0]
            try:
                save_dialog = QFileDialog(self, "选择工程保存路径", chosen_path)
                save_dialog.setFileMode(QFileDialog.AnyFile)
                save_dialog.setAcceptMode(QFileDialog.AcceptSave)
                save_dialog.setNameFilter("NavalArt Project (*.naprj)")  # 设置文件过滤器
                save_dialog.selectFile(default_name)
                save_dialog.exec_()
            except Exception as _e:
                show_state(f"保存工程失败：{_e}", 'error')
                MyMessageBox().information(self, "提示", f"保存工程失败：{_e}", MyMessageBox.Ok)
                return
            # 获取选择的文件路径
            # 判断是否是按确定按钮退出的
            if save_dialog.result():
                try:
                    _prj_path = save_dialog.selectedFiles()[0]
                    _name = _prj_path.split('/')[-1].split('.')[0]
                except IndexError:
                    show_state(f"保存工程失败：未选择文件", 'error')
                    return
                # 检测颜色种类，弹出对话框，选择颜色
                color_dialog = ColorDialog(Handler.window, _na_hull)
                color_dialog.exec_()
                if not color_dialog.canceled:
                    # 生成工程文件对象
                    Handler.window.new_project_thread = ProjectLoadingNewThread(_na_hull, _name, _prj_path,
                                                                                _original_na_p)
                    Handler.window.new_project_thread.update_state.connect(show_state)
                    Handler.window.new_project_thread.finished.connect(after_new)
                    Handler.window.new_project_thread.start()
                else:
                    _end()
                    return
            else:
                _end()
                return
        except Exception as _e:
            raise _e

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
        #     self.init_NaHull_partRelationMap_Layers(adhull)
        #     show_state(f"{self.PTBDesignPath}读取成功", 'success')
        # else:
        #     _txt = "该设计不含进阶船体外壳，请重新选择哦"
        #     MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
        #     self.convertAdhull_button_pressed()
        #     return

    def init_NaHull_partRelationMap_Layers(self, na_hull: NAHull):
        """
        当用户完成了颜色选择后，初始化船体需要绘制的对象DrawMap，同时初始化零件关系图，初始化绘图所需的所有对象
        :param na_hull:
        :return:
        """
        na_hull.glWin = self.ThreeDFrame
        if na_hull.Mode == NAHull.NaPathMode:
            # 此时用户显然已经选取了颜色，要根据绘图的DrawMap对需要绘制的零件关系图进行初始化
            na_hull.partRelationMap.init(na_hull=na_hull)
        na_hull.get_layers()
        # 更新自身信号，清空NAPart.hull_design_tab_id_map，重新填入DrawMap的内容
        self.all_3d_obj["钢铁"].append(na_hull)
        NAPart.hull_design_tab_id_map.clear()
        for _color, objs in na_hull.DrawMap.items():
            self.prj_all_parts.extend(objs)
            for obj in objs:
                NAPart.hull_design_tab_id_map[id(obj) % 4294967296] = obj
        self.xz_layer_obj.extend(na_hull.xzLayers)
        self.xy_layer_obj.extend(na_hull.xyLayers)
        self.left_view_obj.extend(na_hull.leftViews)
        # 更新ThreeDFrame的paintGL
        self.ThreeDFrame.paintGL()
        self.ThreeDFrame.update()

    def clear_all_plot_obj(self):
        for mt, objs in self.all_3d_obj.items():
            objs.clear()
        for _class, objs in self.selected_gl_objects.items():
            objs.clear()
        self.prj_all_parts.clear()
        self.xz_layer_obj.clear()
        self.xy_layer_obj.clear()
        self.left_view_obj.clear()
        for _l in self.ThreeDFrame.gl_commands.values():
            _l = [None, False]
        self.ThreeDFrame.list_id_selected = None
        self.ThreeDFrame.update_selected_list = False


class ArmorDesignTab(QWidget):
    def __init__(self, parent=None):
        self.AddImg = QIcon(QPixmap.fromImage(QImage.fromData(ADD_)))
        self.ChooseImg = QIcon(QPixmap.fromImage(QImage.fromData(CHOOSE_)))
        self.NAPath = NAPath
        self.NADesignPath = ''
        super().__init__(parent)
        # -----------------------------------------------------------------------------------GUI设置
        # 设置全局字体
        self.Font = FONT_8
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = OpenGLWin2(Config.Sensitivity, using_various_mode=True, show_statu_func=show_state)
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
        self.Font = FONT_8
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = OpenGLWin(Config.Sensitivity, using_various_mode=False, show_statu_func=show_state)
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
        # noinspection PyUnresolvedReferences
        choose_action.triggered.connect(self.choose_mode)
        self.down_tool_bar.addAction(choose_action)
        # 打包工具栏
        self.down_layout.addWidget(self.down_tool_bar)

    def init_open_button(self):
        set_top_button_style(self.open_button, 50)  # 打开按钮
        # noinspection PyUnresolvedReferences
        self.open_button.clicked.connect(self.convertAdhull_button_pressed)
        self.up_layout.addWidget(self.open_button, alignment=Qt.AlignLeft)

    def convertAdhull_button_pressed(self):
        try:
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
        except Exception as _e:
            raise Exception

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
        self.Font = FONT_8
        # 初始化界面布局
        self.main_layout = QVBoxLayout()
        self.up_layout = QHBoxLayout()
        self.ThreeDFrame = GLWin(Config.Sensitivity, various_mode=False, show_statu_func=show_state)
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
        # noinspection PyUnresolvedReferences
        choose_action.triggered.connect(self.choose_mode)
        self.down_tool_bar.addAction(choose_action)
        # 打包工具栏
        self.down_layout.addWidget(self.down_tool_bar)

    def init_open_button(self):
        set_top_button_style(self.open_button, 50)  # 打开按钮
        # noinspection PyUnresolvedReferences
        self.open_button.clicked.connect(self.find_na_ship_button_pressed)
        self.up_layout.addWidget(self.open_button, alignment=Qt.AlignLeft)

    def find_na_ship_button_pressed(self):
        try:
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
                na_hull = NAHull(path=file_path, show_statu_func=show_state)
            except AttributeError:
                _txt = f"该文件不是有效的船体设计文件，请重新选择哦"
                # 白色背景的提示框
                MyMessageBox().information(Handler.window, "提示", _txt, MyMessageBox.Ok)
                return
            except PermissionError:
                _txt = "该文件已被其他程序打开，请关闭后重试"
                MyMessageBox().information(Handler.window, "提示", _txt, MyMessageBox.Ok)
                return
            for mt, objs in self.all_3d_obj.items():
                objs.clear()
            show_state(f"正在读取{self.NADesignPath}...", 'process')
            show_state(f"{self.NADesignPath}读取成功", 'success')
            # 检测颜色种类，弹出对话框，选择颜色
            color_dialog = ColorDialog(Handler.window, na_hull)
            color_dialog.exec_()
            self.show_na_hull(na_hull)
        except Exception as _e:
            raise Exception

    def show_na_hull(self, na_hull_obj):
        self.all_3d_obj["钢铁"].append(na_hull_obj)
        # 更新ThreeDFrame的paintGL
        self.update_3d_obj()

    def update_3d_obj(self):
        self.ThreeDFrame.environment_obj = self.environment_obj
        self.ThreeDFrame.all_3d_obj = self.all_3d_obj
        for gl_plot_obj in self.all_3d_obj["钢铁"]:
            if type(gl_plot_obj) == NAHull:
                self.ThreeDFrame.prj_all_parts = gl_plot_obj.Parts


def user_guide(ask_save=True):
    """
    用户引导程序
    """
    if ask_save:
        # 弹出对话框，询问是否保存当前设计
        _txt = "是否保存当前设计？"
        reply = MyMessageBox().question(Handler.window, "提示", _txt, MyMessageBox.Yes | MyMessageBox.No)
        if reply == MyMessageBox.Ok:
            ProjectHandler.current.save()
    # 弹出UserGuideDialog
    user_guide_dialog = UserGuideDialog(Handler)
    Handler.window.setFocus()


def handle_exception(_exception):
    # 将报错信息和调用栈
    clipboard = QApplication.clipboard()
    err_message = f"Fatal Error：{_exception}\n{traceback.format_exc()}"
    # # 对err_message进行base64加密
    # import base64
    # err_message = base64.b64encode(err_message.encode('utf-8')).decode('utf-8')
    clipboard.setText(err_message)
    _title = "致命错误"
    information = f"""
        \t检测到异常，已将错误信息复制到剪贴板\n\t请将错误信息发送到 2593292614@qq.com\n
        {err_message}\n
    """
    MyMessageBox().information(None, _title, information, MyMessageBox.Ok)

    class QQMailThread(QThread):
        def __init__(self):
            super().__init__(None)

        def run(self):
            Connection.send_email(f"Fatal Error：{_exception}\n{traceback.format_exc()}")
            time.sleep(3)

    _qqmail_t = QQMailThread()
    _qqmail_t.start()
    _qqmail_t.wait()
    # 退出程序
    raise _exception


if __name__ == '__main__':
    try:
        # 初始化路径
        PTBPath = find_ptb_path()
        NAPath = os.path.join(find_na_root_path(), "ShipSaves")
        ThumbnailPath = os.path.join(find_na_root_path(), "ProjectThumbnails")
        # 读取配置
        Config = ConfigFile()
        # 初始化界面和事件处理器
        QApp = QApplication(sys.argv)
        QApp.setWindowIcon(QIcon(QPixmap.fromImage(QImage.fromData(ICO_))))
        QApp.setStyleSheet(f"""
            QWidget{{
                background-color:{BG_COLOR1};
                color:{FG_COLOR0};
            }}
            QPushButton{{
                background-color:{BG_COLOR1};
                color:{FG_COLOR0};
                border-radius: 5px;
                border: 1px solid {FG_COLOR0};
                padding-left: 15px;
                padding-right: 15px;
                padding-top: 5px;
                padding-bottom: 5px;
            }}
        """)
        # 初始化主窗口
        QtWindow = MainWin(Config)
        Handler = MainHandler(QtWindow)
        # 其他初始化
        Handler.hull_design_tab.ThreeDFrame.show_state_label = Handler.window.statu_label
        # 检查版本
        check_version()
        # 打开开始界面
        start_dialog = StartWelcomeDialog(None)
        start_dialog.connect_funcs(setting_func=None, help_func=user_guide, about_func=Handler.about)
        start_dialog.exec_()
        if start_dialog.close_program:
            Handler.close()
        # 渐变显示主窗口
        mainWinAnimation = QPropertyAnimation(QtWindow, b"windowOpacity")
        mainWinAnimation.setDuration(500)
        mainWinAnimation.setStartValue(0)
        mainWinAnimation.setEndValue(1)
        QtWindow.hide()
        QtWindow.showMaximized()
        mainWinAnimation.start()
        if start_dialog.open_recent_project and Config.Projects != {}:  # 打开最近的工程
            try:
                open_project(list(Config.Projects.values())[-1])
            except Exception as e:
                show_state(f"读取配置文件失败：{e}", 'error')
                MyMessageBox().information(Handler.window, "提示", f"读取配置文件失败：{e}", MyMessageBox.Ok)
        elif start_dialog.create_new_project:  # 创建新工程
            new_project()
        elif start_dialog.open_project:  # 打开工程
            open_project()
        # 检查是否需要引导
        if not Config.Config["Guided"]:
            # 运行引导程序
            user_guide(ask_save=False)
            Config.Config["Guided"] = True
        # 检查本机地址
        if get_mac_address() is True:  # 是我的电脑
            open_developer_console(Handler, ProjectHandler)
        # 主循环
        sys.exit(QApp.exec_())
    except Exception as e:
        handle_exception(e)
