"""
历史发送面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from utils.custom_dialogs import ConfirmDialog

class SendHistoryPanel(ttk.Frame):
    """历史发送面板"""
    
    def __init__(self, parent, config_manager, main_window=None):
        """
        初始化历史发送面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            main_window: 主窗口引用
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.main_window = main_window
        
        self._create_widgets()
        self._load_history()
    
    def _create_widgets(self):
        """创建控件"""
        # 列表
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建Treeview（显示时间、模式、数据）
        self.tree = ttk.Treeview(list_frame, columns=('time', 'mode', 'data'), show='headings', height=15)
        self.tree.heading('time', text='时间')
        self.tree.heading('mode', text='模式')
        self.tree.heading('data', text='数据')
        self.tree.column('time', width=125, minwidth=100)
        self.tree.column('mode', width=32, minwidth=32)
        self.tree.column('data', width=80, minwidth=60)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 双击发送
        self.tree.bind('<Double-Button-1>', self._on_double_click)
        
        # 右键菜单
        self.tree.bind('<Button-3>', self._show_menu)
    
    def _load_history(self):
        """加载发送历史"""
        self.tree.delete(*self.tree.get_children())
        history = self.config_manager.get_send_history()
        
        for item in history:
            # 兼容旧格式（字符串）和新格式（字典）
            if isinstance(item, str):
                # 旧格式：只有数据
                time_str = ''
                mode = 'TEXT'
                data = item
            else:
                # 新格式：包含时间、模式、数据
                time_str = item.get('time', '')
                mode = item.get('mode', 'TEXT')
                data = item.get('data', '')
            
            # 限制显示长度
            display_data = data.replace('\n', '\\n')
            if len(display_data) > 50:
                display_data = display_data[:50] + '...'
            
            self.tree.insert('', 'end', values=(time_str, mode, display_data), 
                           tags=(mode, data))  # 将完整数据保存在tags中
    
    def _show_menu(self, event):
        """显示右键菜单"""
        menu = tk.Menu(self, tearoff=0)
        
        # 检查是否点击在项目上
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu.add_command(label='发送', command=self._send_selected)
            menu.add_separator()
        
        menu.add_command(label='清空历史', command=self._clear_history)
        menu.post(event.x_root, event.y_root)
    
    def _clear_history(self):
        """清空历史"""
        theme_manager = self.main_window.theme_manager if self.main_window else None
        if ConfirmDialog.ask_yes_no(self.winfo_toplevel(), '确认', 
                                   '确定要清空所有发送历史吗？', theme_manager):
            self.config_manager.clear_send_history()
            self._load_history()
    
    def _send_selected(self):
        """发送选中的历史记录"""
        selection = self.tree.selection()
        if selection and self.main_window:
            item = self.tree.item(selection[0])
            values = item['values']
            tags = item['tags']
            
            mode = values[1]      # 模式在第2列
            data = tags[1]        # 完整数据保存在tags中
            
            # 直接通过主窗口发送
            self._send_from_history(data, mode)
    
    def _on_double_click(self, event):
        """双击发送"""
        selection = self.tree.selection()
        if selection and self.main_window:
            item = self.tree.item(selection[0])
            values = item['values']
            tags = item['tags']
            
            mode = values[1]      # 模式在第2列
            data = tags[1]        # 完整数据保存在tags中
            
            # 直接通过主窗口发送
            self._send_from_history(data, mode)
    
    def _send_from_history(self, data, mode):
        """从历史发送"""
        if not self.main_window:
            return
            
        # 通过工作面板发送
        if self.main_window.work_panel.send_data(data, mode):
            # 刷新历史发送面板
            if hasattr(self.main_window, 'command_panel'):
                self.main_window.command_panel.refresh_history()
    
    def refresh(self):
        """刷新历史列表"""
        self._load_history()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        # Treeview等ttk控件的主题需要通过ttk.Style来设置
        # 这里暂时保留接口，未来可以扩展
        pass

