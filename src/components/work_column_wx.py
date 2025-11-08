"""
工作栏目 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
from .work_tab_wx import WorkTab
from utils.custom_controls_wx import ThemedNotebook


class WorkColumn(wx.Panel):
    """工作栏目 - 管理单栏的多个Tab"""
    
    def __init__(self, parent, config_manager, theme_manager, panel_type='main', 
                 on_column_activated=None, on_tab_data_sent=None):
        """初始化工作栏目"""
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.panel_type = panel_type
        self.on_column_activated = on_column_activated
        self.on_tab_data_sent = on_tab_data_sent
        self.is_active = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 创建容器
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 创建上边框（用于显示激活状态）
        self.top_border = wx.Panel(self, size=(-1, 3))
        self.top_border.SetBackgroundColour(self.GetBackgroundColour())  # 默认与背景色相同
        sizer.Add(self.top_border, 0, wx.EXPAND)
        
        # 使用ThemedNotebook创建Tab页，支持完整主题，允许双击关闭
        self.notebook = ThemedNotebook(self, allow_dclick_close=True)
        # FlatNotebook使用不同的事件
        import wx.lib.agw.flatnotebook as fnb
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self._on_tab_changed)
        self.notebook.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self._on_tab_closing)
        
        # 绑定单击事件来处理加号Tab
        self.notebook.Bind(wx.EVT_LEFT_DOWN, self._on_left_click)
        
        # 标记正在初始化，防止事件触发时创建额外Tab
        self._initializing = True
        
        # 创建第一个Tab
        self._add_new_tab(is_first=True)
        
        # 递归绑定所有子控件的点击事件以激活栏目
        self._bind_activation_event(self)
        
        # 创建加号Tab（占位符，固定在最右侧）
        self.add_tab_panel = wx.Panel(self.notebook)
        # 使用StaticText来居中显示加号
        add_tab_sizer = wx.BoxSizer(wx.VERTICAL)
        add_label = wx.StaticText(self.add_tab_panel, label='+')
        add_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        add_tab_sizer.Add(add_label, 1, wx.ALIGN_CENTER)
        self.add_tab_panel.SetSizer(add_tab_sizer)
        self.notebook.AddPage(self.add_tab_panel, '   +   ')
        
        # 初始化完成
        self._initializing = False
        
        # 在Tab创建完成后绑定右键菜单事件到Tab区域
        # FlatNotebook的Tab区域是_pages属性
        wx.CallAfter(self._bind_right_click_event)
        
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def _bind_right_click_event(self):
        """绑定右键点击事件（延迟绑定，确保_pages已创建）"""
        if hasattr(self.notebook, '_pages') and self.notebook._pages:
            self.notebook._pages.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)
        else:
            self.notebook.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)
    
    def _on_tab_changed(self, event):
        """Tab切换事件"""
        # 如果正在初始化，忽略事件
        if hasattr(self, '_initializing') and self._initializing:
            event.Skip()
            return
        
        # 获取当前选中的Tab索引
        current_index = self.notebook.GetSelection()
        
        # 如果选中的是加号Tab（最后一个），创建新Tab
        if current_index == self.notebook.GetPageCount() - 1:
            # 添加新Tab（内部会自动选中新Tab）
            self._add_new_tab()
            return
        
        event.Skip()
    
    def _on_tab_closing(self, event):
        """Tab关闭前的事件（用于拦截不允许的关闭操作）"""
        # 获取要关闭的Tab索引
        closing_index = event.GetSelection()
        
        # 如果是加号Tab（最后一个），阻止关闭
        if closing_index == self.notebook.GetPageCount() - 1:
            event.Veto()  # 阻止关闭
            return
        
        # 如果是最后一个真实Tab（只剩1个真实Tab + 1个加号Tab），阻止关闭
        if self.notebook.GetPageCount() <= 2:
            event.Veto()  # 阻止关闭
            return
        
        # 清理Tab资源
        page = self.notebook.GetPage(closing_index)
        if hasattr(page, 'cleanup'):
            page.cleanup()
        
        event.Skip()
    
    def _on_left_click(self, event):
        """单击事件"""
        # 获取点击位置
        pos = event.GetPosition()
        
        # FlatNotebook使用TabHitTest方法
        tab_index, where = self.notebook.TabHitTest(pos.x, pos.y)
        
        # 如果点击的是加号Tab（最后一个）
        if tab_index == self.notebook.GetPageCount() - 1 and tab_index >= 0:
            # 添加新Tab（内部会自动选中新Tab）
            self._add_new_tab()
            # 不让事件继续传播，避免切换到加号Tab
            return
        
        # 其他情况让事件继续传播
        event.Skip()
    
    def _add_new_tab(self, is_first=False):
        """添加新Tab"""
        # 计算真实的Tab数量（排除加号Tab，加号Tab固定在最后）
        real_tab_count = self.notebook.GetPageCount()
        tab_name = 'New Tab'
        
        tab = WorkTab(
            self.notebook,
            self.config_manager,
            tab_name=tab_name,
            is_first_tab=is_first,
            on_data_sent=self.on_tab_data_sent,
            panel_type=self.panel_type,
            parent_notebook=self.notebook
        )
        
        # 插入到加号Tab之前（加号固定在最后）
        # is_first时，加号Tab还没创建，直接AddPage
        # 非is_first时，插入到加号Tab之前
        if is_first:
            self.notebook.AddPage(tab, tab_name)
            insert_index = self.notebook.GetPageCount() - 1
        else:
            insert_index = self.notebook.GetPageCount() - 1  # 加号Tab之前
            self.notebook.InsertPage(insert_index, tab, tab_name)
        
        # 选中新添加的Tab
        self.notebook.SetSelection(insert_index)
        
        # 立即应用主题到新Tab
        if self.theme_manager:
            font_size = self.config_manager.get_font_size()
            tab.apply_theme(self.theme_manager, font_size)
        
        return tab

    def _on_right_down(self, event):
        """右键点击事件"""
        # 获取鼠标位置
        pos = event.GetPosition()
        
        # FlatNotebook的_pages.HitTest方法
        try:
            # 使用_pages的HitTest方法来获取Tab索引
            if hasattr(self.notebook, '_pages') and self.notebook._pages:
                hit_result = self.notebook._pages.HitTest(pos)
                
                # HitTest返回元组 (where, tab_index)
                # where: 0=不在Tab上, 1=在Tab上
                # tab_index: Tab的索引
                if isinstance(hit_result, tuple) and len(hit_result) >= 2:
                    where = hit_result[0]
                    tab_index = hit_result[1]
                    
                    # where=1表示点击在Tab上，where=0表示点击在空白区域
                    if where != 1:
                        tab_index = -1
                else:
                    tab_index = -1
            else:
                tab_index = -1
        except Exception as e:
            tab_index = -1
        
        # 如果点击的是有效的Tab且不是加号Tab（最后一个），显示关闭菜单
        if tab_index >= 0 and tab_index < self.notebook.GetPageCount() - 1:
            self._show_tab_menu(tab_index)
            return
        
        event.Skip()
    
    def _show_tab_menu(self, tab_index):
        """显示Tab右键菜单"""
        menu = wx.Menu()
        close_item = menu.Append(wx.ID_ANY, '关闭')
        
        def on_close(e):
            self._close_tab_by_index(tab_index)
        
        self.Bind(wx.EVT_MENU, on_close, close_item)
        self.notebook.PopupMenu(menu)
        menu.Destroy()
    
    def _close_tab_by_index(self, index):
        """通过索引关闭Tab"""
        # 不能关闭加号Tab（最后一个）
        if index >= self.notebook.GetPageCount() - 1:
            return
        
        # 至少保留一个Tab（除了加号Tab）
        if self.notebook.GetPageCount() <= 2:  # 1个真实Tab + 1个加号Tab
            # 静默忽略，不显示提示
            return
        
        # 记住当前索引，关闭后选择合适的Tab
        current_count = self.notebook.GetPageCount()
        
        page = self.notebook.GetPage(index)
        if hasattr(page, 'cleanup'):
            page.cleanup()
        self.notebook.DeletePage(index)
        
        # 关闭后，如果选中的是加号Tab，选择前一个Tab
        if self.notebook.GetSelection() == self.notebook.GetPageCount() - 1:
            # 选中最后一个真实Tab（加号Tab的前一个）
            self.notebook.SetSelection(self.notebook.GetPageCount() - 2)
    
    def close_current_tab(self):
        """关闭当前Tab"""
        current_index = self.notebook.GetSelection()
        if current_index >= 0 and self.notebook.GetPageCount() > 1:
            # 不允许关闭最后一个Tab
            page = self.notebook.GetPage(current_index)
            if hasattr(page, 'cleanup'):
                page.cleanup()
            self.notebook.DeletePage(current_index)
    
    def update_tab_title(self, tab, title):
        """更新Tab标题"""
        for i in range(self.notebook.GetPageCount()):
            if self.notebook.GetPage(i) == tab:
                self.notebook.SetPageText(i, title)
                break
    
    def get_current_tab(self):
        """获取当前选中的Tab"""
        current_index = self.notebook.GetSelection()
        if current_index >= 0 and current_index < self.notebook.GetPageCount() - 1:  # 排除加号Tab
            return self.notebook.GetPage(current_index)
        return None
    
    def get_all_tabs(self):
        """获取所有Tab（不包括加号Tab）"""
        tabs = []
        for i in range(self.notebook.GetPageCount() - 1):  # 排除最后一个加号Tab
            page = self.notebook.GetPage(i)
            tabs.append(page)
        return tabs
    
    def apply_theme(self, theme_manager):
        """应用主题到所有Tab"""
        self.theme_manager = theme_manager
        
        # 设置work_column自身的背景色
        if theme_manager:
            colors = theme_manager.get_theme_colors()
            bg_color = theme_manager.hex_to_wx_colour(colors.get('background', '#FFFFFF'))
            fg_color = theme_manager.hex_to_wx_colour(colors.get('foreground', '#000000'))
            self.SetBackgroundColour(bg_color)
            
            # 应用主题到ThemedNotebook
            if hasattr(self.notebook, 'apply_theme'):
                # 计算Tab区域的背景色（稍微深一点）
                r, g, b = bg_color.Red(), bg_color.Green(), bg_color.Blue()
                tab_bg_color = wx.Colour(max(r - 10, 0), max(g - 10, 0), max(b - 10, 0))
                self.notebook.apply_theme(bg_color, fg_color, tab_bg_color, bg_color)
            else:
                self.notebook.SetBackgroundColour(bg_color)
        
        font_size = self.config_manager.get_font_size()
        for i in range(self.notebook.GetPageCount() - 1):  # 排除加号Tab
            tab = self.notebook.GetPage(i)
            if hasattr(tab, 'apply_theme'):
                tab.apply_theme(theme_manager, font_size)
        
        # 更新边框高亮
        self._update_border_highlight()
    
    def _bind_activation_event(self, widget):
        """递归绑定激活事件到所有子控件"""
        try:
            # 绑定点击事件
            widget.Bind(wx.EVT_LEFT_DOWN, self._on_widget_clicked)
            
            # 递归处理所有子控件
            if hasattr(widget, 'GetChildren'):
                for child in widget.GetChildren():
                    self._bind_activation_event(child)
        except:
            pass
    
    def _on_widget_clicked(self, event):
        """任何子控件被点击 - 激活当前栏目"""
        event.Skip()  # 让事件继续传播，不影响原有功能
        if self.on_column_activated:
            self.on_column_activated(self)
    
    def set_active(self, active):
        """设置激活状态"""
        self.is_active = active
        self._update_border_highlight()
    
    def _update_border_highlight(self):
        """更新边框高亮显示"""
        if self.theme_manager:
            colors = self.theme_manager.get_theme_colors()
            bg_color = self.theme_manager.hex_to_wx_colour(colors.get('background', '#FFFFFF'))
            # 使用active_border颜色
            active_color = self.theme_manager.hex_to_wx_colour(colors.get('active_border', '#0E639C'))
        else:
            bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            active_color = wx.Colour(14, 99, 156)  # #0E639C
        
        # 根据激活状态设置边框颜色
        border_color = active_color if self.is_active else bg_color
        self.top_border.SetBackgroundColour(border_color)
        self.top_border.Refresh()
    
    def cleanup(self):
        """清理资源"""
        for i in range(self.notebook.GetPageCount() - 1):  # 排除加号Tab
            tab = self.notebook.GetPage(i)
            if hasattr(tab, 'cleanup'):
                tab.cleanup()

