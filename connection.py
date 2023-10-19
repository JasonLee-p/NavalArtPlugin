# -*- coding: utf-8 -*-
"""
"""

import requests

from bs4 import BeautifulSoup


def check_web_connection(func):
    """
    检查网络连接
    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        try:
            response = requests.get("https://www.baidu.com")
            if response.status_code == 200:
                return func(*args, **kwargs)
            else:
                return False
        except:
            return False
    return wrapper


def extract_number_from_version(string) -> int:
    """
    提取字符串中的数字
    :param string:
    :return:
    """
    temp = ""
    for char in string:
        if char in "0123456789":
            temp += char
    return int(temp)


class Connection:
    """
    连接类
    """
    history = {}  # time: (request, response)

    @classmethod
    @check_web_connection
    def get_latest_version(cls):
        """
        检查版本
        """
        tar = "http://naval_plugins.e.cn.vc/release"
        response = requests.get(tar)
        links = {}  # version: link

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找所有的链接标签
            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    # 寻找域名最后域名为naplugin{year}_{month}_{day}的链接
                    if href.split("/")[-1].startswith("naplugin") and href.split("//")[0] == "http:":
                        r = requests.get(href)
                        if r.status_code == 200:
                            s = BeautifulSoup(r.text, 'html.parser')
                            # 寻找所有的下载链接
                            for link_ in s.find_all('a'):
                                href_ = link_.get('href')
                                if href_ and href_.endswith("NavalArtHullEditor.exe"):
                                    # 获取倒数第二个域名
                                    version = href_.split("/")[-2]
                                    links[version] = (href, href_)
            # 根据版本号找到最新版本（版本号格式为：不定数量字母+x.x.x.x）
            latest_version = list(links.keys())[0]
            for version in links:
                if extract_number_from_version(version) > extract_number_from_version(latest_version):
                    latest_version = version
            return latest_version, links[latest_version]
        else:
            return None, None
