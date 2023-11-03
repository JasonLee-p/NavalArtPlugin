"""
工具函数
"""

import ctypes
from typing import Literal

import numpy as np
from PySide2.QtCore import Qt
from PySide2.QtGui import QVector3D, QPixmap, QPainter, QPainterPath
from PySide2.QtWidgets import QMessageBox, QWidget
from quaternion import quaternion


class CONST:
    # 具体方位
    FRONT = "front"
    BACK = "back"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    SAME = "same"

    # 方位组合
    FRONT_BACK = "front_back"
    UP_DOWN = "up_down"
    LEFT_RIGHT = "left_right"

    # 八个卦限
    FRONT_UP_LEFT = "front_up_left"
    FRONT_UP_RIGHT = "front_up_right"
    FRONT_DOWN_LEFT = "front_down_left"
    FRONT_DOWN_RIGHT = "front_down_right"
    BACK_UP_LEFT = "back_up_left"
    BACK_UP_RIGHT = "back_up_right"
    BACK_DOWN_LEFT = "back_down_left"
    BACK_DOWN_RIGHT = "back_down_right"

    DIR_INDEX_MAP = {FRONT_BACK: 2, UP_DOWN: 1, LEFT_RIGHT: 0}
    SUBDIR_MAP = {FRONT_BACK: (FRONT, BACK), UP_DOWN: (UP, DOWN), LEFT_RIGHT: (LEFT, RIGHT)}
    DIR_OPPOSITE_MAP = {FRONT: BACK, BACK: FRONT, UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT, SAME: SAME}
    VERTICAL_DIR_MAP = {
        FRONT: (UP, DOWN, LEFT, RIGHT), BACK: (UP, DOWN, LEFT, RIGHT), FRONT_BACK: (UP, DOWN, LEFT, RIGHT),
        UP: (FRONT, BACK, LEFT, RIGHT), DOWN: (FRONT, BACK, LEFT, RIGHT), UP_DOWN: (FRONT, BACK, LEFT, RIGHT),
        LEFT: (FRONT, BACK, UP, DOWN), RIGHT: (FRONT, BACK, UP, DOWN), LEFT_RIGHT: (FRONT, BACK, UP, DOWN)}
    VERTICAL_RAWDIR_MAP = {
        FRONT: (UP_DOWN, LEFT_RIGHT), BACK: (UP_DOWN, LEFT_RIGHT), FRONT_BACK: (UP_DOWN, LEFT_RIGHT),
        UP: (FRONT_BACK, LEFT_RIGHT), DOWN: (FRONT_BACK, LEFT_RIGHT), UP_DOWN: (FRONT_BACK, LEFT_RIGHT),
        LEFT: (FRONT_BACK, UP_DOWN), RIGHT: (FRONT_BACK, UP_DOWN), LEFT_RIGHT: (FRONT_BACK, UP_DOWN)}
    DIR_TO_RAWDIR_MAP = {
        FRONT: FRONT_BACK, BACK: FRONT_BACK, UP: UP_DOWN, DOWN: UP_DOWN, LEFT: LEFT_RIGHT, RIGHT: LEFT_RIGHT}
    # 旋转顺序
    __orders = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
    ROTATE_ORDER = __orders[2]


VECTOR_RELATION_MAP = {
    (0., 0., 1.): {"Larger": CONST.FRONT, "Smaller": CONST.BACK},
    (0., 0., -1.): {"Larger": CONST.BACK, "Smaller": CONST.FRONT},
    (1., 0., 0.): {"Larger": CONST.LEFT, "Smaller": CONST.RIGHT},
    (-1., 0., 0.): {"Larger": CONST.RIGHT, "Smaller": CONST.LEFT},
    (0., 1., 0.): {"Larger": CONST.UP, "Smaller": CONST.DOWN},
    (0., -1., 0.): {"Larger": CONST.DOWN, "Smaller": CONST.UP},
}


