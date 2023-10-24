# -*- coding: utf-8 -*-
"""
定义命令历史类
"""
import copy
from typing import List, Union

from GL_plot.na_hull import (
    PartRelationMap as PRM, NAHull, NaHullXYLayer, NaHullXZLayer, NaHullLeftView,
    NAPart, NAPartNode, NAXYLayerNode, NAXZLayerNode, NALeftViewNode
)


class Memento:
    def __init__(self, part=True, xzLayer=True, xyLayer=True, leftView=True):
        """
        保存自己初始化时各类的状态
        """
        self.attributes_to_copy = [
            ("partRelationMap_basicMap", PRM.last_map.basicMap, True),
            ("partRelationMap_relationMap", PRM.last_map.relationMap, True),
            ("partRelationMap_DotsLayerMap", PRM.last_map.get_DotsLayerMap(), True),
            ("partRelationMap_PartsLayerMap", PRM.last_map.get_PartsLayerMap(), True),
            ("DrawMap", NAHull.current_in_design_tab.DrawMap, True),
            ("xzLayers", NAHull.current_in_design_tab.xzLayers, True),
            ("xyLayers", NAHull.current_in_design_tab.xyLayers, True),
            ("leftViews", NAHull.current_in_design_tab.leftViews, True),
            ("naHullXYLayer_id_map", NaHullXYLayer.id_map, False),
            ("naHullXZLayer_id_map", NaHullXZLayer.id_map, False),
            ("naHullLeftView_id_map", NaHullLeftView.id_map, False),
            ("naParts", [part for part in NAPart.hull_design_tab_id_map.values()], True),
            ("naPartNodes", [node for node in NAPartNode.id_map.values()], True),
            ("naXYLayerNodes", [node for node in NAXYLayerNode.id_map.values()], True),
            ("naXZLayerNodes", [node for node in NAXZLayerNode.id_map.values()], True),
            ("naLeftViewNodes", [node for node in NALeftViewNode.id_map.values()], True)
        ]

        for attr_name, source, use_deepcopy in self.attributes_to_copy:
            if use_deepcopy:
                setattr(self, attr_name, copy.deepcopy(source))
            else:
                setattr(self, attr_name, source)


