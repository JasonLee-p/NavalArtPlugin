# -*- coding: utf-8 -*-
"""
定义一些常用的布局
"""
from abc import abstractmethod
from typing import Literal, List

from .buttons import *

from funcs_utils import CONST, color_print, bool_protection


def get_distance(pos1, pos2):
    """
    计算两个点之间的距离
    :param pos1:
    :param pos2:
    :return:
    """
    return ((pos1.x() - pos2.x()) ** 2 + (pos1.y() - pos2.y()) ** 2) ** 0.5


class TabButton(Button):
    def __init__(self, tab: QWidget, image: QImage, tool_tip, bd_radius=7):
        """
        可拖动的按钮
        :param tab: 所属的Tab
        :param image:
        :param tool_tip:
        :param bd_radius:
        :return:
        """
        super().__init__(None, tool_tip, 0, BG_COLOR1, bd_radius, bg=(BG_COLOR1, BG_COLOR3, GRAY, BG_COLOR3),
                         size=30)
        # 处理参数
        if isinstance(bd_radius, int):
            bd_radius = [bd_radius] * 4
        # 设置样式
        self.setIcon(QIcon(QPixmap(image)))
        self.setFocusPolicy(Qt.NoFocus)
        self.setFlat(True)
        self.tab: MutiDirectionTab = tab
        self.bd_radius = bd_radius
        # 绑定点击事件
        self.pressed.connect(self.pressed_action)
        self.clicked.connect(self.clicked_action)
        # 状态
        self.drag_available = False
        self.click_pos = None
        # 重新定向移动事件
        self.mouseMoveEvent = self.tab.main_widget_with_multidir.mouseMoveEvent
        # 影子按钮，用于拖动显示
        self.temp_button = Button(self.tab.main_widget_with_multidir, None, 0, BG_COLOR1, bd_radius,
                                  bg=(BG_COLOR1, BG_COLOR3, GRAY, BG_COLOR3), size=30)
        self.init_temp_button()
        self.temp_button.setIcon(QIcon(QPixmap(image)))
        self.temp_button.setFocusPolicy(Qt.NoFocus)
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(0, 0, 0, 50))
        self.shadow.setBlurRadius(20)
        self.setGraphicsEffect(self.shadow)
        self.temp_button.setGraphicsEffect(self.shadow)

    def init_temp_button(self):
        self.temp_button.hide()
        self.temp_button.setFocusPolicy(Qt.NoFocus)
        self.temp_button.setFlat(True)
        self.temp_button.setFixedSize(self.size())
        self.temp_button.setStyleSheet(f"""
            QLabel{{
                background-color: {BG_COLOR0};
                color: {FG_COLOR0};
                border: 0px solid {FG_COLOR0};
                border-top-left-radius: {self.bd_radius[0]}px;
                border-top-right-radius: {self.bd_radius[1]}px;
                border-bottom-right-radius: {self.bd_radius[2]}px;
                border-bottom-left-radius: {self.bd_radius[3]}px;
            }}
        """)

    def pressed_action(self):
        self.drag_available = True
        self.click_pos = QCursor.pos()
        self.tab.main_widget_with_multidir.dragging_widget = self.tab

    def clicked_action(self):
        """
        切换标签页
        :return:
        """
        self.drag_available = False
        self.click_pos = None
        self.temp_button.hide()
        self.temp_button.move(-100, -100)
        tab_widget = self.tab.main_widget_with_multidir.TabWidgetMap[self.tab.direction]
        tab_widget.change_tab(self.tab)


