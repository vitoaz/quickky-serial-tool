"""
工作面板 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
import wx.lib.agw.aui as aui
from .work_column_wx import WorkColumn


class WorkPanel(wx.Panel):
    """工作面板 - 管理双栏工作区"""
    
    def __init__(self, parent, config_manager, theme_manager, on_tab_data_sent=None):
        """初始化工作面板"""
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.on_tab_data_sent = on_tab_data_sent
        
        # 双栏模式状态
        self.dual_panel_mode = self.config_manager.get_dual_panel_mode()
        
        # 当前激活的栏目
        self.active_column = None
        
        # 创建分割窗口
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        
        # 创建主栏（左侧）
        self.main_column = WorkColumn(
            self.splitter,
            self.config_manager,
            self.theme_manager,
            panel_type='main',
            on_column_activated=self._on_column_activated,
            on_tab_data_sent=on_tab_data_sent
        )
        
        # 创建副栏（右侧）
        self.secondary_column = WorkColumn(
            self.splitter,
            self.config_manager,
            self.theme_manager,
            panel_type='secondary',
            on_column_activated=self._on_column_activated,
            on_tab_data_sent=on_tab_data_sent
        )
        
        # 默认激活主栏
        self.active_column = self.main_column
        
        # 根据配置决定是否显示双栏
        dual_panel_mode = self.config_manager.get_dual_panel_mode()
        if dual_panel_mode:
            self.splitter.SplitVertically(self.main_column, self.secondary_column, 600)
        else:
            self.splitter.Initialize(self.main_column)
        
        self.splitter.SetMinimumPaneSize(300)
        self.splitter.SetSashGravity(0.5)  # 平均分配空间
        
        # 创建sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        # 初始化时更新栏目高亮
        wx.CallAfter(self._update_column_highlight)
    
    def _on_column_activated(self, column):
        """栏目激活回调"""
        self.active_column = column
        self._update_column_highlight()
    
    def _update_column_highlight(self):
        """更新栏目高亮显示"""
        # 只有在双栏模式下才显示激活边框
        is_dual = self.splitter.IsSplit()
        self.main_column.set_active(self.active_column == self.main_column and is_dual)
        self.secondary_column.set_active(self.active_column == self.secondary_column and is_dual)
    
    def toggle_dual_panel_mode(self, enabled):
        """切换双栏模式"""
        self.dual_panel_mode = enabled
        
        if enabled:
            if not self.splitter.IsSplit():
                self.splitter.SplitVertically(self.main_column, self.secondary_column, 600)
                self.splitter.SetSashGravity(0.5)
        else:
            if self.splitter.IsSplit():
                self.secondary_column.cleanup()
                self.splitter.Unsplit(self.secondary_column)
        
        # 更新高亮显示
        self._update_column_highlight()
        self.Layout()
    
    def apply_theme(self):
        """应用主题到所有工作栏"""
        self.main_column.apply_theme(self.theme_manager)
        self.secondary_column.apply_theme(self.theme_manager)
    
    def get_current_work_tab(self):
        """获取当前激活的工作Tab"""
        # 返回激活栏的当前Tab
        if self.active_column:
            return self.active_column.get_current_tab()
        # 如果没有激活栏，默认返回主栏的当前Tab
        return self.main_column.get_current_tab()
    
    def get_all_work_tabs(self):
        """获取所有工作Tab"""
        all_tabs = []
        all_tabs.extend(self.main_column.get_all_tabs())
        if self.splitter.IsSplit():
            all_tabs.extend(self.secondary_column.get_all_tabs())
        return all_tabs
    
    def send_data(self, data, mode):
        """发送数据到当前工作Tab
        
        Args:
            data: 要发送的数据
            mode: 发送模式 (TEXT/HEX)
            
        Returns:
            bool: 发送是否成功
        """
        work_tab = self.get_current_work_tab()
        if work_tab:
            # 设置发送文本
            work_tab.send_text.SetValue(data)
            
            # 按指定模式发送，不添加到历史记录（因为是从历史或快捷命令发送）
            work_tab._send_data(override_mode=mode, add_to_history=False)
            
            return True
        return False
    
    def cleanup(self):
        """清理资源"""
        self.main_column.cleanup()
        self.secondary_column.cleanup()

