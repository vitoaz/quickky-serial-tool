"""
文件工具类

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import os
import sys


def resource_path(filename):
    """
    获取资源文件路径
    开发模式下用源码目录，打包后用 PyInstaller 的临时目录
    
    Args:
        filename (str): 资源文件名
        
    Returns:
        str: 资源文件的完整路径
    """
    if hasattr(sys, "_MEIPASS"):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, filename)
    
    # 开发模式下，从项目根目录获取
    # 当前文件在 src/utils/ 目录下，需要回到项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(project_root, filename)


def get_base_path():
    """
    获取应用程序基础路径
    
    Returns:
        str: 基础路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的exe环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境，返回项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(os.path.dirname(current_dir))
