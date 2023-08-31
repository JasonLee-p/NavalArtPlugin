"""

"""
import json
import os

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QGridLayout, QPushButton, QFileDialog, QVBoxLayout

from GUI.QtGui import BasicDialog, set_button_style, FG_COLOR0
from GUI.QtGui import MyLabel, MyLineEdit, MyComboBox, MySlider, MyMessageBox
from PTB_design_reader import ReadPTB
from path_utils import find_ptb_path, find_na_path


class ConfigFile:
    def __init__(self):
        """
        配置文件类，用于处理配置文件的读写
        配置文件用json格式存储，包含以下内容：
        1. 用户配置
        2. 船体节点数据
        """
        self.Config = {}
        self.UsingTheme = ''
        self.Sensitivity = {}
        self.Projects = {}
        self.ProjectsFolder = ''

    def load_config(self):
        # 从配置文件中读取配置
        _path = os.path.join(find_na_path(), 'plugin_config.json')
        try:
            with open(_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.Config = data['Config']
            self.UsingTheme = self.Config['Theme']
            self.Sensitivity = self.Config['Sensitivity']
            self.Projects = data['Projects']
            self.ProjectsFolder = data['ProjectsFolder']
        except FileNotFoundError or KeyError:
            self.Config = {
                'Theme': 'Day',
                'Language': 'Chinese',
                'AutoSave': True,
                'AutoSaveInterval': 5,
                'Sensitivity': self.Sensitivity,
            }
            self.UsingTheme = "Night"
            self.Sensitivity = {
                '缩放': 0.5,
                '旋转': 0.5,
                '平移': 0.5,
            }
            self.Projects = {}
            self.ProjectsFolder = ''

    def save_config(self):
        # 将配置写入配置文件
        _path = os.path.join(find_na_path(), 'plugin_config.json')
        with open(_path, 'w', encoding='utf-8') as f:
            json.dump({
                'Config': self.Config,
                'Projects': self.Projects,
                'ProjectsFolder': self.ProjectsFolder,
            }, f, ensure_ascii=False, indent=4)


class NewProjectDialog(BasicDialog):
    def __init__(self, parent, title="新建工程", size=QSize(750, 580)):
        # 控件
        self.center_layout = QVBoxLayout()
        self.center_top_layout = QGridLayout()
        self.center_bottom_layout0 = QGridLayout()
        self.center_bottom_layout1 = QGridLayout()
        self.search_button = QPushButton('浏览')

        self.input_name = MyLineEdit()
        self.input_path = MyLineEdit()

        self.select_circle0 = QPushButton()
        self.select_circle1 = QPushButton()
        self.select_circle2 = QPushButton()
        self.select_circle3 = QPushButton()

        self.combobox_template = MyComboBox()
        self.show_ptb_path = MyLineEdit()
        self.search_ptb_button = QPushButton('浏览')
        self.show_preset_path = MyLineEdit()
        self.search_preset_button = QPushButton('浏览')

        self.length_slider = MySlider(value_range=(50, 1000), current_value=200.0)  # 长度取值条
        self.width_slider = MySlider(value_range=(5, 100), current_value=20.0)  # 宽度取值条
        self.depth_slider = MySlider(value_range=(5, 100), current_value=20.0)  # 型深取值条

        # 布局
        self.center_layout.addLayout(self.center_top_layout)  # -----------------------------------------顶部布局
        self.center_top_layout.addWidget(MyLabel('工程名称：', font=QFont("Microsoft YaHei", 10)), 0, 0)
        self.center_top_layout.addWidget(self.input_name, 0, 1)
        self.center_top_layout.addWidget(MyLabel('工程路径：', font=QFont("Microsoft YaHei", 10)), 1, 0)
        self.center_top_layout.addWidget(self.input_path, 1, 1)
        self.center_top_layout.addWidget(self.search_button, 1, 2)
        self.center_layout.addWidget(MyLabel('初始化选项：', font=QFont("Microsoft YaHei", 10)))  # -------中间文字
        self.center_layout.addLayout(self.center_bottom_layout0)  # ------------------------------------底部0布局
        self.center_bottom_layout0.addWidget(self.select_circle0, 0, 0)
        self.center_bottom_layout0.addWidget(MyLabel('创建空白工程'), 0, 1)
        self.center_bottom_layout0.addWidget(self.select_circle1, 1, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用预设模板'), 1, 1)
        self.center_bottom_layout0.addWidget(self.combobox_template, 1, 2)
        self.center_bottom_layout0.addWidget(self.select_circle2, 2, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用PTB船壳'), 2, 1)
        self.center_bottom_layout0.addWidget(self.show_ptb_path, 2, 2)
        self.center_bottom_layout0.addWidget(self.search_ptb_button, 2, 3)
        self.center_bottom_layout0.addWidget(self.select_circle3, 3, 0)
        self.center_bottom_layout0.addWidget(MyLabel('使用自定义预设'), 3, 1)
        self.center_bottom_layout0.addWidget(self.show_preset_path, 3, 2)
        self.center_bottom_layout0.addWidget(self.search_preset_button, 3, 3)
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
        # 事件
        self.PTBPath = find_ptb_path()
        self.PTBDesignPath = ''
        self.search_button.clicked.connect(self.check_path)
        set_button_style(self.search_button, size=(60, 26), style="圆角边框")
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
        self.select_circle0.setCheckable(True)
        self.select_circle1.setCheckable(True)
        self.select_circle2.setCheckable(True)
        self.select_circle3.setCheckable(True)
        self.button0_clicked()
        self.select_circle0.clicked.connect(self.button0_clicked)
        self.select_circle1.clicked.connect(self.button1_clicked)
        self.select_circle2.clicked.connect(self.button2_clicked)
        self.select_circle3.clicked.connect(self.button3_clicked)
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
        self.search_ptb_button.clicked.connect(self.check_ptb_path)
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
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将下拉框设置为不可用
        self.combobox_template.setEnabled(False)
        self.combobox_template.setStyleSheet(f"color: #808080;")
        # 将PTB图纸和预设设置为不可用
        self.search_ptb_button.setEnabled(False)
        self.show_ptb_path.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button1_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(True)
        self.select_circle2.setChecked(False)
        self.select_circle3.setChecked(False)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将下拉框设置为可用
        self.combobox_template.setEnabled(True)
        self.combobox_template.setStyleSheet(f"color: {FG_COLOR0};")
        # 将PTB图纸和预设设置为不可用
        self.search_ptb_button.setEnabled(False)
        self.show_ptb_path.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button2_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(False)
        self.select_circle2.setChecked(True)
        self.select_circle3.setChecked(False)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        # 将PTB图纸设置为可用
        self.search_ptb_button.setEnabled(True)
        self.show_ptb_path.setStyleSheet(f"color: {FG_COLOR0};")
        # 将下拉框和预设设置为不可用
        self.combobox_template.setEnabled(False)
        self.combobox_template.setStyleSheet(f"color: #808080;")
        self.search_preset_button.setEnabled(False)
        self.show_preset_path.setStyleSheet(f"color: #808080;")

    def button3_clicked(self):
        self.select_circle0.setChecked(False)
        self.select_circle1.setChecked(False)
        self.select_circle2.setChecked(False)
        self.select_circle3.setChecked(True)
        self.select_circle0.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle1.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle2.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: #FFFFFF; border: 1px solid #000000;")
        self.select_circle3.setStyleSheet(
            f"border-radius: {self.circle_size}px; background-color: {self.selected_color};")
        # 将预设设置为可用
        self.search_preset_button.setEnabled(True)
        self.show_preset_path.setStyleSheet(f"color: {FG_COLOR0};")
        # 将下拉框和PTB图纸设置为不可用
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

    def ensure(self):
        self.create_new_project()
        super().ensure()

    def create_new_project(self):
        ...


class ProjectFile:
    def __init__(self, create_mode='blank', read_path=None):
        """
        工程文件类，用于处理工程文件的读写
        工程文件用json格式存储，包含以下内容：
        1. 工程名称
        2. 创建工程的设备安全码（验证工程是否是本机创建，防止盗取工程）
        3. 工程创建时间
        4. 用户在软件内对工程的配置
        5. 船体节点数据
        """
        self.Name = ''
        self.Code = ''
        self.CreateTime = ''
        self.Config = {
            'Camera': {
                'tar': [0, 0, 0],
                'pos': [125, 25, 50],
                'fovy': 0,
            },
        }
        self.HullData = {}
        if create_mode and read_path:
            raise ValueError('create_mode和read_path不能同时指定')
        elif not create_mode and not read_path:
            raise ValueError('尚未指定create_mode或read_path')
        elif create_mode and not read_path:
            self.init_data(create_mode)
        elif read_path and not create_mode:
            self.load_project(read_path)

    def init_data(self, mode='blank'):
        if mode == 'blank':
            self.Name = ''
            self.Code = ''
            self.CreateTime = ''
            self.Config = {}
            self.HullData = {}

    def load_project(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.Name = data['Name']
        self.Code = data['Code']
        self.CreateTime = data['CreateTime']
        self.Config = data['Config']
        self.HullData = data['HullData']

    def save_as_na(self):
        ...

    def save_project(self):
        ...