class ButtonGroup:
    def __init__(self, buttons: List[QPushButton] = None, default_index: int = 0):
        """
        按钮组，只能有一个按钮被选中
        :param buttons:
        :param default_index:
        """
        self.is_operating = False
        if buttons:
            self.buttons = buttons
            for button in buttons:
                button.setCheckable(True)
                button.setChecked(False)
                button.clicked.connect(lambda: self.button_clicked(button))
            buttons[default_index].setChecked(True)
            self.current = buttons[default_index]
        else:
            self.buttons = []
            self.current = None

    def __str__(self):
        return f"ButtonGroup: {len(self.buttons)} buttons, current: {self.current}"

    @bool_protection("is_operating")
    def button_clicked(self, button: QPushButton):
        """
        按钮被点击时，更新当前按钮
        :param button:
        :return:
        """

        if button not in self.buttons:
            color_print(f"[WARNING] Clicked Button {button} not in <{self}>.", "red")
            return False
        if self.current is not None:
            self.current.setChecked(False)
        self.current = button
        self.current.setChecked(True)

    @bool_protection("is_operating")
    def add(self, button: QPushButton):
        """
        添加按钮
        :param button:
        :return:
        """
        button.setCheckable(True)
        button.func_ = lambda: self.button_clicked(button)
        button.clicked.connect(button.func_)
        if button in self.buttons:
            color_print(f"[WARNING] Added Button {button} already in <{self}>.", "red")
            return False
        self.buttons.append(button)
        if self.current:
            self.current.setChecked(False)
        self.current = button
        self.current.setChecked(True)

    @bool_protection("is_operating")
    def remove(self, button: QPushButton):
        """
        移除按钮
        :param button:
        :return:
        """
        # 处理异常传入
        if button not in self.buttons:
            color_print(f"[WARNING] Removed Button {button} not in <{self}>.", "red")
            return False
        # 移除按钮
        self.buttons.remove(button)
        button.clicked.disconnect(button.func_)
        button.setChecked(False)
        if self.current == button:
            if self.buttons:
                self.current = self.buttons[-1]
                self.current.setChecked(True)
                self.current.update()
            else:
                self.current = None


