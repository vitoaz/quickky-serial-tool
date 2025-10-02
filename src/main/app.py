"""
Quickky Serial Tool - 串口调试工具
主应用程序

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.settings_dialog import SettingsDialog
from components.quick_commands_panel import QuickCommandsPanel
from components.send_history_panel import SendHistoryPanel
from components.custom_menubar import CustomMenuBar
from components.work_panel import WorkPanel
from utils.config_manager import ConfigManager
from utils.file_utils import resource_path, get_base_path
from utils.theme_manager import ThemeManager
from utils.ttk_paned_window_minisize import ttk_panedwindow_minsize

# 导入版本信息
try:
    sys.path.insert(0, get_base_path())
    import version
    VERSION = version.VERSION
    BUILD_TIME = version.BUILD_TIME
except:
    VERSION = "1.0.0"
    BUILD_TIME = "未知"

class SerialToolApp(tk.Tk):
    """串口工具主应用"""
    
    def __init__(self):
        super().__init__()
        
        self.title(f'QSerial v{VERSION} - by Aaz')
        self.geometry('1024x600')
        
        # 设置窗口图标
        try:
            # 使用资源文件工具获取图标路径
            png_path = resource_path('icon.png')
            if os.path.exists(png_path):
                png_image = tk.PhotoImage(file=png_path)
                self.wm_iconphoto(True, png_image)
                
        except Exception as e:
            print(f'加载图标失败: {e}')
        
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 主题管理器（传入self作为root窗口）
        self.theme_manager = ThemeManager(self)
        
        self._create_widgets()
        
        # 创建自定义菜单栏
        self._create_custom_menu()
        
        # 在创建Tab之前先加载主题
        self._load_and_apply_theme()
        
        # 再次应用主题确保所有控件都正确
        self.after(100, self._apply_theme_to_all_widgets)
        
        # 退出处理
        self.protocol('WM_DELETE_WINDOW', self._on_closing)
    
    def _create_custom_menu(self):
        """创建自定义菜单栏"""
        # 创建自定义菜单栏
        self.custom_menubar = CustomMenuBar(self, relief='flat', bd=0)
        self.custom_menubar.pack(side='top', fill='x', before=self.main_paned)
        
        # 获取可用主题
        available_themes = self.theme_manager.get_available_themes()
        current_theme = self.config_manager.get_theme()
        
        # 创建变量
        self.theme_var = tk.StringVar(value=current_theme)
        self.dual_panel_var = tk.BooleanVar(value=self.config_manager.get_dual_panel_mode())
        self.command_panel_var = tk.BooleanVar(value=self.config_manager.get_command_panel_visible())
        
        # 文件菜单
        file_items = [
            {'label': '导出配置', 'command': self._export_config},
            {'label': '导入配置', 'command': self._import_config},
            {'type': 'separator'},
            {'label': '设置', 'command': self._show_settings},
            {'type': 'separator'},
            {'label': '退出', 'command': self._on_closing}
        ]
        self.custom_menubar.add_menu('文件', file_items)
        
        # 视图菜单
        view_items = [
            {'label': '双栏模式', 'type': 'checkbutton', 'variable': self.dual_panel_var, 'command': self._toggle_dual_panel},
            {'label': '命令面板', 'type': 'checkbutton', 'variable': self.command_panel_var, 'command': self._toggle_command_panel}
        ]
        self.custom_menubar.add_menu('视图', view_items)
        
        # 主题菜单
        theme_items = []
        for theme_name in available_themes:
            theme_items.append({
                'label': theme_name.capitalize(),
                'type': 'radiobutton',
                'variable': self.theme_var,
                'value': theme_name,
                'command': lambda t=theme_name: self._change_theme(t)
            })
        self.custom_menubar.add_menu('主题', theme_items)
        
        # 帮助菜单
        help_items = [
            {'label': '关于', 'command': self._show_about}
        ]
        self.custom_menubar.add_menu('帮助', help_items)
    
    def _create_widgets(self):
        """创建控件"""
        # 主容器 - 左右分栏
        self.main_paned = ttk.PanedWindow(self, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True)
        
        # 创建主容器的最小尺寸管理器
        self.main_minsize_manager = ttk_panedwindow_minsize(self.main_paned, 'horizontal')
        
        # 创建工作面板
        self.work_panel = WorkPanel(
            self.main_paned,
            self.config_manager,
            self.theme_manager,
            on_tab_data_sent=self._on_work_tab_data_sent
        )
        self.main_minsize_manager.add_panel(self.work_panel, min_size=600, weight=4)
        
        # 右侧命令面板容器（设置固定宽度）
        self.right_container = ttk.Frame(self.main_paned, width=280)
        self.right_container.pack_propagate(False)  # 防止子控件改变Frame大小
        
        # 命令面板
        self.command_notebook = ttk.Notebook(self.right_container)
        self.command_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 从配置加载命令面板显示状态
        self.right_panel_visible = self.config_manager.get_command_panel_visible()
        if self.right_panel_visible:
            # 权重为0让它不自动扩展
            self.main_minsize_manager.add_panel(self.right_container, min_size=250, weight=0)
        
        # 快捷指令Tab
        self.quick_commands_panel = QuickCommandsPanel(
            self.command_notebook, 
            self.config_manager,
            on_send_callback=self._send_quick_command
        )
        self.command_notebook.add(self.quick_commands_panel, text='快捷指令')
        
        # 历史发送Tab
        self.send_history_panel = SendHistoryPanel(
            self.command_notebook,
            self.config_manager,
            on_send_callback=self._send_from_history
        )
        self.command_notebook.add(self.send_history_panel, text='历史发送')
        
        # 绑定命令面板的Tab切换事件，用于刷新历史列表
        self.command_notebook.bind('<<NotebookTabChanged>>', self._on_command_tab_changed)
    
    
    def _on_work_tab_data_sent(self):
        """工作Tab数据发送后回调"""
        # 刷新历史发送面板
        self.send_history_panel.refresh()
    
    def _on_command_tab_changed(self, event):
        """命令面板Tab切换事件"""
        # 获取当前选中的Tab索引
        current_index = self.command_notebook.index('current')
        # 如果切换到历史发送Tab
        if current_index == 1:  # 历史发送Tab的索引是1
            self.send_history_panel.refresh()
    
    def _toggle_dual_panel(self):
        """切换双栏模式"""
        dual_panel_mode = self.dual_panel_var.get()
        self.config_manager.set_dual_panel_mode(dual_panel_mode)
        
        # 委托给工作面板处理
        self.work_panel.toggle_dual_panel_mode(dual_panel_mode)
    
    def _toggle_command_panel(self):
        """切换命令面板显示/隐藏"""
        self.right_panel_visible = self.command_panel_var.get()
        
        if self.right_panel_visible:
            # 显示命令面板，权重为0保持固定大小
            self.main_minsize_manager.add_panel(self.right_container, min_size=250, weight=0)
        else:
            # 隐藏命令面板
            self.main_minsize_manager.remove_panel(self.right_container)
        
        # 保存状态到配置
        self.config_manager.set_command_panel_visible(self.right_panel_visible)
    
    def _get_current_work_tab(self):
        """获取当前工作Tab"""
        return self.work_panel.get_current_work_tab()
    
    def _send_quick_command(self, command, mode):
        """
        发送快捷指令
        
        Args:
            command: 指令内容
            mode: 发送模式(TEXT/HEX)
        """
        work_tab = self._get_current_work_tab()
        if work_tab:
            # 设置发送文本
            work_tab.send_text.delete('1.0', 'end')
            work_tab.send_text.insert('1.0', command)
            
            # 根据指令的模式发送（不看当前Tab的发送模式）
            work_tab._send_data(override_mode=mode)
            
            # 立即刷新历史发送面板
            self.send_history_panel.refresh()
    
    def _send_from_history(self, data, mode):
        """
        从历史发送
        
        Args:
            data: 发送数据
            mode: 发送模式(TEXT/HEX)
        """
        work_tab = self._get_current_work_tab()
        if work_tab:
            # 设置发送文本
            work_tab.send_text.delete('1.0', 'end')
            work_tab.send_text.insert('1.0', data)
            
            # 直接按历史记录的模式发送
            work_tab._send_data(override_mode=mode)
            
            # 立即刷新历史发送面板
            self.send_history_panel.refresh()
    
    def _export_config(self):
        """导出配置"""
        file_path = filedialog.asksaveasfilename(
            title='导出配置',
            defaultextension='.json',
            filetypes=[('JSON文件', '*.json'), ('所有文件', '*.*')]
        )
        
        if file_path:
            if self.config_manager.export_config(file_path):
                messagebox.showinfo('成功', '配置导出成功！')
            else:
                messagebox.showerror('错误', '配置导出失败！')
    
    def _import_config(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(
            title='导入配置',
            filetypes=[('JSON文件', '*.json'), ('所有文件', '*.*')]
        )
        
        if file_path:
            if self.config_manager.import_config(file_path):
                messagebox.showinfo('成功', '配置导入成功！请重启应用以应用配置。')
            else:
                messagebox.showerror('错误', '配置导入失败！')
    
    def _show_settings(self):
        """显示设置"""
        SettingsDialog(self, self.config_manager)
    
    def _show_about(self):
        """显示关于"""
        about_text = f"""QSerial (Quickky Serial Tool)

