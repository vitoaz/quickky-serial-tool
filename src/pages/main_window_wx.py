"""
主窗口页面 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
import wx.lib.agw.aui as aui
import os

from utils.config_manager import ConfigManager
from utils.file_utils import resource_path
from utils.theme_manager_wx import ThemeManagerWx
from utils.app_info import AppInfo
from components.work_panel_wx import WorkPanel
from components.command_panel_wx import CommandPanel


class MainWindow(wx.Frame):
    """主窗口类"""
    
    def __init__(self, parent):
        """初始化主窗口"""
        # 获取窗口标题和尺寸
        title = AppInfo.get_window_title()
        width, height = 1200, 700
        
        super().__init__(parent, title=title, size=(width, height))
        
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 主题管理器
        self.theme_manager = ThemeManagerWx()
        
        # 设置窗口图标
        self._setup_icon()
        
        # 窗口居中
        self.Centre()
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建主面板
        self._create_widgets()
        
        # 应用主题
        self._load_and_apply_theme()
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self._on_closing)
    
    def _setup_icon(self):
        """设置窗口图标"""
        try:
            png_path = resource_path('icon.png')
            if os.path.exists(png_path):
                icon = wx.Icon(png_path, wx.BITMAP_TYPE_PNG)
                self.SetIcon(icon)
        except Exception as e:
            print(f'加载图标失败: {e}')
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = wx.MenuBar()
        
        # 文件菜单
        file_menu = wx.Menu()
        export_item = file_menu.Append(wx.ID_ANY, '导出配置', '导出配置到文件')
        import_item = file_menu.Append(wx.ID_ANY, '导入配置', '从文件导入配置')
        file_menu.AppendSeparator()
        settings_item = file_menu.Append(wx.ID_PREFERENCES, '设置', '打开设置对话框')
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, '退出', '退出应用程序')
        
        self.Bind(wx.EVT_MENU, self._export_config, export_item)
        self.Bind(wx.EVT_MENU, self._import_config, import_item)
        self.Bind(wx.EVT_MENU, self._show_settings, settings_item)
        self.Bind(wx.EVT_MENU, self._on_closing, exit_item)
        
        menubar.Append(file_menu, '文件')
        
        # 视图菜单
        view_menu = wx.Menu()
        self.dual_panel_item = view_menu.AppendCheckItem(wx.ID_ANY, '双栏模式', '切换双栏/单栏模式')
        self.command_panel_item = view_menu.AppendCheckItem(wx.ID_ANY, '命令面板', '显示/隐藏命令面板')
        
        # 设置初始状态
        self.dual_panel_item.Check(self.config_manager.get_dual_panel_mode())
        self.command_panel_item.Check(self.config_manager.get_command_panel_visible())
        
        self.Bind(wx.EVT_MENU, self._toggle_dual_panel, self.dual_panel_item)
        self.Bind(wx.EVT_MENU, self._toggle_command_panel, self.command_panel_item)
        
        menubar.Append(view_menu, '视图')
        
        # 主题菜单
        theme_menu = wx.Menu()
        available_themes = self.theme_manager.get_available_themes()
        current_theme = self.config_manager.get_theme()
        
        self.theme_items = {}
        for theme_name in available_themes:
            item = theme_menu.AppendRadioItem(wx.ID_ANY, theme_name.capitalize(), f'切换到{theme_name}主题')
            self.theme_items[theme_name] = item
            if theme_name == current_theme:
                item.Check(True)
            self.Bind(wx.EVT_MENU, lambda evt, t=theme_name: self._change_theme(t), item)
        
        menubar.Append(theme_menu, '主题')
        
        # 帮助菜单
        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, '关于', '关于本程序')
        self.Bind(wx.EVT_MENU, self._show_about, about_item)
        
        menubar.Append(help_menu, '帮助')
        
        self.SetMenuBar(menubar)
    
    def _create_widgets(self):
        """创建控件"""
        # 创建主分割窗口
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
        
        # 创建工作面板（左侧）
        self.work_panel = WorkPanel(
            self.splitter,
            self.config_manager,
            self.theme_manager,
            on_tab_data_sent=self._on_work_tab_data_sent
        )
        
        # 创建命令面板（右侧）
        self.command_panel = CommandPanel(
            self.splitter,
            self.config_manager,
            main_window=self
        )
        
        # 从配置加载命令面板显示状态
        if self.config_manager.get_command_panel_visible():
            # 显示命令面板
            self.splitter.SplitVertically(self.work_panel, self.command_panel, -300)
            self.splitter.SetMinimumPaneSize(250)
        else:
            # 隐藏命令面板
            self.splitter.Initialize(self.work_panel)
        
        # 创建sizer并添加splitter
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def _on_work_tab_data_sent(self):
        """工作Tab数据发送后回调"""
        # 刷新历史发送面板
        if hasattr(self, 'command_panel'):
            self.command_panel.refresh_history()
    
    def _toggle_dual_panel(self, event):
        """切换双栏模式"""
        dual_panel_mode = self.dual_panel_item.IsChecked()
        self.config_manager.set_dual_panel_mode(dual_panel_mode)
        
        # 委托给工作面板处理
        self.work_panel.toggle_dual_panel_mode(dual_panel_mode)
    
    def _toggle_command_panel(self, event):
        """切换命令面板显示/隐藏"""
        visible = self.command_panel_item.IsChecked()
        
        if visible:
            # 显示命令面板
            if not self.splitter.IsSplit():
                self.splitter.SplitVertically(self.work_panel, self.command_panel, -300)
                self.splitter.SetMinimumPaneSize(250)
        else:
            # 隐藏命令面板
            if self.splitter.IsSplit():
                self.splitter.Unsplit(self.command_panel)
        
        # 保存状态到配置
        self.config_manager.set_command_panel_visible(visible)
        
        # 刷新布局
        self.Layout()
    
    def _export_config(self, event):
        """导出配置"""
        dlg = wx.FileDialog(
            self,
            '导出配置',
            wildcard='JSON文件 (*.json)|*.json|所有文件 (*.*)|*.*',
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            if self.config_manager.export_config(file_path):
                wx.MessageBox('配置导出成功！', '成功', wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox('配置导出失败！', '错误', wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def _import_config(self, event):
        """导入配置"""
        dlg = wx.FileDialog(
            self,
            '导入配置',
            wildcard='JSON文件 (*.json)|*.json|所有文件 (*.*)|*.*',
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            if self.config_manager.import_config(file_path):
                wx.MessageBox('配置导入成功！请重启应用以应用配置。', '成功', wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox('配置导入失败！', '错误', wx.OK | wx.ICON_ERROR)
        
        dlg.Destroy()
    
    def _show_settings(self, event):
        """显示设置"""
        from pages.settings_dialog_wx import SettingsDialog
        dlg = SettingsDialog(self, self.config_manager)
        dlg.ShowModal()
        dlg.Destroy()
    
    def _show_about(self, event):
        """显示关于"""
        about_text = AppInfo.get_about_text()
        wx.MessageBox(about_text, '关于', wx.OK | wx.ICON_INFORMATION)
    
    def _load_and_apply_theme(self):
        """加载并应用主题"""
        theme_name = self.config_manager.get_theme()
        self.theme_manager.load_theme(theme_name)
        self._apply_theme_to_all_widgets()
    
    def _change_theme(self, theme_name):
        """切换主题"""
        self.config_manager.set_theme(theme_name)
        self.theme_manager.load_theme(theme_name)
        self._apply_theme_to_all_widgets()
    
    def _apply_theme_to_all_widgets(self):
        """应用主题到所有控件"""
        colors = self.theme_manager.get_theme_colors()
        
        if not colors:
            return
        
        try:
            # 应用到主窗口
            bg_color = colors.get('frame_bg', '#F5F5F5')
            self.SetBackgroundColour(bg_color)
            
            # 应用到工作面板
            if hasattr(self, 'work_panel'):
                self.work_panel.apply_theme()
            
            # 应用到命令面板
            if hasattr(self, 'command_panel'):
                self.command_panel.apply_theme(self.theme_manager)
            
            # 刷新界面
            self.Refresh()
            
        except Exception as e:
            print(f"应用主题失败: {e}")
    
    def _on_closing(self, event):
        """关闭应用"""
        # 清理工作面板
        if hasattr(self, 'work_panel'):
            self.work_panel.cleanup()
        
        self.Destroy()

