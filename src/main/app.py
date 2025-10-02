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


def main():
    """主函数 - 应用程序入口点"""
    # 创建并启动主窗口
    app = MainWindow()
    app.mainloop()


if __name__ == '__main__':
    main()