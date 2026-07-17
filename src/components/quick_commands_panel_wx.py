"""
快捷指令面板组件 (wxPython版本)

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

import wx
import wx.lib.agw.aui as aui
import wx.lib.agw.flatnotebook as fnb
from utils.hex_utils import HexUtils
from utils.custom_controls_wx import ThemedButton, ThemedNotebook


class QuickCommandsPanel(wx.Panel):
    """快捷指令面板"""
    
    def __init__(self, parent, config_manager, main_window=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.main_window = main_window
        self.drag_item = None  # 用于拖动排序
        
        self._create_widgets()
        self._load_groups()
    
    def _create_widgets(self):
        """创建控件"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 使用ThemedNotebook创建分组Tab，允许拖动调整顺序
        self.group_notebook = ThemedNotebook(self, allow_drag=True)
        # 延迟绑定右键事件到Tab区域（用于Tab标签上的右键菜单）
        wx.CallAfter(self._bind_right_click_event)
        
        # 绑定Tab拖动完成事件，保存新的顺序
        self.group_notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_DROPPED, self._on_tab_dropped)
        
        sizer.Add(self.group_notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def _bind_right_click_event(self):
        """绑定右键点击事件（延迟绑定，确保_pages已创建）"""
        if hasattr(self.group_notebook, '_pages') and self.group_notebook._pages:
            self.group_notebook._pages.Bind(wx.EVT_RIGHT_DOWN, self._show_group_menu)
        else:
            self.group_notebook.Bind(wx.EVT_RIGHT_DOWN, self._show_group_menu)
    
    def _on_tab_dropped(self, event):
        """Tab拖动完成后，保存新的分组顺序"""
        # 获取当前所有Tab的顺序，重新构建分组列表
        new_groups = []
        for i in range(self.group_notebook.GetPageCount()):
            tab_name = self.group_notebook.GetPageText(i)
            # 从原分组列表中找到对应的分组数据
            groups = self.config_manager.get_quick_command_groups()
            for group in groups:
                if group['name'] == tab_name:
                    new_groups.append(group)
                    break
        
        # 保存新的分组顺序
        if new_groups:
            self.config_manager.set_quick_command_groups(new_groups)
    
    def _load_groups(self):
        """加载分组"""
        # 清空现有Tab
        while self.group_notebook.GetPageCount() > 0:
            self.group_notebook.DeletePage(0)

        groups = self.config_manager.get_quick_command_groups()

        # 如果没有分组，创建默认分组
        if not groups:
            groups = [{'name': '默认', 'commands': []}]
            self.config_manager.set_quick_command_groups(groups)

        # 为每个分组创建Tab
        for group in groups:
            self._create_group_tab(group)

    def _refresh_tab(self, tab_index):
        """刷新指定Tab的内容"""
        if tab_index < 0 or tab_index >= self.group_notebook.GetPageCount():
            return

        # 获取Tab页面
        page = self.group_notebook.GetPage(tab_index)
        if not page:
            return

        # 查找ListCtrl
        list_ctrl = None
        for child in page.GetChildren():
            if isinstance(child, wx.ListCtrl):
                list_ctrl = child
                break

        if not list_ctrl:
            return

        # 清空现有项目
        list_ctrl.DeleteAllItems()

        # 从配置中重新加载该分组的数据
        groups = self.config_manager.get_quick_command_groups()
        if tab_index < len(groups):
            group = groups[tab_index]
            for cmd in group['commands']:
                name = cmd.get('name', '')
                mode = cmd.get('mode', 'TEXT')
                # 获取data字段，如果不存在则使用command字段
                data = cmd.get('data', cmd.get('command', ''))
                # 确保data是字符串
                if not isinstance(data, str):
                    data = str(data) if data is not None else ''
                # 转义换行符用于显示
                display_data = data.replace('\n', '\\n').replace('\r', '\\r')

                # 在数据前面添加模式标注
                mode_prefix = '[H] ' if mode == 'HEX' else '[T] '
                display_data = mode_prefix + display_data

                index = list_ctrl.InsertItem(list_ctrl.GetItemCount(), name)
                list_ctrl.SetItem(index, 1, display_data)

        # 重新应用主题到这个Tab
        if self.main_window and hasattr(self.main_window, 'theme_manager'):
            self._apply_theme_to_tab(tab_index)

    def _create_group_tab(self, group):
        """创建分组Tab"""
        tab_panel = wx.Panel(self.group_notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建ListCtrl
        list_ctrl = wx.ListCtrl(tab_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        list_ctrl.InsertColumn(0, '名称', width=80)
        list_ctrl.InsertColumn(1, '数据', width=155)
        
        # 设置较小的字体
        font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        list_ctrl.SetFont(font)
        
        # 加载该分组的指令
        for cmd in group['commands']:
            name = cmd.get('name', '')
            mode = cmd.get('mode', 'TEXT')
            # 获取data字段，如果不存在则使用command字段
            data = cmd.get('data', cmd.get('command', ''))
            # 确保data是字符串
            if not isinstance(data, str):
                data = str(data) if data is not None else ''
            # 转义换行符用于显示
            display_data = data.replace('\n', '\\n').replace('\r', '\\r')
            
            # 在数据前面添加模式标注
            mode_prefix = '[H] ' if mode == 'HEX' else '[T] '
            display_data = mode_prefix + display_data
            
            index = list_ctrl.InsertItem(list_ctrl.GetItemCount(), name)
            list_ctrl.SetItem(index, 1, display_data)
        
        sizer.Add(list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        tab_panel.SetSizer(sizer)
        
        self.group_notebook.AddPage(tab_panel, group['name'])
        
        # 绑定事件
        list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_item_double_click)
        list_ctrl.Bind(wx.EVT_RIGHT_DOWN, self._show_command_menu)
        
        # 绑定拖动排序事件
        list_ctrl.Bind(wx.EVT_LIST_BEGIN_DRAG, self._on_drag_start)
        list_ctrl.Bind(wx.EVT_MOTION, self._on_drag_motion)
        list_ctrl.Bind(wx.EVT_LEFT_UP, self._on_drag_release)
    
    def _show_group_menu(self, event):
        """显示分组右键菜单"""
        # 获取鼠标位置
        pos = event.GetPosition()
        
        # 获取点击的Tab索引
        tab_index = -1
        try:
            if hasattr(self.group_notebook, '_pages') and self.group_notebook._pages:
                hit_result = self.group_notebook._pages.HitTest(pos)
                
                # HitTest返回元组 (where, tab_index)
                # where: 0=不在Tab上, 1=在Tab上
                if isinstance(hit_result, tuple) and len(hit_result) >= 2:
                    where = hit_result[0]
                    tab_index = hit_result[1]
                    
                    # 只在Tab上才显示菜单
                    if where != 1:
                        tab_index = -1
        except Exception as e:
            tab_index = -1
        
        # 如果没有点击在Tab上，使用当前选中的Tab
        if tab_index < 0:
            tab_index = self.group_notebook.GetSelection()
        
        menu = wx.Menu()
        add_group_item = menu.Append(wx.ID_ANY, '新建分组')
        
        if tab_index >= 0:
            menu.AppendSeparator()
            rename_item = menu.Append(wx.ID_ANY, '编辑分组')
            delete_item = menu.Append(wx.ID_ANY, '删除分组')
            
            self.Bind(wx.EVT_MENU, lambda e: self._rename_group(tab_index), rename_item)
            self.Bind(wx.EVT_MENU, lambda e: self._delete_group(tab_index), delete_item)
        
        self.Bind(wx.EVT_MENU, self._add_group, add_group_item)
        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def _show_command_menu(self, event):
        """显示指令右键菜单"""
        # 获取当前选中的ListCtrl
        current_page = self.group_notebook.GetCurrentPage()
        if not current_page:
            return
        
        list_ctrl = None
        for child in current_page.GetChildren():
            if isinstance(child, wx.ListCtrl):
                list_ctrl = child
                break
        
        if not list_ctrl:
            return
        
        # 获取鼠标点击的项 - 使用事件对象获取相对于list_ctrl的位置
        pos = event.GetPosition()
        # 将panel的坐标转换为list_ctrl的坐标
        list_ctrl_pos = list_ctrl.ScreenToClient(current_page.ClientToScreen(pos))
        item_index, flags = list_ctrl.HitTest(list_ctrl_pos)
        
        menu = wx.Menu()
        
        if item_index >= 0:
            # 清除之前的选中
            selected = list_ctrl.GetFirstSelected()
            while selected != -1:
                list_ctrl.Select(selected, False)
                selected = list_ctrl.GetNextSelected(selected)
            # 选中右键点击的项
            list_ctrl.Select(item_index)
            list_ctrl.Focus(item_index)
            
            send_item = menu.Append(wx.ID_ANY, '发送')
            edit_item = menu.Append(wx.ID_ANY, '编辑指令')
            delete_item = menu.Append(wx.ID_ANY, '删除指令')
            menu.AppendSeparator()
            
            self.Bind(wx.EVT_MENU, lambda e: self._send_command(list_ctrl), send_item)
            self.Bind(wx.EVT_MENU, lambda e: self._edit_command(list_ctrl), edit_item)
            self.Bind(wx.EVT_MENU, lambda e: self._delete_command(list_ctrl), delete_item)
        
        add_item = menu.Append(wx.ID_ANY, '添加指令')
        self.Bind(wx.EVT_MENU, lambda e: self._add_command(list_ctrl), add_item)
        
        list_ctrl.PopupMenu(menu)
        menu.Destroy()
    
    def _apply_theme_to_tab(self, tab_index):
        """对指定Tab应用主题"""
        if not self.main_window or not hasattr(self.main_window, 'theme_manager'):
            return
        
        page = self.group_notebook.GetPage(tab_index)
        theme_manager = self.main_window.theme_manager
        colors = theme_manager.get_theme_colors()
        if not colors:
            return
        
        bg_color = theme_manager.hex_to_wx_colour(colors.get('text_bg', '#FFFFFF'))
        fg_color = theme_manager.hex_to_wx_colour(colors.get('text_fg', '#000000'))
        
        # 查找ListCtrl并应用主题
        for child in page.GetChildren():
            if isinstance(child, wx.ListCtrl):
                child.SetBackgroundColour(bg_color)
                child.SetForegroundColour(fg_color)
                child.Refresh()
    
    def _add_group(self, event):
        """添加分组"""
        # 使用主窗口作为父控件，确保对话框相对主窗口居中
        parent = self.main_window if self.main_window else self
        dialog = InputDialog(parent, '新建分组', '请输入分组名称:')
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue()
            if name:
                groups = self.config_manager.get_quick_command_groups()
                groups.append({'name': name, 'commands': []})
                self.config_manager.set_quick_command_groups(groups)
                # 直接创建新Tab，而不是刷新所有
                self._create_group_tab({'name': name, 'commands': []})
                
                # 对新Tab应用主题
                new_tab_index = self.group_notebook.GetPageCount() - 1
                self._apply_theme_to_tab(new_tab_index)
                
                # 切换到新分组
                self.group_notebook.SetSelection(new_tab_index)
        dialog.Destroy()
    
    def _rename_group(self, tab_index):
        """编辑分组"""
        groups = self.config_manager.get_quick_command_groups()
        old_name = groups[tab_index]['name']
        
        # 使用主窗口作为父控件，确保对话框相对主窗口居中
        parent = self.main_window if self.main_window else self
        dialog = InputDialog(parent, '编辑分组', '请输入分组名称:', old_name)
        if dialog.ShowModal() == wx.ID_OK:
            name = dialog.GetValue()
            if name and name != old_name:
                groups[tab_index]['name'] = name
                self.config_manager.set_quick_command_groups(groups)
                # 只更新Tab标题，而不是刷新所有
                self.group_notebook.SetPageText(tab_index, name)
        dialog.Destroy()
    
    def _delete_group(self, tab_index):
        """删除分组"""
        groups = self.config_manager.get_quick_command_groups()
        if len(groups) <= 1:
            wx.MessageBox('至少需要保留一个分组', '警告', wx.OK | wx.ICON_WARNING)
            return
        
        result = wx.MessageBox(f'确定要删除分组"{groups[tab_index]["name"]}"吗？', 
                              '确认', wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            groups.pop(tab_index)
            self.config_manager.set_quick_command_groups(groups)
            # 直接删除Tab，而不是刷新所有
            self.group_notebook.DeletePage(tab_index)
    
    def _add_command(self, list_ctrl):
        """添加指令"""
        # 使用主窗口作为父控件，确保对话框相对主窗口居中
        parent = self.main_window if self.main_window else self
        dialog = CommandDialog(parent, '添加快捷指令')
        if dialog.ShowModal() == wx.ID_OK:
            name, mode, command = dialog.GetResult()
            
            # 获取当前分组索引
            current_tab = self.group_notebook.GetSelection()
            groups = self.config_manager.get_quick_command_groups()
            groups[current_tab]['commands'].append({
                'name': name,
                'mode': mode,
                'command': command,
                'data': command  # 同时保存data字段以兼容
            })
            self.config_manager.set_quick_command_groups(groups)
            self._refresh_tab(current_tab)
        dialog.Destroy()
    
    def _edit_command(self, list_ctrl):
        """编辑指令"""
        index = list_ctrl.GetFirstSelected()
        if index < 0:
            return
        
        # 获取当前分组索引和指令索引
        current_tab = self.group_notebook.GetSelection()
        groups = self.config_manager.get_quick_command_groups()
        cmd = groups[current_tab]['commands'][index]
        
        # 获取data字段，如果不存在则使用command字段
        data = cmd.get('data', cmd.get('command', ''))
        # 确保data是字符串
        if not isinstance(data, str):
            data = str(data) if data is not None else ''
        
        # 使用主窗口作为父控件，确保对话框相对主窗口居中
        parent = self.main_window if self.main_window else self
        dialog = CommandDialog(parent, '编辑快捷指令', 
                              cmd.get('name', ''), cmd.get('mode', 'TEXT'), data)
        if dialog.ShowModal() == wx.ID_OK:
            name, mode, command = dialog.GetResult()
            groups[current_tab]['commands'][index] = {
                'name': name,
                'mode': mode,
                'command': command,
                'data': command  # 同时保存data字段以兼容
            }
            self.config_manager.set_quick_command_groups(groups)
            self._refresh_tab(current_tab)
        dialog.Destroy()
    
    def _delete_command(self, list_ctrl):
        """删除指令"""
        index = list_ctrl.GetFirstSelected()
        if index < 0:
            return
        
        result = wx.MessageBox('确定要删除选中的指令吗？', '确认', 
                              wx.YES_NO | wx.ICON_QUESTION)
        if result == wx.YES:
            current_tab = self.group_notebook.GetSelection()
            groups = self.config_manager.get_quick_command_groups()
            groups[current_tab]['commands'].pop(index)
            self.config_manager.set_quick_command_groups(groups)
            self._refresh_tab(current_tab)
    
    def _send_command(self, list_ctrl):
        """发送指令"""
        index = list_ctrl.GetFirstSelected()
        if index >= 0 and self.main_window:
            # 从配置中获取完整的指令信息（包含未转义的内容）
            current_tab = self.group_notebook.GetSelection()
            groups = self.config_manager.get_quick_command_groups()
            cmd = groups[current_tab]['commands'][index]
            
            # 获取data字段，如果不存在则使用command字段
            data = cmd.get('data', cmd.get('command', ''))
            # 确保data是字符串
            if not isinstance(data, str):
                data = str(data) if data is not None else ''
            mode = cmd.get('mode', 'TEXT')
            
            self._send_quick_command(data, mode)
    
    def _on_item_double_click(self, event):
        """双击发送指令"""
        list_ctrl = event.GetEventObject()
        index = event.GetIndex()
        
        if index >= 0 and self.main_window:
            # 从配置中获取完整的指令信息（包含未转义的内容）
            current_tab = self.group_notebook.GetSelection()
            groups = self.config_manager.get_quick_command_groups()
            cmd = groups[current_tab]['commands'][index]
            
            # 获取data字段，如果不存在则使用command字段
            data = cmd.get('data', cmd.get('command', ''))
            # 确保data是字符串
            if not isinstance(data, str):
                data = str(data) if data is not None else ''
            mode = cmd.get('mode', 'TEXT')
            
            self._send_quick_command(data, mode)
    
    def _send_quick_command(self, command, mode):
        """发送快捷指令"""
        if not self.main_window:
            return
        
        # 通过工作面板发送
        if self.main_window.work_panel.send_data(command, mode):
            # 刷新历史发送面板
            if hasattr(self.main_window, 'command_panel'):
                self.main_window.command_panel.refresh_history()
    
    def _on_drag_start(self, event):
        """开始拖动"""
        list_ctrl = event.GetEventObject()
        item_index = event.GetIndex()
        self.drag_item = (list_ctrl, item_index)
        event.Skip()
    
    def _on_drag_motion(self, event):
        """拖动中"""
        if self.drag_item and event.Dragging() and event.LeftIsDown():
            list_ctrl, drag_index = self.drag_item
            # 获取当前鼠标位置下的项目
            pos = event.GetPosition()
            target_index, flags = list_ctrl.HitTest(pos)
            
            if target_index != wx.NOT_FOUND and target_index != drag_index:
                # 获取拖动项的数据
                name = list_ctrl.GetItemText(drag_index, 0)
                mode = list_ctrl.GetItemText(drag_index, 1)
                content = list_ctrl.GetItemText(drag_index, 2)
                
                # 删除原项
                list_ctrl.DeleteItem(drag_index)
                
                # 在新位置插入
                new_index = list_ctrl.InsertItem(target_index, name)
                list_ctrl.SetItem(new_index, 1, mode)
                list_ctrl.SetItem(new_index, 2, content)
                
                # 选中新项
                list_ctrl.Select(new_index)
                
                # 更新拖动项索引
                self.drag_item = (list_ctrl, new_index)
        event.Skip()
    
    def _on_drag_release(self, event):
        """结束拖动"""
        if self.drag_item:
            list_ctrl, _ = self.drag_item
            # 保存新顺序
            current_tab = self.group_notebook.GetSelection()
            groups = self.config_manager.get_quick_command_groups()
            
            commands = []
            for i in range(list_ctrl.GetItemCount()):
                name = list_ctrl.GetItemText(i, 0)
                mode = list_ctrl.GetItemText(i, 1)
                content = list_ctrl.GetItemText(i, 2)
                # 恢复换行符
                content = content.replace('\\n', '\n').replace('\\r', '\r')
                commands.append({
                    'name': name,
                    'mode': mode,
                    'command': content
                })
            
            groups[current_tab]['commands'] = commands
            self.config_manager.set_quick_command_groups(groups)
            self.drag_item = None
        event.Skip()
    
    def apply_theme(self, theme_manager):
        """应用主题"""
        colors = theme_manager.get_theme_colors()
        if not colors:
            return
        
        try:
            # 应用到所有分组的ListCtrl
            bg_color = theme_manager.hex_to_wx_colour(colors.get('text_bg', '#FFFFFF'))
            fg_color = theme_manager.hex_to_wx_colour(colors.get('text_fg', '#000000'))
            
            for i in range(self.group_notebook.GetPageCount()):
                page = self.group_notebook.GetPage(i)
                # 查找ListCtrl
                for child in page.GetChildren():
                    if isinstance(child, wx.ListCtrl):
                        child.SetBackgroundColour(bg_color)
                        child.SetForegroundColour(fg_color)
                        child.Refresh()
            
            # 应用主题到ThemedNotebook
            if hasattr(self.group_notebook, 'apply_theme'):
                self.group_notebook.apply_theme(bg_color, fg_color)
            
        except Exception as e:
            print(f"应用主题到快捷命令面板时出错: {e}")


class CommandDialog(wx.Dialog):
    """指令编辑对话框"""
    
    def __init__(self, parent, title, name='', mode='TEXT', command=''):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE)
        
        self.result = None
        self._create_widgets(name, mode, command)
    
    def _create_widgets(self, name, mode, command):
        """创建控件"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 名称
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(wx.StaticText(self, label='名称:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.name_ctrl = wx.TextCtrl(self, value=name, size=(250, -1))
        name_sizer.Add(self.name_ctrl, 1, wx.EXPAND)
        sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 模式
        mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mode_sizer.Add(wx.StaticText(self, label='模式:'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.mode_text = wx.RadioButton(self, label='TEXT', style=wx.RB_GROUP)
        self.mode_hex = wx.RadioButton(self, label='HEX')
        self.mode_text.SetValue(mode == 'TEXT')
        self.mode_hex.SetValue(mode == 'HEX')
        mode_sizer.Add(self.mode_text, 0, wx.RIGHT, 10)
        mode_sizer.Add(self.mode_hex, 0)
        sizer.Add(mode_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        # 内容
        content_label = wx.StaticText(self, label='内容:')
        sizer.Add(content_label, 0, wx.LEFT | wx.TOP, 10)
        self.command_ctrl = wx.TextCtrl(self, value=command, 
                                       style=wx.TE_MULTILINE, size=(300, 100))
        sizer.Add(self.command_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        
        # 错误提示
        self.error_label = wx.StaticText(self, label='')
        self.error_label.SetForegroundColour(wx.RED)
        sizer.Add(self.error_label, 0, wx.LEFT | wx.RIGHT, 10)
        
        # 按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, label='确定')
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label='取消')
        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.Add(ok_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(cancel_btn, 0)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.Fit()
        self.CenterOnParent()
        
        self.name_ctrl.SetFocus()
    
    def _on_ok(self, event):
        """确定"""
        name = self.name_ctrl.GetValue().strip()
        mode = 'HEX' if self.mode_hex.GetValue() else 'TEXT'
        command = self.command_ctrl.GetValue().strip()
        
        if not name or not command:
            self.error_label.SetLabel('名称和内容不能为空')
            wx.CallLater(3000, lambda: self.error_label.SetLabel(''))
            return
        
        # HEX模式下检查格式
        if mode == 'HEX':
            if not HexUtils.validate_hex_format(command):
                self.error_label.SetLabel(HexUtils.get_format_error_message())
                wx.CallLater(3000, lambda: self.error_label.SetLabel(''))
                return
        
        self.result = (name, mode, command)
        self.EndModal(wx.ID_OK)
    
    def GetResult(self):
        """获取结果"""
        return self.result


class InputDialog(wx.Dialog):
    """输入对话框"""
    
    def __init__(self, parent, title, label, initial_value=''):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE)
        
        self.value = None
        self._create_widgets(label, initial_value)
    
    def _create_widgets(self, label, initial_value):
        """创建控件"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 标签
        label_text = wx.StaticText(self, label=label)
        sizer.Add(label_text, 0, wx.ALL, 10)
        
        # 输入框（添加wxTE_PROCESS_ENTER样式以支持回车键事件）
        self.entry = wx.TextCtrl(self, value=initial_value, size=(250, -1), 
                                style=wx.TE_PROCESS_ENTER)
        self.entry.SetSelection(-1, -1)
        sizer.Add(self.entry, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # 错误提示
        self.error_label = wx.StaticText(self, label='')
        self.error_label.SetForegroundColour(wx.RED)
        sizer.Add(self.error_label, 0, wx.LEFT | wx.RIGHT, 10)
        
        # 按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(self, wx.ID_OK, label='确定')
        cancel_btn = wx.Button(self, wx.ID_CANCEL, label='取消')
        ok_btn.Bind(wx.EVT_BUTTON, self._on_ok)
        cancel_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CANCEL))
        btn_sizer.Add(ok_btn, 0, wx.RIGHT, 5)
        btn_sizer.Add(cancel_btn, 0)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        self.SetSizer(sizer)
        self.Fit()
        self.CenterOnParent()
        
        self.entry.SetFocus()
        self.entry.Bind(wx.EVT_TEXT_ENTER, self._on_ok)
    
    def _on_ok(self, event):
        """确定"""
        value = self.entry.GetValue().strip()
        if not value:
            self.error_label.SetLabel('分组名称不能为空')
            wx.CallLater(3000, lambda: self.error_label.SetLabel(''))
            return
        
        self.value = value
        self.EndModal(wx.ID_OK)
    
    def GetValue(self):
        """获取值"""
        return self.value