class MutiDirectionTab(QWidget):
    def __init__(self, main_widget_with_multidir, init_direction=CONST.RIGHT,
                 image: QImage = None, name: str = None,
                 bg: Union[ThemeColor, str] = BG_COLOR1, fg: Union[ThemeColor, str] = FG_COLOR0,
                 bd_radius: Union[int, Tuple[int, int, int, int]] = 0):
        """
        一个可各个方向拖动的单标签页
        """
        # 处理参数
        if isinstance(bd_radius, int):
            bd_radius = [bd_radius] * 4
        super().__init__()
        self.is_being_dragged = False
        self.m_Position = None
        self.name = name
        self.direction = init_direction
        self.main_widget_with_multidir = main_widget_with_multidir
        # 按钮
        self.button = TabButton(self, image=image, tool_tip=name)
        # 设置样式
        self.setStyleSheet(f"""
            QWidget{{
                background-color: {bg};
                color: {fg};
                border: 0px solid {fg};
                border-top-left-radius: {bd_radius[0]}px;
                border-top-right-radius: {bd_radius[1]}px;
                border-bottom-right-radius: {bd_radius[2]}px;
                border-bottom-left-radius: {bd_radius[3]}px;
            }}
        """)
        self.drag_area = self.init_drag_area()
        self.hide()
        self._layout = QVBoxLayout(self)
        self.top_widget = QWidget()
        self.top_layout = QHBoxLayout(self.top_widget)
        self.title_label = TextLabel(self, name, YAHEI[9], fg)
        self.title_label.setFixedHeight(30)
        self._init_top_widget()

    def _init_top_widget(self):
        self._layout.setContentsMargins(10, 5, 10, 10)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.top_widget, alignment=Qt.AlignTop)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(0)
        self.top_layout.addWidget(self.title_label, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addWidget(self.drag_area, Qt.AlignRight | Qt.AlignVCenter)




    def init_drag_area(self):
        # 添加拖动条，控制窗口大小
        drag_widget = QWidget()
        # 设置宽度最大化
        drag_widget.setFixedWidth(10000)
        drag_widget.setStyleSheet("background-color: rgba(0,0,0,0)")
        drag_widget.mouseMoveEvent = self.button.mouseMoveEvent
        drag_widget.mousePressEvent = self.button.mousePressEvent
        drag_widget.mouseReleaseEvent = self.button.mouseReleaseEvent
        return drag_widget

    def change_layout(self, direction):
        """
        根据方向改变布局
        """
        ...


class FreeTabWidget(QWidget):
    ALIGN_MAP = {CONST.LEFT: Qt.AlignLeft | Qt.AlignVCenter, CONST.RIGHT: Qt.AlignRight | Qt.AlignVCenter,
                 CONST.UP: Qt.AlignTop | Qt.AlignHCenter, CONST.DOWN: Qt.AlignBottom | Qt.AlignHCenter}
    LAYOUT_MAP = {CONST.LEFT: QHBoxLayout, CONST.RIGHT: QHBoxLayout, CONST.UP: QVBoxLayout, CONST.DOWN: QVBoxLayout}

    def __init__(self, bt_widget, bt_direction: Literal['left', 'right', 'up', 'down'], multi_direction_tab=None):
        """
        一个可自由拖动的标签页
        :param bt_widget: 装按钮的容器，无需初始化布局
        :param bt_direction: 按钮容器的布局方向，为 CONST.LEFT/RIGHT/UP/DOWN
        """
        self.multi_direction_tab = multi_direction_tab
        super().__init__()
        # 状态变量
        self.is_dragging = False
        self.current_tab = None
        self.all_tabs = []
        # 控件
        self.button_group = ButtonGroup()
        self.bt_widget = bt_widget
        self.bt_direction = bt_direction
        self.bt_widget_layout: QLayout = FreeTabWidget.LAYOUT_MAP[bt_direction](self.bt_widget)
        self.bt_widget_layout.setAlignment(FreeTabWidget.ALIGN_MAP[bt_direction])
        self.bt_widget_layout.setContentsMargins(5, 5, 5, 5)
        self.bt_widget_layout.setSpacing(5)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.set_style()

    def set_style(self):
        # 设置样式
        self.setStyleSheet(f"""
            QWidget{{
                background-color: {BG_COLOR0};
                color: {FG_COLOR0};
                border: 0px solid {FG_COLOR0};
            }}
        """)

    def add_tab(self, tab: MutiDirectionTab):
        """
        添加标签页
        :param tab:
        :return:
        """
        if not self.multi_direction_tab:
            return
        self.button_group.add(tab.button)
        tab.direction = self.multi_direction_tab.DirMap[self]
        self.bt_widget_layout.addWidget(tab.button)
        self.layout.addWidget(tab)
        self.all_tabs.append(tab)
        if self.current_tab:
            self.current_tab.hide()
        self.current_tab = tab
        tab.show()

    def remove_tab(self, tab: MutiDirectionTab):
        """
        移除标签页
        :param tab:
        :return:
        """
        self.button_group.remove(tab.button)
        tab.direction = None
        self.bt_widget_layout.removeWidget(tab.button)
        self.layout.removeWidget(tab)
        self.all_tabs.remove(tab)
        if self.current_tab == tab:
            if self.all_tabs:
                self.current_tab = self.all_tabs[-1]
                self.current_tab.show()
            else:
                self.current_tab = None
        tab.hide()

    def change_tab(self, tab: MutiDirectionTab):
        """
        切换标签页
        :param tab:
        :return:
        """
        if tab not in self.all_tabs:
            color_print(f"[WARNING] Tab {tab} not in <{self}>.", "red")
            return False
        if self.current_tab:
            self.current_tab.hide()
        self.current_tab = tab
        tab.show()

    def preview_add_tab(self):
        """
        当有临时按钮被拖入
        :return:
        """
        self.setStyleSheet(f"""
            QWidget{{
                background-color: {BG_COLOR0};
                color: {FG_COLOR0};
                border: 1px solid {LIGHTER_BLUE};
            }}
        """)


class MainWidgetWithMultiDirectionTab(QWidget):

    def __init__(self, center_widget: QWidget):
        """
        一个带有多个可各个方向拖动的标签的窗口
        下方的标签占据整个窗口宽度
        """
        super().__init__()
        self._dragged_in_tab_widget = None
        self.center_widget = center_widget
        self.center_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.current_widgets = {CONST.LEFT: Union[MutiDirectionTab, None], CONST.RIGHT: Union[MutiDirectionTab, None],
                                CONST.DOWN: Union[MutiDirectionTab, None]}
        self.dragging_widget: Union[MutiDirectionTab, None] = None
        self.is_dragging = False
        # 总布局
        self.layout = QHBoxLayout(self)
        # Spliter
        self.ver_spliter = Splitter(Qt.Horizontal)  # 垂直分割器，用于分割左右两个TabWidget
        self.hor_spliter = Splitter(Qt.Vertical)  # 水平分割器，用于分割中间的控件和下方的TabWidget
        # 按钮容器
        self.left_bt_widget = QWidget()
        self.left_bt_layout = QVBoxLayout(self.left_bt_widget)
        self.left_up_bt_widget = QWidget()  # 用于 left_tab_widget 的按钮
        self.left_down_bt_widget = QWidget()  # 用于 down_tab_widget 的按钮
        self.right_bt_widget = QWidget()  # 用于 right_tab_widget 的按钮
        # TabWidgets
        self.down_tab_widget = FreeTabWidget(self.left_down_bt_widget, CONST.DOWN, self)
        self.left_tab_widget = FreeTabWidget(self.left_up_bt_widget, CONST.UP, self)
        self.right_tab_widget = FreeTabWidget(self.right_bt_widget, CONST.UP, self)
        self.DirMap = {self.left_tab_widget: CONST.LEFT,
                       self.right_tab_widget: CONST.RIGHT,
                       self.down_tab_widget: CONST.DOWN}
        self.TabWidgetMap = {CONST.LEFT: self.left_tab_widget, CONST.RIGHT: self.right_tab_widget,
                             CONST.DOWN: self.down_tab_widget}
        self.init_ui()

    def init_ui(self):
        self.ver_spliter.addWidget(self.left_tab_widget)
        self.ver_spliter.addWidget(self.center_widget)
        self.ver_spliter.addWidget(self.right_tab_widget)
        self.hor_spliter.addWidget(self.ver_spliter)
        self.hor_spliter.addWidget(self.down_tab_widget)

        # self.ver_spliter.setStretchFactor(0, 0)
        # self.ver_spliter.setStretchFactor(1, 1)
        # self.ver_spliter.setStretchFactor(2, 0)
        # self.hor_spliter.setStretchFactor(0, 1)
        # self.hor_spliter.setStretchFactor(1, 0)

        self.layout.addWidget(self.left_bt_widget)
        self.layout.addWidget(VerSpliter())
        self.layout.addWidget(self.hor_spliter)
        self.layout.addWidget(VerSpliter())
        self.layout.addWidget(self.right_bt_widget)

        self.left_bt_layout.addWidget(self.left_up_bt_widget, alignment=Qt.AlignTop)
        self.left_bt_layout.addWidget(self.left_down_bt_widget, alignment=Qt.AlignBottom)

        self.left_up_bt_widget.setFixedWidth(40)
        self.left_down_bt_widget.setFixedWidth(40)
        self.left_bt_widget.setFixedWidth(40)
        self.right_bt_widget.setFixedWidth(40)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.left_bt_layout.setContentsMargins(0, 0, 0, 0)
        self.left_bt_layout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)

    def add_tab(self, tab: MutiDirectionTab, direction: Literal['left', 'right', 'down']):
        """
        添加标签页
        :param tab:
        :param direction:
        :return:
        """
        self.TabWidgetMap[direction].add_tab(tab)

    def move_tab(self, tab: MutiDirectionTab, orgin_dir: Literal['left', 'right', 'down'],
                 target_dir: Literal['left', 'right', 'down']):
        """
        移动标签页
        """
        tab.is_operating = False
        self.TabWidgetMap[orgin_dir].remove_tab(tab)
        self.TabWidgetMap[target_dir].add_tab(tab)
        self.update()

    def remove_tab(self, tab: MutiDirectionTab):
        """
        移除标签页
        :param tab:
        :return:
        """
        self.TabWidgetMap[tab.direction].remove_tab(tab)
        self.update()

    def mouseMoveEvent(self, event):
        """
        标签页按钮的 mouseMoveEvent 已经被重新定向到这里
        """
        # 如果按钮被按下，先找到按钮
        if self.dragging_widget and event.buttons() == Qt.LeftButton and self.dragging_widget.button.drag_available:
            # 如果按钮被按下，且鼠标移动，说明开始拖动
            pos = QCursor.pos()
            pos_diff = pos - self.dragging_widget.button.click_pos
            if self.is_dragging is False:
                # 如果距离离起始已经大于10，就要开始绘制拖动时的半透明小按钮
                if get_distance(self.dragging_widget.button.click_pos, pos) > 10:
                    self.is_dragging = True
                    self.dragging_widget.button.temp_button.show()
            else:
                self.draw_temp_button(pos_diff)
                _dragged_in_tab_widget = self.check_pos_in_area()
                if _dragged_in_tab_widget:
                    self._dragged_in_tab_widget = _dragged_in_tab_widget
                    self._dragged_in_tab_widget.preview_add_tab()
                elif self._dragged_in_tab_widget:
                    self._dragged_in_tab_widget.set_style()
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.dragging_widget:
            self.dragging_widget.button.temp_button.move(-100, -100)
            self.dragging_widget.button.temp_button.hide()
            self.dragging_widget.button.drag_available = False
            self.dragging_widget.button.click_pos = None
            tab_widget = self.check_pos_in_area()
            if tab_widget:
                from_dir = self.dragging_widget.direction
                tar_dir = self.DirMap[tab_widget]
                self.move_tab(self.dragging_widget, from_dir, tar_dir)
            self.is_dragging = False
            self.dragging_widget = None

    def draw_temp_button(self, pos_diff):
        """
        绘制拖动时的半透明小按钮
        """
        temp_button = self.dragging_widget.button.temp_button
        bt = self.dragging_widget.button
        # 获取原始按钮的位置
        pos = bt.pos() + bt.parent().pos() + bt.parent().parent().pos()
        temp_button.move(pos.x() + pos_diff.x(), pos.y() + pos_diff.y())
        temp_button.update()

    def check_pos_in_area(self):
        """
        检查鼠标释放时的区域
        """
        pos = QCursor.pos()
        for tab_widget in [self.left_tab_widget, self.right_tab_widget, self.down_tab_widget]:
            if tab_widget.isVisible():
                tab_widget_pos = tab_widget.pos() + tab_widget.parent().pos() + tab_widget.parent().parent().pos()
                tab_widget_size = tab_widget.size()
                if tab_widget_pos.x() < pos.x() < tab_widget_pos.x() + tab_widget_size.width() and \
                        tab_widget_pos.y() < pos.y() < tab_widget_pos.y() + tab_widget_size.height():
                    return tab_widget
        return False


