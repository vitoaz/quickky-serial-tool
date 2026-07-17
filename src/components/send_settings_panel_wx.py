"""
发送设置面板组件 (wxPython版本)

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

import wx


class SendSettingsPanel(wx.StaticBoxSizer):
    """发送设置面板"""
    
    def __init__(self, parent, config_manager, on_change_callback=None, 
                 on_mode_change_callback=None):
        """初始化发送设置面板"""
        box = wx.StaticBox(parent, label='发送设置')
        super().__init__(box, wx.VERTICAL)
        
        self.parent = parent
        self.config_manager = config_manager
        self.on_change_callback = on_change_callback
        self.on_mode_change_callback = on_mode_change_callback
        self.old_mode = 'TEXT'
        self.current_port = None  # 当前串口
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        panel = wx.Panel(self.GetStaticBox())
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 模式选择
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_sizer.Add(wx.StaticText(panel, label='模式:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.text_radio = wx.RadioButton(panel, label='TEXT', style=wx.RB_GROUP)
        self.hex_radio = wx.RadioButton(panel, label='HEX')
        self.text_radio.Bind(wx.EVT_RADIOBUTTON, self._on_mode_changed)
        self.hex_radio.Bind(wx.EVT_RADIOBUTTON, self._on_mode_changed)
        mode_sizer.Add(self.text_radio, 0, wx.RIGHT, 5)
        mode_sizer.Add(self.hex_radio, 0)
        sizer.Add(mode_sizer, 0, wx.ALL, 3)
        
        # 循环发送
        self.loop_send_check = wx.CheckBox(panel, label='循环发送')
        self.loop_send_check.Bind(wx.EVT_CHECKBOX, self._on_loop_changed)
        sizer.Add(self.loop_send_check, 0, wx.ALL, 3)
        
        # 周期设置
        period_sizer = wx.BoxSizer(wx.HORIZONTAL)
        period_sizer.Add(wx.StaticText(panel, label='周期:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.period_spin = wx.SpinCtrl(panel, value='1000', min=100, max=999999, size=(80, -1))
        self.period_spin.Bind(wx.EVT_SPINCTRL, self._on_setting_changed)
        self.period_spin.Enable(False)
        period_sizer.Add(self.period_spin, 0)
        period_sizer.Add(wx.StaticText(panel, label='ms'), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        sizer.Add(period_sizer, 0, wx.ALL, 3)
        
        panel.SetSizer(sizer)
        self.Add(panel, 0, wx.ALL | wx.EXPAND, 8)
    
    def _on_mode_changed(self, event):
        """模式变化事件"""
        new_mode = 'HEX' if self.hex_radio.GetValue() else 'TEXT'
        if self.on_mode_change_callback and self.old_mode != new_mode:
            self.on_mode_change_callback(self.old_mode, new_mode)
        self.old_mode = new_mode
        self._on_setting_changed(event)
    
    def _on_loop_changed(self, event):
        """循环发送勾选变化"""
        enabled = self.loop_send_check.GetValue()
        self.period_spin.Enable(enabled)
        self._on_setting_changed(event)
    
    def _on_setting_changed(self, event):
        """设置变化事件"""
        # 保存配置到配置管理器
        if self.current_port:
            settings = self.get_settings()
            self.config_manager.update_send_settings(self.current_port, settings)
            
            if self.on_change_callback:
                self.on_change_callback(settings)
    
    def get_settings(self):
        """获取当前设置"""
        return {
            'mode': 'HEX' if self.hex_radio.GetValue() else 'TEXT',
            'loop_send': self.loop_send_check.GetValue(),
            'loop_period_ms': self.period_spin.GetValue()
        }
    
    def load_config(self, port, config):
        """加载配置"""
        self.current_port = port  # 保存当前串口
        
        if config['mode'] == 'HEX':
            self.hex_radio.SetValue(True)
        else:
            self.text_radio.SetValue(True)
        
        self.old_mode = config['mode']
        
        self.loop_send_check.SetValue(config.get('loop_send', False))
        self.period_spin.SetValue(config.get('loop_period_ms', 1000))
        self.period_spin.Enable(config.get('loop_send', False))
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        colors = theme_manager.get_theme_colors()
        if not colors:
            return
        
        try:
            # 应用到Panel和Label
            panel_bg = theme_manager.hex_to_wx_colour(colors.get('background', '#FFFFFF'))
            panel_fg = theme_manager.hex_to_wx_colour(colors.get('foreground', '#000000'))
            
            # SpinCtrl
            fg_color = theme_manager.hex_to_wx_colour(colors.get('text_fg', '#000000'))
            self.period_spin.SetForegroundColour(fg_color)
            self.period_spin.SetBackgroundColour(panel_bg)
            self.period_spin.Refresh()

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
            
            # 从StaticBox开始递归（self是Sizer，GetStaticBox()获取StaticBox和其子控件）
            if static_box:
                # StaticBox包含所有子控件
                apply_to_labels(static_box)
            
        except Exception as e:
            print(f"应用主题到发送设置面板时出错: {e}")

