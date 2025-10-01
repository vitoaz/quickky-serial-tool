"""
发送设置面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk

class SendSettingsPanel(ttk.LabelFrame):
    """发送设置面板"""
    
    def __init__(self, parent, config_manager, on_change_callback=None):
        """
        初始化发送设置面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_change_callback: 配置变化回调函数
        """
        super().__init__(parent, text='发送设置', padding=(8, 5))
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        self.current_port = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 模式选择
        ttk.Label(self, text='模式:').grid(row=0, column=0, sticky='w', pady=2)
        
        mode_frame = ttk.Frame(self)
        mode_frame.grid(row=0, column=1, sticky='w', pady=2)
        
        self.mode_var = tk.StringVar(value='TEXT')
        ttk.Radiobutton(mode_frame, text='TEXT', variable=self.mode_var, 
                       value='TEXT', command=self._on_setting_changed).pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text='HEX', variable=self.mode_var, 
                       value='HEX', command=self._on_setting_changed).pack(side='left', padx=5)
        
        # 循环发送
        loop_frame = ttk.Frame(self)
        loop_frame.grid(row=1, column=0, columnspan=2, sticky='w', pady=2)
        
        self.loop_send_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(loop_frame, text='循环发送', 
                       variable=self.loop_send_var,
                       command=self._on_loop_changed).pack(side='left')
        
        ttk.Label(loop_frame, text='周期:').pack(side='left', padx=(10, 5))
        
        self.loop_period_var = tk.StringVar(value='1000')
        self.loop_period_entry = ttk.Entry(loop_frame, textvariable=self.loop_period_var, width=10)
        self.loop_period_entry.pack(side='left')
        self.loop_period_entry.config(state='disabled')
        self.loop_period_entry.bind('<KeyRelease>', self._on_setting_changed)
        
        ttk.Label(loop_frame, text='ms').pack(side='left', padx=(5, 0))
        
        self.columnconfigure(1, weight=1)
    
    def _on_loop_changed(self):
        """循环发送变化事件"""
        if self.loop_send_var.get():
            self.loop_period_entry.config(state='normal')
        else:
            self.loop_period_entry.config(state='disabled')
        
        self._on_setting_changed()
    
    def _on_setting_changed(self, event=None):
        """设置变化事件"""
        if self.current_port:
            settings = self.get_settings()
            self.config_manager.update_send_settings(self.current_port, settings)
            
            if self.on_change_callback:
                self.on_change_callback(settings)
    
    def get_settings(self):
        """获取当前设置"""
        try:
            loop_period = int(self.loop_period_var.get())
        except ValueError:
            loop_period = 1000
        
        return {
            'mode': self.mode_var.get(),
            'loop_send': self.loop_send_var.get(),
            'loop_period_ms': loop_period
        }
    
    def load_config(self, port, config):
        """加载配置"""
        self.current_port = port
        self.mode_var.set(config.get('mode', 'TEXT'))
        self.loop_send_var.set(config.get('loop_send', False))
        self.loop_period_var.set(str(config.get('loop_period_ms', 1000)))
        
        # 更新周期输入框状态
        if self.loop_send_var.get():
            self.loop_period_entry.config(state='normal')
        else:
            self.loop_period_entry.config(state='disabled')