def rotate_quaternion(vec, rot: list):
    """
    对np.array类型的向量进行四元数旋转
    :param vec:
    :param rot: list
    :return:
    """
    if rot == [0, 0, 0]:
        # 标准化为单位向量
        return vec / np.linalg.norm(vec)
    # 转换为弧度
    rot = np.radians(rot)
    # 计算旋转的四元数
    q_x = np.array([np.cos(rot[0] / 2), np.sin(rot[0] / 2), 0, 0])
    q_y = np.array([np.cos(rot[1] / 2), 0, np.sin(rot[1] / 2), 0])
    q_z = np.array([np.cos(rot[2] / 2), 0, 0, np.sin(rot[2] / 2)])

    # 合并三个旋转四元数
    q = quaternion(1, 0, 0, 0)
    if CONST.ROTATE_ORDER == "XYZ":
        q = q * quaternion(*q_x) * quaternion(*q_y) * quaternion(*q_z)
    elif CONST.ROTATE_ORDER == "XZY":
        q = q * quaternion(*q_x) * quaternion(*q_z) * quaternion(*q_y)
    elif CONST.ROTATE_ORDER == "YXZ":
        q = q * quaternion(*q_y) * quaternion(*q_x) * quaternion(*q_z)
    elif CONST.ROTATE_ORDER == "YZX":
        q = q * quaternion(*q_y) * quaternion(*q_z) * quaternion(*q_x)
    elif CONST.ROTATE_ORDER == "ZXY":
        q = q * quaternion(*q_z) * quaternion(*q_x) * quaternion(*q_y)
    elif CONST.ROTATE_ORDER == "ZYX":
        q = q * quaternion(*q_z) * quaternion(*q_y) * quaternion(*q_x)
    else:
        raise ValueError("Invalid RotateOrder!")

    # 进行四元数旋转
    rotated_point_quat = q * np.quaternion(0, *vec) * np.conj(q)
    # 提取旋转后的点坐标
    rotated_point = np.array([rotated_point_quat.x, rotated_point_quat.y, rotated_point_quat.z])
    # 标准化为单位向量
    rotated_point = rotated_point / np.linalg.norm(rotated_point)
    return rotated_point


def get_part_world_dirs(part_rot: list, excepted_dir: Literal["front_back", "up_down", "left_right"] = None):
    """
    获取零件本地坐标系方向在全局坐标系中的方向
    :param part_rot: list
    :param excepted_dir: 被排除的方向 Literal[CONST.FRONT_BACK, CONST.UP_DOWN, CONST.LEFT_RIGHT]
    :return:
    """
    front_vec, left_vec, up_vec = None, None, None
    if not excepted_dir:
        front_vec = tuple(rotate_quaternion(np.array([0., 0., 1.]), part_rot))
        left_vec = tuple(rotate_quaternion(np.array([1., 0., 0.]), part_rot))
        up_vec = tuple(rotate_quaternion(np.array([0., 1., 0.]), part_rot))
    elif excepted_dir == CONST.FRONT_BACK:
        left_vec = tuple(rotate_quaternion(np.array([1., 0., 0.]), part_rot))
        up_vec = tuple(rotate_quaternion(np.array([0., 1., 0.]), part_rot))
    elif excepted_dir == CONST.UP_DOWN:
        front_vec = tuple(rotate_quaternion(np.array([0., 0., 1.]), part_rot))
        left_vec = tuple(rotate_quaternion(np.array([1., 0., 0.]), part_rot))
    elif excepted_dir == CONST.LEFT_RIGHT:
        front_vec = tuple(rotate_quaternion(np.array([0., 0., 1.]), part_rot))
        up_vec = tuple(rotate_quaternion(np.array([0., 1., 0.]), part_rot))
    front, back, left, right, up, down = None, None, None, None, None, None
    if front_vec in VECTOR_RELATION_MAP.keys():
        front = VECTOR_RELATION_MAP[front_vec]["Larger"]
        back = VECTOR_RELATION_MAP[front_vec]["Smaller"]
    if left_vec in VECTOR_RELATION_MAP.keys():
        left = VECTOR_RELATION_MAP[left_vec]["Larger"]
        right = VECTOR_RELATION_MAP[left_vec]["Smaller"]
    if up_vec in VECTOR_RELATION_MAP.keys():
        up = VECTOR_RELATION_MAP[up_vec]["Larger"]
        down = VECTOR_RELATION_MAP[up_vec]["Smaller"]
    return {CONST.FRONT: front, CONST.BACK: back, CONST.LEFT: left,
            CONST.RIGHT: right, CONST.UP: up, CONST.DOWN: down}


def get_normal(dot1, dot2, dot3, center=None):
    """
    计算三角形的法向量，输入为元组
    :param dot1: 元组，三角形的第一个点
    :param dot2: 元组，三角形的第二个点
    :param dot3: 元组，三角形的第三个点
    :param center: QVector3D，三角形的中心点
    :return: QVector3D
    """
    if isinstance(center, tuple):
        center = QVector3D(*center)
    v1 = QVector3D(*dot2) - QVector3D(*dot1)
    v2 = QVector3D(*dot3) - QVector3D(*dot1)
    if center is None:
        return QVector3D.crossProduct(v1, v2).normalized()
    triangle_center = QVector3D(*dot1) + QVector3D(*dot2) + QVector3D(*dot3)
    # 如果法向量与视线夹角大于90度，翻转法向量
    if QVector3D.dotProduct(QVector3D.crossProduct(v1, v2), triangle_center - center) > 0:
        return QVector3D.crossProduct(v1, v2).normalized()
    else:
        return QVector3D.crossProduct(v1, v2).normalized()


