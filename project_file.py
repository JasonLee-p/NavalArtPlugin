"""

"""
import json
import os
import time

from PyQt5.QtWidgets import QMessageBox
from path_utils import find_na_root_path


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
            raise ValueError(f"operation_mode must be in {ProjectFile._available_modes}")
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
