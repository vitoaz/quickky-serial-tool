# -*- coding: utf-8 -*-
"""
历史发送面板 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx


class SendHistoryPanel(wx.Panel):
    """历史发送面板"""
    
    def __init__(self, parent, config_manager, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.main_window = main_window
        self.full_data_list = []  # 存储完整数据
        
        self._create_widgets()
        self._load_history()
    
    def _create_widgets(self):
        """创建控件"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建ListCtrl
        self.list_ctrl = wx.ListCtrl(self, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, '时间', width=125)
        self.list_ctrl.InsertColumn(1, '模式', width=40)
        self.list_ctrl.InsertColumn(2, '数据', width=150)
        
        # 设置较小的字体
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.list_ctrl.SetFont(font)
        
        sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(sizer)
        
        # 绑定双击事件和右键菜单
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_double_click)
        self.list_ctrl.Bind(wx.EVT_RIGHT_DOWN, self._show_menu)
    
    def _load_history(self):
        """加载发送历史"""
        self.list_ctrl.DeleteAllItems()
        self.full_data_list = []  # 清空完整数据列表
        history = self.config_manager.get_send_history()
        
        for item in history:
            # 兼容旧格式
            if isinstance(item, str):
                time_str = ''
                mode = 'TEXT'
                data = item
            else:
                time_str = item.get('time', '')
                mode = item.get('mode', 'TEXT')
                data = item.get('data', '')
            
            # 存储完整数据
            self.full_data_list.append({'mode': mode, 'data': data})
            
            # 限制显示长度
            display_data = data.replace('\n', '\\n')
            if len(display_data) > 50:
                display_data = display_data[:50] + '...'
            
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), time_str)
            self.list_ctrl.SetItem(index, 1, mode)
            self.list_ctrl.SetItem(index, 2, display_data)
    
    def _show_menu(self, event):
        """显示右键菜单"""
        # 获取鼠标点击的项 - 直接使用事件位置，不需要转换
        pos = event.GetPosition()
        item_index, flags = self.list_ctrl.HitTest(pos)
        
        menu = wx.Menu()
        
        if item_index >= 0:
            # 清除之前的选中
            selected = self.list_ctrl.GetFirstSelected()
            while selected != -1:
                self.list_ctrl.Select(selected, False)
                selected = self.list_ctrl.GetNextSelected(selected)
            # 选中右键点击的项
            self.list_ctrl.Select(item_index)
            self.list_ctrl.Focus(item_index)
            
            send_item = menu.Append(wx.ID_ANY, '发送')
            menu.AppendSeparator()
            
            self.Bind(wx.EVT_MENU, lambda e: self._send_selected(), send_item)
        
        clear_item = menu.Append(wx.ID_ANY, '清空历史')
        self.Bind(wx.EVT_MENU, self._on_clear_history, clear_item)
        
        self.list_ctrl.PopupMenu(menu)
        menu.Destroy()
    
    def _on_clear_history(self, event):
        """清空历史"""
        result = wx.MessageBox('确定要清空所有发送历史吗？', '确认', 
                              wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            self.config_manager.clear_send_history()
            self._load_history()
    
    def _send_selected(self):
        """发送选中的历史记录"""
        index = self.list_ctrl.GetFirstSelected()
        if index >= 0 and self.main_window and index < len(self.full_data_list):
            item_data = self.full_data_list[index]
            mode = item_data['mode']
            data = item_data['data']
            
            # 发送数据
            self._send_from_history(data, mode)
    
    def _on_item_double_click(self, event):
        """双击发送"""
        index = event.GetIndex()
        if index >= 0 and self.main_window and index < len(self.full_data_list):
            item_data = self.full_data_list[index]
            mode = item_data['mode']
            data = item_data['data']
            
            # 发送数据
            self._send_from_history(data, mode)
    
    def _send_from_history(self, data, mode):
        """从历史发送"""
        if not self.main_window:
            return
        
        # 通过工作面板发送
        if self.main_window.work_panel.send_data(data, mode):
            # 刷新历史发送面板
            if hasattr(self.main_window, 'command_panel'):
                self.main_window.command_panel.refresh_history()
    
    def refresh(self):
        """刷新历史列表"""
        self._load_history()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        pass
