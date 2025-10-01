"""
串口设置面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk
from utils.serial_manager import SerialManager

class SerialSettingsPanel(ttk.LabelFrame):
    """串口设置面板"""
    
    # 常用波特率
    BAUDRATES = [300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 
                 38400, 57600, 115200, 230400, 460800, 921600, 
                 1000000, 1500000, 2000000]
    
    # 校验位选项
    PARITIES = ['None', 'Even', 'Odd', 'Mark', 'Space']
    
    # 数据位选项
    BYTESIZES = [5, 6, 7, 8]
    
    # 停止位选项
    STOPBITS = [1, 1.5, 2]
    
    # 流控选项
    FLOW_CONTROLS = ['None', 'Hardware', 'Software']
    
    def __init__(self, parent, config_manager, on_change_callback=None):
        """
        初始化串口设置面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_change_callback: 配置变化回调函数
        """
        super().__init__(parent, text='串口设置', padding=(8, 5))
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 串口号
        ttk.Label(self, text='串口号:').grid(row=0, column=0, sticky='w', pady=2)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(self, textvariable=self.port_var, state='readonly', width=18)
        self.port_combo.grid(row=0, column=1, pady=2, sticky='ew')
        self.port_combo['postcommand'] = self._refresh_ports
        self.port_combo.bind('<<ComboboxSelected>>', self._on_port_changed)
        
        # 波特率
        ttk.Label(self, text='波特率:').grid(row=1, column=0, sticky='w', pady=2)
        self.baudrate_var = tk.StringVar(value='115200')
        self.baudrate_combo = ttk.Combobox(self, textvariable=self.baudrate_var, 
                                          values=self.BAUDRATES, width=18)
        self.baudrate_combo.grid(row=1, column=1, pady=2, sticky='ew')
        self.baudrate_combo.bind('<<ComboboxSelected>>', self._on_setting_changed)
        self.baudrate_combo.bind('<KeyRelease>', self._on_setting_changed)
        
        # 校验位
        ttk.Label(self, text='校验位:').grid(row=2, column=0, sticky='w', pady=2)
        self.parity_var = tk.StringVar(value='None')
        self.parity_combo = ttk.Combobox(self, textvariable=self.parity_var, 
                                        values=self.PARITIES, state='readonly', width=18)
        self.parity_combo.grid(row=2, column=1, pady=2, sticky='ew')
        self.parity_combo.bind('<<ComboboxSelected>>', self._on_setting_changed)
        
        # 数据位
        ttk.Label(self, text='数据位:').grid(row=3, column=0, sticky='w', pady=2)
        self.bytesize_var = tk.StringVar(value='8')
        self.bytesize_combo = ttk.Combobox(self, textvariable=self.bytesize_var, 
                                          values=self.BYTESIZES, state='readonly', width=18)
        self.bytesize_combo.grid(row=3, column=1, pady=2, sticky='ew')
        self.bytesize_combo.bind('<<ComboboxSelected>>', self._on_setting_changed)
        
        # 停止位
        ttk.Label(self, text='停止位:').grid(row=4, column=0, sticky='w', pady=2)
        self.stopbits_var = tk.StringVar(value='1')
        self.stopbits_combo = ttk.Combobox(self, textvariable=self.stopbits_var, 
                                          values=self.STOPBITS, state='readonly', width=18)
        self.stopbits_combo.grid(row=4, column=1, pady=2, sticky='ew')
        self.stopbits_combo.bind('<<ComboboxSelected>>', self._on_setting_changed)
        
        # 流控
        ttk.Label(self, text='流控:').grid(row=5, column=0, sticky='w', pady=2)
        self.flow_control_var = tk.StringVar(value='None')
        self.flow_control_combo = ttk.Combobox(self, textvariable=self.flow_control_var, 
                                              values=self.FLOW_CONTROLS, state='readonly', width=18)
        self.flow_control_combo.grid(row=5, column=1, pady=2, sticky='ew')
        self.flow_control_combo.bind('<<ComboboxSelected>>', self._on_setting_changed)
        
        self.columnconfigure(1, weight=1)
    
    def _refresh_ports(self):
        """刷新可用串口列表"""
        ports = SerialManager.get_available_ports()
        self.port_combo['values'] = ports
    
    def _on_port_changed(self, event=None):
        """串口号变化事件"""
        port = self.port_var.get()
        if port:
            # 加载该串口的配置
            config = self.config_manager.get_port_config(port)
            self.load_config(config['serial_settings'])
            self.config_manager.set_last_port(port)
            
            if self.on_change_callback:
                self.on_change_callback('port', port)
    
    def _on_setting_changed(self, event=None):
        """设置变化事件"""
        port = self.port_var.get()
        if port:
            settings = self.get_settings()
            self.config_manager.update_serial_settings(port, settings)
            
            if self.on_change_callback:
                self.on_change_callback('settings', settings)
    
    def get_settings(self):
        """获取当前设置"""
        try:
            baudrate = int(self.baudrate_var.get())
        except ValueError:
            baudrate = 115200
        
        try:
            stopbits = float(self.stopbits_var.get())
        except ValueError:
            stopbits = 1
        
        return {
            'baudrate': baudrate,
            'parity': self.parity_var.get(),
            'bytesize': int(self.bytesize_var.get()),
            'stopbits': stopbits,
            'flow_control': self.flow_control_var.get()
        }
    
    def load_config(self, config):
        """加载配置"""
        self.baudrate_var.set(str(config.get('baudrate', 115200)))
        self.parity_var.set(config.get('parity', 'None'))
        self.bytesize_var.set(str(config.get('bytesize', 8)))
        self.stopbits_var.set(str(config.get('stopbits', 1)))
        self.flow_control_var.set(config.get('flow_control', 'None'))
    
    def get_current_port(self):
        """获取当前选中的串口"""
        return self.port_var.get()
    
    def set_current_port(self, port):
        """设置当前串口"""
        self.port_var.set(port)
        self._on_port_changed()
    
    def set_enabled(self, enabled):
        """启用或禁用所有控件"""
        state = 'normal' if enabled else 'disabled'
        readonly_state = 'readonly' if enabled else 'disabled'
        
        # 串口号和波特率使用readonly状态（可以看到但不能修改）
        self.port_combo.config(state=readonly_state)
        self.baudrate_combo.config(state=readonly_state)
        
        # 其他控件使用disabled状态
        self.parity_combo.config(state=readonly_state)
        self.bytesize_combo.config(state=readonly_state)
        self.stopbits_combo.config(state=readonly_state)
        self.flow_control_combo.config(state=readonly_state)

