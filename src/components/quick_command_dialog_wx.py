"""
快捷指令编辑对话框 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
from utils.custom_controls_wx import ThemedButton


class QuickCommandDialog(wx.Dialog):
    """快捷指令编辑对话框"""
    
    def __init__(self, parent, command=None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            command: 要编辑的指令字典，None表示新建
        """
        title = '编辑指令' if command else '添加指令'
        super().__init__(parent, title=title, size=(400, 300))
        
        self.command = command or {}
        
        self._create_widgets()
        self._load_data()
        
        self.Centre()
    
    def _create_widgets(self):
        """创建控件"""
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 指令名称
        name_label = wx.StaticText(panel, label='指令名称:')
        sizer.Add(name_label, 0, wx.ALL, 5)
        
        self.name_text = wx.TextCtrl(panel)
        sizer.Add(self.name_text, 0, wx.EXPAND | wx.ALL, 5)
        
        # 指令内容
        data_label = wx.StaticText(panel, label='指令内容:')
        sizer.Add(data_label, 0, wx.ALL, 5)
        
        self.data_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 100))
        sizer.Add(self.data_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # 发送模式
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_label = wx.StaticText(panel, label='发送模式:')
        mode_sizer.Add(mode_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        
        self.text_radio = wx.RadioButton(panel, label='TEXT', style=wx.RB_GROUP)
        self.hex_radio = wx.RadioButton(panel, label='HEX')
        mode_sizer.Add(self.text_radio, 0, wx.RIGHT, 10)
        mode_sizer.Add(self.hex_radio, 0)
        
        sizer.Add(mode_sizer, 0, wx.ALL, 5)
        
        # 按钮
        btn_sizer = wx.StdDialogButtonSizer()
        ok_btn = ThemedButton(panel, wx.ID_OK)
        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        cancel_btn = ThemedButton(panel, wx.ID_CANCEL)
        btn_sizer.AddButton(ok_btn)
        btn_sizer.AddButton(cancel_btn)
        btn_sizer.Realize()
        
        sizer.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        
        panel.SetSizer(sizer)
    
    def _load_data(self):
        """加载数据"""
        if self.command:
            self.name_text.SetValue(self.command.get('name', ''))
            self.data_text.SetValue(self.command.get('data', ''))
            mode = self.command.get('mode', 'TEXT')
            if mode == 'HEX':
                self.hex_radio.SetValue(True)
            else:
                self.text_radio.SetValue(True)
    
    def _on_ok(self, event):
        """确定按钮"""
        name = self.name_text.GetValue().strip()
        data = self.data_text.GetValue().strip()
        
        if not name:
            wx.MessageBox('请输入指令名称', '错误', wx.OK | wx.ICON_ERROR)
            return
        
        if not data:
            wx.MessageBox('请输入指令内容', '错误', wx.OK | wx.ICON_ERROR)
            return
        
        self.result = {
            'name': name,
            'data': data,
            'mode': 'HEX' if self.hex_radio.GetValue() else 'TEXT'
        }
        
        self.EndModal(wx.ID_OK)
    
    def get_command(self):
        """获取指令数据"""
        return getattr(self, 'result', None)

