"""
快捷指令面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils.dialog_utils import DialogUtils

class QuickCommandsPanel(ttk.Frame):
    """快捷指令面板"""
    
    def __init__(self, parent, config_manager, on_send_callback=None):
        """
        初始化快捷指令面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_send_callback: 发送指令回调函数(command_data, mode)
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.on_send_callback = on_send_callback
        self.drag_item = None
        
        self._create_widgets()
        self._load_groups()
    
    def _create_widgets(self):
        """创建控件"""
        # 使用Notebook创建分组Tab
        self.group_notebook = ttk.Notebook(self)
        self.group_notebook.pack(fill='both', expand=True)
        
        # 绑定右键菜单到Notebook的tab区域
        self.group_notebook.bind('<Button-3>', self._show_group_menu)
    
    def _load_groups(self):
        """加载分组"""
        # 清空现有Tab
        for tab in self.group_notebook.tabs():
            self.group_notebook.forget(tab)
        
        groups = self.config_manager.get_quick_command_groups()
        
        # 如果没有分组，创建默认分组
        if not groups:
            groups = [{'name': '默认', 'commands': []}]
            self.config_manager.set_quick_command_groups(groups)
        
        # 为每个分组创建Tab
        for group in groups:
            self._create_group_tab(group)
    
    def _create_group_tab(self, group):
        """创建分组Tab"""
        tab_frame = ttk.Frame(self.group_notebook)
        self.group_notebook.add(tab_frame, text=group['name'])
        
        # 创建Treeview
        tree = ttk.Treeview(tab_frame, columns=('name', 'mode', 'content'), show='headings', height=15)
        tree.heading('name', text='名称')
        tree.heading('mode', text='模式')
        tree.heading('content', text='内容')
        tree.column('name', width=60, minwidth=40)
        tree.column('mode', width=40, minwidth=40)
        tree.column('content', width=150, minwidth=100)
        
        # 设置字体大小
        style = ttk.Style()
        style.configure('Treeview', font=('', 9))
        style.configure('Treeview.Heading', font=('', 9))
        
        scrollbar = ttk.Scrollbar(tab_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # 加载该分组的指令
        for cmd in group['commands']:
            mode = cmd.get('mode', 'TEXT')
            # 转义换行符用于显示，确保command是字符串
            command_str = str(cmd['command']) if cmd['command'] is not None else ''
            display_command = command_str.replace('\n', '\\n').replace('\r', '\\r')
            tree.insert('', 'end', values=(cmd['name'], mode, display_command))
        
        # 双击发送
        tree.bind('<Double-Button-1>', self._on_double_click)
        
        # 右键菜单
        tree.bind('<Button-3>', self._show_command_menu)
        
        # 拖动排序
        tree.bind('<Button-1>', self._on_drag_start)
        tree.bind('<B1-Motion>', self._on_drag_motion)
        tree.bind('<ButtonRelease-1>', self._on_drag_release)
    
    def _show_group_menu(self, event):
        """显示分组右键菜单"""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='新建分组', command=self._add_group)
        
        # 检查是否点击在Tab上
        try:
            clicked_tab = self.group_notebook.tk.call(self.group_notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                tab_index = int(clicked_tab)
                menu.add_separator()
                menu.add_command(label='重命名分组', command=lambda: self._rename_group(tab_index))
                menu.add_command(label='删除分组', command=lambda: self._delete_group(tab_index))
        except:
            pass
        
        menu.post(event.x_root, event.y_root)
    
    def _show_command_menu(self, event):
        """显示指令右键菜单"""
        tree = event.widget
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='添加指令', command=lambda: self._add_command(tree))
        
        # 检查是否点击在项目上
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.add_separator()
            menu.add_command(label='编辑指令', command=lambda: self._edit_command(tree))
            menu.add_command(label='删除指令', command=lambda: self._delete_command(tree))
        
        menu.post(event.x_root, event.y_root)
    
    def _add_group(self):
        """添加分组"""
        dialog = InputDialog(self.winfo_toplevel(), '新建分组', '请输入分组名称:')
        if dialog.result:
            groups = self.config_manager.get_quick_command_groups()
            groups.append({'name': dialog.result, 'commands': []})
            self.config_manager.set_quick_command_groups(groups)
            self._load_groups()
            # 切换到新分组
            self.group_notebook.select(len(groups) - 1)
    
    def _rename_group(self, tab_index):
        """重命名分组"""
        groups = self.config_manager.get_quick_command_groups()
        old_name = groups[tab_index]['name']
        dialog = InputDialog(self.winfo_toplevel(), '重命名分组', '请输入新的分组名称:', old_name)
        if dialog.result and dialog.result != old_name:
            groups[tab_index]['name'] = dialog.result
            self.config_manager.set_quick_command_groups(groups)
            self._load_groups()
            self.group_notebook.select(tab_index)
    
    def _delete_group(self, tab_index):
        """删除分组"""
        groups = self.config_manager.get_quick_command_groups()
        if len(groups) <= 1:
            messagebox.showwarning('警告', '至少需要保留一个分组')
            return
        
        if messagebox.askyesno('确认', f'确定要删除分组"{groups[tab_index]["name"]}"吗？'):
            groups.pop(tab_index)
            self.config_manager.set_quick_command_groups(groups)
            self._load_groups()
    
    def _add_command(self, tree):
        """添加指令"""
        dialog = CommandDialog(self.winfo_toplevel(), '添加快捷指令')
        if dialog.result:
            name, mode, command = dialog.result
            
            # 获取当前分组索引
            current_tab = self.group_notebook.index('current')
            groups = self.config_manager.get_quick_command_groups()
            groups[current_tab]['commands'].append({
                'name': name,
                'mode': mode,
                'command': command
            })
            self.config_manager.set_quick_command_groups(groups)
            self._load_groups()
            self.group_notebook.select(current_tab)
    
    def _edit_command(self, tree):
        """编辑指令"""
        selection = tree.selection()
        if not selection:
            return
        
        # 获取当前分组索引和指令索引
        current_tab = self.group_notebook.index('current')
        index = tree.index(selection[0])
        groups = self.config_manager.get_quick_command_groups()
        cmd = groups[current_tab]['commands'][index]
        
        dialog = CommandDialog(self.winfo_toplevel(), '编辑快捷指令', 
                               cmd['name'], cmd.get('mode', 'TEXT'), cmd['command'])
        if dialog.result:
            name, mode, command = dialog.result
            groups[current_tab]['commands'][index] = {
                'name': name,
                'mode': mode,
                'command': command
            }
            self.config_manager.set_quick_command_groups(groups)
            self._load_groups()
            self.group_notebook.select(current_tab)
    
    def _delete_command(self, tree):
        """删除指令"""
        selection = tree.selection()
        if not selection:
            return
        
        if messagebox.askyesno('确认', '确定要删除选中的指令吗？'):
            current_tab = self.group_notebook.index('current')
            index = tree.index(selection[0])
            groups = self.config_manager.get_quick_command_groups()
            groups[current_tab]['commands'].pop(index)
            self.config_manager.set_quick_command_groups(groups)
            self._load_groups()
            self.group_notebook.select(current_tab)
    
    def _on_double_click(self, event):
        """双击发送指令"""
        tree = event.widget
        selection = tree.selection()
        if selection and self.on_send_callback:
            item = tree.item(selection[0])
            values = item['values']
            command = values[2]  # 内容在第3列
            mode = values[1]      # 模式在第2列
            # 传递指令和模式给回调
            self.on_send_callback(command, mode)
    
    def _on_drag_start(self, event):
        """开始拖动"""
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            self.drag_item = (tree, item)
    
    def _on_drag_motion(self, event):
        """拖动中"""
        if self.drag_item:
            tree, drag_item = self.drag_item
            target = tree.identify_row(event.y)
            if target and target != drag_item:
                # 移动项目
                tree.move(drag_item, '', tree.index(target))
    
    def _on_drag_release(self, event):
        """结束拖动"""
        if self.drag_item:
            tree, _ = self.drag_item
            # 保存新顺序
            current_tab = self.group_notebook.index('current')
            groups = self.config_manager.get_quick_command_groups()
            
            commands = []
            for item in tree.get_children():
                values = tree.item(item)['values']
                commands.append({
                    'name': values[0],
                    'mode': values[1],
                    'command': values[2]
                })
            groups[current_tab]['commands'] = commands
            self.config_manager.set_quick_command_groups(groups)
            self.drag_item = None

