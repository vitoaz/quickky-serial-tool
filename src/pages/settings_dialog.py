"""
设置对话框

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils.dialog_utils import DialogUtils

class SettingsDialog(tk.Toplevel):
    """设置对话框"""
    
    def __init__(self, parent, config_manager):
        """
        初始化设置对话框
        
        Args:
            parent: 父窗口
            config_manager: 配置管理器
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.parent_window = parent
        
        self.title('设置')
        self.resizable(False, False)
        self.transient(parent)
        
        # 先隐藏窗口，避免闪烁
        self.withdraw()
        
        # 加载当前设置
        self.settings = self.config_manager.get_global_settings()
        
        self._create_widgets()
        
        # 应用父窗口的标题栏主题
        self._apply_titlebar_theme()
        
        # 使用工具类显示对话框
        DialogUtils.show_modal_dialog(self, parent, 400, 300)
        
        # 阻塞父窗口
        self.wait_window()
    
    def _create_widgets(self):
        """创建控件"""
        # 主容器
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # 设置项容器
        settings_frame = ttk.Frame(main_frame)
        settings_frame.pack(fill='both', expand=True)
        
        # 数据接收缓冲区大小
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill='x', pady=10)
        
        ttk.Label(row1, text='数据接收缓冲区大小:', width=20, anchor='w').pack(side='left')
        self.buffer_size_var = tk.IntVar(value=self.settings.get('receive_buffer_size', 10000))
        buffer_size_spinbox = ttk.Spinbox(
            row1,
            from_=1000,
            to=100000,
            increment=1000,
            textvariable=self.buffer_size_var,
            width=15
        )
        buffer_size_spinbox.pack(side='left', padx=(10, 5))
        ttk.Label(row1, text='行').pack(side='left')
        
        # 发送历史最大条数
        row2 = ttk.Frame(settings_frame)
        row2.pack(fill='x', pady=10)
        
        ttk.Label(row2, text='发送历史最大条数:', width=20, anchor='w').pack(side='left')
        self.history_max_var = tk.IntVar(value=self.settings.get('send_history_max', 200))
        history_max_spinbox = ttk.Spinbox(
            row2,
            from_=50,
            to=1000,
            increment=50,
            textvariable=self.history_max_var,
            width=15
        )
        history_max_spinbox.pack(side='left', padx=(10, 5))
        ttk.Label(row2, text='条').pack(side='left')
        
        # 接收区域字体大小
        row3 = ttk.Frame(settings_frame)
        row3.pack(fill='x', pady=10)
        
        ttk.Label(row3, text='接收区域字体大小:', width=20, anchor='w').pack(side='left')
        self.font_size_var = tk.IntVar(value=self.settings.get('fontSize', 9))
        font_size_spinbox = ttk.Spinbox(
            row3,
            from_=6,
            to=20,
            increment=1,
            textvariable=self.font_size_var,
            width=15
        )
        font_size_spinbox.pack(side='left', padx=(10, 5))
        ttk.Label(row3, text='点').pack(side='left')
        
        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(20, 0))
        
        ttk.Button(button_frame, text='确定', command=self._on_ok, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text='取消', command=self._on_cancel, width=10).pack(side='left', padx=5)
    
    def _on_ok(self):
        """确定按钮处理"""
        try:
            buffer_size = self.buffer_size_var.get()
            history_max = self.history_max_var.get()
            font_size = self.font_size_var.get()
            
            # 验证输入
            if buffer_size < 1000 or buffer_size > 100000:
                messagebox.showerror('错误', '数据接收缓冲区大小必须在1000-100000行之间', parent=self)
                return
            
            if history_max < 50 or history_max > 1000:
                messagebox.showerror('错误', '发送历史最大条数必须在50-1000条之间', parent=self)
                return
            
            if font_size < 6 or font_size > 20:
                messagebox.showerror('错误', '字体大小必须在6-20点之间', parent=self)
                return
            
            # 保存设置
            settings = {
                'receive_buffer_size': buffer_size,
                'send_history_max': history_max,
                'fontSize': font_size
            }
            self.config_manager.set_global_settings(settings)
            
            # 提示需要重新应用设置
            messagebox.showinfo('提示', '设置已保存。字体大小将在切换主题后生效。', parent=self)
            
            self.destroy()
            
        except tk.TclError:
            messagebox.showerror('错误', '请输入有效的数字', parent=self)
    
    def _on_cancel(self):
        """取消按钮处理"""
        self.destroy()
    
    def _apply_titlebar_theme(self):
        """应用标题栏主题"""
        try:
            import ctypes
            
            # 等待窗口完全创建
            self.update_idletasks()
                
            # 获取窗口句柄
            hwnd = ctypes.windll.user32.FindWindowW(None, self.title())
            if not hwnd:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            
            # 检查父窗口的主题
            theme_name = self.config_manager.get_theme()
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            
            if theme_name == 'dark':
                value = ctypes.c_int(1)
            else:
                value = ctypes.c_int(0)
            
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
            
            # 强制刷新窗口
            self.withdraw()
            self.deiconify()
            
        except Exception as e:
            print(f"设置对话框标题栏主题失败: {e}")

