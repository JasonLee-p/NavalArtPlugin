# -*- coding: utf-8 -*-
"""
对话框
"""
# 本地库
import os

from PyQt5.QtCore import QPropertyAnimation, QRect
from PyQt5.QtGui import QTextBlockFormat
from PyQt5.QtWidgets import QProgressBar

from util_funcs import open_url
from path_utils import find_ptb_path, find_na_root_path
from ship_reader import ReadPTB
from GUI import *


def set_button_style(button, size: tuple, font=FONT_14, style="普通", active_color='gray', icon=None):
    from GUI.basic import set_button_style
    set_button_style(button, size, font, style, active_color, icon)


def getFG_fromBG(bg_color):
    from GUI.basic import getFG_fromBG
    return getFG_fromBG(bg_color)


def front_completion(string, length, add_char):
    from GUI.basic import front_completion
    return front_completion(string, length, add_char)


class CheckNewVersionDialog(BasicDialog):
    def __init__(self, parent, current_version, title="", size=QSize(300, 250)):
        self.current_version = current_version
        self.center_layout = QGridLayout()
        self.checking_label = MyLabel("正在检查更新", font=FONT_12)
        self.animate_bar = QProgressBar()
        self.label_current_text = QLabel("当前版本：")
        self.label_current_version = QLabel(self.current_version)
        self.label_latest_text = QLabel("最新版本：")
        self.label_latest_version = None
        self.label_update_text = QLabel("确定前往官网更新？")
        self.set_layout()
        super().__init__(parent, 10, title, size, self.center_layout)
        # 图标
        self.ICO = QPixmap.fromImage(QImage.fromData(ICO_))
        self.setWindowIcon(QIcon(self.ICO))
        self.download = False  # 是否下载

    def check_update_success(self, latest_version):
        self.label_latest_version = QLabel(latest_version)
        # 删除原有的控件
        self.center_layout.removeWidget(self.checking_label)
        self.center_layout.removeWidget(self.animate_bar)
        self.checking_label.deleteLater()
        self.animate_bar.deleteLater()
        # 添加新的控件
        self.center_layout.addWidget(self.label_current_text, 0, 0)
        self.center_layout.addWidget(self.label_current_version, 0, 1)
        self.center_layout.addWidget(self.label_latest_text, 1, 0)
        self.center_layout.addWidget(self.label_latest_version, 1, 1)
        self.center_layout.addWidget(self.label_update_text, 2, 0, 1, 2)
        self.label_current_version.setFixedSize(100, 30)
        self.label_latest_version.setFixedSize(100, 30)
        self.label_update_text.setFixedSize(200, 50)
        # 设置QLabel的样式
        RED = "#FF4444"
        GREEN = "#00FF00"
        self.label_current_version.setStyleSheet(f"background-color: {BG_COLOR2};"
                                                 f"border-radius: 5px; font-family: {YAHEI}; font-size: 18px; color: {RED};")
        self.label_latest_version.setStyleSheet(f"background-color: {BG_COLOR2};"
                                                f"border-radius: 5px; font-family: {YAHEI}; font-size: 18px; color: {GREEN};")
        TextStyleSheet = f"color: {FG_COLOR0}; font-size: 18px; font-family: {YAHEI};"
        self.label_current_text.setStyleSheet(TextStyleSheet)
        self.label_latest_text.setStyleSheet(TextStyleSheet)
        self.label_update_text.setStyleSheet(TextStyleSheet)
        # 设置字体
        for label in [self.label_current_text, self.label_current_version,
                      self.label_latest_text, self.label_latest_version,
                      self.label_update_text]:
            label.setFont(FONT_14)

        # 居中
        self.label_current_text.setAlignment(Qt.AlignCenter)
        self.label_current_version.setAlignment(Qt.AlignCenter)
        self.label_latest_text.setAlignment(Qt.AlignCenter)
        self.label_latest_version.setAlignment(Qt.AlignCenter)
        self.label_update_text.setAlignment(Qt.AlignCenter)

    def check_update_failed(self):
        self.checking_label.setText("检查更新失败")
        self.center_layout.removeWidget(self.animate_bar)
        self.animate_bar.deleteLater()
        self.center_layout.addWidget(self.checking_label, 0, 0, 1, 2)

    def set_layout(self):
        """
        设置布局
        :return:
        """
        self.center_layout.setContentsMargins(40, 26, 40, 0)
        self.center_layout.setSpacing(10)
        self.center_layout.setAlignment(Qt.AlignCenter)
        AB_RADIUS = 3
        self.animate_bar.setFixedSize(220, 2 * AB_RADIUS)
        self.animate_bar.setStyleSheet(
            f"""
            QProgressBar {{
                text-align: center;
                background-color: {GRAY};
                color: {FG_COLOR0};
            }}
            QProgressBar::chunk {{
                background-color: {FG_COLOR0};
            }}
            """
        )
        self.animate_bar.setRange(0, 0)
        self.checking_label.setFixedSize(220, 60)
        # 居中显示
        self.center_layout.addWidget(self.checking_label, 0, 0, 1, 2)
        self.center_layout.addWidget(self.animate_bar, 1, 0, 1, 2)
        self.checking_label.setAlignment(Qt.AlignCenter)
        self.animate_bar.setAlignment(Qt.AlignCenter)

    def ensure(self):
        self.download = True
        super().ensure()