class CommandDialog(tk.Toplevel):
    """指令编辑对话框"""
    
    def __init__(self, parent, title, name='', mode='TEXT', command=''):
        super().__init__(parent)
        self.title(title)
        self.result = None
        
        # 设置模态
        self.transient(parent)
        
        # 先隐藏窗口，避免闪烁
        self.withdraw()
        
        # 名称
        ttk.Label(self, text='名称:').grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.name_entry = ttk.Entry(self, width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, columnspan=2)
        self.name_entry.insert(0, name)
        
        # 模式
        ttk.Label(self, text='模式:').grid(row=1, column=0, padx=10, pady=10, sticky='w')
        mode_frame = ttk.Frame(self)
        mode_frame.grid(row=1, column=1, padx=10, pady=10, sticky='w', columnspan=2)
        
        self.mode_var = tk.StringVar(value=mode)
        ttk.Radiobutton(mode_frame, text='TEXT', variable=self.mode_var, value='TEXT').pack(side='left', padx=5)
        ttk.Radiobutton(mode_frame, text='HEX', variable=self.mode_var, value='HEX').pack(side='left', padx=5)
        
        # 内容
        ttk.Label(self, text='内容:').grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        self.command_text = tk.Text(self, width=30, height=5)
        self.command_text.grid(row=2, column=1, padx=10, pady=10, columnspan=2)
        self.command_text.insert('1.0', command)
        
        # 按钮
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text='确定', command=self._ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='取消', command=self._cancel).pack(side='left', padx=5)
        
        # 使用工具类显示对话框
        DialogUtils.show_modal_dialog(self, parent)
        
        self.name_entry.focus()
        self.wait_window()
    
    def _ok(self):
        """确定"""
        name = self.name_entry.get().strip()
        mode = self.mode_var.get()
        command = self.command_text.get('1.0', 'end-1c').strip()
        
        if not name or not command:
            messagebox.showwarning('警告', '名称和内容不能为空')
            return
        
        self.result = (name, mode, command)
        self.destroy()
    
    def _cancel(self):
        """取消"""
        self.destroy()

class InputDialog(tk.Toplevel):
    """输入对话框"""
    
    def __init__(self, parent, title, label, initial_value=''):
        super().__init__(parent)
        self.title(title)
        self.result = None
        
        # 设置模态
        self.transient(parent)
        
        # 先隐藏窗口，避免闪烁
        self.withdraw()
        
        # 标签
        ttk.Label(self, text=label).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        
        # 输入框
        self.entry = ttk.Entry(self, width=30)
        self.entry.grid(row=0, column=1, padx=10, pady=10)
        self.entry.insert(0, initial_value)
        self.entry.select_range(0, 'end')
        
        # 按钮
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text='确定', command=self._ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='取消', command=self._cancel).pack(side='left', padx=5)
        
        # 使用工具类显示对话框
        DialogUtils.show_modal_dialog(self, parent)
        
        self.entry.focus()
        
        # 绑定回车键
        self.entry.bind('<Return>', lambda e: self._ok())
        
        self.wait_window()
    
    def _ok(self):
        """确定"""
        value = self.entry.get().strip()
        if value:
            self.result = value
            self.destroy()
    
    def _cancel(self):
        """取消"""
        self.destroy()