class Window(QWidget):
    def __init__(
            self, parent, title: str, ico_bites: bytes, ico_size: int = 26, topH: int = 40, bottomH: int = 35,
            size: Tuple[int, int] = (800, 600), show_maximize: bool = True, resizable: bool = True,
            font=YAHEI[6], bg: Union[str, ThemeColor] = BG_COLOR1, fg: Union[str, ThemeColor] = FG_COLOR0,
            bd_radius: Union[int, Tuple[int, int, int, int]] = 7,
            ask_if_close=True
    ):
        """
        提供带图标，顶栏，顶栏关闭按钮，底栏的窗口及其布局，
        其他的控件需要自己添加布局
        可以重载 init_top_widget, init_center_widget, init_bottom_widget 来自定义布局
        :param parent:
        :param title:
        :param ico_bites:
        :param ico_size:
        :param topH:
        :param bottomH:
        :param size:
        :param show_maximize:
        :param resizable:
        :param font:
        :param bg:
        :param fg:
        :param bd_radius:
        """
        super().__init__(parent)
        self.hide()
        # 处理参数
        if isinstance(bd_radius, int):
            bd_radius = [bd_radius] * 4
        self.setWindowFlags(Qt.FramelessWindowHint)  # 隐藏边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self._init_size = size
        self.ask_if_close = ask_if_close
        # 基础样式
        self.setFont(font)
        self.shadow = QGraphicsDropShadowEffect()
        # 设置非最大化的大小
        self.setFixedSize(QSize(size[0], size[1]))
        self.bg = bg
        self.fg = fg
        self.topH = topH
        self.bottomH = bottomH
        self.btWid = 55
        self.resizable = resizable
        self.title = title
        self.ico_size = ico_size
        self.bd_radius = bd_radius
        # 初始化控件
        self.layout = QVBoxLayout(self)
        self.top_widget = QWidget()
        self.center_widget = QWidget()
        self.bottom_widget = QWidget()
        self.top_layout = QHBoxLayout(self.top_widget)
        self.center_layout = QHBoxLayout(self.center_widget)
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        # 图标和基础按钮
        self.ico_label = IconLabel(None, ico_bites, self.title, topH)
        self.close_button = CloseButton(None, bd_radius=self.bd_radius)
        self.cancel_button = CancelButton(None, bd_radius=self.bd_radius)
        self.ensure_button = EnsureButton(None, bd_radius=self.bd_radius)
        self.maximize_button = MaximizeButton(None)
        self.minimize_button = MinimizeButton(None)
        # 标题
        self.title_label = TextLabel(None, self.title, YAHEI[8], self.fg)
        # 其他可能用到的控件
        self.status_label = QLabel(None)
        # 顶部拖动区域
        self.m_flag = False
        self.m_Position = None
        self.drag_area = self.init_drag_area()
        self.init_ui()
        # 显示
        self.animate()
        if show_maximize:
            self.showMaximized()
        else:
            self.show()

    def init_ui(self):
        # 设置窗口阴影

        self.shadow.setOffset(5, 5)
        self.shadow.setColor(QColor(0, 0, 0, 250))
        self.shadow.setBlurRadius(20)
        self.setGraphicsEffect(self.shadow)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.addWidget(self.top_widget, alignment=Qt.AlignTop)
        self.layout.addWidget(HorSpliter())
        self.layout.addWidget(self.center_widget, stretch=1)
        self.layout.addWidget(HorSpliter())
        self.layout.addWidget(self.bottom_widget, alignment=Qt.AlignBottom)
        for _layout in [self.top_layout, self.center_layout, self.bottom_layout]:
            _layout.setContentsMargins(0, 0, 0, 0)
            _layout.setSpacing(0)
        self.init_top_widget()
        self.init_center_widget()
        self.init_bottom_widget()
        self.bind_bt_funcs()

    def init_top_widget(self):
        self.top_widget.setFixedHeight(self.topH)
        # 控件
        self.top_layout.addWidget(self.ico_label, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addWidget(self.drag_area, Qt.AlignLeft | Qt.AlignVCenter)
        self.top_layout.addWidget(self.title_label, Qt.AlignLeft | Qt.AlignVCenter)

    def init_drag_area(self):
        # 添加拖动条，控制窗口大小
        drag_widget = QWidget()
        # 设置宽度最大化
        drag_widget.setFixedWidth(10000)
        drag_widget.setStyleSheet("background-color: rgba(0,0,0,0)")
        drag_widget.mouseMoveEvent = self.mouseMoveEvent
        drag_widget.mousePressEvent = self.mousePressEvent
        drag_widget.mouseReleaseEvent = self.mouseReleaseEvent
        return drag_widget

    def mousePressEvent(self, event):
        # 鼠标按下时，记录当前位置，若在标题栏内且非最大化，则允许拖动
        if event.button() == Qt.LeftButton and event.y() < self.topH and self.isMaximized() is False:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()
            event.accept()

    def mouseReleaseEvent(self, _):
        # 拖动窗口时，鼠标释放后停止拖动
        self.m_flag = False if self.m_flag else self.m_flag

    def mouseMoveEvent(self, event):
        # 当鼠标在标题栏按下且非最大化时，移动窗口
        if Qt.LeftButton and self.m_flag:
            self.move(event.globalPos() - self.m_Position)
            event.accept()

    @abstractmethod
    def init_center_widget(self):
        self.center_widget.setStyleSheet(f"""
            QWidget{{
                background-color: {self.bg};
                color: {self.fg};
            }}
        """)

    def init_bottom_widget(self):
        self.bottom_widget.setFixedHeight(self.bottomH)
        # 控件
        self.bottom_layout.addWidget(self.cancel_button, Qt.AlignRight | Qt.AlignVCenter)
        self.bottom_layout.addWidget(self.ensure_button, Qt.AlignRight | Qt.AlignVCenter)

    def bind_bt_funcs(self):
        self.close_button.clicked.connect(self.close)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button.clicked.connect(self.showMaximized)
        self.ensure_button.clicked.connect(self.ensure)
        self.cancel_button.clicked.connect(self.cancel)

    def ensure(self):
        self.close()

    def cancel(self):
        self.close()

    def close(self):
        if self.ask_if_close:
            reply = QMessageBox.question(self, '确认', '确认退出？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        self.animate(1, 0, 100)
        while self.windowOpacity() > 0:
            QApplication.processEvents()
        super().close()

    def _show_statu(self, message, message_type: Literal['highlight', 'success', 'process', 'error'] = 'process'):
        color_map = {
            'highlight': 'orange',
            'success': f"{FG_COLOR0}",
            'process': 'gray',
            'error': f"{FG_COLOR1}",
        }
        self.status_label.setStyleSheet(f"color: {color_map[message_type]};")
        self.status_label.setText(message)
        self.status_label.adjustSize()

    @classmethod
    def show_statu(cls, window: 'Window', message,
                   message_type: Literal['highlight', 'success', 'process', 'error'] = 'process'):
        window._show_statu(message, message_type)

    def showMaximized(self):
        if self.resizable and not self.isMaximized():
            super().showMaximized()
            self.maximize_button.setIcon(QIcon(QPixmap.fromImage(NORMAL_IMAGE)))
        else:
            super().showNormal()
            self.maximize_button.setIcon(QIcon(QPixmap.fromImage(MAXIMIZE_IMAGE)))

    def animate(self, start=0, end=1, duration=200):
        self.animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.animation.setDuration(duration)
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()
