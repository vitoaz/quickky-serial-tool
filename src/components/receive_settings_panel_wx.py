"""
接收设置面板组件 (wxPython版本)

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

import wx


class ReceiveSettingsPanel(wx.StaticBoxSizer):
    """接收设置面板"""
    
    def __init__(self, parent, config_manager, on_change_callback=None, 
                 on_save_log_callback=None):
        """初始化接收设置面板"""
        box = wx.StaticBox(parent, label='接收设置')
        super().__init__(box, wx.VERTICAL)
        
        self.parent = parent
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        self.on_save_log_callback = on_save_log_callback
        self.current_port = None  # 当前串口
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        self.panel = wx.Panel(self.GetStaticBox())
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 模式
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_sizer.Add(wx.StaticText(self.panel, label='模式:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.text_radio = wx.RadioButton(self.panel, label='TEXT', style=wx.RB_GROUP)
        self.hex_radio = wx.RadioButton(self.panel, label='HEX')
        self.text_radio.Bind(wx.EVT_RADIOBUTTON, self._on_mode_changed)
        self.hex_radio.Bind(wx.EVT_RADIOBUTTON, self._on_mode_changed)
        mode_sizer.Add(self.text_radio, 0, wx.RIGHT, 5)
        mode_sizer.Add(self.hex_radio, 0)
        sizer.Add(mode_sizer, 0, wx.ALL, 3)
        
        # 编码方式
        encoding_sizer = wx.BoxSizer(wx.HORIZONTAL)
        encoding_sizer.Add(wx.StaticText(self.panel, label='编码:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.encoding_utf8 = wx.RadioButton(self.panel, label='UTF-8', style=wx.RB_GROUP)
        self.encoding_ascii = wx.RadioButton(self.panel, label='ASCII')
        self.encoding_utf8.Bind(wx.EVT_RADIOBUTTON, self._on_setting_changed)
        self.encoding_ascii.Bind(wx.EVT_RADIOBUTTON, self._on_setting_changed)
        encoding_sizer.Add(self.encoding_utf8, 0, wx.RIGHT, 5)
        encoding_sizer.Add(self.encoding_ascii, 0)
        sizer.Add(encoding_sizer, 0, wx.ALL, 3)
        
        # 日志模式
        self.log_mode_check = wx.CheckBox(self.panel, label='日志模式（添加时间戳）')
        self.log_mode_check.Bind(wx.EVT_CHECKBOX, self._on_setting_changed)
        sizer.Add(self.log_mode_check, 0, wx.ALL, 3)
        
        # 保存日志文件
        self.save_log_check = wx.CheckBox(self.panel, label='保存日志文件')
        self.save_log_check.Bind(wx.EVT_CHECKBOX, self._on_save_log_changed)
        sizer.Add(self.save_log_check, 0, wx.ALL, 3)
        
        # 串口自动重连
        self.auto_reconnect_check = wx.CheckBox(self.panel, label='串口自动重连')
        self.auto_reconnect_check.Bind(wx.EVT_CHECKBOX, self._on_setting_changed)
        sizer.Add(self.auto_reconnect_check, 0, wx.ALL, 3)
        
        # 接收自动滚屏
        self.auto_scroll_check = wx.CheckBox(self.panel, label='接收自动滚屏')
        self.auto_scroll_check.SetValue(True)
        self.auto_scroll_check.Bind(wx.EVT_CHECKBOX, self._on_setting_changed)
        sizer.Add(self.auto_scroll_check, 0, wx.ALL, 3)
        
        self.panel.SetSizer(sizer)
        self.Add(self.panel, 0, wx.ALL | wx.EXPAND, 8)
    
    def _on_mode_changed(self, event):
        """模式变化事件"""
        self._on_setting_changed(event)
        # 编码选项只在TEXT模式下可用
        is_text = self.text_radio.GetValue()
        self.encoding_utf8.Enable(is_text)
        self.encoding_ascii.Enable(is_text)
    
    def _on_setting_changed(self, event):
        """设置变化事件"""
        # 保存配置到配置管理器
        if self.current_port:
            settings = self.get_settings()
            self.config_manager.update_receive_settings(self.current_port, settings)
            
            if self.on_change_callback:
                self.on_change_callback(settings)
    
    def _on_save_log_changed(self, event):
        """保存日志勾选变化"""
        if self.save_log_check.GetValue():
            # 弹出文件选择对话框
            if self.on_save_log_callback:
                if not self.on_save_log_callback():
                    # 用户取消，取消勾选
                    self.save_log_check.SetValue(False)
        
        self._on_setting_changed(event)
    
    def get_settings(self):
        """获取当前设置"""
        return {
            'mode': 'HEX' if self.hex_radio.GetValue() else 'TEXT',
            'encoding': 'UTF-8' if self.encoding_utf8.GetValue() else 'ASCII',
            'log_mode': self.log_mode_check.GetValue(),
            'save_log': self.save_log_check.GetValue(),
            'auto_reconnect': self.auto_reconnect_check.GetValue(),
            'auto_scroll': self.auto_scroll_check.GetValue()
        }
    
    def load_config(self, port, config):
        """加载配置"""
        self.current_port = port  # 保存当前串口
        
        if config['mode'] == 'HEX':
            self.hex_radio.SetValue(True)
            self.encoding_utf8.Enable(False)
            self.encoding_ascii.Enable(False)
        else:
            self.text_radio.SetValue(True)
            self.encoding_utf8.Enable(True)
            self.encoding_ascii.Enable(True)
        
        if config.get('encoding', 'UTF-8') == 'UTF-8':
            self.encoding_utf8.SetValue(True)
        else:
            self.encoding_ascii.SetValue(True)
        
        self.log_mode_check.SetValue(config.get('log_mode', False))
        self.save_log_check.SetValue(config.get('save_log', False))
        self.auto_reconnect_check.SetValue(config.get('auto_reconnect', False))
        self.auto_scroll_check.SetValue(config.get('auto_scroll', True))
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        if theme_manager:
            colors = theme_manager.get_theme_colors()
            
            # 应用到Panel和Label
            panel_bg = theme_manager.hex_to_wx_colour(colors.get('background', '#FFFFFF'))
            panel_fg = theme_manager.hex_to_wx_colour(colors.get('foreground', '#000000'))
            
            # 设置StaticBox（边框标题）的颜色
            static_box = self.GetStaticBox()
            if static_box:
                static_box.SetForegroundColour(panel_fg)
            
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
            
            # 从内部panel开始递归（panel包含所有的StaticText和CheckBox）
            if hasattr(self, 'panel'):
                apply_to_labels(self.panel)