class StartWelcomeDialog(BasicDialog):
    def ensure(self):
        self.close_program = False
        self.close()

    def open_recent_button_clicked(self):
        self.open_recent_project = True
        self.ensure()

    def create_new_button_clicked(self):
        self.create_new_project = True
        self.ensure()

    def open_project_button_clicked(self):
        self.open_project = True
        self.ensure()

    def __init__(self, parent, title="", size=QSize(1100, 800)):
        # 信号
        self.close_program = True
        self.open_recent_project = False
        self.create_new_project = False
        self.open_project = False
        # 控件
        self.ICO = QPixmap.fromImage(QImage.fromData(ICO_))
        self.center_layout = QHBoxLayout()
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.left_grid_layout = QGridLayout()
        self.title = MyLabel("欢迎使用 NavalArt 船体编辑器", font=FONT_20)
        self.buttons = {
            "最近打开": QPushButton("最近打开"),
            "新建工程": QPushButton("新建工程"),
            "打开工程": QPushButton("打开工程"),
            "设置": QPushButton("设置"),
            "帮助": QPushButton("帮助"),
            "关于": QPushButton("关于"),
        }
        self.Hei = size.height()
        self.Wid = size.width()
        self.set_layout()
        super().__init__(parent, (10, 10, 116, 116), title, size, self.center_layout, hide_bottom=True)
        self.hide()
        # 图标
        self.ICO = QPixmap.fromImage(QImage.fromData(ICO_))
        self.setWindowIcon(QIcon(self.ICO))
        # 渐变动画
        DUR = 200
        # 窗口透明度
        self.animation0 = QPropertyAnimation(self.parent(), b"windowOpacity")
        self.animation0.setStartValue(0)
        self.animation0.setEndValue(1)
        # 窗口位置（从右下）
        self.animation1 = QPropertyAnimation(self, b"geometry")
        self.animation1.setStartValue(QRect(self.x() + 100, self.y() + 100, 0, 0))
        self.animation1.setEndValue(QRect(self.x(), self.y(), self.Wid, self.Hei))
        # 窗口总体饱和度
        self.animation2 = QPropertyAnimation(self, b"saturation")
        self.animation2.setStartValue(0)
        self.animation2.setEndValue(1)

        self.animations = [self.animation0, self.animation1, self.animation2]
        for a in self.animations:
            a.setDuration(DUR)
            a.start()

    def set_layout(self):
        """
        设置布局
        :return:
        """
        self.center_layout.addWidget(self.left_widget, stretch=2)
        self.center_layout.addWidget(self.right_widget, stretch=1)
        self.left_widget.setLayout(self.left_layout)
        self.right_widget.setLayout(self.right_layout)
        self.right_widget.setFixedHeight(self.Hei - 100)
        self.center_layout.setContentsMargins(60, 25, 40, 0)
        self.left_layout.setContentsMargins(20, 10, 20, 0)
        self.right_layout.setContentsMargins(15, 30, 15, 55)
        self.center_layout.setSpacing(30)
        self.left_layout.setSpacing(10)
        self.right_layout.setSpacing(20)
        self.set_left_layout()
        self.set_right_layout()

    def set_left_layout(self):
        """
        设置左侧布局
        :return:
        """
        self.left_layout.addWidget(self.title)
        self.left_layout.setAlignment(Qt.AlignCenter)
        self.title.setAlignment(Qt.AlignCenter)
        # 添加文本
        _text = "   NavalArt 船体编辑器，是一款基于颜色选取的船体编辑器。" \
                "我们深知在 NavalArt 游戏内部编辑船体的痛点，" \
                "因此我们开发了这款船体编辑器，希望能够帮助到大家。\n" \
                "   我们将持续更新，如果您有任何建议，请联系我们："
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        # 设置边距
        text_edit.setFixedHeight(145)
        text_edit.setFrameShape(QFrame.NoFrame)
        text_edit.setFrameShadow(QFrame.Plain)
        text_edit.setLineWidth(0)
        # 设置样式
        cursor = text_edit.textCursor()
        block_format = QTextBlockFormat()
        block_format.setLineHeight(125, QTextBlockFormat.ProportionalHeight)  # 设置行间距
        block_format.setIndent(0)  # 设置首行缩进
        # 应用段落格式到文本游标
        cursor.setBlockFormat(block_format)
        cursor.insertText(_text)
        text_edit.setTextCursor(cursor)
        # 光标不变
        text_edit.setFocusPolicy(Qt.NoFocus)
        # 解绑事件
        text_edit.wheelEvent = lambda event: None
        text_edit.mousePressEvent = lambda event: None
        text_edit.mouseMoveEvent = lambda event: None
        text_edit.mouseReleaseEvent = lambda event: None
        # 取消滚动条
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_edit.setStyleSheet(
            f"background-color: {BG_COLOR0};"
            f"color: {FG_COLOR0};"
            f"padding-left: 22px;"
            f"padding-right: 22px;"
            f"padding-top: 10px;"
            f"padding-bottom: 5px;"
            f"border-radius: 46px;"
        )
        text_edit.setFont(FONT_11)
        # 添加布局
        self.left_layout.addStretch(1)
        self.left_layout.addWidget(text_edit)
        self.left_layout.addLayout(self.left_grid_layout)
        self.set_left_down_grid_layout()

    def set_left_down_grid_layout(self):
        email_text = MyLabel("E-mail：", font=FONT_10)
        email_content = MyLabel("2593292614@qq.com", font=FONT_10)
        bilibili_text = MyLabel("哔哩哔哩：", font=FONT_10)
        bilibili_content = MyLabel("咕咕的园艏", font=FONT_10)
        # 添加下划线
        email_content.setFrameShape(QFrame.HLine)
        bilibili_content.setFrameShape(QFrame.HLine)
        bilibili_url = "https://space.bilibili.com/507183077?spm_id_from=333.1007.0.0"
        email_url = "mailto:2593292614@qq.com"
        # 设置样式
        styleSheet = f"""
            color: {FG_COLOR0};
            background-color: {BG_COLOR1};
            border-radius: 10px;
        """
        # 设置鼠标悬停样式
        hover_styleSheet = f"""
            color: #00FFFF;
            background-color: {BG_COLOR1};
            border-radius: 10px;
        """
        email_text.setStyleSheet(styleSheet)
        bilibili_text.setStyleSheet(styleSheet)
        email_content.setStyleSheet(styleSheet)
        bilibili_content.setStyleSheet(styleSheet)
        email_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        bilibili_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        email_content.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        bilibili_content.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        email_content.setFixedSize(230, 23)
        bilibili_content.setFixedSize(230, 23)
        email_content.setCursor(Qt.PointingHandCursor)
        bilibili_content.setCursor(Qt.PointingHandCursor)
        email_content.enterEvent = lambda event: email_content.setStyleSheet(hover_styleSheet)
        email_content.leaveEvent = lambda event: email_content.setStyleSheet(styleSheet)
        bilibili_content.enterEvent = lambda event: bilibili_content.setStyleSheet(hover_styleSheet)
        bilibili_content.leaveEvent = lambda event: bilibili_content.setStyleSheet(styleSheet)
        # 设置鼠标点击事件
        email_content.mousePressEvent = open_url(email_url)
        bilibili_content.mousePressEvent = open_url(bilibili_url)
        # 添加布局
        self.left_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.left_grid_layout.setSpacing(5)
        self.left_grid_layout.setAlignment(Qt.AlignCenter)
        self.left_grid_layout.addWidget(email_text, 0, 0)
        self.left_grid_layout.addWidget(email_content, 0, 1)
        self.left_grid_layout.addWidget(bilibili_text, 1, 0)
        self.left_grid_layout.addWidget(bilibili_content, 1, 1)

    def set_right_layout(self):
        """
        设置右侧布局
        :return:
        """
        # 添加图标大图
        ico = QLabel()
        ico.setPixmap(self.ICO)
        ico.setAlignment(Qt.AlignCenter)
        # 添加布局
        self.right_layout.addWidget(ico)
        # 文字
        _font = FONT_13
        for button in self.buttons.values():
            self.right_layout.addWidget(button, alignment=Qt.AlignCenter)
            button.setFont(_font)
            button.setFixedSize(220, 33)
            # 设置左边间隔
            button.setStyleSheet(
                # 三种状态
                f"QPushButton{{"
                f"background-color: {BG_COLOR0};"
                f"color: {FG_COLOR0};"
                f"border-radius: 10px;"
                f"}}"
                f"QPushButton:hover{{"
                f"background-color: {BG_COLOR1};"
                f"color: {FG_COLOR0};"
                f"border-radius: 10px;"
                f"}}"
                f"QPushButton:pressed{{"
                f"background-color: {BG_COLOR2};"
                f"color: {FG_COLOR0};"
                f"border-radius: 10px;"
                f"}}"
            )
        self.right_widget.setStyleSheet(
            f"background-color: {BG_COLOR0};"
            f"color: {FG_COLOR0};"
            f"border-top-left-radius: 78px;"
            f"border-top-right-radius: 78px;"
            f"border-bottom-left-radius: 78px;"
            f"border-bottom-right-radius: 78px;"
        )
        self.right_layout.addStretch(1)

    # noinspection PyUnresolvedReferences
    def connect_funcs(self, setting_func=None, help_func=None, about_func=None):
        """
        连接函数
        :param setting_func:
        :param help_func:
        :param about_func:
        :return:
        """
        self.buttons["最近打开"].clicked.connect(self.open_recent_button_clicked)
        self.buttons["新建工程"].clicked.connect(self.create_new_button_clicked)
        self.buttons["打开工程"].clicked.connect(self.open_project_button_clicked)
        if setting_func is not None:
            self.buttons["设置"].clicked.connect(setting_func)
        if help_func is not None:
            self.buttons["帮助"].clicked.connect(help_func)
        if about_func is not None:
            self.buttons["关于"].clicked.connect(about_func)


