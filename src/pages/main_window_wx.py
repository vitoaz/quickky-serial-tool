"""
主窗口页面 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
import wx.lib.agw.aui as aui
import wx.lib.agw.flatmenu as FM
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
        width, height = 1200, 720
        
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
        """创建菜单栏（使用FlatMenu）"""
        # 设置FlatMenu的全局主题（在创建菜单之前）
        import wx.lib.agw.artmanager as AM
        art = AM.ArtManager()
        art.SetMenuTheme(AM.Style2007)  # 使用可自定义的主题
        
        # 创建FlatMenuBar - 设置合适的大小和选项
        self.menubar = FM.FlatMenuBar(self, wx.ID_ANY, 
                                      iconSize=16,  # 图标大小
                                      spacer=5,     # 间距
                                      options=0)    # 不显示工具栏
        
        # 文件菜单
        file_menu = FM.FlatMenu()
        export_item = FM.FlatMenuItem(file_menu, wx.ID_ANY, '导出配置', '导出配置到文件')
        import_item = FM.FlatMenuItem(file_menu, wx.ID_ANY, '导入配置', '从文件导入配置')
        settings_item = FM.FlatMenuItem(file_menu, wx.ID_PREFERENCES, '设置', '打开设置对话框')
        exit_item = FM.FlatMenuItem(file_menu, wx.ID_EXIT, '退出', '退出应用程序')
        
        file_menu.AppendItem(export_item)
        file_menu.AppendItem(import_item)
        file_menu.AppendSeparator()
        file_menu.AppendItem(settings_item)
        file_menu.AppendSeparator()
        file_menu.AppendItem(exit_item)
        
        self.Bind(wx.EVT_MENU, self._export_config, id=export_item.GetId())
        self.Bind(wx.EVT_MENU, self._import_config, id=import_item.GetId())
        self.Bind(wx.EVT_MENU, self._show_settings, id=settings_item.GetId())
        self.Bind(wx.EVT_MENU, self._on_closing, id=exit_item.GetId())
        
        self.menubar.Append(file_menu, '文件')
        
        # 视图菜单
        view_menu = FM.FlatMenu()
        self.dual_panel_item = FM.FlatMenuItem(view_menu, wx.ID_ANY, '双栏模式', '切换双栏/单栏模式', wx.ITEM_CHECK)
        self.command_panel_item = FM.FlatMenuItem(view_menu, wx.ID_ANY, '命令面板', '显示/隐藏命令面板', wx.ITEM_CHECK)
        
        view_menu.AppendItem(self.dual_panel_item)
        view_menu.AppendItem(self.command_panel_item)
        
        # 设置初始状态
        self.dual_panel_item.Check(self.config_manager.get_dual_panel_mode())
        self.command_panel_item.Check(self.config_manager.get_command_panel_visible())
        
        self.Bind(wx.EVT_MENU, self._toggle_dual_panel, id=self.dual_panel_item.GetId())
        self.Bind(wx.EVT_MENU, self._toggle_command_panel, id=self.command_panel_item.GetId())
        
        self.menubar.Append(view_menu, '视图')
        
        # 主题菜单
        theme_menu = FM.FlatMenu()
        available_themes = self.theme_manager.get_available_themes()
        current_theme = self.config_manager.get_theme()
        
        self.theme_items = {}
        for theme_name in available_themes:
            item = FM.FlatMenuItem(theme_menu, wx.ID_ANY, theme_name.capitalize(), f'切换到{theme_name}主题', wx.ITEM_RADIO)
            theme_menu.AppendItem(item)
            self.theme_items[theme_name] = item
            if theme_name == current_theme:
                item.Check(True)
            self.Bind(wx.EVT_MENU, lambda evt, t=theme_name: self._change_theme(t), id=item.GetId())
        
        self.menubar.Append(theme_menu, '主题')
        
        # 帮助菜单
        help_menu = FM.FlatMenu()
        about_item = FM.FlatMenuItem(help_menu, wx.ID_ABOUT, '关于', '关于本程序')
        help_menu.AppendItem(about_item)
        self.Bind(wx.EVT_MENU, self._show_about, id=about_item.GetId())
        
        self.menubar.Append(help_menu, '帮助')
    
    def _create_widgets(self):
        """创建控件"""
        # 创建工作面板（左侧）
        self.work_panel = WorkPanel(
            self,
            self.config_manager,
            self.theme_manager,
            on_tab_data_sent=self._on_work_tab_data_sent
        )
        
        # 创建命令面板（右侧，固定宽度250）
        self.command_panel = CommandPanel(
            self,
            self.config_manager,
            main_window=self
        )
        self.command_panel.SetMinSize((250, -1))
        self.command_panel.SetMaxSize((250, -1))
        
        # 创建主垂直sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 添加FlatMenu菜单栏
        if hasattr(self, 'menubar'):
            main_sizer.Add(self.menubar, 0, wx.EXPAND)
        
        # 添加分割线（菜单栏下方）
        separator = wx.Panel(self, size=(-1, 1))
        separator.SetBackgroundColour(wx.Colour(200, 200, 200))
        main_sizer.Add(separator, 0, wx.EXPAND)
        
        # 创建水平sizer放置工作面板和命令面板
        content_sizer = wx.BoxSizer(wx.HORIZONTAL)
        content_sizer.Add(self.work_panel, 1, wx.EXPAND)
        
        # 根据配置决定是否显示命令面板
        if self.config_manager.get_command_panel_visible():
            content_sizer.Add(self.command_panel, 0, wx.EXPAND)
        
        main_sizer.Add(content_sizer, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
        
        # 保存引用
        self.menu_separator = separator
        self.content_sizer = content_sizer
    
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
        
        # 移除content_sizer中的所有控件
        self.content_sizer.Clear()
        
        # 重新添加工作面板
        self.content_sizer.Add(self.work_panel, 1, wx.EXPAND)
        
        if visible:
            # 显示命令面板
            self.content_sizer.Add(self.command_panel, 0, wx.EXPAND)
            self.command_panel.Show()
        else:
            # 隐藏命令面板
            self.command_panel.Hide()
        
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
            bg_color = self.theme_manager.hex_to_wx_colour(colors.get('frame_bg', '#F5F5F5'))
            fg_color = self.theme_manager.hex_to_wx_colour(colors.get('text_fg', '#000000'))
            
            self.SetBackgroundColour(bg_color)
            self.SetForegroundColour(fg_color)
            
            # 应用到菜单栏
            self._apply_theme_to_menubar(bg_color, fg_color)
            
            # 应用到标题栏（仅Windows 10+）
            self._apply_theme_to_titlebar(colors)
            
            # 应用到Splitter
            if hasattr(self, 'splitter'):
                self.splitter.SetBackgroundColour(bg_color)
            
            # 应用到工作面板（会递归应用到所有WorkTab和子控件）
            if hasattr(self, 'work_panel'):
                self.work_panel.apply_theme()
            
            # 应用到命令面板（会递归应用到快捷指令和历史发送）
            if hasattr(self, 'command_panel'):
                self.command_panel.apply_theme(self.theme_manager)
            
            # 应用到菜单分隔线
            if hasattr(self, 'menu_separator'):
                separator_color = self.theme_manager.hex_to_wx_colour(colors.get('border', '#CCCCCC'))
                self.menu_separator.SetBackgroundColour(separator_color)
            
            # 刷新界面
            self.Refresh()
            
        except Exception as e:
            print(f"应用主题失败: {e}")
    
    def _apply_theme_to_menubar(self, bg_color, fg_color):
        """应用主题到菜单栏（FlatMenu）"""
        try:
            if hasattr(self, 'menubar') and self.menubar:
                # 设置FlatMenuBar的高度
                self.menubar.SetSize(-1, 28)  # 设置合适的高度
                # 直接设置FlatMenuBar和所有菜单的颜色
                self.menubar.SetBackgroundColour(bg_color)
                self.menubar.SetForegroundColour(fg_color)
                self.menubar.Refresh()
        except Exception as e:
            print(f"应用主题到菜单栏时出错: {e}")
    
    def _lighten_color(self, color, factor=1.2):
        """使颜色变浅"""
        try:
            r = min(255, int(color.Red() * factor))
            g = min(255, int(color.Green() * factor))
            b = min(255, int(color.Blue() * factor))
            return wx.Colour(r, g, b)
        except:
            return color
    
    def _set_submenu_colors(self, menu, bg_color, fg_color):
        """递归设置子菜单颜色"""
        try:
            # 遍历菜单项
            for item in menu.GetMenuItems():
                if item.IsSubMenu():
                    submenu = item.GetSubMenu()
                    if submenu:
                        submenu.SetBackgroundColour(bg_color)
                        submenu.SetForegroundColour(fg_color)
                        # 递归处理子菜单
                        self._set_submenu_colors(submenu, bg_color, fg_color)
        except:
            pass
    
    def _apply_theme_to_titlebar(self, colors):
        """应用主题到标题栏（仅Windows 10及以上）"""
        try:
            import sys
            if sys.platform == 'win32':
                # 尝试使用Windows API设置深色标题栏
                theme_name = self.theme_manager._current_theme_name
                is_dark = theme_name.lower() in ['dark', 'black', 'night']
                
                try:
                    import ctypes
                    hwnd = self.GetHandle()
                    # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    value = ctypes.c_int(1 if is_dark else 0)
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
                    )
                except:
                    pass
        except:
            pass
    
    def _on_closing(self, event):
        """关闭应用"""
        # 清理工作面板
        if hasattr(self, 'work_panel'):
            self.work_panel.cleanup()
        
        self.Destroy()

