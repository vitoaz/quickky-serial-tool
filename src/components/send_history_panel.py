"""
历史发送面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk

class SendHistoryPanel(ttk.Frame):
    """历史发送面板"""
    
    def __init__(self, parent, config_manager, on_send_callback=None):
        """
        初始化历史发送面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_send_callback: 发送回调函数
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.on_send_callback = on_send_callback
        
        self._create_widgets()
        self._load_history()
    
    def _create_widgets(self):
        """创建控件"""
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(toolbar, text='搜索:').pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side='left', padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_search)
        
        ttk.Button(toolbar, text='清空历史', command=self._clear_history, width=10).pack(side='right', padx=5)
        
        # 列表
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建Listbox
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 双击发送
        self.listbox.bind('<Double-Button-1>', self._on_double_click)
    
    def _load_history(self, filter_text=''):
        """加载发送历史"""
        self.listbox.delete(0, 'end')
        history = self.config_manager.get_send_history()
        
        for item in history:
            if filter_text.lower() in item.lower():
                # 限制显示长度
                display_text = item.replace('\n', '\\n')
                if len(display_text) > 60:
                    display_text = display_text[:60] + '...'
                self.listbox.insert('end', display_text)
    
    def _on_search(self, event=None):
        """搜索"""
        filter_text = self.search_var.get()
        self._load_history(filter_text)
    
    def _clear_history(self):
        """清空历史"""
        from tkinter import messagebox
        if messagebox.askyesno('确认', '确定要清空所有发送历史吗？'):
            self.config_manager.config['send_history'] = []
            self.config_manager.save_config()
            self._load_history()
    
    def _on_double_click(self, event):
        """双击发送"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            history = self.config_manager.get_send_history()
            
            # 考虑搜索过滤
            filter_text = self.search_var.get()
            if filter_text:
                filtered_history = [item for item in history if filter_text.lower() in item.lower()]
                data = filtered_history[index]
            else:
                data = history[index]
            
            if self.on_send_callback:
                self.on_send_callback(data)
    
    def refresh(self):
        """刷新历史列表"""
        self._load_history(self.search_var.get())

