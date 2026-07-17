"""
串口设置面板组件 (wxPython版本)

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

import wx
from utils.serial_manager import SerialManager
from utils.custom_controls_wx import ThemedComboBox


class SerialSettingsPanel(wx.StaticBoxSizer):
    """串口设置面板"""
    
    BAUDRATES = ['300', '600', '1200', '2400', '4800', '9600', '14400', '19200', 
                 '38400', '57600', '115200', '230400', '460800', '921600',
                 '1000000', '1500000', '2000000']
    PARITIES = ['None', 'Even', 'Odd', 'Mark', 'Space']
    BYTESIZES = ['5', '6', '7', '8']
    STOPBITS = ['1', '1.5', '2']
    FLOW_CONTROLS = ['None', 'Hardware', 'Software']
    
    def __init__(self, parent, config_manager, on_change_callback=None, panel_type='main'):
        """初始化串口设置面板"""
        box = wx.StaticBox(parent, label='串口设置')
        super().__init__(box, wx.VERTICAL)
        
        self.parent = parent
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        self.panel_type = panel_type
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        self.panel = wx.Panel(self.GetStaticBox())
        grid = wx.FlexGridSizer(6, 2, 5, 5)
        
        # 串口号
        grid.Add(wx.StaticText(self.panel, label='串口号:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.port_combo = ThemedComboBox(self.panel, choices=[''], style=wx.CB_READONLY, size=(150, -1))
        self.port_combo.Bind(wx.EVT_COMBOBOX, self._on_port_changed)
        self.port_combo.Bind(wx.EVT_COMBOBOX_DROPDOWN, self._refresh_ports)
        grid.Add(self.port_combo, 0, wx.EXPAND)
        
        # 波特率
        grid.Add(wx.StaticText(self.panel, label='波特率:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.baudrate_combo = ThemedComboBox(self.panel, value='115200', choices=self.BAUDRATES, size=(150, -1))
        self.baudrate_combo.Bind(wx.EVT_COMBOBOX, self._on_setting_changed)
        self.baudrate_combo.Bind(wx.EVT_TEXT, self._on_setting_changed)
        grid.Add(self.baudrate_combo, 0, wx.EXPAND)
        
        # 校验位
        grid.Add(wx.StaticText(self.panel, label='校验位:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.parity_combo = ThemedComboBox(self.panel, value='None', choices=self.PARITIES, 
                                       style=wx.CB_READONLY, size=(150, -1))
        self.parity_combo.Bind(wx.EVT_COMBOBOX, self._on_setting_changed)
        grid.Add(self.parity_combo, 0, wx.EXPAND)
        
        # 数据位
        grid.Add(wx.StaticText(self.panel, label='数据位:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.bytesize_combo = ThemedComboBox(self.panel, value='8', choices=self.BYTESIZES, 
                                         style=wx.CB_READONLY, size=(150, -1))
        self.bytesize_combo.Bind(wx.EVT_COMBOBOX, self._on_setting_changed)
        grid.Add(self.bytesize_combo, 0, wx.EXPAND)
        
        # 停止位
        grid.Add(wx.StaticText(self.panel, label='停止位:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.stopbits_combo = ThemedComboBox(self.panel, value='1', choices=self.STOPBITS, 
                                         style=wx.CB_READONLY, size=(150, -1))
        self.stopbits_combo.Bind(wx.EVT_COMBOBOX, self._on_setting_changed)
        grid.Add(self.stopbits_combo, 0, wx.EXPAND)
        
        # 流控
        grid.Add(wx.StaticText(self.panel, label='流控:'), 0, wx.ALIGN_CENTER_VERTICAL)
        self.flow_control_combo = ThemedComboBox(self.panel, value='None', choices=self.FLOW_CONTROLS, 
                                             style=wx.CB_READONLY, size=(150, -1))
        self.flow_control_combo.Bind(wx.EVT_COMBOBOX, self._on_setting_changed)
        grid.Add(self.flow_control_combo, 0, wx.EXPAND)
        
        self.panel.SetSizer(grid)
        self.Add(self.panel, 0, wx.ALL | wx.EXPAND, 8)
    
    def _refresh_ports(self, event=None):
        """刷新可用串口列表"""
        ports = SerialManager.get_available_ports()
        
        # 按COM后的数值排序
        def port_sort_key(port):
            """提取COM后的数字用于排序"""
            if port.upper().startswith('COM'):
                try:
                    # 提取COM后的数字
                    num_str = port[3:].strip()
                    return int(num_str)
                except ValueError:
                    # 如果无法转换为数字，返回一个很大的值，排在后面
                    return float('inf')
            else:
                # 非COM开头的串口，排在最后
                return float('inf')
        
        ports = sorted(ports, key=port_sort_key)
        
        self.port_combo.Clear()
        for port in ports:
            self.port_combo.Append(port)
    
    def _on_port_changed(self, event):
        """串口号变化事件"""
        port = self.port_combo.GetValue()
        if port:
            config = self.config_manager.get_port_config(port)
            self.load_config(config['serial_settings'])
            self.config_manager.set_last_port(port, self.panel_type)
            
            if self.on_change_callback:
                self.on_change_callback('port', port)
    
    def _on_setting_changed(self, event):
        """设置变化事件"""
        port = self.port_combo.GetValue()
        if port:
            settings = self.get_settings()
            self.config_manager.update_serial_settings(port, settings)
            
            if self.on_change_callback:
                self.on_change_callback('settings', settings)
    
    def get_settings(self):
        """获取当前设置"""
        try:
            baudrate = int(self.baudrate_combo.GetValue())
        except ValueError:
            baudrate = 115200
        
        try:
            stopbits = float(self.stopbits_combo.GetValue())
        except ValueError:
            stopbits = 1
        
        return {
            'baudrate': baudrate,
            'parity': self.parity_combo.GetValue(),
            'bytesize': int(self.bytesize_combo.GetValue()),
            'stopbits': stopbits,
            'flow_control': self.flow_control_combo.GetValue()
        }
    
    def load_config(self, config):
        """加载配置"""
        self.baudrate_combo.SetValue(str(config.get('baudrate', 115200)))
        self.parity_combo.SetValue(config.get('parity', 'None'))
        self.bytesize_combo.SetValue(str(config.get('bytesize', 8)))
        
        # 停止位特殊处理
        stopbits = config.get('stopbits', 1)
        if isinstance(stopbits, (int, float)):
            if stopbits == int(stopbits):
                self.stopbits_combo.SetValue(str(int(stopbits)))
            else:
                self.stopbits_combo.SetValue(str(stopbits))
        else:
            self.stopbits_combo.SetValue(str(stopbits))
        
        self.flow_control_combo.SetValue(config.get('flow_control', 'None'))
    
    def get_current_port(self):
        """获取当前选择的串口"""
        return self.port_combo.GetValue()
    
    def set_current_port(self, port):
        """设置当前串口"""
        if port:
            # 如果串口不在列表中，先添加它
            if self.port_combo.FindString(port) == wx.NOT_FOUND:
                self.port_combo.Append(port)
            self.port_combo.SetValue(port)
            self.port_combo.Refresh()
            self.port_combo.Update()
            self._on_port_changed(None)
    
    def set_enabled(self, enabled):
        """设置控件启用/禁用状态"""
        # 直接禁用整个panel，避免单个控件样式被系统修改
        self.panel.Enable(enabled)
    
    def get_available_ports(self):
        """获取可用串口列表"""
        return SerialManager.get_available_ports()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        colors = theme_manager.get_theme_colors()
        if not colors:
            return
        
        try:
            # 应用到Panel和Label
            panel_bg = theme_manager.hex_to_wx_colour(colors.get('background', '#FFFFFF'))
            panel_fg = theme_manager.hex_to_wx_colour(colors.get('foreground', '#000000'))
            
            # 设置StaticBox（边框标题）的颜色
            static_box = self.GetStaticBox()
            if static_box:
                static_box.SetForegroundColour(panel_fg)
            
            # 应用主题到ThemedComboBox
            text_bg = theme_manager.hex_to_wx_colour(colors.get('text_bg', '#FFFFFF'))
            text_fg = theme_manager.hex_to_wx_colour(colors.get('text_fg', '#000000'))
            for combo in [self.port_combo, self.baudrate_combo, self.parity_combo, 
                         self.bytesize_combo, self.stopbits_combo, self.flow_control_combo]:
                if hasattr(combo, 'apply_theme'):
                    combo.apply_theme(text_bg, text_fg)
            
            # 递归应用到所有StaticText、RadioButton、CheckBox和Panel
            def apply_to_labels(widget):
                try:
                    if isinstance(widget, wx.StaticText):
                        widget.SetForegroundColour(panel_fg)
                        widget.SetBackgroundColour(panel_bg)
                    elif isinstance(widget, (wx.RadioButton, wx.CheckBox)):
                        # RadioButton和CheckBox也需要设置前景色
                        widget.SetForegroundColour(panel_fg)
                    elif isinstance(widget, wx.Panel):
                        widget.SetBackgroundColour(panel_bg)
                    
                    if hasattr(widget, 'GetChildren'):
                        for child in widget.GetChildren():
                            apply_to_labels(child)
                except:
                    pass
            
            # 从内部panel开始递归（panel包含所有的StaticText）
            if hasattr(self, 'panel'):
                apply_to_labels(self.panel)
            
        except Exception as e:
            print(f"应用主题到串口设置面板时出错: {e}")

