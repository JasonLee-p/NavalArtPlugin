"""

"""
import json
import os
import time

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGridLayout, QPushButton, QFileDialog, QVBoxLayout, QMessageBox

from GUI.QtGui import BasicDialog, set_button_style, FG_COLOR0
from GUI.QtGui import MyLabel, MyLineEdit, MyComboBox, MySlider, MyMessageBox
from PTB_design_reader import ReadPTB
from path_utils import find_ptb_path, find_na_root_path


class ConfigFile:
    def __init__(self):
        """
        配置文件类，用于处理配置文件的读写
        配置文件用json格式存储，包含以下内容：
        1. 用户配置
        2. 船体节点数据
        """
        # 寻找naval_art目录的上级目录
        _path = os.path.join(find_na_root_path(), 'plugin_config.json')
        try:
            with open(_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.Config = data['Config']
            self.UsingTheme = self.Config['Theme']
            self.Sensitivity = self.Config['Sensitivity']
            self.Projects = data['Projects']
            self.ProjectsFolder = data['ProjectsFolder']
        except FileNotFoundError:
            self.UsingTheme = "Day"
            self.Sensitivity = {
                '缩放': 0.5,
                '旋转': 0.5,
                '平移': 0.5,
            }
            self.Config = {
                'Theme': self.UsingTheme,
                'Language': 'Chinese',
                'AutoSave': True,
                'AutoSaveInterval': 5,
                'Sensitivity': self.Sensitivity,
            }
            self.Projects = {}
            self.ProjectsFolder = ''

    def save_config(self):
        # 将配置写入配置文件
        if self.Projects != {}:
            self.ProjectsFolder = os.path.dirname(list(self.Projects.values())[-1])
        # 寻找上级目录
        _path = os.path.join(find_na_root_path(), 'plugin_config.json')
        with open(_path, 'w', encoding='utf-8') as f:
            json.dump({
                'Config': self.Config,
                'Projects': self.Projects,
                'ProjectsFolder': self.ProjectsFolder,
            }, f, ensure_ascii=False, indent=2)


class NewProjectDialog(BasicDialog):
    def ensure(self):
        # 外传参数
        self.create_new_project = True
        if self.select_circle0.isChecked():
            self.generate_mode = '空白'
        elif self.select_circle1.isChecked():
            self.generate_mode = 'NA'
            self.ProjectName = self.input_name.text()
            self.ProjectPath = self.input_path.text() + '/' + self.ProjectName
        elif self.select_circle2.isChecked():
            self.generate_mode = '预设'
        elif self.select_circle3.isChecked():
            self.generate_mode = 'PTB'
        elif self.select_circle4.isChecked():
            self.generate_mode = '自定义'
        else:
            self.create_new_project = False
            return
        if self.input_name.text() == '' or self.input_path.text() == '':
            message = QMessageBox(QMessageBox.Warning, '警告', '工程名称和工程路径不能为空！')
            message.exec_()
            self.create_new_project = False
            return
        super().ensure()

    def __init__(self, parent, title="新建工程", size=QSize(750, 580)):
        # 外传参数（初始化ProjectFile类需要的参数）
        self.create_new_project = False
        self.generate_mode = None
        self.ProjectName = ''
        self.ProjectPath = ''

        self.NAPath = os.path.join(find_na_root_path(), 'ShipSaves')
        self.OriginalNAPath = ''
        self.PTBPath = find_ptb_path()
        self.PTBDesignPath = ''
        # 控件
        self.center_layout = QVBoxLayout()
        self.center_top_layout = QGridLayout()
        self.center_bottom_layout0 = QGridLayout()
        self.center_bottom_layout1 = QGridLayout()
        self.search_prj_path_button = QPushButton('浏览')

        self.input_name = MyLineEdit()  # 工程名称输入框
        self.input_path = MyLineEdit()  # 工程路径输入框

        self.select_circle0 = QPushButton()
        self.select_circle1 = QPushButton()
        self.select_circle2 = QPushButton()
        self.select_circle3 = QPushButton()
        self.select_circle4 = QPushButton()

        self.combobox_template = MyComboBox()  # 预设下拉框
        self.show_na_path = MyLineEdit()  # NA船体路径显示框
        self.search_na_button = QPushButton('浏览')  # NA船体路径选择按钮
        self.show_ptb_path = MyLineEdit()  # PTB图纸路径显示框
        self.search_ptb_button = QPushButton('浏览')  # PTB图纸路径选择按钮
        self.show_preset_path = MyLineEdit()  # 预设路径显示框
        self.search_preset_button = QPushButton('浏览')  # 预设路径选择按钮

        self.length_slider = MySlider(value_range=(50, 1000), current_value=200.0)  # 长度取值条
        self.width_slider = MySlider(value_range=(5, 100), current_value=20.0)  # 宽度取值条
        self.depth_slider = MySlider(value_range=(5, 100), current_value=20.0)  # 型深取值条

        # 布局
        self.center_layout.addLayout(self.center_top_layout)  # -----------------------------------------顶部布局
        self.center_top_layout.addWidget(MyLabel('工程名称：', font=QFont("Microsoft YaHei", 10)), 0, 0)
        self.center_top_layout.addWidget(self.input_name, 0, 1)
        self.center_top_layout.addWidget(MyLabel('工程路径：', font=QFont("Microsoft YaHei", 10)), 1, 0)
        self.center_top_layout.addWidget(self.input_path, 1, 1)
        self.center_top_layout.addWidget(self.search_prj_path_button, 1, 2)
        self.center_layout.addWidget(MyLabel('初始化选项：', font=QFont("Microsoft YaHei", 10)))  # -------中间文字
        self.center_layout.addLayout(self.center_bottom_layout0)  # ------------------------------------底部0布局
        self.center_bottom_layout0.addWidget(self.select_circle0, 0, 0)
        self.center_bottom_layout0.addWidget(MyLabel('创建空白工程'), 0, 1)
        self.center_bottom_layout0.addWidget(self.select_circle1, 1, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用本地NA船体'), 1, 1)
        self.center_bottom_layout0.addWidget(self.show_na_path, 1, 2)
        self.center_bottom_layout0.addWidget(self.search_na_button, 1, 3)
        self.center_bottom_layout0.addWidget(self.select_circle2, 2, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用预设模板'), 2, 1)
        self.center_bottom_layout0.addWidget(self.combobox_template, 2, 2)
        self.center_bottom_layout0.addWidget(self.select_circle3, 3, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用PTB船壳'), 3, 1)
        self.center_bottom_layout0.addWidget(self.show_ptb_path, 3, 2)
        self.center_bottom_layout0.addWidget(self.search_ptb_button, 3, 3)
        self.center_bottom_layout0.addWidget(self.select_circle4, 4, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用自定义预设'), 4, 1)
        self.center_bottom_layout0.addWidget(self.show_preset_path, 4, 2)
        self.center_bottom_layout0.addWidget(self.search_preset_button, 4, 3)
        self.center_layout.addWidget(MyLabel('船体参数（供预设使用）：', font=QFont("Microsoft YaHei", 10)))  # -------底部1布局
        self.center_layout.addLayout(self.center_bottom_layout1)
        self.center_bottom_layout1.addWidget(MyLabel('船长：'), 0, 0)
        self.center_bottom_layout1.addWidget(self.length_slider, 0, 1)
        self.center_bottom_layout1.addWidget(MyLabel('船宽：'), 1, 0)
        self.center_bottom_layout1.addWidget(self.width_slider, 1, 1)
        self.center_bottom_layout1.addWidget(MyLabel('型深：'), 2, 0)
        self.center_bottom_layout1.addWidget(self.depth_slider, 2, 1)
        # 设置控件属性
        self.selected_color = "tan"
        self.circle_size = 8
        self.set_widgets()
        # 设置信号槽
        self.search_prj_path_button.clicked.connect(self.check_path)
        set_button_style(self.search_prj_path_button, size=(60, 26), style="圆角边框")
        set_button_style(self.search_na_button, size=(60, 26), style="圆角边框")
        set_button_style(self.search_ptb_button, size=(60, 26), style="圆角边框")
        set_button_style(self.search_preset_button, size=(60, 26), style="圆角边框")
        super().__init__(parent, title, size, self.center_layout)

    def set_widgets(self):
        self.center_layout.setContentsMargins(70, 55, 70, 0)
        self.center_layout.setSpacing(20)
        self.center_top_layout.setContentsMargins(0, 0, 0, 0)
        self.center_top_layout.setSpacing(10)
        self.center_bottom_layout0.setContentsMargins(25, 0, 0, 0)
        self.center_bottom_layout0.setSpacing(10)
        self.center_bottom_layout1.setContentsMargins(25, 0, 0, 0)
        self.center_bottom_layout1.setSpacing(10)
        self.input_name.setPlaceholderText('请输入工程名称')
        self.input_path.setPlaceholderText('请选择工程路径')
        self.input_path.setReadOnly(True)
        # 设置小圆圈
        self.select_circle0.setFixedSize(2 * self.circle_size, 2 * self.circle_size)
        self.select_circle1.setFixedSize(2 * self.circle_size, 2 * self.circle_size)
        self.select_circle2.setFixedSize(2 * self.circle_size, 2 * self.circle_size)
        self.select_circle3.setFixedSize(2 * self.circle_size, 2 * self.circle_size)
        self.select_circle4.setFixedSize(2 * self.circle_size, 2 * self.circle_size)
        self.select_circle0.setCheckable(True)
        self.select_circle1.setCheckable(True)
        self.select_circle2.setCheckable(True)
        self.select_circle3.setCheckable(True)
        self.select_circle4.setCheckable(True)
        self.button0_clicked()
        self.select_circle0.clicked.connect(self.button0_clicked)
        self.select_circle1.clicked.connect(self.button1_clicked)
        self.select_circle2.clicked.connect(self.button2_clicked)
        self.select_circle3.clicked.connect(self.button3_clicked)
        self.select_circle4.clicked.connect(self.button4_clicked)
        # 设置下拉框
        self.combobox_template.addItems([
            '美系BB', '德系BB', '日系BB', '英系BB', '法系BB', '意系BB', '苏系BB',
            '美系大巡', '德系BC', '英系BC',
            '二战驱逐舰',
            '二战巡洋舰',
            '二战航空母舰',
            '现代驱逐舰',
            '现代航空母舰',
        ])
        self.search_na_button.clicked.connect(self.check_na_path)
        self.search_ptb_button.clicked.connect(self.check_ptb_path)
        self.show_na_path.setPlaceholderText('请选择NA船体')
        self.show_na_path.setReadOnly(True)
        self.show_ptb_path.setPlaceholderText('请选择PTB图纸')
        self.show_ptb_path.setReadOnly(True)
        self.search_preset_button.clicked.connect(self.select_preset)
        self.show_preset_path.setPlaceholderText('请选择预设')
        self.show_preset_path.setReadOnly(True)

    def button0_clicked(self):
        self.select_circle0.setChecked(True)
        self.select_circle1.setChecked(False)
        self.select_circle2.setChecked(False)
        self.select_circle3.setChecked(False)
        self.select_circle4.setChecked(False)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle4.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将下拉框设置为不可用
        self.combobox_template.setEnabled(False)
        self.combobox_template.setStyleSheet(f"color: #808080;")
        # 将PTB图纸，NA图纸和预设设置为不可用
        self.search_na_button.setEnabled(False)
        self.show_na_path.setStyleSheet(f"color: #808080;")
        self.search_ptb_button.setEnabled(False)
        self.show_ptb_path.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button1_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(True)
        self.select_circle2.setChecked(False)
        self.select_circle3.setChecked(False)
        self.select_circle4.setChecked(False)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle4.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将NA图纸设置为可用
        self.search_na_button.setEnabled(True)
        self.show_na_path.setStyleSheet(f"color: {FG_COLOR0};")
        # 将下拉框和PTB图纸，预设设置为不可用
        self.combobox_template.setEnabled(False)
        self.combobox_template.setStyleSheet(f"color: #808080;")
        self.search_ptb_button.setEnabled(False)
        self.show_ptb_path.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button2_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(False)
        self.select_circle2.setChecked(True)
        self.select_circle3.setChecked(False)
        self.select_circle4.setChecked(False)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle4.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将下拉框设置为可用
        self.combobox_template.setEnabled(True)
        self.combobox_template.setStyleSheet(f"color: {FG_COLOR0};")
        # 将NA图纸和PTB图纸，预设设置为不可用
        self.search_na_button.setEnabled(False)
        self.show_na_path.setStyleSheet(f"color: #808080;")
        self.search_ptb_button.setEnabled(False)
        self.show_ptb_path.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button3_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(False)
        self.select_circle2.setChecked(False)
        self.select_circle3.setChecked(True)
        self.select_circle4.setChecked(False)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle4.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将PTB图纸设置为可用
        self.search_ptb_button.setEnabled(True)
        self.show_ptb_path.setStyleSheet(f"color: {FG_COLOR0};")
        # 将NA图纸，下拉框和预设设置为不可用
        self.search_na_button.setEnabled(False)
        self.show_na_path.setStyleSheet(f"color: #808080;")
        self.combobox_template.setEnabled(False)
        self.combobox_template.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button4_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(False)
        self.select_circle2.setChecked(False)
        self.select_circle3.setChecked(False)
        self.select_circle4.setChecked(True)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle4.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        # 将预设设置为可用
        self.search_preset_button.setEnabled(True)
        self.show_preset_path.setStyleSheet(f"color: {FG_COLOR0};")
        # 将NA图纸，下拉框和PTB图纸设置为不可用
        self.search_na_button.setEnabled(False)
        self.show_na_path.setStyleSheet(f"color: #808080;")
        self.combobox_template.setEnabled(False)
        self.combobox_template.setStyleSheet(f"color: #808080;")
        self.search_ptb_button.setEnabled(False)
        self.show_ptb_path.setStyleSheet(f"color: #808080;")

    def check_path(self):
        """
        用户选择路径
        """
        path = QFileDialog.getExistingDirectory(self, "选择工程路径", "./")
        self.input_path.setText(path)

    def check_na_path(self):
        # 打开文件选择窗口，目录为NavalArt目录
        file_dialog = QFileDialog(self, "选择图纸", self.NAPath)
        file_dialog.setNameFilter("na files (*.na)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
            self.show_na_path.setText(file_path.split("/")[-1].split(".")[0])  # 显示文件名
            self.OriginalNAPath = file_path
        except IndexError:
            return

    def check_ptb_path(self):
        # 打开文件选择窗口，目录为PTB目录
        file_dialog = QFileDialog(self, "选择图纸", self.PTBPath)
        file_dialog.setNameFilter("xml files (*.xml)")
        file_dialog.exec_()
        try:
            file_path = file_dialog.selectedFiles()[0]  # 获取选择的文件路径
            self.PTBDesignPath = file_path
            try:
                design_reader = ReadPTB(file_path)
            except IndexError and KeyError and AttributeError:
                _txt = "该文件不是有效的船体设计文件，请重新选择哦"
                # 白色背景的提示框
                MyMessageBox().information(self, "提示", _txt, MyMessageBox.Ok)
                return
            if design_reader.result["adHull"]:  # 如果存在进阶船壳
                # 显示后两层路径
                self.show_ptb_path.setText(file_path.split("/")[-2] + "/" + file_path.split("/")[-1])
                return self.PTBDesignPath
            else:
                _txt = "该设计不含进阶船体外壳，请重新选择哦"
                MyMessageBox.information(self, "提示", _txt, MyMessageBox.Ok)
                self.check_ptb_path()
                return
        except IndexError:
            return

    def select_preset(self):
        ...


class ProjectFile:
    PreDesign = '预设计'
    Designing = '设计中'

    ADD = 'add'
    DELETE = 'delete'
    CLEAR = 'clear'
    OVERWRITE = 'overwrite'

    EMPTY = '空白'
    NA = 'NA'
    PRESET = '预设'
    PTB = 'PTB'
    CUSTOM = '自定义'
    LOAD = '从文件加载'

    _available_modes = [EMPTY, NA, PRESET, PTB, CUSTOM, LOAD]

    def __init__(
            self, name, path, original_na_file_path,
            na_parts_data=None, operations=None, mode="空白", code='', save_time=''
    ):
        """
        工程文件类，用于处理工程文件的读写
        工程文件用json格式存储，包含以下内容：
        1. 工程名称
        2. 创建工程的设备安全码（验证工程是否是本机创建，防止盗取工程）
        3. 工程创建时间
        4. 用户在软件内对工程的配置
        5. 船体节点数据
        :param name: 工程名称
        :param path: 工程路径，包含文件名
        :param original_na_file_path: 原NA文件路径
        :param na_parts_data: 船体节点数据
        :param mode: 工程创建模式
        """
        self._succeed_init = False
        # 工程文件的属性
        if mode not in ProjectFile._available_modes:
            raise ValueError(f"mode must be in {ProjectFile._available_modes}")
        if mode == ProjectFile.LOAD:
            # 检查安全码
            if not self.check_data(code, save_time, na_parts_data, operations):
                QMessageBox(QMessageBox.Warning, '警告', '工程文件已被修改！').exec_()
                return
        self.Name = name
        self.Path = path
        self.OriginalFilePath = original_na_file_path
        self.Code = code  # 工程安全码，用于验证工程文件是否被私自修改
        self.CreateTime = f"{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday} " \
                          f"{time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}"
        self.SaveTime = save_time
        self.State = ProjectFile.PreDesign
        self.Camera = {"tar": [0, 0, 0], "pos": [125, 25, 50], "fovy": 0}
        self.Config = {'State': self.State, 'Camera': self.Camera}
        self.NAPartsData = na_parts_data
        self.Operations = operations if operations else {}
        self.json_data = {
            'Name': self.Name,
            'Code': self.Code,
            'CreateTime': self.CreateTime,
            'SaveTime': self.SaveTime,
            'OriginalFilePath': self.OriginalFilePath,
            'Config': self.Config,
            'NAPartsData': self.NAPartsData,
            'Operations': self.Operations,
        }
        self.create_mode = mode
        self._succeed_init = True

    @staticmethod
    def load_project(path) -> 'ProjectFile':  # 从文件加载工程
        # 判断是否为json
        if not path.endswith('.json'):
            # 提示错误
            QMessageBox(QMessageBox.Warning, '警告', '工程文件格式错误！').exec_()
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        try:
            project_file = ProjectFile(
                data['Name'], path, data['OriginalFilePath'], data['NAPartsData'], data['Operations'], mode=ProjectFile.LOAD,
                code=data['Code'], save_time=data['SaveTime'])
        except KeyError:
            QMessageBox(QMessageBox.Warning, '警告', '工程文件格式错误！').exec_()
            return None
        if project_file._succeed_init:
            return project_file
        else:
            return None

    def update_na_parts_data(self, na_parts_data, mode):
        if mode == ProjectFile.ADD:
            for part in na_parts_data:
                if part not in self.NAPartsData:
                    self.NAPartsData[part] = na_parts_data[part]
        elif mode == ProjectFile.DELETE:
            for part in na_parts_data:
                if part in self.NAPartsData:
                    del self.NAPartsData[part]
        elif mode == ProjectFile.CLEAR:
            self.NAPartsData = {}
        elif mode == ProjectFile.OVERWRITE:
            self.NAPartsData = na_parts_data

    @staticmethod
    def check_data(code, save_time, na_parts_data, operations):
        from hashlib import sha1
        if code != str(sha1((save_time + str(na_parts_data) + str(operations)).encode('utf-8')).hexdigest()):
            return False
        else:
            return True

    def get_check_code(self):  # 获取工程安全码
        from hashlib import sha1
        return str(sha1((self.SaveTime + str(self.NAPartsData) + str(self.Operations)).encode('utf-8')).hexdigest())

    def save(self):
        # 将工程数据写入工程文件
        self.SaveTime = f"{time.localtime().tm_year}-{time.localtime().tm_mon}-{time.localtime().tm_mday} " \
                        f"{time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}"
        self.Code = self.get_check_code()
        self.json_data = {
            'Name': self.Name,
            'Code': self.Code,
            'CreateTime': self.CreateTime,
            'SaveTime': self.SaveTime,
            'OriginalFilePath': self.OriginalFilePath,
            'Config': self.Config,
            'NAPartsData': self.NAPartsData,
            'Operations': self.Operations,
        }
        with open(self.Path, 'w', encoding='utf-8') as f:
            json.dump(self.json_data, f, ensure_ascii=False, indent=2)

    def save_as_na(self, changed_na_file, output_file_path):  # 导出为NA船体
        # 以xml形式，na文件格式保存
        """
        文件格式：
        <root>
          <ship author="22222222222" description="description" hornType="1" hornPitch="0.9475011" tracerCol="E53D4FFF">
            <part id="0">
              <data length="4.5" height="1" frontWidth="0.2" backWidth="0.5" frontSpread="0.05" backSpread="0.2" upCurve="0" downCurve="1" heightScale="1" heightOffset="0" />
              <position x="0" y="0" z="114.75" />
              <rotation x="0" y="0" z="0" />
              <scale x="1" y="1" z="1" />
              <color hex="975740" />
              <armor value="5" />
            </part>
            <part id="190">
              <position x="0" y="-8.526513E-14" z="117.0312" />
              <rotation x="90" y="0" z="0" />
              <scale x="0.03333336" y="0.03333367" z="0.1666679" />
              <color hex="975740" />
              <armor value="5" />
            </part>
          </root>
        :param changed_na_file:
        :param output_file_path:
        :return:
        """