版本: {VERSION}
构建时间: {BUILD_TIME}

作者: Aaz
邮箱: vitoyuz@foxmail.com

一个功能强大的串口调试工具

开源地址:
Gitee: https://gitee.com/vitoaaazzz/quickky-serial-tool
GitHub: https://github.com/vitoaz/quickky-serial-tool"""
        
        messagebox.showinfo('关于', about_text)
    
    def _load_and_apply_theme(self):
        """加载并应用主题"""
        theme_name = self.config_manager.get_theme()
        self.theme_manager.load_theme(theme_name)
        # 先应用ttk样式
        self.theme_manager.apply_ttk_theme()
        # 再应用到具体控件
        self._apply_theme_to_all_widgets()
        # 应用到菜单栏和标题栏
        self._apply_theme_to_menu_and_titlebar()
    
    def _change_theme(self, theme_name):
        """切换主题"""
        self.config_manager.set_theme(theme_name)
        self.theme_manager.load_theme(theme_name)
        # 先应用ttk样式
        self.theme_manager.apply_ttk_theme()
        # 再应用到具体控件
        self._apply_theme_to_all_widgets()
        # 应用到菜单栏和标题栏
        self._apply_theme_to_menu_and_titlebar()
    
    def _apply_theme_to_all_widgets(self):
        """应用主题到所有控件"""
        colors = self.theme_manager.get_theme_colors()
        
        if not colors:
            return
        
        try:
            # 应用到主窗口
            self.configure(bg=colors.get('frame_bg', '#F5F5F5'))
            
            # 应用到右侧容器
            if hasattr(self, 'right_container'):
                self.right_container.configure(style='TFrame')
            
            
            # 递归更新所有Frame的背景色
            self._update_frames_bg(self, colors)
            
            # 应用到工作面板
            if hasattr(self, 'work_panel'):
                self.work_panel.apply_theme()
            
            # 应用到命令面板
            if hasattr(self, 'quick_commands_panel'):
                if hasattr(self.quick_commands_panel, 'apply_theme'):
                    self.quick_commands_panel.apply_theme(self.theme_manager)
            
            if hasattr(self, 'send_history_panel'):
                if hasattr(self.send_history_panel, 'apply_theme'):
                    self.send_history_panel.apply_theme(self.theme_manager)
            
            # 刷新窗口显示
            self.update_idletasks()
            
        except Exception as e:
            print(f"应用主题失败: {e}")
    
    def _update_frames_bg(self, widget, colors):
        """递归更新所有Frame背景色"""
        try:
            # 尝试配置ttk.Frame
            if isinstance(widget, ttk.Frame):
                try:
                    widget.configure(style='TFrame')
                except:
                    pass
            
            # 递归处理子控件
            for child in widget.winfo_children():
                self._update_frames_bg(child, colors)
        except:
            pass
    
    def _apply_theme_to_menu_and_titlebar(self):
        """应用主题到菜单栏和标题栏"""
        colors = self.theme_manager.get_theme_colors()
        
        if not colors:
            return
        
        try:
            # 应用主题到自定义菜单栏
            if hasattr(self, 'custom_menubar'):
                self.custom_menubar.apply_theme(colors)
            
            # Windows 10/11 标题栏深色模式（需要特殊API）
            try:
                import ctypes
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                
                # 检查是否为Dark主题
                theme_name = self.config_manager.get_theme()
                if theme_name == 'dark':
                    # 启用深色标题栏 (Windows 10 build 17763+)
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    value = ctypes.c_int(1)
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_USE_IMMERSIVE_DARK_MODE,
                        ctypes.byref(value),
                        ctypes.sizeof(value)
                    )
                else:
                    # 禁用深色标题栏
                    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                    value = ctypes.c_int(0)
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_USE_IMMERSIVE_DARK_MODE,
                        ctypes.byref(value),
                        ctypes.sizeof(value)
                    )
            except Exception as e:
                print(f"设置标题栏主题失败: {e}")
                
        except Exception as e:
            print(f"应用菜单主题失败: {e}")
    
    def _on_closing(self):
        """关闭应用"""
        # 清理工作面板
        if hasattr(self, 'work_panel'):
            self.work_panel.cleanup()
        
        self.destroy()

def main():
    """主函数"""
    app = SerialToolApp()
    app.mainloop()

if __name__ == '__main__':
    main()