def operating_control(func):
    """
    用于保护状态栈，防止多线程同时操作
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        if StateHistory.current.operating:
            return False
        StateHistory.current.operating = True
        execute = func(*args, **kwargs)
        StateHistory.current.operating = False
        return execute
    return wrapper


class StateHistory:
    current: Union["StateHistory", None] = None

    def __init__(self, show_statu_func):
        # 初始化一个定长的状态栈
        self.max_length = 10000
        self.stateStack: List[Union[Memento, "Operation", None]] = [None] * self.max_length
        self.current_index = None
        self.show_statu_func = show_statu_func
        self.operating = False
        StateHistory.current = self

    def init_stack(self):
        """
        初始化状态
        :return:
        """
        self.stateStack[0] = Memento()
        self.current_index = 0  # 当前状态的索引

    @operating_control
    def execute_operation(self, operation_obj):
        """
        执行命令后，保存状态
        :param operation_obj:
        :return:
        """
        operation_obj.execute()
        if self.current_index == self.max_length - 1:
            self.stateStack = self.stateStack[1:] + [operation_obj]
            self.show_statu_func("操作栈已满", "warning")
        else:
            self.current_index += 1
            self.stateStack[self.current_index] = operation_obj
            self.show_statu_func(f"{operation_obj.name}\t{self.current_index + 1}", "process")

    @operating_control
    def execute(self):
        """
        执行命令后，保存状态
        :return:
        """
        if self.current_index == self.max_length - 1:
            self.stateStack = self.stateStack[1:] + [Memento()]
            self.show_statu_func("满栈", "warning")
        else:
            # 如果当前状态不是最后一个状态，说明是撤回后执行的命令，需要删除当前状态之后的所有状态
            if self.stateStack[self.current_index + 1] is not None:
                self.stateStack = self.stateStack[:self.current_index + 1] + [None] * (
                        self.max_length - self.current_index - 1)
            self.current_index += 1
            self.stateStack[self.current_index] = Memento()

    @operating_control
    def undo(self):
        """
        撤回到上一个状态
        """
        if self.current_index > 0:
            if not isinstance(self.stateStack[self.current_index], Memento):
                self.stateStack[self.current_index].undo()
                self.show_statu_func(f"Ctrl+Z 撤回 {self.stateStack[self.current_index].name}\t{self.current_index}", "process")
                self.current_index -= 1
            else:
                self.show_statu_func(f"Ctrl+Z 撤回 {self.current_index}", "process")
                self.current_index -= 1
                self.reset_information()
        else:
            self.show_statu_func("Ctrl+Z 没有更多的历史记录", "warning")

    @operating_control
    def redo(self):
        """
        重做命令
        """
        if self.current_index is not None and self.stateStack[self.current_index + 1] is not None:
            self.current_index += 1
            if isinstance(self.stateStack[self.current_index], Memento):
                self.reset_information()
                self.show_statu_func(f"Ctrl+Shift+Z 重做 {self.current_index + 1}", "process")
            else:
                self.stateStack[self.current_index].redo()
                self.show_statu_func(f"Ctrl+Shift+Z 重做 {self.stateStack[self.current_index].name}\t{self.current_index + 1}", "process")
        else:
            self.show_statu_func("Ctrl+Shift+Z 没有更多的历史记录", "warning")

    # 由于是动态绑定的，所以pycharm无法识别，但是实际上是存在的
    # noinspection PyUnresolvedReferences
    def reset_information(self):
        """
        重置所有类的信息
        :return:
        """
        memento_ = self.stateStack[self.current_index]
        if not isinstance(memento_, Memento):
            return
        PRM.last_map.basicMap = memento_.partRelationMap_basicMap
        PRM.last_map.relationMap = memento_.partRelationMap_relationMap
        PRM.last_map.xyDotsLayerMap, PRM.last_map.xzDotsLayerMap, PRM.last_map.yzDotsLayerMap = \
            memento_.partRelationMap_DotsLayerMap
        PRM.last_map.xyPartsLayerMap, PRM.last_map.xzPartsLayerMap, PRM.last_map.yzPartsLayerMap = \
            memento_.partRelationMap_PartsLayerMap
        NAHull.current_in_design_tab.DrawMap = memento_.DrawMap
        NAHull.current_in_design_tab.xzLayers = memento_.xzLayers
        NAHull.current_in_design_tab.xyLayers = memento_.xyLayers
        NAHull.current_in_design_tab.leftViews = memento_.leftViews
        NAPart.hull_design_tab_id_map = {id(part) % 4294967296: part for part in memento_.naParts}
        NAPartNode.id_map = {id(node) % 4294967296: node for node in memento_.naPartNodes}
        NAXYLayerNode.id_map = {id(node) % 4294967296: node for node in memento_.naXYLayerNodes}
        NAXZLayerNode.id_map = {id(node) % 4294967296: node for node in memento_.naXZLayerNodes}
        NALeftViewNode.id_map = {id(node) % 4294967296: node for node in memento_.naLeftViewNodes}


def push_global_statu(func):
    """
    装饰器，用于执行函数形式的命令后保存全局状态
    注意，这个功能并不被推荐，因为保存全局状态非常耗时，而且容易出错
    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        execute = func(*args, **kwargs)
        if execute is not False:
            StateHistory.current.execute()
        return execute

    return wrapper


def push_operation(func):
    """
    装饰器，用于获取操作对象，保存到操作栈中。
    :param func: 函数返回值必须为操作对象（基类为 Operation）或者 None
    :return:
    """

    def wrapper(*args, **kwargs):
        operation_obj = func(*args, **kwargs)
        if operation_obj:
            StateHistory.current.execute_operation(operation_obj)

    return wrapper