class NewProjectDialog(BasicDialog):
    current = None

    def ensure(self):
        # 外传参数
        self.create_new_project = True
        if self.select_circle0.isChecked():
            self.generate_mode = '空白'
        elif self.select_circle1.isChecked():
            self.generate_mode = 'NA'
            self.ProjectName = self.input_name.text()
            self.ProjectPath = self.input_path.text() + '/' + self.ProjectName + '.json'
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

    def __init__(self, parent, border_radius=10, title="新建工程", size=QSize(750, 600)):
        # 外传参数（初始化ProjectFile类需要的参数）
        self.create_new_project = False
        self.generate_mode = None
        self.ProjectName = ''
        self.ProjectPath = ''

        self.NAPath = os.path.join(find_na_root_path(), 'ShipSaves')
        self.OriginalNAPath = ''
        self.PTBPath = find_ptb_path()
        self.PTBDesignPath = ''
        self.ProjectFolder = ProjectFolder
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
        self.center_top_layout.addWidget(MyLabel('工程名称：', font=FONT_10), 0, 0)
        self.center_top_layout.addWidget(self.input_name, 0, 1)
        self.center_top_layout.addWidget(MyLabel('工程路径：', font=FONT_10), 1, 0)
        self.center_top_layout.addWidget(self.input_path, 1, 1)
        self.center_top_layout.addWidget(self.search_prj_path_button, 1, 2)
        self.center_layout.addWidget(MyLabel('初始化选项：', font=FONT_10))  # -------中间文字
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
        self.center_layout.addWidget(MyLabel('船体参数（供预设使用）：', font=FONT_10))  # -------底部1布局
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
        super().__init__(parent, border_radius, title, size, self.center_layout)
        # 图标
        self.ICO = QPixmap.fromImage(QImage.fromData(ICO_))
        self.setWindowIcon(QIcon(self.ICO))
        NewProjectDialog.current = self

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
        # textEdit
        for te in [self.input_name, self.input_path, self.show_na_path, self.show_ptb_path, self.show_preset_path]:
            te.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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
        self.combobox_template.disable()
        # 将PTB图纸，NA图纸和预设设置为不可用
        for button in [self.search_na_button, self.search_ptb_button, self.search_preset_button]:
            button.setEnabled(False)
        for line_edit in [self.show_na_path, self.show_ptb_path, self.show_preset_path]:
            line_edit.disable()

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
        self.show_na_path.enable()
        # 将下拉框和PTB图纸，预设设置为不可用
        for w in [self.combobox_template, self.search_ptb_button, self.search_preset_button]:
            w.setEnabled(False)
        for w in [self.combobox_template, self.show_ptb_path, self.show_preset_path]:
            w.disable()

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
        self.combobox_template.enable()
        # 将NA图纸和PTB图纸，预设设置为不可用
        for w in [self.search_na_button, self.search_ptb_button, self.search_preset_button]:
            w.setEnabled(False)
        for w in [self.show_na_path, self.show_ptb_path, self.show_preset_path]:
            w.disable()

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
        self.show_ptb_path.enable()
        # 将NA图纸，下拉框和预设设置为不可用
        for w in [self.search_na_button, self.combobox_template, self.search_preset_button]:
            w.setEnabled(False)
        for w in [self.show_na_path, self.combobox_template, self.show_preset_path]:
            w.disable()

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
        self.show_preset_path.enable()
        # 将NA图纸，下拉框和PTB图纸设置为不可用
        for w in [self.search_na_button, self.combobox_template, self.search_ptb_button]:
            w.setEnabled(False)
        for w in [self.show_na_path, self.show_ptb_path, self.combobox_template]:
            w.disable()

    def check_path(self):
        """
        用户选择路径
        """
        choose_path_from = self.ProjectFolder
        path = QFileDialog.getExistingDirectory(self, "选择工程路径", choose_path_from)
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
                MyMessageBox().information(None, "提示", _txt, MyMessageBox.Ok)
                return
            if design_reader.result["adHull"]:  # 如果存在进阶船壳
                # 显示后两层路径
                self.show_ptb_path.setText(file_path.split("/")[-2] + "/" + file_path.split("/")[-1])
                return self.PTBDesignPath
            else:
                _txt = "该设计不含进阶船体外壳，请重新选择哦"
                MyMessageBox.information(None, "提示", _txt, MyMessageBox.Ok)
                self.check_ptb_path()
                return
        except IndexError:
            return

    def select_preset(self):
        ...


