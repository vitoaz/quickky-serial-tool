"""
工作面板组件 - 管理整个工作区域和双栏模式

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk

from .work_column import WorkColumn
from utils.ttk_paned_window_minisize import ttk_panedwindow_minsize


class WorkPanel(ttk.Frame):
    """工作面板 - 管理工作区域和双栏模式"""
    
    def __init__(self, parent, config_manager, theme_manager, on_tab_data_sent=None):
        """
        初始化工作面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            theme_manager: 主题管理器
            on_tab_data_sent: Tab数据发送回调
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.on_tab_data_sent = on_tab_data_sent
        
        # 双栏模式状态
        self.dual_panel_mode = self.config_manager.get_dual_panel_mode()
        
        # 当前激活的栏目
        self.active_column = None
        
        # 工作栏目列表
        self.work_columns = []
        
        self._create_widgets()
        self._create_initial_tabs()
    
    def _create_widgets(self):
        """创建控件"""
        # 创建工作区域的PanedWindow（始终存在）
        self.work_paned = ttk.PanedWindow(self, orient='horizontal')
        self.work_paned.pack(fill='both', expand=True)
        
        # 创建工作区域的最小尺寸管理器
        self.minsize_manager = ttk_panedwindow_minsize(self.work_paned, 'horizontal')
        
        # 创建主栏（始终存在）
        self.main_column = WorkColumn(
            self.work_paned, 
            self.config_manager, 
            self.theme_manager,
            column_type='main',
            on_column_activated=self._on_column_activated,
            on_tab_data_sent=self.on_tab_data_sent
        )
        self.minsize_manager.add_panel(self.main_column, min_size=400, weight=1)
        self.work_columns.append(self.main_column)
        
        # 创建副栏
        self.secondary_column = WorkColumn(
            self.work_paned,
            self.config_manager,
            self.theme_manager, 
            column_type='secondary',
            on_column_activated=self._on_column_activated,
            on_tab_data_sent=self.on_tab_data_sent
        )
        self.work_columns.append(self.secondary_column)
        
        # 根据配置决定是否显示副栏
        if self.dual_panel_mode:
            self.minsize_manager.add_panel(self.secondary_column, min_size=400, weight=1)
        
        # 设置主栏为默认激活
        self.active_column = self.main_column
        self._update_column_highlight()
    
    def _create_initial_tabs(self):
        """创建初始Tab"""
        # 主栏创建第一个Tab
        self.main_column.add_work_tab(is_first_tab=True)
        
        # 如果是双栏模式，副栏也创建一个Tab
        if self.dual_panel_mode:
            self.secondary_column.add_work_tab(is_first_tab=True)
    
    def _on_column_activated(self, column):
        """栏目激活回调"""
        self.active_column = column
        self._update_column_highlight()
    
    def _update_column_highlight(self):
        """更新栏目高亮显示"""
        # 更新所有栏目的激活状态
        for column in self.work_columns:
            is_active = (column == self.active_column)
            column.set_active(is_active and self.dual_panel_mode)
    
    def toggle_dual_panel_mode(self, enabled):
        """切换双栏模式"""
        self.dual_panel_mode = enabled
        
        if enabled:
            # 切换到双栏：显示副栏
            self.minsize_manager.add_panel(self.secondary_column, min_size=400, weight=1)
            
            # 检查副栏是否有Tab，如果没有则创建一个
            if not self.secondary_column.has_tabs():
                self.secondary_column.add_work_tab(is_first_tab=True)
            
            # 更新高亮显示
            self._update_column_highlight()
        else:
            # 取消双栏：隐藏副栏并清理Tab
            self.secondary_column.close_all_tabs()
            self.minsize_manager.remove_panel(self.secondary_column)
            
            # 确保主栏为激活状态
            self.active_column = self.main_column
            self._update_column_highlight()
    
    def get_current_work_tab(self):
        """获取当前激活的工作Tab"""
        if self.active_column:
            return self.active_column.get_current_tab()
        return None
    
    def get_all_work_tabs(self):
        """获取所有工作Tab"""
        all_tabs = []
        for column in self.work_columns:
            all_tabs.extend(column.get_all_tabs())
        return all_tabs
    
    def apply_theme(self):
        """应用主题"""
        # 应用到所有栏目
        for column in self.work_columns:
            column.apply_theme()
        
        # 更新高亮显示
        self._update_column_highlight()
    
    def cleanup(self):
        """清理资源"""
        for column in self.work_columns:
            column.cleanup()
