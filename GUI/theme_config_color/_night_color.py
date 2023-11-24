from PySide2.QtGui import QColor


class ThemeColor:
    def __init__(self, color: str):
        self.color = color

    def __str__(self):
        return self.color

    def __repr__(self):
        return self.color

    @property
    def rgb(self):
        if self.color[0] == '#':
            return int(self.color[1:3], 16), int(self.color[3:5], 16), int(self.color[5:7], 16)
        else:
            # 是一个颜色名，例如：'red'
            return QColor(self.color).getRgb()[:3]


THEME: str = 'night'
BG_COLOR0 = ThemeColor('#222324')
BG_COLOR1 = ThemeColor('#333434')
BG_COLOR2 = ThemeColor('#555657')
BG_COLOR3 = ThemeColor('#666789')
FG_COLOR0 = ThemeColor('#f0f0f0')
FG_COLOR1 = ThemeColor('#ffaaaa')

GLTheme = {
    "背景": (0.1, 0.1, 0.1, 1),
    "主光源": [(0.4, 0.4, 0.4, 1.0), (0.55, 0.55, 0.55, 1.0), (0.45, 0.47, 0.47, 1.0)],
    "辅助光": [(0.3, 0.3, 0.3, 1.0), (0.3, 0.3, 0.3, 1.0), (0.3, 0.3, 0.3, 1.0)],
    "选择框": [(1, 1, 1, 1)],
    "被选中": [(0.0, 0.7, 0.7, 1)],
    "橙色": [(1, 0.9, 0.5, 1.0)],
    "节点": [(0.0, 0.8, 0.8, 1)],
    "线框": [(0.7, 0.7, 0.7, 0.6), (0.2, 0.25, 0.3, 0.6), (0.2, 0.25, 0.3, 0.5), (0,)],
    "水线": [(0.0, 0.7, 0.7, 0.6), (0.3, 0.4, 0.5, 0.6), (0.2, 0.25, 0.3, 0.2), (50,)],
    "钢铁": [(0.4, 0.4, 0.4, 1.0)],
    "半透明": [(1, 1, 1, 0.15)],
    "甲板": [(0.46, 0.43, 0.39, 1.0), (0.15, 0.17, 0.17, 1.0), (0, 0, 0, 0.2), (0,)],
    "海面": [(0.3, 0.6, 0.7, 0.7)],
    "海底": [(0.09, 0.08, 0.05, 1)],
    "光源": [(1.0, 1.0, 1.0, 1.0)]
}