class SelectNaDialog(BasicDialog):
    def __init__(self, parent, title="选择您的NavalArt设计", size=QSize(1300, 700)):
        # 信号
        self.NaPath = os.path.join(find_na_root_path(), 'ShipSaves')
        self.NaThumbnailPath = os.path.join(self.NaPath, 'Thumbnails')
        self.selected_na_design = None
        # =======================================================================================布局
        self.center_layout = QVBoxLayout()
        # 滚动区，用于显示缩略图，缩略图下方是一个label，用于显示船体名称
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget_layout = QGridLayout()
        super().__init__(parent, 10, title, size, self.center_layout, resizable=True)
        # 当鼠标移动到窗口边缘按下，添加缩放功能
        self.setMouseTracking(True)
        self.na_designs = {}
        self.set_widgets()
        self.container_group = SelectWidgetGroup(
            list(self.na_designs.values()), self.scroll_area_widget,
            original_style_sheet=f"background-color: {BG_COLOR0}; border-radius: 10px;",
            selected_style_sheet=f"background-color: {BG_COLOR3}; border-radius: 10px;"
        )

    def set_widgets(self):
        self.center_layout.setContentsMargins(25, 25, 25, 25)
        self.center_layout.setSpacing(25)
        self.center_layout.addWidget(self.scroll_area)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.scroll_area_widget.setLayout(self.scroll_area_widget_layout)
        self.scroll_area_widget_layout.setAlignment(Qt.AlignCenter)
        self.scroll_area_widget_layout.setContentsMargins(30, 30, 30, 30)
        self.scroll_area_widget_layout.setSpacing(25)
        # 遍历NaPath下的所有.na文件，在ThumbnailPath下找到对应的缩略图，显示在scroll_area中
        total_num = 0
        for file in os.listdir(self.NaPath):
            if not file.endswith('.na'):
                continue
            # 在ThumbnailPath下找到对应的缩略图
            thumbnail_path = os.path.join(self.NaThumbnailPath, file.split('.')[0] + '.png')
            if not os.path.exists(thumbnail_path):
                continue
            # 生成文字label
            label = MyLabel(file.split('.')[0], font=FONT_10)
            label.setAlignment(Qt.AlignCenter)
            # 生成图片label
            thumbnail = QPixmap(thumbnail_path).scaled(220, 200, Qt.KeepAspectRatio)
            thumbnail_label = QLabel()
            thumbnail_label.setPixmap(thumbnail)
            thumbnail_label.setAlignment(Qt.AlignCenter)
            # 主容器（按钮，上图片下文字）
            bt = QPushButton()
            bt.setFixedSize(260, 220)
            bt.setStyleSheet(f"background-color: {BG_COLOR0}; border-radius: 10px;")
            bt_layout = QVBoxLayout()
            bt_layout.addWidget(thumbnail_label)
            bt_layout.addWidget(label)
            bt.setLayout(bt_layout)
            # 将容器添加到布局中
            self.na_designs[file.split('.')[0]] = bt
            self.scroll_area_widget_layout.addWidget(bt, total_num // 4, total_num % 4, Qt.AlignCenter)
            total_num += 1
        self.set_scroll_area_widget(total_num)

    def set_scroll_area_widget(self, total_num):
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedSize(1250, 585)
        self.scroll_area.setStyleSheet(f"background-color: {BG_COLOR0}; border-radius: 10px;")
        self.scroll_area_widget.setFixedSize(1200, 240 * (total_num // 4 + 1))
        self.scroll_area_widget_layout.setAlignment(Qt.AlignTop)
        style = str(f"background-color: {BG_COLOR0}; border-radius: 10px;")
        self.scroll_area_widget.setStyleSheet(style)

    def ensure(self):
        index = self.container_group.selected_bt_index
        self.selected_na_design = list(self.na_designs.keys())[index]
        super().ensure()


class ThemeDialog(BasicDialog):
    def __init__(self, config, show_state_func, parent, title="设置主题", size=QSize(300, 200)):
        self.config = config
        self.show_state_func = show_state_func
        self.center_layout = QGridLayout()
        self.cb0 = QPushButton("")
        self.cb1 = QPushButton("")
        self.cb2 = QPushButton("")
        self.button_group = CircleSelectButtonGroup(
            [self.cb0, self.cb1, self.cb2],
            parent=self,
            half_size=7
        )
        self.lb0 = MyLabel("白天", font=FONT_10)
        self.lb1 = MyLabel("夜晚", font=FONT_10)
        self.lb2 = MyLabel("自定义", font=FONT_10)
        # 布局
        self.center_layout.addWidget(self.cb0, 0, 0)
        self.center_layout.addWidget(self.cb1, 1, 0)
        self.center_layout.addWidget(self.cb2, 2, 0)
        self.center_layout.addWidget(self.lb0, 0, 1)
        self.center_layout.addWidget(self.lb1, 1, 1)
        self.center_layout.addWidget(self.lb2, 2, 1)
        super().__init__(parent, 10, title, size, self.center_layout)
        self.set_widget()

    def set_widget(self):
        self.center_layout.setSpacing(8)
        self.center_layout.setContentsMargins(30, 20, 30, 0)
        # 读取config中的主题设置
        if self.config.Config["Theme"] == "Day":
            self.cb0.click()
        elif self.config.Config["Theme"] == "Night":
            self.cb1.click()
        elif self.config.Config["Theme"] == "Custom":
            self.cb2.click()
        # 将单击label事件触发单击button事件
        self.lb0.mousePressEvent = lambda x: self.cb0.click()
        self.lb1.mousePressEvent = lambda x: self.cb1.click()
        self.lb2.mousePressEvent = lambda x: self.cb2.click()

    def ensure(self):
        super().ensure()
        if self.button_group.selected_bt_index == 0:
            self.config.Config["Theme"] = "Day"
        elif self.button_group.selected_bt_index == 1:
            self.config.Config["Theme"] = "Night"
        elif self.button_group.selected_bt_index == 2:
            # 提示自定义功能未开放
            MyMessageBox().information(None, "提示", "自定义功能未开放", MyMessageBox.Ok)
            return
        # 提示保存成功，建议重启程序
        self.show_state_func("主题保存成功，建议重启程序", "success")
        self.config.save_config()  # 保存配置


class SensitiveDialog(BasicDialog):
    def __init__(self, config, camera, parent, title="设置灵敏度", size=QSize(300, 200)):
        self.config = config
        self.camera = camera
        self.center_layout = QGridLayout()
        self.lb0 = MyLabel("缩放灵敏度", font=FONT_10)
        self.lb1 = MyLabel("旋转灵敏度", font=FONT_10)
        self.lb2 = MyLabel("平移灵敏度", font=FONT_10)
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
        self.sld0.setValue(int(100 * self.config.Sensitivity["缩放"]))
        self.sld1.setValue(int(100 * self.config.Sensitivity["旋转"]))
        self.sld2.setValue(int(100 * self.config.Sensitivity["平移"]))
        self.center_layout.addWidget(self.lb0, 0, 0)
        self.center_layout.addWidget(self.lb1, 1, 0)
        self.center_layout.addWidget(self.lb2, 2, 0)
        self.center_layout.addWidget(self.sld0, 0, 1)
        self.center_layout.addWidget(self.sld1, 1, 1)
        self.center_layout.addWidget(self.sld2, 2, 1)
        self.result = [self.config.Sensitivity["缩放"], self.config.Sensitivity["旋转"],
                       self.config.Sensitivity["平移"]]
        for i in range(3):
            self.result[i] = self.result[i] * 100
        # 绑定事件
        self.sld0.valueChanged.connect(self.value_changed0)
        self.sld1.valueChanged.connect(self.value_changed1)
        self.sld2.valueChanged.connect(self.value_changed2)
        super().__init__(parent, 10, title, size, self.center_layout)
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
        self.config.Sensitivity["缩放"] = self.result[0] * 0.01
        self.config.Sensitivity["旋转"] = self.result[1] * 0.01
        self.config.Sensitivity["平移"] = self.result[2] * 0.01
        self.config.save_config()
        for c in self.camera.all_cameras:
            c.Sensitivity = self.config.Sensitivity


class ColorDialog(BasicDialog):
    color_selected = pyqtSignal()

    def __init__(self, parent, na_hull):
        self.canceled = False
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
        self.center_layout = QVBoxLayout()
        # 滚动区
        self.center_grid_layout = QGridLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area_widget = QWidget()

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
        self.all_choose_box.setFixedSize(80, 70)
        self.all_choose_box.stateChanged.connect(self.all_choose_box_state_changed)
        # 设置布局
        top_and_bottom_and_button_height = 170
        single_line_h = 200
        if 3 < self.color_num <= 15:
            size = QSize(100 + self.color_num * 85, 380)
            self.scroll_area_widget.setFixedSize(size.width() - 25, single_line_h + 20)
        elif 15 < self.color_num <= 45:
            size = QSize(100 + 15 * 85, (1 + lines) * single_line_h + top_and_bottom_and_button_height)
            self.scroll_area_widget.setFixedSize(size.width() - 25, (1 + lines) * single_line_h + 20)
        elif 45 < self.color_num:
            size = QSize(100 + 15 * 85, 3 * single_line_h + top_and_bottom_and_button_height)
            self.scroll_area_widget.setFixedSize(size.width() - 25, (1 + lines) * single_line_h + 20)
        else:
            size = QSize(320, 380)
            self.scroll_area_widget.setFixedSize(size.width() - 25, single_line_h + 20)
        self.scroll_area.setFixedSize(size.width(), size.height() - top_and_bottom_and_button_height + 20)
        super().__init__(parent, 10, self.title, size, self.center_layout)
        self.set_widget()
        self.cancel_button.clicked.connect(self.cancel)
        self.close_button.clicked.connect(self.cancel)

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
        self.scroll_area_widget.setLayout(self.center_grid_layout)
        self.scroll_area.setWidget(self.scroll_area_widget)
        self.center_layout.addWidget(self.scroll_area)
        self.center_layout.setAlignment(Qt.AlignCenter)
        self.center_grid_layout.setAlignment(Qt.AlignCenter)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.center_layout.addWidget(self.all_choose_box, alignment=Qt.AlignCenter)
        # 滚动区边框取消
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setStyleSheet("border: 0px;")
        self.center_grid_layout.setHorizontalSpacing(20)
        self.center_grid_layout.setVerticalSpacing(15)
        self.center_grid_layout.setContentsMargins(10, 40, 10, 0)

    # noinspection PyUnresolvedReferences
    def close(self) -> bool:
        return super().close()

    def cancel(self):
        self.canceled = True
        self.close()

    # noinspection PyUnresolvedReferences
    def ensure(self):
        draw_map = {}
        for color, choose_box in self.color_choose_map.items():
            if choose_box.isChecked():
                draw_map[color] = self.color_parts_map[color]
        self.na_hull.DrawMap = draw_map
        if draw_map:
            self.color_selected.emit()  # 发送自定义信号通知颜色选择完成
            self.close()
        else:
            MyMessageBox().information(None, "提示", "未选择任何颜色", MyMessageBox.Ok)


class ExportDialog(BasicDialog):
    def __init__(self, parent, title="导出", size=QSize(300, 200)):
        # 和外界交互的变量
        self.export2na = False
        self.export2obj = False
        # 布局
        self.center_layout = QGridLayout()
        self.b0 = QPushButton("")
        self.b1 = QPushButton("")
        self.l0 = MyLabel("导出到na文件", font=FONT_10)
        self.l1 = MyLabel("导出为obj文件", font=FONT_10)
        self.button_group = CircleSelectButtonGroup(
            [self.b0, self.b1],
            parent=self,
            half_size=7,
            default_index=0
        )
        self.center_layout.addWidget(self.b0, 0, 0)
        self.center_layout.addWidget(self.b1, 1, 0)
        self.center_layout.addWidget(self.l0, 0, 1)
        self.center_layout.addWidget(self.l1, 1, 1)

        super().__init__(parent, 10, title, size, self.center_layout)
        self.set_widget()

    def set_widget(self):
        self.center_layout.setSpacing(15)
        self.center_layout.setContentsMargins(30, 30, 30, 30)

    def ensure(self):
        if self.button_group.selected_bt_index == 0:
            self.export2na = True
        elif self.button_group.selected_bt_index == 1:
            self.export2obj = True
        super().ensure()


class UserGuideDialog(BasicDialog):

    def __init__(self, parent, title="新手教程", size=QSize(800, 600)):
        self.center_layout = QVBoxLayout()
        # 显示用户指南还没做完，敬请期待
        self.lb0 = MyLabel("新手教程尚未完成，敬请期待!", font=FONT_10)
        self.lb0.setAlignment(Qt.AlignCenter)
        self.center_layout.addWidget(self.lb0)
        ...  # TODO:
        super().__init__(parent, 10, title, size, self.center_layout)
        self.set_widget()

    def set_widget(self):
        self.center_layout.setSpacing(0)
        self.center_layout.setContentsMargins(0, 0, 0, 0)

    def ensure(self):
        super().ensure()
