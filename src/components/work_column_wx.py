"""
工作栏目 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
import wx.lib.agw.flatnotebook as fnb
from .work_tab_wx import WorkTab


class WorkColumn(wx.Panel):
    """工作栏目 - 管理单栏的多个Tab"""
    
    def __init__(self, parent, config_manager, theme_manager, panel_type='main', 
                 on_tab_data_sent=None):
        """初始化工作栏目"""
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.theme_manager = theme_manager
        self.panel_type = panel_type
        self.on_tab_data_sent = on_tab_data_sent
        
        self._create_widgets()
    
    def _create_widgets(self):
        """创建控件"""
        # 创建容器
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 使用 Notebook 创建Tab页
        self.notebook = wx.Notebook(self)
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._on_tab_changed)
        self.notebook.Bind(wx.EVT_LEFT_DCLICK, self._on_double_click)
        self.notebook.Bind(wx.EVT_RIGHT_DOWN, self._on_right_click)
        self.notebook.Bind(wx.EVT_LEFT_DOWN, self._on_left_click)
        
        # 创建第一个Tab
        self._add_new_tab(is_first=True)
        
        # 创建加号Tab（占位符，固定在最右侧）
        self.add_tab_panel = wx.Panel(self.notebook)
        # 使用StaticText来居中显示加号
        add_tab_sizer = wx.BoxSizer(wx.VERTICAL)
        add_label = wx.StaticText(self.add_tab_panel, label='+')
        add_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        add_tab_sizer.Add(add_label, 1, wx.ALIGN_CENTER)
        self.add_tab_panel.SetSizer(add_tab_sizer)
        self.notebook.AddPage(self.add_tab_panel, '   +   ')
        
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
    
    def _on_tab_changed(self, event):
        """Tab切换事件"""
        # 如果切换到加号Tab，不做任何操作（让单击事件处理）
        event.Skip()
    
    def _on_left_click(self, event):
        """单击事件"""
        # 获取点击位置
        pos = event.GetPosition()
        
        # 使用HitTest直接判断点击的Tab
        tab_index, flags = self.notebook.HitTest(pos)
        
        # 如果点击的是加号Tab（最后一个）
        if tab_index == self.notebook.GetPageCount() - 1:
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
        insert_index = self.notebook.GetPageCount() - (0 if is_first else 1)
        self.notebook.InsertPage(insert_index, tab, tab_name)
        
        # 选中新添加的Tab
        self.notebook.SetSelection(insert_index)
        
        # 应用主题
        if self.theme_manager:
            font_size = self.config_manager.get_font_size()
            tab.apply_theme(self.theme_manager, font_size)
        
        return tab
    
    def _on_double_click(self, event):
        """双击Tab处理"""
        # 使用当前选中的Tab
        tab_index = self.notebook.GetSelection()
        
        if tab_index >= 0:
            # 如果双击的是加号Tab（最后一个），忽略双击事件
            if tab_index == self.notebook.GetPageCount() - 1:
                # 加号Tab忽略双击，只响应单击
                pass
            else:
                # 如果双击的是普通Tab，关闭它
                self._close_tab_by_index(tab_index)
        
        event.Skip()
    
    def _on_right_click(self, event):
        """右键菜单"""
        # 使用当前选中的Tab
        tab_index = self.notebook.GetSelection()
        
        # 如果不是加号Tab（最后一个），显示关闭菜单
        if tab_index < self.notebook.GetPageCount() - 1:
            self._show_tab_menu(tab_index, event)
        
        event.Skip()
    
    def _show_tab_menu(self, tab_index, event):
        """显示Tab右键菜单"""
        menu = wx.Menu()
        close_item = menu.Append(wx.ID_ANY, '关闭Tab')
        
        def on_close(e):
            self._close_tab_by_index(tab_index)
        
        menu.Bind(wx.EVT_MENU, on_close, close_item)
        self.PopupMenu(menu)
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
        font_size = self.config_manager.get_font_size()
        for i in range(self.notebook.GetPageCount() - 1):  # 排除加号Tab
            tab = self.notebook.GetPage(i)
            if hasattr(tab, 'apply_theme'):
                tab.apply_theme(theme_manager, font_size)
    
    def cleanup(self):
        """清理资源"""
        for i in range(self.notebook.GetPageCount() - 1):  # 排除加号Tab
            tab = self.notebook.GetPage(i)
            if hasattr(tab, 'cleanup'):
                tab.cleanup()

