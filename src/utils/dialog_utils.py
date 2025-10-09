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
        将对话框居中显示在父窗口中（支持多显示器）
        
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
        
        # 更新父窗口信息，确保获取最新位置
        parent.update_idletasks()
        
        # 获取父窗口位置和尺寸
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # 计算对话框在父窗口中的居中位置（使用父窗口的绝对坐标）
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # 设置对话框位置和大小（使用绝对坐标）
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
        
        # 设置窗口完全透明
        dialog.withdraw()
        dialog.attributes('-alpha', 0.0)

        # 应用标题栏主题（在显示之前）
        if hasattr(dialog, 'theme_manager') and dialog.theme_manager:
            dialog.theme_manager.apply_titlebar_theme(dialog)
        
        # 居中显示窗口
        DialogUtils.center_dialog(dialog, parent, width, height)
        
        # 显示窗口（透明状态）
        dialog.deiconify()
        
        # 强制完成所有布局和渲染任务
        dialog.update_idletasks()
        dialog.update()
        
        # 恢复窗口不透明
        dialog.attributes('-alpha', 1.0)
        dialog.grab_set()
        