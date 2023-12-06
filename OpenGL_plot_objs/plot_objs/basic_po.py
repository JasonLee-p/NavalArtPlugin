# -*- coding: utf-8 -*-
"""
定义基础的OpenGL绘制对象，采用4.6核心模式
"""
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import c_void_p
from OpenGL.arrays import vbo
from OpenGL.raw.GL.VERSION.GL_2_0 import glEnableVertexAttribArray

from funcs_utils import color_print, bool_protection, CONST


class PlotObj:
    def __init__(self):
        self.pos = np.array([0, 0, 0], dtype=np.float32)
        self.color = np.array([127, 127, 127, 255], dtype=np.uint8)
        self.vertices_with_normal = None
        self.indices = None
        self.vbo = None
        # 状态量
        self.is_updating = False

    @bool_protection("is_updating")
    def draw(self):
        if self.vertices_with_normal is None or self.indices is None:
            color_print("[ERROR] 顶点或索引未初始化", "red")
            return
        # 绑定顶点缓冲区
        self.vertices_with_normal.bind()
        # 绑定索引缓冲区
        self.indices.bind()
        # 启用顶点属性
        glEnableVertexAttribArray(0)
        # 设置顶点属性指针
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * 4, None)
        # 启用法线属性
        glEnableVertexAttribArray(1)
        # 设置法线属性指针
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * 4, c_void_p(3 * 4))
        # 设置模型矩阵
        # 绘制
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_INT, None)
        # 解绑
        self.vertices_with_normal.unbind()
        self.indices.unbind()

    @bool_protection("is_updating")
    def update(self, vertices: np.ndarray, indices: np.ndarray):
        """
        更新顶点和索引
        :param vertices: np.float32
        :param indices: np.int
        :return:
        """
        self.vertices_with_normal = vbo.VBO(vertices)
        self.indices = vbo.VBO(indices, target=GL_ELEMENT_ARRAY_BUFFER)

    def move(self, offset: np.ndarray, target_pos: np.ndarray = None):
        """
        移动
        :param offset:
        :param target_pos:
        :return:
        """
        if target_pos is not None:
            self.pos = target_pos
        else:
            self.pos += offset
        vertices = self.vertices_with_normal.data.reshape(-1, 6)
        vertices[:, :3] += offset
        self.update(vertices, self.indices.data)


class Cube(PlotObj):
    def __init__(self, pos: np.ndarray, size: np.ndarray, color: np.ndarray = np.array([127, 127, 127, 255])):
        super().__init__()
        self.pos = pos
        self.size = size  # [x, y, z]
        self.half_size = size / 2
        self.color = color
        vertices_with_normal, indices = self.get_cube_vertices()
        self.update(vertices_with_normal, indices)

    def get_cube_vertices(self):
        """
        获取立方体的顶点和索引
        :return:
        """
        p = self.pos
        hs = self.half_size
        cube_vertices = {CONST.FRONT_UP_LEFT: np.array([p[0] - hs[0], p[1] + hs[1], p[2] + hs[2]]),
                         CONST.FRONT_UP_RIGHT: np.array([p[0] + hs[0], p[1] + hs[1], p[2] + hs[2]]),
                         CONST.FRONT_DOWN_LEFT: np.array([p[0] - hs[0], p[1] - hs[1], p[2] + hs[2]]),
                         CONST.FRONT_DOWN_RIGHT: np.array([p[0] + hs[0], p[1] - hs[1], p[2] + hs[2]]),
                         CONST.BACK_UP_LEFT: np.array([p[0] - hs[0], p[1] + hs[1], p[2] - hs[2]]),
                         CONST.BACK_UP_RIGHT: np.array([p[0] + hs[0], p[1] + hs[1], p[2] - hs[2]]),
                         CONST.BACK_DOWN_LEFT: np.array([p[0] - hs[0], p[1] - hs[1], p[2] - hs[2]]),
                         CONST.BACK_DOWN_RIGHT: np.array([p[0] + hs[0], p[1] - hs[1], p[2] - hs[2]])}
        # 顶点法线
        vertices_with_normal = np.array([
            # 前面
            *cube_vertices[CONST.FRONT_UP_LEFT], *CONST.FRONT_NORMAL,
            *cube_vertices[CONST.FRONT_UP_RIGHT], *CONST.FRONT_NORMAL,
            *cube_vertices[CONST.FRONT_DOWN_LEFT], *CONST.FRONT_NORMAL,
            *cube_vertices[CONST.FRONT_DOWN_RIGHT], *CONST.FRONT_NORMAL,
            # 后面
            *cube_vertices[CONST.BACK_UP_LEFT], *CONST.BACK_NORMAL,
            *cube_vertices[CONST.BACK_UP_RIGHT], *CONST.BACK_NORMAL,
            *cube_vertices[CONST.BACK_DOWN_LEFT], *CONST.BACK_NORMAL,
            *cube_vertices[CONST.BACK_DOWN_RIGHT], *CONST.BACK_NORMAL,
            # 左面
            *cube_vertices[CONST.BACK_UP_LEFT], *CONST.LEFT_NORMAL,
            *cube_vertices[CONST.FRONT_UP_LEFT], *CONST.LEFT_NORMAL,
            *cube_vertices[CONST.BACK_DOWN_LEFT], *CONST.LEFT_NORMAL,
            *cube_vertices[CONST.FRONT_DOWN_LEFT], *CONST.LEFT_NORMAL,
            # 右面
            *cube_vertices[CONST.BACK_UP_RIGHT], *CONST.RIGHT_NORMAL,
            *cube_vertices[CONST.FRONT_UP_RIGHT], *CONST.RIGHT_NORMAL,
            *cube_vertices[CONST.BACK_DOWN_RIGHT], *CONST.RIGHT_NORMAL,
            *cube_vertices[CONST.FRONT_DOWN_RIGHT], *CONST.RIGHT_NORMAL,
            # 上面
            *cube_vertices[CONST.BACK_UP_LEFT], *CONST.UP_NORMAL,
            *cube_vertices[CONST.BACK_UP_RIGHT], *CONST.UP_NORMAL,
            *cube_vertices[CONST.FRONT_UP_LEFT], *CONST.UP_NORMAL,
            *cube_vertices[CONST.FRONT_UP_RIGHT], *CONST.UP_NORMAL,
            # 下面
            *cube_vertices[CONST.BACK_DOWN_LEFT], *CONST.DOWN_NORMAL,
            *cube_vertices[CONST.BACK_DOWN_RIGHT], *CONST.DOWN_NORMAL,
            *cube_vertices[CONST.FRONT_DOWN_LEFT], *CONST.DOWN_NORMAL,
            *cube_vertices[CONST.FRONT_DOWN_RIGHT], *CONST.DOWN_NORMAL,
        ], dtype=np.float32)
        # 索引（逆时针序）
        indices = np.array([
            # 前面
            0, 1, 2, 1, 2, 3,
            # 后面
            4, 5, 6, 5, 6, 7,
            # 左面
            8, 9, 10, 9, 10, 11,
            # 右面
            12, 13, 14, 13, 14, 15,
            # 上面
            16, 17, 18, 17, 18, 19,
            # 下面
            20, 21, 22, 21, 22, 23
        ], dtype=np.uint32)
        return vertices_with_normal, indices

    def update_size(self, size: np.ndarray):
        self.size = size
        self.half_size = size / 2
        vertices_with_normal, indices = self.get_cube_vertices()
        self.update(vertices_with_normal, indices)