def get_bezier(start, s_control, back, b_control, x):
    """
    计算贝塞尔曲线上的点的坐标，用np.array类型表示
    :param start: 起点
    :param s_control: 起点控制点
    :param back: 终点
    :param b_control: 终点控制点
    :param x: 点的x坐标，x在start[0]和back[0]之间
    :return: 返回贝塞尔曲线上的点坐标
    """
    # 计算 t 值
    t = (x - start[0]) / (back[0] - start[0])
    # 贝塞尔曲线公式
    result = (1 - t) ** 3 * start + 3 * (1 - t) ** 2 * t * s_control + 3 * (1 - t) * t ** 2 * b_control + t ** 3 * back
    return np.array(result)


def fit_bezier(front_k, back_k, x_scl, y_scl, n, draw=False):
    """
    计算贝塞尔曲线上的区间的斜率
    :param front_k:
    :param back_k:
    :param x_scl:
    :param y_scl:
    :param n:
    :param draw:
    :return:
    """
    # 过滤n值>=2
    if n < 2:
        raise ValueError("n must be greater than or equal to 2")

    # 计算控制点位置
    distance = x_scl / 4
    start = np.array([0, 0])
    end = np.array([x_scl, y_scl])
    dir_s = np.array([1, front_k])
    dir_b = np.array([1, back_k])
    # 标准化后乘以距离
    dir_s = dir_s * distance / np.linalg.norm(dir_s)
    dir_b = dir_b * distance / np.linalg.norm(dir_b)
    start_control = start + dir_s
    end_control = end - dir_b
    if draw:
        # 在matplotlib绘制贝塞尔曲线：
        import matplotlib.pyplot as plt
        # 从0到length之间生成100个点
        t_values = np.linspace(0, x_scl, 100)
        # 初始化存储曲线上点的空数组
        curve_points = []
        # 计算贝塞尔曲线上的点
        for t in t_values:
            point = get_bezier(start, start_control, end, end_control, t / x_scl)
            curve_points.append(point)
        # 转换为NumPy数组以便于绘图
        curve_points = np.array(curve_points)
        # 绘制贝塞尔曲线
        plt.figure(figsize=(8, 6))
        plt.plot(curve_points[:, 0], curve_points[:, 1], label='Bezier Curve', color='blue')
        plt.scatter([start[0], start_control[0], end[0], end_control[0]],
                    [start[1], start_control[1], end[1], end_control[1]],
                    color='red', marker='o', label='Control Points')
        plt.title('Bezier Curve')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.legend()
        plt.grid(True)
        plt.show()
    # 存储斜率的列表
    slopes = []
    # 计算每段的长度
    last_point = None
    step = x_scl / n
    # 计算每段的斜率
    for i in range(n):
        # 计算当前参数值
        x = (i + 1) * step
        # 计算贝塞尔曲线上的点坐标
        point = get_bezier(start, start_control, end, end_control, x)
        # 计算与前一个点的斜率，如果为第一个点则计算与起点的斜率
        if i == 0:
            slope = (point[1] - start[1]) / step
        else:
            slope = (point[1] - last_point[1]) / step
        # 将斜率添加到列表中
        slopes.append(slope)
        # 保存上一个点的坐标
        last_point = point

    return slopes


def open_url(url):
    def func(event):
        from PySide2.QtCore import QUrl
        from PySide2.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(url))

    return func


def not_implemented(func):
    """
    装饰器，弹出提示框，提示该功能暂未实现
    :return:
    """

    def wrapper(*args, **kwargs):
        QMessageBox.information(None, "提示", "该功能暂未实现，敬请期待！", QMessageBox.Ok)

    return wrapper


def empty_func(*args, **kwargs):
    """
    空函数，用于占位
    :param args:
    :param kwargs:
    :return:
    """
    pass


def get_mac_address():
    """
    获取本机物理地址
    :return:
    """
    # import uuid
    # mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    # print(mac)
    # if mac == "ac675d19d986":
    #     # return mac
    #     return True
    # return mac
    return True


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as _e:
        print(_e)
        return False


def color_print(text, color: Literal["red", "green", "yellow", "blue", "magenta", "cyan", "white"] = "green"):
    """
    输出带颜色的文字
    :param text: 文字
    :param color: 颜色
    :return:
    """
    color_dict = {"red": 31, "green": 32, "yellow": 33, "blue": 34, "magenta": 35, "cyan": 36, "white": 37}
    print(f"\033[{color_dict[color]}m{text}\033[0m")
