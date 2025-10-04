"""
自定义对话框类

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk
from .dialog_utils import DialogUtils


class ConfirmDialog(tk.Toplevel):
    """确认对话框"""
    
    def __init__(self, parent, title, message, theme_manager=None):
        super().__init__(parent)
        self.title(title)
        self.result = False
        self.theme_manager = theme_manager
        
        # 设置模态
        self.transient(parent)
        self.resizable(False, False)
        
        # 先隐藏窗口，避免闪烁
        self.withdraw()
        
        # 应用主题
        self._apply_theme()
        
        # 创建控件
        self._create_widgets(message)
        
    def _create_widgets(self, message):
        """创建控件"""
        # 主容器
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 消息标签
        message_label = ttk.Label(main_frame, text=message, wraplength=300)
        message_label.pack(pady=(0, 20))
        
        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        # 确定和取消按钮
        ttk.Button(button_frame, text='确定', command=self._on_yes, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text='取消', command=self._on_no, width=10).pack(side='left', padx=5)
        
        # 绑定ESC键
        self.bind('<Escape>', lambda e: self._on_no())
        
    def _apply_theme(self):
        """应用主题"""
        if self.theme_manager:
            # 应用窗口背景色
            bg_color = self.theme_manager.get_color('frame_bg', '#F5F5F5')
            self.configure(bg=bg_color)
    
    def _on_yes(self):
        """确定按钮"""
        self.result = True
        self.destroy()
    
    def _on_no(self):
        """取消按钮"""
        self.result = False
        self.destroy()
    
    @staticmethod
    def ask_yes_no(parent, title, message, theme_manager=None):
        """
        显示确认对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 确认消息
            theme_manager: 主题管理器
            
        Returns:
            bool: 用户选择结果
        """
        dialog = ConfirmDialog(parent, title, message, theme_manager)
        DialogUtils.show_modal_dialog(dialog, parent, 350, 150)
        dialog.wait_window()
        return dialog.result


class InfoDialog(tk.Toplevel):
    """信息对话框"""
    
    def __init__(self, parent, title, message, theme_manager=None):
        super().__init__(parent)
        self.title(title)
        self.theme_manager = theme_manager
        
        # 设置模态
        self.transient(parent)
        self.resizable(False, False)
        
        # 先隐藏窗口，避免闪烁
        self.withdraw()
        
        # 应用主题
        self._apply_theme()
        
        # 创建控件
        self._create_widgets(message)
        
    def _create_widgets(self, message):
        """创建控件"""
        # 主容器
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 消息标签
        message_label = ttk.Label(main_frame, text=message, wraplength=400, justify='left')
        message_label.pack(pady=(0, 20))
        
        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        # 确定按钮
        ok_button = ttk.Button(button_frame, text='确定', command=self.destroy, width=10)
        ok_button.pack()
        ok_button.focus()
        
        # 绑定ESC和回车键
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.destroy())
        
    def _apply_theme(self):
        """应用主题"""
        if self.theme_manager:
            # 应用窗口背景色
            bg_color = self.theme_manager.get_color('frame_bg', '#F5F5F5')
            self.configure(bg=bg_color)
    
    @staticmethod
    def show_info(parent, title, message, theme_manager=None):
        """
        显示信息对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            message: 信息内容
            theme_manager: 主题管理器
        """
        dialog = InfoDialog(parent, title, message, theme_manager)
        DialogUtils.show_modal_dialog(dialog, parent, 380, 320)
        dialog.wait_window()
