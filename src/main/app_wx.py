"""
Quickky Serial Tool - 串口调试工具 (wxPython版本)
应用程序启动入口

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

import sys
import os
import wx

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.main_window_wx import MainWindow


def main():
    """主函数 - 应用程序入口点"""
    # 创建wxPython应用
    app = wx.App(False)
    
    # 创建主窗口
    frame = MainWindow(None)
    frame.Show(True)
    
    # 启动事件循环
    app.MainLoop()


if __name__ == '__main__':
    main()

