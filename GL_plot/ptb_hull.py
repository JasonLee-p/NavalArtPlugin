"""
定义了PTB物体的绘制对象
"""

from ship_reader import ReadPTB
from .basic import get_normal, SolidObject


class AdHull(ReadPTB, SolidObject):
    def __init__(self, path):
        ReadPTB.__init__(self, path)
        SolidObject.__init__(self, None)
        self.path = path
        self.obj = self.result['adHull']
        self.ShipName = self.obj.ShipName
        self.Position = self.obj.Position
        self.Dock = self.obj.Dock
        self.Rail = self.obj.Rail
        self.WaterLineHeight = self.obj.WaterLineHeight
        self.HullColor = self.obj.HullColor
        self.WaterLineColor = self.obj.WaterLineColor
        self.Slices = self.obj.Slices
        self.SlicesPoints = self.obj.SlicesPoints
        self.SlicesPoints_half = {}
        for key, value in self.SlicesPoints.items():
            # 切半，只保留左半边
            self.SlicesPoints_half[key] = value[:len(value) // 2]

        # SlicePoints 键值对是：分段名称 和 节点集合，其中节点先从前到后遍历左边再从前到后遍历右边，方向一致。
        self.lines = {}
        self.deck_dots = []
        self.height = 0
        self.get_deck_dots()  # 给self.deck_dots赋值
        self.faces = {
            "color": [0.5, 0.5, 0.5, 1],
            "normal": [],
            "faces": []
        }
        for i in range(len(self.SlicesPoints_half) - 1):  # 给self.faces赋值
            mode = "normal" if i < len(self.SlicesPoints_half) // 2 else "back"
            for t in self.obj.get_plot_triangles(
                    list(self.SlicesPoints_half.values())[i],
                    list(self.SlicesPoints_half.values())[i + 1],
                    mode=mode
            ):
                self.faces["faces"].append(t)
        self.center = self.get_center()  # 给self.center赋值
        self.faces["normal"] = []
        for face_ in self.faces["faces"]:
            self.faces["normal"].append(get_normal(*face_, self.center))  # 给self.faces["normal"]赋值

    def get_deck_dots(self):
        """
        根据self.SlicesPoints中的点集，生成self.lines中的线段集合
        """
        slice_num = len(self.SlicesPoints)
        # 生成线段
        for i in range(slice_num):
            node_set = list(self.SlicesPoints.values())[i]
            slice_node_num = len(node_set) // 2
            # 翻转node_set后一半的顺序
            node_set_transposed = node_set[:slice_node_num] + node_set[slice_node_num:][::-1]
            # 生成甲板
            self.deck_dots.append(node_set_transposed[-1])
            self.deck_dots.append(node_set_transposed[0])

    def draw(self, gl, material="钢铁", theme_color=None):
        gl.glLoadName(id(self) % 4294967296)
        super(AdHull, self).draw(gl, "钢铁", theme_color)
        self.draw_deck(gl, theme_color)  # 绘制甲板
        # self.draw_water_line(gl2_0, theme_color)  # 绘制水线

    def draw_water_line(self, gl, theme_color=None):
        water_line = self.obj.get_xz_from_y(self.WaterLineHeight * self.height / 3)
        # 现在water_line只有左侧点，需要补充右侧点
        new = []
        for i in range(len(water_line)):
            new.append((water_line[i][0], water_line[i][1]))
            new.append((-water_line[i][0], water_line[i][1]))
        # 现在water_line只有x和z，需要补充y
        for i in range(len(new)):
            new[i] = (new[i][0], self.WaterLineHeight * self.height / 3, new[i][1])
        # 绘制水线
        gl.glLineWidth(1)
        gl.glColor3f(0.5, 0.5, 0.5)
        mt = "水线"
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[mt][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[mt][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[mt][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[mt][3])
        gl.glBegin(gl.GL_QUAD_STRIP)
        for dot in new:
            gl.glVertex3f(*dot)
        gl.glEnd()

    def draw_deck(self, gl, theme_color=None):
        gl.glLineWidth(1)
        gl.glColor3f(0.5, 0.5, 0.5)
        mt = "甲板"
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT, theme_color[mt][0])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_DIFFUSE, theme_color[mt][1])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, theme_color[mt][2])
        gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, theme_color[mt][3])
        gl.glNormal3f(0, 1, 0)
        gl.glBegin(gl.GL_QUAD_STRIP)
        for dot in self.deck_dots:
            gl.glVertex3f(*dot)
        gl.glEnd()

    def get_max_slices_node_num_and_height(self):
        """
        获取所有分段中节点数最多的分段的节点数
        """
        max_num = 0
        lowest_y = 0
        highest_y = 0
        for name, node_set in self.SlicesPoints.items():
            if len(node_set) > max_num:
                max_num = len(node_set)
            for node in node_set:
                if node[1] < lowest_y:
                    lowest_y = node[1]
                if node[1] > highest_y:
                    highest_y = node[1]
        return max_num, highest_y - lowest_y

    @staticmethod
    def transposePTB2NA(SlicesPoints):
        # PTB的前后是x，上下是y，左右是z，NA的前后是z，上下是y，左右是x
        for slice_name in SlicesPoints:
            for i in range(len(SlicesPoints[slice_name])):
                SlicesPoints[slice_name][i] = (SlicesPoints[slice_name][i][2],
                                               SlicesPoints[slice_name][i][1],
                                               SlicesPoints[slice_name][i][0])
        return SlicesPoints
