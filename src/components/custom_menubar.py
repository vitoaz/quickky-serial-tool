"""
自定义菜单栏控件

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk


class CustomMenuBar(tk.Frame):
    """自定义菜单栏控件"""
    
    def __init__(self, parent, **kwargs):
        """
        初始化自定义菜单栏
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent, **kwargs)
        self.menus = {}  # 存储菜单项 {菜单名: {子菜单}}
        self.menu_buttons = {}  # 存储菜单按钮
        self.current_popup = None  # 当前打开的弹出菜单
        
        # 主题颜色（默认值，可以通过apply_theme更新）
        self.colors = {
            'bg': '#F5F5F5',
            'fg': '#000000',
            'active_bg': '#0078D7',
            'active_fg': '#FFFFFF',
            'select_color': '#0078D7',
            'border': '#D0D0D0',
            'hover_bg': '#E5F1FB'  # hover背景色
        }
        
        # 添加底部边框
        self.bottom_border = tk.Frame(self, height=1, bg=self.colors['border'])
        self.bottom_border.pack(side='bottom', fill='x')
        
    def add_menu(self, label, menu_items):
        """
        添加菜单
        
        Args:
            label: 菜单标签
            menu_items: 菜单项列表，格式：
                [
                    {'label': '标签', 'command': 回调函数},
                    {'label': '标签', 'type': 'checkbutton', 'variable': tk.Variable, 'command': 回调函数},
                    {'label': '标签', 'type': 'radiobutton', 'variable': tk.Variable, 'value': 值, 'command': 回调函数},
                    {'type': 'separator'},
                    {'label': '标签', 'submenu': [子菜单项列表]}
                ]
        """
        self.menus[label] = menu_items
        
        # 创建菜单按钮
        btn = tk.Label(
            self,
            text=label,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            padx=10,
            pady=3
        )
        btn.pack(side='left')
        self.menu_buttons[label] = btn
        
        # 绑定事件
        btn.bind('<Button-1>', lambda e, l=label: self._show_menu(e, l))
        btn.bind('<Enter>', lambda e, b=btn: self._on_menu_enter(b))
        btn.bind('<Leave>', lambda e, b=btn: self._on_menu_leave(b))
        
    def _on_menu_enter(self, button):
        """菜单按钮鼠标进入"""
        if not self.current_popup:
            button.config(bg=self.colors['hover_bg'], fg=self.colors['fg'])
        
    def _on_menu_leave(self, button):
        """菜单按钮鼠标离开"""
        if not self.current_popup:
            button.config(bg=self.colors['bg'], fg=self.colors['fg'])
    
    def _show_menu(self, event, label):
        """显示菜单"""
        # 如果有打开的菜单，先关闭
        if self.current_popup:
            self.current_popup.destroy()
            self.current_popup = None
            # 恢复所有按钮颜色
            for btn in self.menu_buttons.values():
                btn.config(bg=self.colors['bg'], fg=self.colors['fg'])
            return
        
        # 高亮当前菜单按钮（使用hover颜色）
        button = self.menu_buttons[label]
        button.config(bg=self.colors['hover_bg'], fg=self.colors['fg'])
        
        # 创建弹出菜单
        menu_items = self.menus[label]
        self.current_popup = tk.Toplevel(self)
        self.current_popup.wm_overrideredirect(True)  # 无边框窗口
        self.current_popup.wm_attributes('-topmost', True)
        
        # 计算位置
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        self.current_popup.wm_geometry(f'+{x}+{y}')
        
        # 创建菜单内容容器（用于边框）
        border_frame = tk.Frame(
            self.current_popup,
            bg=self.colors['border'],
            padx=1,
            pady=1
        )
        border_frame.pack(fill='both', expand=True)
        
        # 创建菜单内容
        menu_frame = tk.Frame(
            border_frame,
            bg=self.colors['bg']
        )
        menu_frame.pack(fill='both', expand=True)
        
        self._create_menu_items(menu_frame, menu_items)
        
        # 绑定失去焦点时关闭
        self.current_popup.bind('<FocusOut>', lambda e: self._close_popup())
        # 点击外部关闭
        self.current_popup.bind('<Button-1>', lambda e: self._close_popup())
        
        # 确保窗口获得焦点
        self.current_popup.focus_set()
        
    def _create_menu_items(self, parent, items):
        """创建菜单项"""
        for item in items:
            if item.get('type') == 'separator':
                # 分隔线
                sep = tk.Frame(parent, height=1, bg=self.colors['border'], bd=0)
                sep.pack(fill='x', padx=2, pady=2)
            elif item.get('type') == 'checkbutton':
                # 复选框菜单项
                self._create_checkbutton_item(parent, item)
            elif item.get('type') == 'radiobutton':
                # 单选框菜单项
                self._create_radiobutton_item(parent, item)
            elif 'submenu' in item:
                # 子菜单
                self._create_submenu_item(parent, item)
            else:
                # 普通菜单项
                self._create_normal_item(parent, item)
    
    def _create_normal_item(self, parent, item):
        """创建普通菜单项"""
        label = tk.Label(
            parent,
            text=item['label'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w',
            padx=30,
            pady=6
        )
        label.pack(fill='x')
        
        # 绑定事件
        label.bind('<Button-1>', lambda e: self._on_menu_click(item.get('command')))
        label.bind('<Enter>', lambda e: label.config(bg=self.colors['hover_bg'], fg=self.colors['fg']))
        label.bind('<Leave>', lambda e: label.config(bg=self.colors['bg'], fg=self.colors['fg']))
    
    def _create_checkbutton_item(self, parent, item):
        """创建复选框菜单项"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill='x')
        
        # 复选框指示器容器（用于左边距）
        check_container = tk.Frame(frame, bg=self.colors['bg'])
        check_container.pack(side='left', padx=(10, 0))
        
        var = item.get('variable')
        check_label = tk.Label(
            check_container,
            text='✓' if var and var.get() else ' ',
            bg=self.colors['bg'],
            fg=self.colors['select_color'],
            width=2,
            anchor='e'
        )
        check_label.pack(side='left')
        
        # 文本标签
        text_label = tk.Label(
            frame,
            text=item['label'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w',
            padx=2,
            pady=6
        )
        text_label.pack(side='left', fill='x', expand=True, padx=(2, 20))
        
        # 绑定事件
        def on_check_click(e):
            if var:
                var.set(not var.get())
                check_label.config(text='✓' if var.get() else ' ')
            if item.get('command'):
                item['command']()
            self._close_popup()
        
        for widget in [check_container, check_label, text_label]:
            widget.bind('<Button-1>', on_check_click)
            widget.bind('<Enter>', lambda e: self._set_frame_active(frame, True))
            widget.bind('<Leave>', lambda e: self._set_frame_active(frame, False))
    
    def _create_radiobutton_item(self, parent, item):
        """创建单选框菜单项"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(fill='x')
        
        # 单选框指示器容器（用于左边距）
        radio_container = tk.Frame(frame, bg=self.colors['bg'])
        radio_container.pack(side='left', padx=(10, 0))
        
        var = item.get('variable')
        value = item.get('value')
        radio_label = tk.Label(
            radio_container,
            text='✓' if var and var.get() == value else ' ',
            bg=self.colors['bg'],
            fg=self.colors['select_color'],
            width=2,
            anchor='e'
        )
        radio_label.pack(side='left')
        
        # 文本标签
        text_label = tk.Label(
            frame,
            text=item['label'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w',
            padx=2,
            pady=6
        )
        text_label.pack(side='left', fill='x', expand=True, padx=(2, 20))
        
        # 绑定事件
        def on_radio_click(e):
            if var:
                var.set(value)
                # 更新所有单选框的显示状态
                self._close_popup()
                # 重新打开菜单以更新显示
            if item.get('command'):
                item['command']()
        
        for widget in [radio_container, radio_label, text_label]:
            widget.bind('<Button-1>', on_radio_click)
            widget.bind('<Enter>', lambda e: self._set_frame_active(frame, True))
            widget.bind('<Leave>', lambda e: self._set_frame_active(frame, False))
    
    def _create_submenu_item(self, parent, item):
        """创建子菜单项"""
        label = tk.Label(
            parent,
            text=item['label'] + ' ▶',
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w',
            padx=20,
            pady=4
        )
        label.pack(fill='x')
        
        # 绑定事件
        label.bind('<Enter>', lambda e: label.config(bg=self.colors['hover_bg'], fg=self.colors['fg']))
        label.bind('<Leave>', lambda e: label.config(bg=self.colors['bg'], fg=self.colors['fg']))
    
    def _set_frame_active(self, frame, active):
        """设置frame及其所有子控件的激活状态"""
        bg = self.colors['hover_bg'] if active else self.colors['bg']
        fg = self.colors['fg']
        
        def update_widget(widget):
            """递归更新控件"""
            try:
                if isinstance(widget, tk.Frame):
                    widget.config(bg=bg)
                elif isinstance(widget, tk.Label):
                    if widget.cget('text') in ['✓', ' ', '●', '○']:
                        widget.config(bg=bg, fg=self.colors['select_color'])
                    else:
                        widget.config(bg=bg, fg=fg)
                
                # 递归处理子控件
                for child in widget.winfo_children():
                    update_widget(child)
            except:
                pass
        
        update_widget(frame)
    
    def _on_menu_click(self, command):
        """菜单项点击事件"""
        self._close_popup()
        if command:
            command()
    
    def _close_popup(self):
        """关闭弹出菜单"""
        if self.current_popup:
            self.current_popup.destroy()
            self.current_popup = None
            # 恢复所有按钮颜色
            for btn in self.menu_buttons.values():
                btn.config(bg=self.colors['bg'], fg=self.colors['fg'])
    
    def apply_theme(self, colors):
        """
        应用主题颜色
        
        Args:
            colors: 颜色字典，包含：
                - labelframe_bg: 背景色
                - foreground: 前景色
                - selectbackground: 选中背景色
                - selectforeground: 选中前景色
                - checkbox_selected: 复选框选中色
                - border: 边框色
        """
        bg_color = colors.get('labelframe_bg', '#F5F5F5')
        
        # 计算hover颜色（相对背景色稍微高亮）
        hover_bg = self._calculate_hover_color(bg_color)
        
        self.colors = {
            'bg': bg_color,
            'fg': colors.get('foreground', '#000000'),
            'active_bg': colors.get('selectbackground', '#0078D7'),
            'active_fg': colors.get('selectforeground', '#FFFFFF'),
            'select_color': colors.get('checkbox_selected', '#0078D7'),
            'border': colors.get('border', '#D0D0D0'),
            'hover_bg': hover_bg
        }
        
        # 更新组件背景
        self.config(bg=self.colors['bg'])
        
        # 更新底部边框
        if hasattr(self, 'bottom_border'):
            self.bottom_border.config(bg=self.colors['border'])
        
        # 更新所有菜单按钮
        for btn in self.menu_buttons.values():
            btn.config(bg=self.colors['bg'], fg=self.colors['fg'])
    
    def _calculate_hover_color(self, bg_color):
        """
        计算hover颜色（相对背景色稍微高亮）
        
        Args:
            bg_color: 背景色（hex格式）
        
        Returns:
            hover颜色（hex格式）
        """
        try:
            # 移除#号
            if bg_color.startswith('#'):
                bg_color = bg_color[1:]
            
            # 转换为RGB
            r = int(bg_color[0:2], 16)
            g = int(bg_color[2:4], 16)
            b = int(bg_color[4:6], 16)
            
            # 判断是暗色还是亮色
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            
            if brightness > 128:
                # 亮色背景：稍微变暗
                factor = 0.92
            else:
                # 暗色背景：变亮更多，使hover更明显
                factor = 1.25
            
            # 应用变化
            r = int(min(255, max(0, r * factor)))
            g = int(min(255, max(0, g * factor)))
            b = int(min(255, max(0, b * factor)))
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            # 出错时返回默认值
            return '#E5F1FB' if brightness > 128 else '#3C3C3C'

