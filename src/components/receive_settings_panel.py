"""
接收设置面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk

class ReceiveSettingsPanel(ttk.LabelFrame):
    """接收设置面板"""
    
    def __init__(self, parent, config_manager, on_change_callback=None, on_clear_callback=None, on_save_log_callback=None):
        """
        初始化接收设置面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_change_callback: 配置变化回调函数
            on_clear_callback: 清除接收回调函数
            on_save_log_callback: 保存日志勾选回调函数
        """
        super().__init__(parent, text='接收设置', padding=(8, 5))
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        self.on_clear_callback = on_clear_callback
        self.on_save_log_callback = on_save_log_callback
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
                       value='TEXT', command=self._on_mode_changed).pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text='HEX', variable=self.mode_var, 
                       value='HEX', command=self._on_mode_changed).pack(side='left', padx=5)
        
        # 编码选择
        ttk.Label(self, text='编码:').grid(row=1, column=0, sticky='w', pady=2)
        
        encoding_frame = ttk.Frame(self)
        encoding_frame.grid(row=1, column=1, sticky='w', pady=2)
        
        self.encoding_var = tk.StringVar(value='UTF-8')
        self.encoding_utf8_radio = ttk.Radiobutton(encoding_frame, text='UTF-8', 
                                                   variable=self.encoding_var, value='UTF-8',
                                                   command=self._on_setting_changed)
        self.encoding_utf8_radio.pack(side='left', padx=5)
        
        self.encoding_ascii_radio = ttk.Radiobutton(encoding_frame, text='ASCII', 
                                                    variable=self.encoding_var, value='ASCII',
                                                    command=self._on_setting_changed)
        self.encoding_ascii_radio.pack(side='left', padx=5)
        
        # 按日志模式显示
        self.log_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text='日志模式显示', 
                       variable=self.log_mode_var,
                       command=self._on_setting_changed).grid(row=2, column=0, columnspan=2, sticky='w', pady=2)
        
        # 保存日志
        self.save_log_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text='保存日志', 
                       variable=self.save_log_var,
                       command=self._on_save_log_changed).grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
        
        # 自动重连
        self.auto_reconnect_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text='自动重连', 
                       variable=self.auto_reconnect_var,
                       command=self._on_setting_changed).grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        
        # 自动滚屏
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text='自动滚屏', 
                       variable=self.auto_scroll_var,
                       command=self._on_setting_changed).grid(row=5, column=0, columnspan=2, sticky='w', pady=2)
        
        # 清除接收按钮
        clear_btn = tk.Label(self, text='清除接收', fg='blue', cursor='hand2', font=('', 9))
        clear_btn.grid(row=6, column=0, columnspan=2, sticky='w', pady=5)
        clear_btn.bind('<Button-1>', self._on_clear_clicked)
        clear_btn.bind('<Enter>', lambda e: clear_btn.config(font=('', 9, 'underline')))
        clear_btn.bind('<Leave>', lambda e: clear_btn.config(font=('', 9)))
        
        self.columnconfigure(1, weight=1)
    
    def _on_mode_changed(self):
        """模式变化事件"""
        mode = self.mode_var.get()
        
        # HEX模式下禁用编码选择
        if mode == 'HEX':
            self.encoding_utf8_radio.config(state='disabled')
            self.encoding_ascii_radio.config(state='disabled')
        else:
            self.encoding_utf8_radio.config(state='normal')
            self.encoding_ascii_radio.config(state='normal')
        
        self._on_setting_changed()
    
    def _on_setting_changed(self):
        """设置变化事件"""
        if self.current_port:
            settings = self.get_settings()
            self.config_manager.update_receive_settings(self.current_port, settings)
            
            if self.on_change_callback:
                self.on_change_callback(settings)
    
    def _on_save_log_changed(self):
        """保存日志变化事件"""
        # 如果勾选了保存日志，触发回调
        if self.save_log_var.get() and self.on_save_log_callback:
            if not self.on_save_log_callback():
                # 如果回调返回False（用户取消），取消勾选
                self.save_log_var.set(False)
                return
        
        # 保存设置
        self._on_setting_changed()
    
    def _on_clear_clicked(self, event=None):
        """清除按钮点击事件"""
        if self.on_clear_callback:
            self.on_clear_callback()
    
    def get_settings(self):
        """获取当前设置"""
        return {
            'mode': self.mode_var.get(),
            'encoding': self.encoding_var.get(),
            'log_mode': self.log_mode_var.get(),
            'save_log': self.save_log_var.get(),
            'auto_reconnect': self.auto_reconnect_var.get(),
            'auto_scroll': self.auto_scroll_var.get()
        }
    
    def load_config(self, port, config):
        """加载配置"""
        self.current_port = port
        self.mode_var.set(config.get('mode', 'TEXT'))
        self.encoding_var.set(config.get('encoding', 'UTF-8'))
        self.log_mode_var.set(config.get('log_mode', False))
        self.save_log_var.set(config.get('save_log', False))
        self.auto_reconnect_var.set(config.get('auto_reconnect', False))
        self.auto_scroll_var.set(config.get('auto_scroll', True))
        
        # 更新编码选择状态
        self._on_mode_changed()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        colors = theme_manager.get_theme_colors()
        
        # 应用主题到清除接收按钮（这是tk.Label，不是ttk控件）
        try:
            for widget in self.winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text') == '清除接收':
                    widget.configure(
                        bg=colors.get('labelframe_bg', '#EFEFEF'),
                        fg=colors.get('link_color', '#0066CC')
                    )
        except Exception as e:
            print(f"应用主题到接收设置面板失败: {e}")

