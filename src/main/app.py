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

from pages.work_tab import WorkTab
from pages.settings_dialog import SettingsDialog
from components.quick_commands_panel import QuickCommandsPanel
from components.send_history_panel import SendHistoryPanel
from utils.config_manager import ConfigManager
from utils.file_utils import resource_path
from utils.theme_manager import ThemeManager

# 导入版本信息
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
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
        
        # 工作Tab列表
        self.work_tabs = []
        self.tab_counter = 1
        
        # 当前激活的notebook（用于双栏模式）
        self.active_notebook = None
        
        self._create_menu()
        self._create_widgets()
        
        # 在创建Tab之前先加载主题
        self._load_and_apply_theme()
        
        self._create_initial_tab()
        
        # 再次应用主题确保所有控件都正确
        self.after(100, self._apply_theme_to_all_widgets)
        
        # 退出处理
        self.protocol('WM_DELETE_WINDOW', self._on_closing)
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='文件', menu=file_menu)
        file_menu.add_command(label='导出配置', command=self._export_config)
        file_menu.add_command(label='导入配置', command=self._import_config)
        file_menu.add_separator()
        file_menu.add_command(label='设置', command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label='退出', command=self._on_closing)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='视图', menu=view_menu)
        self.dual_panel_var = tk.BooleanVar(value=self.config_manager.get_dual_panel_mode())
        view_menu.add_checkbutton(label='双栏模式', variable=self.dual_panel_var, 
                                  command=self._toggle_dual_panel)
        self.command_panel_var = tk.BooleanVar(value=self.config_manager.get_command_panel_visible())
        view_menu.add_checkbutton(label='命令面板', variable=self.command_panel_var,
                                  command=self._toggle_command_panel)
        
        # 主题子菜单
        view_menu.add_separator()
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label='主题', menu=theme_menu)
        
        # 获取可用主题并创建单选菜单
        self.theme_var = tk.StringVar(value=self.config_manager.get_theme())
        available_themes = self.theme_manager.get_available_themes()
        
        for theme_name in available_themes:
            theme_menu.add_radiobutton(
                label=theme_name.capitalize(),
                variable=self.theme_var,
                value=theme_name,
                command=lambda t=theme_name: self._change_theme(t)
            )
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='帮助', menu=help_menu)
        help_menu.add_command(label='关于', command=self._show_about)
    
    def _create_widgets(self):
        """创建控件"""
        # 主容器 - 左右分栏
        self.main_paned = ttk.PanedWindow(self, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True)
        
        # 左侧工作面板（支持双栏）
        self.work_area_container = ttk.Frame(self.main_paned)
        self.main_paned.add(self.work_area_container, weight=4)
        
        # 创建工作区域（单栏或双栏）
        self.dual_panel_mode = self.config_manager.get_dual_panel_mode()
        self._create_work_area()
        
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
            self.main_paned.add(self.right_container, weight=0)
        
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
    
    def _create_work_area(self):
        """创建工作区域（支持双栏）"""
        # 创建工作区域的PanedWindow（始终存在）
        self.work_paned = ttk.PanedWindow(self.work_area_container, orient='horizontal')
        self.work_paned.pack(fill='both', expand=True)
        
        # 左栏（主栏，始终存在）- 使用Frame实现顶部边框
        self.main_panel_container = tk.Frame(self.work_paned)
        self.work_paned.add(self.main_panel_container, weight=1)
        
        # 顶部边框（4px）- 未激活时透明
        self.main_panel_top_border = tk.Frame(self.main_panel_container, height=4)
        self.main_panel_top_border.pack(fill='x', side='top')
        
        self.main_panel = tk.Frame(self.main_panel_container, bg='white')
        self.main_panel.pack(fill='both', expand=True)
        
        self.work_notebook = self._create_notebook(self.main_panel)
        
        # 右栏（副栏，根据双栏模式显示/隐藏）- 使用Frame实现顶部边框
        self.secondary_panel_container = tk.Frame(self.work_paned)
        
        # 顶部边框（4px）- 未激活时透明
        self.secondary_panel_top_border = tk.Frame(self.secondary_panel_container, height=4)
        self.secondary_panel_top_border.pack(fill='x', side='top')
        
        self.secondary_panel = tk.Frame(self.secondary_panel_container, bg='white')
        self.secondary_panel.pack(fill='both', expand=True)
        
        self.work_notebook_secondary = self._create_notebook(self.secondary_panel)
        
        # 根据配置决定是否显示副栏
        if self.dual_panel_mode:
            self.work_paned.add(self.secondary_panel_container, weight=1)
        
        # 设置主栏为默认激活
        self.active_notebook = self.work_notebook
        self._update_panel_highlight()
    
    def _create_notebook(self, parent):
        """创建一个Notebook控件"""
        # 绑定父容器点击事件
        parent.bind('<Button-1>', lambda e: self._on_panel_click(parent))
        
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # 绑定notebook点击事件
        notebook.bind('<Button-1>', lambda e: self._on_panel_click(parent))
        
        # 创建加号Tab（作为占位符）
        add_tab_placeholder = ttk.Frame(notebook)
        notebook.add(add_tab_placeholder, text='+')
        
        # 绑定Tab切换事件
        notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        # 绑定双击Tab关闭
        notebook.bind('<Double-Button-1>', self._on_double_click)
        # 绑定鼠标中键点击关闭Tab
        notebook.bind('<Button-2>', self._on_middle_click)
        # 绑定右键菜单
        notebook.bind('<Button-3>', self._on_right_click)
        
        return notebook
    
    def _create_initial_tab(self):
        """创建初始工作Tab"""
        self._add_work_tab()
        
        # 如果是双栏模式，副栏也创建一个Tab
        if self.dual_panel_mode:
            self._add_work_tab(notebook=self.work_notebook_secondary)
    
    def _on_double_click(self, event):
        """双击Tab关闭"""
        try:
            # 获取触发事件的notebook
            notebook = event.widget
            clicked_tab = notebook.tk.call(notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                # 获取实际的Tab widget
                tab_widget = notebook.nametowidget(notebook.tabs()[index])
                # 关闭Tab
                self._close_tab_widget(tab_widget, notebook)
        except:
            pass
    
    def _on_middle_click(self, event):
        """鼠标中键点击关闭Tab"""
        try:
            # 获取触发事件的notebook
            notebook = event.widget
            clicked_tab = notebook.tk.call(notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                # 获取实际的Tab widget
                tab_widget = notebook.nametowidget(notebook.tabs()[index])
                # 关闭Tab
                self._close_tab_widget(tab_widget, notebook)
        except:
            pass
    
    def _on_right_click(self, event):
        """右键菜单"""
        try:
            # 获取触发事件的notebook
            notebook = event.widget
            clicked_tab = notebook.tk.call(notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                # 获取实际的Tab widget
                tab_widget = notebook.nametowidget(notebook.tabs()[index])
                # 显示菜单
                menu = tk.Menu(self, tearoff=0)
                menu.add_command(label='关闭', command=lambda: self._close_tab_widget(tab_widget, notebook))
                menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def _on_panel_click(self, panel):
        """面板点击事件，用于激活面板"""
        # 根据点击的面板确定对应的notebook
        if panel == self.main_panel:
            self.active_notebook = self.work_notebook
        elif panel == self.secondary_panel:
            self.active_notebook = self.work_notebook_secondary
        
        self._update_panel_highlight()
    
    def _on_work_tab_widget_click(self, work_tab):
        """工作Tab内部控件点击事件"""
        # 找到该work_tab所在的notebook
        for notebook in [self.work_notebook, self.work_notebook_secondary]:
            try:
                # 检查work_tab是否在这个notebook中
                if work_tab in notebook.winfo_children():
                    self.active_notebook = notebook
                    self._update_panel_highlight()
                    return
            except:
                pass
    
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
    
    def _on_tab_changed(self, event):
        """Tab切换事件处理"""
        # 确定是哪个notebook触发的事件
        notebook = event.widget
        
        # 更新激活的notebook
        self.active_notebook = notebook
        self._update_panel_highlight()
        
        # 获取当前选中的Tab索引
        current_index = notebook.index('current')
        
        # 如果点击的是加号Tab（最后一个）
        if current_index == notebook.index('end') - 1:
            # 计算该notebook当前有多少个普通Tab（不含加号）
            notebook_tab_count = notebook.index('end') - 1
            
            # 只有在该notebook已经有Tab的情况下才允许创建新Tab
            # 这样可以防止关闭最后一个Tab后自动创建新Tab
            if notebook_tab_count > 0:
                # 在对应的notebook创建新Tab
                self._add_work_tab(notebook=notebook)
    
    def _update_panel_highlight(self):
        """更新面板高亮显示 - 只有激活时显示顶部4px边框"""
        # 获取主题颜色
        if hasattr(self, 'theme_manager'):
            colors = self.theme_manager.get_theme_colors()
            bg_color = colors.get('labelframe_bg', '#F5F5F5')  # 使用labelframe背景色
            active_color = colors.get('active_border', '#4A90E2')
        else:
            bg_color = '#F5F5F5'
            active_color = '#4A90E2'
        
        if not self.dual_panel_mode:
            # 单栏模式：边框使用背景色（不显示）
            if hasattr(self, 'main_panel_top_border'):
                self.main_panel_top_border.config(bg=bg_color)
            return
        
        # 双栏模式：重置所有顶部边框为背景色（不显示）
        if hasattr(self, 'main_panel_top_border'):
            self.main_panel_top_border.config(bg=bg_color)
        if hasattr(self, 'secondary_panel_top_border'):
            self.secondary_panel_top_border.config(bg=bg_color)
        
        # 激活面板的顶部边框使用激活色
        if self.active_notebook == self.work_notebook:
            if hasattr(self, 'main_panel_top_border'):
                self.main_panel_top_border.config(bg=active_color)
        elif self.active_notebook == self.work_notebook_secondary:
            if hasattr(self, 'secondary_panel_top_border'):
                self.secondary_panel_top_border.config(bg=active_color)
    
    def _toggle_dual_panel(self):
        """切换双栏模式"""
        self.dual_panel_mode = self.dual_panel_var.get()
        self.config_manager.set_dual_panel_mode(self.dual_panel_mode)
        
        if self.dual_panel_mode:
            # 切换到双栏：显示副栏
            self.work_paned.add(self.secondary_panel_container, weight=1)
            
            # 检查副栏是否有Tab，如果没有则创建一个
            secondary_tab_count = self.work_notebook_secondary.index('end') - 1  # 排除加号Tab
            if secondary_tab_count == 0:
                self._add_work_tab(notebook=self.work_notebook_secondary)
            
            # 更新高亮显示
            self._update_panel_highlight()
        else:
            # 取消双栏：隐藏副栏
            # 首先关闭副栏所有Tab的串口连接
            secondary_tab_count = self.work_notebook_secondary.index('end') - 1
            tabs_to_remove = []
            
            for i in range(secondary_tab_count):
                try:
                    tab = self.work_notebook_secondary.nametowidget(self.work_notebook_secondary.tabs()[i])
                    if tab in self.work_tabs:
                        # 关闭串口连接
                        if hasattr(tab, 'serial_manager') and tab.serial_manager.is_open():
                            tab._disconnect()
                        tabs_to_remove.append(tab)
                except:
                    pass
            
            # 从work_tabs列表中移除副栏的Tab
            for tab in tabs_to_remove:
                if tab in self.work_tabs:
                    self.work_tabs.remove(tab)
            
            # 清空副栏所有Tab
            for i in range(secondary_tab_count - 1, -1, -1):
                try:
                    self.work_notebook_secondary.forget(i)
                except:
                    pass
            
            # 移除副栏
            self.work_paned.remove(self.secondary_panel_container)
    
    def _toggle_command_panel(self):
        """切换命令面板显示/隐藏"""
        self.right_panel_visible = self.command_panel_var.get()
        
        if self.right_panel_visible:
            # 显示命令面板，权重为0保持固定大小
            self.main_paned.add(self.right_container, weight=0)
        else:
            # 隐藏命令面板
            self.main_paned.remove(self.right_container)
        
        # 保存状态到配置
        self.config_manager.set_command_panel_visible(self.right_panel_visible)
    
    def _add_work_tab(self, notebook=None):
        """添加工作Tab"""
        # 如果没有指定notebook，使用主notebook
        if notebook is None:
            notebook = self.work_notebook
        
        # 判断是主栏还是副栏
        panel_type = 'secondary' if notebook == self.work_notebook_secondary else 'main'
        
        # 检查该notebook是否已有Tab（不含加号Tab）
        current_tab_count = notebook.index('end') - 1
        # 如果是该notebook的第一个Tab，则需要加载上次的串口
        is_first_tab = (current_tab_count == 0)
        
        tab_name = 'New Tab'
        
        work_tab = WorkTab(notebook, self.config_manager, tab_name, is_first_tab, 
                          on_widget_click=self._on_work_tab_widget_click,
                          on_data_sent=self._on_work_tab_data_sent,
                          panel_type=panel_type)
        
        # 在加号Tab之前插入新Tab
        insert_index = notebook.index('end') - 1
        notebook.insert(insert_index, work_tab, text=tab_name)
        
        self.work_tabs.append(work_tab)
        self.tab_counter += 1
        
        # 切换到新Tab
        notebook.select(insert_index)
        
        # 更新Tab标题
        self._update_tab_title_for_notebook(notebook, insert_index, tab_name)
        
        # 如果主题已加载，应用主题到新Tab
        if hasattr(self, 'theme_manager') and self.theme_manager.current_theme:
            font_size = self.config_manager.get_font_size()
            # 延迟应用主题，确保控件已完全创建
            self.after(10, lambda: work_tab.apply_theme(self.theme_manager, font_size))
    
    def _update_tab_title(self, index, title):
        """更新Tab标题"""
        self.work_notebook.tab(index, text=title)
    
    def _update_tab_title_for_notebook(self, notebook, index, title):
        """更新指定notebook的Tab标题"""
        notebook.tab(index, text=title)
    
    def _close_tab_widget(self, tab_widget, notebook):
        """关闭指定的Tab widget"""
        # 检查是否是加号Tab
        if tab_widget not in self.work_tabs:
            return
        
        # 至少保留一个Tab，静默处理（整个应用至少需要一个Tab）
        if len(self.work_tabs) <= 1:
            return
        
        # 每个栏至少保留一个Tab
        current_notebook_tabs = notebook.index('end') - 1  # 不含加号Tab
        if current_notebook_tabs <= 1:
            # 该栏只有1个Tab，不允许关闭
            return
        
        # 关闭串口连接
        if hasattr(tab_widget, 'serial_manager') and tab_widget.serial_manager.is_open():
            tab_widget._disconnect()
        
        # 获取Tab在notebook中的索引
        try:
            tab_index = notebook.index(tab_widget)
        except:
            return
        
        # 计算删除后该notebook还剩多少Tab（不包括加号Tab）
        remaining_count = current_notebook_tabs - 1  # 删除后剩余的Tab数量
        
        # 先选中其他Tab，避免自动选中"+"Tab
        if remaining_count > 0:
            new_index = min(tab_index, remaining_count - 1)  # 选中前一个或最后一个
            notebook.select(new_index)
        
        # 从work_tabs列表中移除
        if tab_widget in self.work_tabs:
            self.work_tabs.remove(tab_widget)
        
        # 最后删除Tab
        notebook.forget(tab_index)
    
    def _get_current_work_tab(self):
        """获取当前工作Tab（双栏模式下返回激活notebook的当前Tab）"""
        try:
            # 在双栏模式下，使用激活的notebook
            notebook = self.active_notebook if self.active_notebook else self.work_notebook
            
            # 获取当前选中的Tab
            current_index = notebook.index('current')
            
            # 获取该Tab的widget
            if current_index < notebook.index('end') - 1:  # 不是加号Tab
                tab_widget = notebook.nametowidget(notebook.tabs()[current_index])
                if tab_widget in self.work_tabs:
                    return tab_widget
            
            return None
        except:
            return None
    
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
            
            # 全局设置按钮手型指针
            self.option_add('*TButton*cursor', 'hand2')
            
            # 应用到主容器
            if hasattr(self, 'work_area_container'):
                self.work_area_container.configure(style='TFrame')
            
            if hasattr(self, 'right_container'):
                self.right_container.configure(style='TFrame')
            
            # 应用到主面板和副面板
            if hasattr(self, 'main_panel'):
                self.main_panel.configure(bg=colors.get('background', '#FFFFFF'))
            
            if hasattr(self, 'secondary_panel'):
                self.secondary_panel.configure(bg=colors.get('background', '#FFFFFF'))
            
            # 更新面板边框颜色
            if hasattr(self, '_update_panel_highlight'):
                self._update_panel_highlight()
            
            # 递归更新所有Frame的背景色
            self._update_frames_bg(self, colors)
            
            # 应用到所有工作Tab
            font_size = self.config_manager.get_font_size()
            for work_tab in self.work_tabs:
                if hasattr(work_tab, 'apply_theme'):
                    work_tab.apply_theme(self.theme_manager, font_size)
            
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
            # 配置菜单栏颜色
            try:
                menubar = self.nametowidget(self.cget('menu'))
                if menubar:
                    menubar.configure(
                        bg=colors.get('labelframe_bg', '#EFEFEF'),
                        fg=colors.get('foreground', '#000000'),
                        activebackground=colors.get('selectbackground', '#0078D7'),
                        activeforeground=colors.get('selectforeground', '#FFFFFF'),
                        relief='flat',
                        bd=0
                    )
                    
                    # 递归配置所有菜单项
                    self._configure_menu_recursive(menubar, colors)
            except Exception as e:
                print(f"配置菜单栏失败: {e}")
            
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
    
    def _configure_menu_recursive(self, menu, colors):
        """递归配置菜单颜色"""
        try:
            menu.configure(
                bg=colors.get('labelframe_bg', '#EFEFEF'),
                fg=colors.get('foreground', '#000000'),
                activebackground=colors.get('selectbackground', '#0078D7'),
                activeforeground=colors.get('selectforeground', '#FFFFFF'),
                selectcolor=colors.get('checkbox_selected', colors.get('selectbackground', '#0078D7')),
                relief='flat',
                bd=0
            )
            
            # 处理所有菜单项，包括级联菜单
            last_index = menu.index('end')
            if last_index is not None:
                for i in range(last_index + 1):
                    try:
                        menu_type = menu.type(i)
                        if menu_type == 'cascade':
                            # 获取子菜单并递归配置
                            submenu = menu.nametowidget(menu.entrycget(i, 'menu'))
                            self._configure_menu_recursive(submenu, colors)
                    except:
                        pass
        except Exception as e:
            print(f"配置菜单项失败: {e}")
    
    def _on_closing(self):
        """关闭应用"""
        # 清理所有工作Tab
        for work_tab in self.work_tabs:
            work_tab.cleanup()
        
        self.destroy()

def main():
    """主函数"""
    app = SerialToolApp()
    app.mainloop()

if __name__ == '__main__':
    main()

