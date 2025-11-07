"""
设置对话框 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx


class SettingsDialog(wx.Dialog):
    """设置对话框"""
    
    def __init__(self, parent, config_manager):
        super().__init__(parent, title='设置', style=wx.DEFAULT_DIALOG_STYLE)
        
        self.config_manager = config_manager
        self.parent_window = parent
        self.settings = self.config_manager.get_global_settings()
        
        self._create_widgets()
        self.CenterOnParent()
    
    def _create_widgets(self):
        """创建控件"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 数据接收缓冲区大小
        buffer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buffer_sizer.Add(wx.StaticText(self, label='数据接收缓冲区大小:'), 0, 
                        wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.buffer_size_spin = wx.SpinCtrl(self, value=str(self.settings.get('receive_buffer_size', 10000)), 
                                           min=1000, max=100000, 
                                           initial=self.settings.get('receive_buffer_size', 10000))
        buffer_sizer.Add(self.buffer_size_spin, 1, wx.EXPAND)
        sizer.Add(buffer_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 发送历史最大条数
        history_sizer = wx.BoxSizer(wx.HORIZONTAL)
        history_sizer.Add(wx.StaticText(self, label='发送历史最大条数:'), 0, 
                         wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.history_max_spin = wx.SpinCtrl(self, value=str(self.settings.get('send_history_max', 200)), 
                                           min=50, max=1000, 
                                           initial=self.settings.get('send_history_max', 200))
        history_sizer.Add(self.history_max_spin, 1, wx.EXPAND)
        sizer.Add(history_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 接收区域字体大小
        font_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_sizer.Add(wx.StaticText(self, label='接收区域字体大小:'), 0, 
                      wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.font_size_spin = wx.SpinCtrl(self, value=str(self.settings.get('fontSize', 9)), 
                                         min=6, max=20, 
                                         initial=self.settings.get('fontSize', 9))
        font_sizer.Add(self.font_size_spin, 1, wx.EXPAND)
        sizer.Add(font_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 自动重连间隔
        reconnect_sizer = wx.BoxSizer(wx.HORIZONTAL)
        reconnect_sizer.Add(wx.StaticText(self, label='自动重连间隔（秒）:'), 0, 
                           wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        self.reconnect_interval_spin = wx.SpinCtrl(self, 
                                                  value=str(self.settings.get('reconnect_interval', 5)), 
                                                  min=1, max=30, 
                                                  initial=self.settings.get('reconnect_interval', 5))
        reconnect_sizer.Add(self.reconnect_interval_spin, 1, wx.EXPAND)
        sizer.Add(reconnect_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 按钮
        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = wx.Button(self, wx.ID_OK, label='确定')
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label='取消')
        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.Fit()
    
    def _on_ok(self, event):
        """确定按钮处理"""
        buffer_size = self.buffer_size_spin.GetValue()
        history_max = self.history_max_spin.GetValue()
        font_size = self.font_size_spin.GetValue()
        reconnect_interval = self.reconnect_interval_spin.GetValue()
        
        # 验证输入
        if buffer_size < 1000 or buffer_size > 100000:
            wx.MessageBox('数据接收缓冲区大小必须在1000-100000行之间', '错误', 
                         wx.OK | wx.ICON_ERROR)
            return
        
        if history_max < 50 or history_max > 1000:
            wx.MessageBox('发送历史最大条数必须在50-1000条之间', '错误', 
                         wx.OK | wx.ICON_ERROR)
            return
        
        if font_size < 6 or font_size > 20:
            wx.MessageBox('字体大小必须在6-20之间', '错误', 
                         wx.OK | wx.ICON_ERROR)
            return
        
        if reconnect_interval < 1 or reconnect_interval > 30:
            wx.MessageBox('自动重连间隔必须在1-30秒之间', '错误', 
                         wx.OK | wx.ICON_ERROR)
            return
        
        # 保存设置
        settings = {
            'receive_buffer_size': buffer_size,
            'send_history_max': history_max,
            'fontSize': font_size,
            'reconnect_interval': reconnect_interval
        }
        self.config_manager.set_global_settings(settings)
        
        # 通知父窗口重新应用主题（使字体设置生效）
        if hasattr(self.parent_window, '_apply_theme_to_all_widgets'):
            self.parent_window._apply_theme_to_all_widgets()
        
        self.EndModal(wx.ID_OK)
