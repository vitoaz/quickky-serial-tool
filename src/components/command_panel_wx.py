"""
命令面板 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
from .quick_commands_panel_wx import QuickCommandsPanel
from .send_history_panel_wx import SendHistoryPanel
from utils.custom_controls_wx import ThemedNotebook


class CommandPanel(wx.Panel):
    """命令面板 - 包含快捷指令和历史发送"""
    
    def __init__(self, parent, config_manager, main_window=None):
        """初始化命令面板"""
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.main_window = main_window
        
        self.SetMinSize((250, -1))
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 使用ThemedNotebook创建Tab页
        self.notebook = ThemedNotebook(self)
        
        # 快捷指令面板
        self.quick_commands_panel = QuickCommandsPanel(
            self.notebook,
            self.config_manager,
            main_window=self.main_window
        )
        self.notebook.AddPage(self.quick_commands_panel, '快捷指令')
        
        # 历史发送面板
        self.send_history_panel = SendHistoryPanel(
            self.notebook,
            self.config_manager,
            main_window=self.main_window
        )
        self.notebook.AddPage(self.send_history_panel, '历史发送')
        
        # 创建sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def refresh_history(self):
        """刷新历史发送面板"""
        if hasattr(self.send_history_panel, 'refresh'):
            self.send_history_panel.refresh()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        # 设置命令面板自身的背景色
        if theme_manager:
            colors = theme_manager.get_theme_colors()
            bg_color = theme_manager.hex_to_wx_colour(colors.get('background', '#FFFFFF'))
            fg_color = theme_manager.hex_to_wx_colour(colors.get('foreground', '#000000'))
            self.SetBackgroundColour(bg_color)
            
            # 应用主题到ThemedNotebook
            if hasattr(self.notebook, 'apply_theme'):
                self.notebook.apply_theme(bg_color, fg_color)
        
        if hasattr(self.quick_commands_panel, 'apply_theme'):
            self.quick_commands_panel.apply_theme(theme_manager)
        if hasattr(self.send_history_panel, 'apply_theme'):
            self.send_history_panel.apply_theme(theme_manager)

