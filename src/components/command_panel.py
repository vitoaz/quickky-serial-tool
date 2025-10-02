"""
命令面板组件 - 管理右侧命令面板区域

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk

from .quick_commands_panel import QuickCommandsPanel
from .send_history_panel import SendHistoryPanel


class CommandPanel(ttk.Frame):
    """命令面板 - 管理快捷指令和历史发送"""
    
    def __init__(self, parent, config_manager, on_send_quick_command=None, on_send_from_history=None):
        """
        初始化命令面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_send_quick_command: 快捷指令发送回调
            on_send_from_history: 历史发送回调
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.on_send_quick_command = on_send_quick_command
        self.on_send_from_history = on_send_from_history
        
        # 设置固定宽度
        self.configure(width=280)
        self.pack_propagate(False)  # 防止子控件改变Frame大小
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 命令面板Notebook
        self.command_notebook = ttk.Notebook(self)
        self.command_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 快捷指令Tab
        self.quick_commands_panel = QuickCommandsPanel(
            self.command_notebook, 
            self.config_manager,
            on_send_callback=self.on_send_quick_command
        )
        self.command_notebook.add(self.quick_commands_panel, text='快捷指令')
        
        # 历史发送Tab
        self.send_history_panel = SendHistoryPanel(
            self.command_notebook,
            self.config_manager,
            on_send_callback=self.on_send_from_history
        )
        self.command_notebook.add(self.send_history_panel, text='历史发送')
        
        # 绑定Tab切换事件，用于刷新历史列表
        self.command_notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _on_tab_changed(self, event):
        """Tab切换事件处理"""
        # 获取当前选中的Tab索引
        current_index = self.command_notebook.index('current')
        # 如果切换到历史发送Tab
        if current_index == 1:  # 历史发送Tab的索引是1
            self.send_history_panel.refresh()
    
    def refresh_history(self):
        """刷新历史发送面板"""
        if hasattr(self, 'send_history_panel'):
            self.send_history_panel.refresh()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        try:
            # 应用到快捷指令面板
            if hasattr(self.quick_commands_panel, 'apply_theme'):
                self.quick_commands_panel.apply_theme(theme_manager)
            
            # 应用到历史发送面板
            if hasattr(self.send_history_panel, 'apply_theme'):
                self.send_history_panel.apply_theme(theme_manager)
                
        except Exception as e:
            print(f"命令面板主题应用失败: {e}")
    
    def get_width(self):
        """获取面板宽度"""
        return 280
    
    def get_min_width(self):
        """获取面板最小宽度"""
        return 250
