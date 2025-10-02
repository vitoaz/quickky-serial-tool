"""
对话框工具类

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk


class DialogUtils:
    """对话框工具类"""
    
    @staticmethod
    def center_dialog(dialog, parent, width=None, height=None):
        """
        将对话框居中显示在父窗口中
        
        Args:
            dialog: 对话框窗口
            parent: 父窗口
            width: 对话框宽度（可选，不指定则使用实际宽度）
            height: 对话框高度（可选，不指定则使用实际高度）
        """
        # 如果没有指定尺寸，使用默认尺寸避免闪烁
        if width is None:
            width = 400
        if height is None:
            height = 300
        
        # 获取父窗口位置和尺寸
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # 确保对话框不会超出屏幕边界
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        
        if x < 0:
            x = 0
        elif x + width > screen_width:
            x = screen_width - width
            
        if y < 0:
            y = 0
        elif y + height > screen_height:
            y = screen_height - height
        
        # 设置对话框位置和大小
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    @staticmethod
    def show_modal_dialog(dialog, parent, width=None, height=None):
        """
        显示模态对话框
        
        Args:
            dialog: 对话框窗口
            parent: 父窗口
            width: 对话框宽度（可选）
            height: 对话框高度（可选）
        """
        # 居中显示
        DialogUtils.center_dialog(dialog, parent, width, height)
        
        # 显示窗口并设置模态
        dialog.deiconify()
        dialog.grab_set()
        
        # 在窗口显示后应用标题栏主题
        if hasattr(dialog, 'theme_manager') and dialog.theme_manager:
            dialog.after(10, lambda: dialog.theme_manager.apply_titlebar_theme(dialog))