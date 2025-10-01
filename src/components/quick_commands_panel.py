"""
快捷指令面板组件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class QuickCommandsPanel(ttk.Frame):
    """快捷指令面板"""
    
    def __init__(self, parent, config_manager, on_send_callback=None):
        """
        初始化快捷指令面板
        
        Args:
            parent: 父控件
            config_manager: 配置管理器
            on_send_callback: 发送指令回调函数
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.on_send_callback = on_send_callback
        self.drag_item = None
        
        self._create_widgets()
        self._load_commands()
    
    def _create_widgets(self):
        """创建控件"""
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(toolbar, text='添加', command=self._add_command, width=8).pack(side='left', padx=2)
        ttk.Button(toolbar, text='编辑', command=self._edit_command, width=8).pack(side='left', padx=2)
        ttk.Button(toolbar, text='删除', command=self._delete_command, width=8).pack(side='left', padx=2)
        
        # 列表
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建Treeview（添加模式列）
        self.tree = ttk.Treeview(list_frame, columns=('name', 'mode', 'command'), show='headings', height=15)
        self.tree.heading('name', text='名称')
        self.tree.heading('mode', text='模式')
        self.tree.heading('command', text='指令')
        self.tree.column('name', width=80)
        self.tree.column('mode', width=50)
        self.tree.column('command', width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 双击发送
        self.tree.bind('<Double-Button-1>', self._on_double_click)
        
        # 拖动排序
        self.tree.bind('<Button-1>', self._on_drag_start)
        self.tree.bind('<B1-Motion>', self._on_drag_motion)
        self.tree.bind('<ButtonRelease-1>', self._on_drag_release)
    
    def _load_commands(self):
        """加载快捷指令"""
        self.tree.delete(*self.tree.get_children())
        commands = self.config_manager.get_quick_commands()
        for cmd in commands:
            mode = cmd.get('mode', 'TEXT')
            self.tree.insert('', 'end', values=(cmd['name'], mode, cmd['command']))
    
    def _add_command(self):
        """添加指令"""
        dialog = CommandDialog(self.winfo_toplevel(), '添加快捷指令')
        if dialog.result:
            name, mode, command = dialog.result
            self.config_manager.add_quick_command(name, command, mode)
            self._load_commands()
    
    def _edit_command(self):
        """编辑指令"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning('警告', '请先选择要编辑的指令')
            return
        
        index = self.tree.index(selection[0])
        commands = self.config_manager.get_quick_commands()
        cmd = commands[index]
        
        dialog = CommandDialog(self.winfo_toplevel(), '编辑快捷指令', 
                               cmd['name'], cmd.get('mode', 'TEXT'), cmd['command'])
        if dialog.result:
            name, mode, command = dialog.result
            commands[index] = {'name': name, 'mode': mode, 'command': command}
            self.config_manager.config['quick_commands'] = commands
            self.config_manager.save_config()
            self._load_commands()
    
    def _delete_command(self):
        """删除指令"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning('警告', '请先选择要删除的指令')
            return
        
        if messagebox.askyesno('确认', '确定要删除选中的指令吗？'):
            index = self.tree.index(selection[0])
            self.config_manager.remove_quick_command(index)
            self._load_commands()
    
    def _on_double_click(self, event):
        """双击发送指令"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            command = item['values'][2]  # 指令在第3列
            if self.on_send_callback:
                self.on_send_callback(command)
    
    def _on_drag_start(self, event):
        """开始拖动"""
        item = self.tree.identify_row(event.y)
        if item:
            self.drag_item = item
    
    def _on_drag_motion(self, event):
        """拖动中"""
        if self.drag_item:
            target = self.tree.identify_row(event.y)
            if target and target != self.drag_item:
                # 移动项目
                self.tree.move(self.drag_item, '', self.tree.index(target))
    
    def _on_drag_release(self, event):
        """结束拖动"""
        if self.drag_item:
            # 保存新顺序
            commands = []
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                commands.append({
                    'name': values[0],
                    'mode': values[1],
                    'command': values[2]
                })
            self.config_manager.config['quick_commands'] = commands
            self.config_manager.save_config()
            self.drag_item = None

class CommandDialog(tk.Toplevel):
    """指令编辑对话框"""
    
    def __init__(self, parent, title, name='', mode='TEXT', command=''):
        super().__init__(parent)
        self.title(title)
        self.result = None
        
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
        
        # 指令
        ttk.Label(self, text='指令:').grid(row=2, column=0, padx=10, pady=10, sticky='nw')
        self.command_text = tk.Text(self, width=30, height=5)
        self.command_text.grid(row=2, column=1, padx=10, pady=10, columnspan=2)
        self.command_text.insert('1.0', command)
        
        # 按钮
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text='确定', command=self._ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='取消', command=self._cancel).pack(side='left', padx=5)
        
        # 设置对话框
        self.transient(parent)
        self.grab_set()
        
        # 相对主窗口居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f'+{x}+{y}')
        
        self.name_entry.focus()
        self.wait_window()
    
    def _ok(self):
        """确定"""
        name = self.name_entry.get().strip()
        mode = self.mode_var.get()
        command = self.command_text.get('1.0', 'end-1c').strip()
        
        if not name or not command:
            messagebox.showwarning('警告', '名称和指令不能为空')
            return
        
        self.result = (name, mode, command)
        self.destroy()
    
    def _cancel(self):
        """取消"""
        self.destroy()

