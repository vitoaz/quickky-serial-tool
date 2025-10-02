"""
Quickky Serial Tool - 串口调试工具
应用程序启动入口

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.main_window import MainWindow
from utils.file_utils import get_base_path

# 导入版本信息
def get_version_info():
    """获取版本信息"""
    try:
        sys.path.insert(0, get_base_path())
        import version
        return version.VERSION, version.BUILD_TIME
    except:
        return "1.0.0", "未知"


def main():
    """主函数 - 应用程序入口点"""
    # 获取版本信息
    version, build_time = get_version_info()
    
    # 创建并启动主窗口
    app = MainWindow(version=version, build_time=build_time)
    app.mainloop()


if __name__ == '__main__':
    main()