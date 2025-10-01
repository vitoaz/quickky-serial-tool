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
from components.quick_commands_panel import QuickCommandsPanel
from components.send_history_panel import SendHistoryPanel
from utils.config_manager import ConfigManager

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
        
        self.title(f'Quickky Serial Tool v{VERSION}')
        self.geometry('1200x700')
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon.png')
            if os.path.exists(icon_path):
                icon_image = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, icon_image)
        except Exception as e:
            print(f'加载图标失败: {e}')
        
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 工作Tab列表
        self.work_tabs = []
        self.tab_counter = 1
        
        self._create_menu()
        self._create_widgets()
        self._create_initial_tab()
        
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
        file_menu.add_command(label='退出', command=self._on_closing)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='帮助', menu=help_menu)
        help_menu.add_command(label='关于', command=self._show_about)
    
    def _create_widgets(self):
        """创建控件"""
        # 主容器 - 左右分栏
        self.main_paned = ttk.PanedWindow(self, orient='horizontal')
        self.main_paned.pack(fill='both', expand=True)
        
        # 左侧工作面板
        left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(left_frame, weight=3)
        
        # 创建Notebook
        self.work_notebook = ttk.Notebook(left_frame)
        self.work_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建加号Tab（作为占位符）
        self.add_tab_placeholder = ttk.Frame(self.work_notebook)
        self.work_notebook.add(self.add_tab_placeholder, text='+')
        
        # 绑定Tab切换事件
        self.work_notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        # 绑定双击Tab关闭
        self.work_notebook.bind('<Double-Button-1>', self._on_double_click)
        # 绑定鼠标中键点击关闭Tab
        self.work_notebook.bind('<Button-2>', self._on_middle_click)
        # 绑定右键菜单
        self.work_notebook.bind('<Button-3>', self._on_right_click)
        
        # 右侧命令面板容器
        self.right_container = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_container, weight=1)
        
        # 收起按钮（在命令面板顶部）
        toggle_frame = ttk.Frame(self.right_container)
        toggle_frame.pack(fill='x', padx=5, pady=(5, 0))
        
        self.hide_btn = ttk.Button(toggle_frame, text='>>', width=3, command=self._toggle_right_panel)
        self.hide_btn.pack(side='right')
        
        # 命令面板
        self.command_notebook = ttk.Notebook(self.right_container)
        self.command_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 从配置加载命令面板显示状态
        self.right_panel_visible = self.config_manager.get_command_panel_visible()
        
        # 如果初始状态是隐藏，则应用隐藏状态
        if not self.right_panel_visible:
            self.after(100, self._apply_initial_panel_state)
        
        # 创建展开按钮frame（初始隐藏）
        self.show_btn_frame = ttk.Frame(self.main_paned)
        self.show_btn = ttk.Button(self.show_btn_frame, text='<<', width=3, command=self._toggle_right_panel)
        self.show_btn.pack(fill='both', expand=True, padx=2, pady=5)
        
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
    
    def _create_initial_tab(self):
        """创建初始工作Tab"""
        self._add_work_tab()
    
    def _on_double_click(self, event):
        """双击Tab关闭"""
        try:
            clicked_tab = self.work_notebook.tk.call(self.work_notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                # 如果不是加号Tab，则关闭
                if index < len(self.work_tabs):
                    self._close_tab(index)
        except:
            pass
    
    def _on_middle_click(self, event):
        """鼠标中键点击关闭Tab"""
        try:
            clicked_tab = self.work_notebook.tk.call(self.work_notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                # 如果不是加号Tab，则关闭
                if index < len(self.work_tabs):
                    self._close_tab(index)
        except:
            pass
    
    def _on_right_click(self, event):
        """右键菜单"""
        try:
            clicked_tab = self.work_notebook.tk.call(self.work_notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                index = int(clicked_tab)
                # 如果不是加号Tab，显示菜单
                if index < len(self.work_tabs):
                    menu = tk.Menu(self, tearoff=0)
                    menu.add_command(label='关闭', command=lambda: self._close_tab(index))
                    menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def _on_tab_changed(self, event):
        """Tab切换事件处理"""
        # 获取当前选中的Tab索引
        current_index = self.work_notebook.index('current')
        
        # 如果点击的是加号Tab（最后一个）
        if current_index == self.work_notebook.index('end') - 1:
            # 创建新Tab
            self._add_work_tab()
    
    def _apply_initial_panel_state(self):
        """应用初始面板状态"""
        if not self.right_panel_visible:
            # 隐藏命令面板
            self.main_paned.remove(self.right_container)
            self.main_paned.add(self.show_btn_frame, weight=0)
    
    def _toggle_right_panel(self):
        """收起/展开右侧命令面板"""
        if self.right_panel_visible:
            # 收起右侧面板，显示展开按钮（<<）
            self.main_paned.remove(self.right_container)
            self.main_paned.add(self.show_btn_frame, weight=0)
            self.right_panel_visible = False
        else:
            # 展开右侧面板，显示收起按钮（>>）
            self.main_paned.remove(self.show_btn_frame)
            self.main_paned.add(self.right_container, weight=1)
            self.right_panel_visible = True
        
        # 保存状态到配置
        self.config_manager.set_command_panel_visible(self.right_panel_visible)
    
    def _add_work_tab(self):
        """添加工作Tab"""
        # 第一个Tab显示为默认标题，其他显示New Tab
        is_first_tab = (self.tab_counter == 1)
        tab_name = 'New Tab'
        
        work_tab = WorkTab(self.work_notebook, self.config_manager, tab_name, is_first_tab)
        
        # 在加号Tab之前插入新Tab
        insert_index = self.work_notebook.index('end') - 1
        self.work_notebook.insert(insert_index, work_tab, text=tab_name)
        
        self.work_tabs.append(work_tab)
        self.tab_counter += 1
        
        # 切换到新Tab
        self.work_notebook.select(insert_index)
        
        # 更新Tab标题，添加关闭按钮
        self._update_tab_title(insert_index, tab_name)
    
    def _update_tab_title(self, index, title):
        """更新Tab标题"""
        self.work_notebook.tab(index, text=title)
    
    def _close_tab(self, index):
        """关闭指定Tab"""
        # 至少保留一个Tab，静默处理
        if len(self.work_tabs) <= 1:
            return
        
        # 关闭串口连接
        tab = self.work_tabs[index]
        if hasattr(tab, 'serial_manager') and tab.serial_manager.is_open():
            tab._disconnect()
        
        # 移除Tab
        self.work_notebook.forget(index)
        self.work_tabs.pop(index)
        
        # 如果有Tab剩余，选中前一个
        if self.work_tabs:
            new_index = max(0, index - 1)
            self.work_notebook.select(new_index)
    
    def _get_current_work_tab(self):
        """获取当前工作Tab"""
        try:
            index = self.work_notebook.index('current')
            # 确保不是加号Tab
            if index < len(self.work_tabs):
                return self.work_tabs[index]
            return None
        except:
            return None
    
    def _send_quick_command(self, command):
        """发送快捷指令"""
        work_tab = self._get_current_work_tab()
        if work_tab:
            work_tab.send_text.delete('1.0', 'end')
            work_tab.send_text.insert('1.0', command)
            work_tab._send_data()
    
    def _send_from_history(self, data):
        """从历史发送"""
        work_tab = self._get_current_work_tab()
        if work_tab:
            work_tab.send_text.delete('1.0', 'end')
            work_tab.send_text.insert('1.0', data)
    
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
    
    def _show_about(self):
        """显示关于"""
        about_text = f"""Quickky Serial Tool

版本: {VERSION}
构建时间: {BUILD_TIME}

作者: Aaz
邮箱: vitoyuz@foxmail.com

一个功能强大的串口调试工具"""
        
        messagebox.showinfo('关于', about_text)
    
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

