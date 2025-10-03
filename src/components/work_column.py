"""
工作栏目组件 - 管理单个栏目的notebook和tab

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk

from .work_tab import WorkTab


class WorkColumn(tk.Frame):
    """工作栏目 - 管理单个栏目（主栏/副栏）"""
    
    def __init__(self, parent, config_manager, theme_manager, column_type='main', 
                 on_column_activated=None, on_tab_data_sent=None):
        """
        初始化工作栏目
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            theme_manager: 主题管理器
            column_type: 栏目类型 ('main' 或 'secondary')
            on_column_activated: 栏目激活回调
            on_tab_data_sent: Tab数据发送回调
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.column_type = column_type
        self.on_column_activated = on_column_activated
        self.on_tab_data_sent = on_tab_data_sent
        
        # Tab计数器
        self.tab_counter = 1
        
        # 工作Tab列表
        self.work_tabs = []
        
        # 是否激活状态
        self.is_active = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 顶部边框（4px）- 用于激活状态指示
        self.top_border = tk.Frame(self, height=4)
        self.top_border.pack(fill='x', side='top')
        
        # 主面板
        self.main_panel = tk.Frame(self, bg='white')
        self.main_panel.pack(fill='both', expand=True)
        
        # 绑定点击事件
        self.bind('<Button-1>', self._on_click)
        self.main_panel.bind('<Button-1>', self._on_click)
        
        # 创建notebook
        self.notebook = self._create_notebook()
    
    def _create_notebook(self):
        """创建notebook控件"""
        notebook = ttk.Notebook(self.main_panel)
        notebook.pack(fill='both', expand=True)
        
        # 绑定事件
        notebook.bind('<Button-1>', self._on_click)
        notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        notebook.bind('<Double-Button-1>', self._on_double_click)
        notebook.bind('<Button-2>', self._on_middle_click)
        notebook.bind('<Button-3>', self._on_right_click)
        
        # 创建加号Tab（作为占位符）
        add_tab_placeholder = ttk.Frame(notebook)
        notebook.add(add_tab_placeholder, text='+')
        
        return notebook
    
    def _on_click(self, event=None):
        """点击事件处理"""
        if self.on_column_activated:
            self.on_column_activated(self)
    
    def _on_tab_changed(self, event):
        """Tab切换事件处理"""
        # 激活当前栏目
        self._on_click()
        
        # 获取当前选中的Tab索引
        current_index = self.notebook.index('current')
        
        # 如果点击的是加号Tab（最后一个）
        if current_index == self.notebook.index('end') - 1:
            # 计算该notebook当前有多少个普通Tab（不含加号）
            tab_count = self.notebook.index('end') - 1
            
            # 只有在已经有Tab的情况下才允许创建新Tab
            if tab_count > 0:
                self.add_work_tab()
    
    def _on_double_click(self, event):
        """双击Tab关闭"""
        try:
            clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                tab_widget = self.notebook.nametowidget(self.notebook.tabs()[index])
                self._close_tab_widget(tab_widget)
        except:
            pass
    
    def _on_middle_click(self, event):
        """鼠标中键点击关闭Tab"""
        try:
            clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                tab_widget = self.notebook.nametowidget(self.notebook.tabs()[index])
                self._close_tab_widget(tab_widget)
        except:
            pass
    
    def _on_right_click(self, event):
        """右键菜单"""
        try:
            clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                tab_widget = self.notebook.nametowidget(self.notebook.tabs()[index])
                
                # 显示菜单
                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label='关闭', command=lambda: self._close_tab_widget(tab_widget))
                menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def add_work_tab(self, is_first_tab=False):
        """添加工作Tab"""
        tab_name = 'New Tab'
        
        # 创建工作Tab
        work_tab = WorkTab(
            self.notebook, 
            self.config_manager, 
            tab_name, 
            is_first_tab,
            on_widget_click=self._on_work_tab_click,
            on_data_sent=self.on_tab_data_sent,
            panel_type=self.column_type
        )
        
        # 在加号Tab之前插入新Tab
        insert_index = self.notebook.index('end') - 1
        self.notebook.insert(insert_index, work_tab, text=tab_name)
        
        self.work_tabs.append(work_tab)
        self.tab_counter += 1
        
        # 切换到新Tab
        self.notebook.select(insert_index)
        
        # 如果主题已加载，应用主题到新Tab
        if self.theme_manager and self.theme_manager.current_theme:
            font_size = self.config_manager.get_font_size()
            # 延迟应用主题，确保控件已完全创建
            self.after(10, lambda: work_tab.apply_theme(self.theme_manager, font_size))
        
        return work_tab
    
    def _on_work_tab_click(self, work_tab):
        """工作Tab内部控件点击事件"""
        # 激活当前栏目
        self._on_click()
    
    def _close_tab_widget(self, tab_widget):
        """关闭指定的Tab widget"""
        # 检查是否是加号Tab
        if tab_widget not in self.work_tabs:
            return
        
        # 每个栏至少保留一个Tab
        if len(self.work_tabs) <= 1:
            return
        
        # 清理Tab资源（包括串口连接、定时器等）
        if hasattr(tab_widget, 'cleanup'):
            tab_widget.cleanup()
        
        # 获取Tab在notebook中的索引
        try:
            tab_index = self.notebook.index(tab_widget)
        except:
            return
        
        # 计算删除后还剩多少Tab（不包括加号Tab）
        remaining_count = len(self.work_tabs) - 1
        
        # 先选中其他Tab，避免自动选中"+"Tab
        if remaining_count > 0:
            new_index = min(tab_index, remaining_count - 1)
            self.notebook.select(new_index)
        
        # 从work_tabs列表中移除
        if tab_widget in self.work_tabs:
            self.work_tabs.remove(tab_widget)
        
        # 最后删除Tab并销毁widget
        self.notebook.forget(tab_index)
        tab_widget.destroy()  # 确保widget被销毁
    
    def get_current_tab(self):
        """获取当前选中的工作Tab"""
        try:
            current_index = self.notebook.index('current')
            
            # 获取该Tab的widget
            if current_index < self.notebook.index('end') - 1:  # 不是加号Tab
                tab_widget = self.notebook.nametowidget(self.notebook.tabs()[current_index])
                if tab_widget in self.work_tabs:
                    return tab_widget
            
            return None
        except:
            return None
    
    def get_all_tabs(self):
        """获取所有工作Tab"""
        return self.work_tabs.copy()
    
    def has_tabs(self):
        """检查是否有工作Tab"""
        return len(self.work_tabs) > 0
    
    def close_all_tabs(self):
        """关闭所有Tab"""
        # 关闭所有串口连接
        for tab in self.work_tabs:
            if hasattr(tab, 'serial_manager') and tab.serial_manager.is_open():
                tab._disconnect()
        
        # 清空Tab列表
        self.work_tabs.clear()
        
        # 清空notebook所有Tab（除了加号Tab）
        tab_count = self.notebook.index('end') - 1
        for i in range(tab_count - 1, -1, -1):
            try:
                self.notebook.forget(i)
            except:
                pass
    
    def set_active(self, active):
        """设置激活状态"""
        self.is_active = active
        self._update_border_highlight()
    
    def _update_border_highlight(self):
        """更新边框高亮显示"""
        if hasattr(self, 'theme_manager') and self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            bg_color = colors.get('labelframe_bg', '#F5F5F5')
            active_color = colors.get('active_border', '#4A90E2')
        else:
            bg_color = '#F5F5F5'
            active_color = '#4A90E2'
        
        # 根据激活状态设置边框颜色
        border_color = active_color if self.is_active else bg_color
        self.top_border.config(bg=border_color)
    
    def apply_theme(self):
        """应用主题"""
        if not self.theme_manager:
            return
            
        colors = self.theme_manager.get_theme_colors()
        
        if not colors:
            return
        
        try:
            # 应用到主面板
            self.main_panel.configure(bg=colors.get('background', '#FFFFFF'))
            
            # 更新边框颜色
            self._update_border_highlight()
            
            # 应用到所有工作Tab
            font_size = self.config_manager.get_font_size()
            for work_tab in self.work_tabs:
                if hasattr(work_tab, 'apply_theme'):
                    work_tab.apply_theme(self.theme_manager, font_size)
            
        except Exception as e:
            print(f"应用栏目主题失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        for work_tab in self.work_tabs:
            if hasattr(work_tab, 'cleanup'):
                work_tab.cleanup()
