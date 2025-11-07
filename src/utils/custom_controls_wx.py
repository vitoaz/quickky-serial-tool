"""
自定义控件工具 - 支持Dark主题的控件
用于替换wxPython原生控件以实现完整的主题支持

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import wx
import wx.lib.buttons as buttons
import wx.lib.agw.flatnotebook as fnb


class ThemedButton(buttons.GenButton):
    """支持主题的按钮"""
    
    def __init__(self, parent, id=wx.ID_ANY, label='', pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0, name='button'):
        super().__init__(parent, id, label, pos, size, style, name=name)
        
        # 设置默认样式
        self.SetBezelWidth(1)
        self.SetUseFocusIndicator(False)
        
    def apply_theme(self, bg_color, fg_color, hover_color=None):
        """应用主题颜色"""
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        
        # GenButton使用不同的方法名
        try:
            if hover_color:
                # 尝试设置hover颜色（不同版本API可能不同）
                if hasattr(self, 'SetFaceMidColour'):
                    self.SetFaceMidColour(hover_color)
            else:
                # 自动计算hover颜色（稍微亮一点）
                r, g, b = bg_color.Red(), bg_color.Green(), bg_color.Blue()
                hover = wx.Colour(min(r + 20, 255), min(g + 20, 255), min(b + 20, 255))
                if hasattr(self, 'SetFaceMidColour'):
                    self.SetFaceMidColour(hover)
        except:
            pass
        
        self.Refresh()


class ThemedSpinCtrl(wx.Panel):
    """支持主题的SpinCtrl - 使用TextCtrl和按钮组合实现"""
    
    def __init__(self, parent, id=wx.ID_ANY, value='0', pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, min=0, max=100, initial=0, name='spinctrl'):
        super().__init__(parent, id, pos, size, style, name)
        
        self._min = min
        self._max = max
        self._value = initial if initial else int(value) if value else 0
        
        # 创建布局
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 文本框
        self.text_ctrl = wx.TextCtrl(self, value=str(self._value), 
                                     style=wx.TE_RIGHT | wx.TE_PROCESS_ENTER)
        self.text_ctrl.Bind(wx.EVT_TEXT, self._on_text_change)
        self.text_ctrl.Bind(wx.EVT_TEXT_ENTER, self._on_text_enter)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        
        # 按钮容器
        btn_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 向上按钮
        self.up_btn = wx.Button(self, label='▲', size=(20, -1))
        self.up_btn.Bind(wx.EVT_BUTTON, self._on_up)
        btn_sizer.Add(self.up_btn, 1, wx.EXPAND)
        
        # 向下按钮
        self.down_btn = wx.Button(self, label='▼', size=(20, -1))
        self.down_btn.Bind(wx.EVT_BUTTON, self._on_down)
        btn_sizer.Add(self.down_btn, 1, wx.EXPAND)
        
        sizer.Add(btn_sizer, 0, wx.EXPAND)
        self.SetSizer(sizer)
        
        self._bg_color = wx.WHITE
        self._fg_color = wx.BLACK
        
    def _on_up(self, event):
        """增加值"""
        new_value = min(self._value + 1, self._max)
        self.SetValue(new_value)
        self._fire_event()
        
    def _on_down(self, event):
        """减少值"""
        new_value = max(self._value - 1, self._min)
        self.SetValue(new_value)
        self._fire_event()
        
    def _on_text_change(self, event):
        """文本变化"""
        try:
            value = int(self.text_ctrl.GetValue())
            if self._min <= value <= self._max:
                self._value = value
        except ValueError:
            pass
        event.Skip()
        
    def _on_text_enter(self, event):
        """按下回车"""
        self._validate_and_set()
        self._fire_event()
        
    def _validate_and_set(self):
        """验证并设置值"""
        try:
            value = int(self.text_ctrl.GetValue())
            value = max(self._min, min(value, self._max))
            self._value = value
            self.text_ctrl.SetValue(str(value))
        except ValueError:
            self.text_ctrl.SetValue(str(self._value))
            
    def _fire_event(self):
        """触发SpinCtrl事件"""
        event = wx.CommandEvent(wx.wxEVT_SPINCTRL, self.GetId())
        event.SetEventObject(self)
        event.SetInt(self._value)
        self.GetEventHandler().ProcessEvent(event)
        
    def GetValue(self):
        """获取当前值"""
        self._validate_and_set()
        return self._value
        
    def SetValue(self, value):
        """设置值"""
        value = max(self._min, min(int(value), self._max))
        self._value = value
        self.text_ctrl.SetValue(str(value))
        
    def Enable(self, enable=True):
        """启用/禁用"""
        super().Enable(enable)
        self.text_ctrl.Enable(enable)
        self.up_btn.Enable(enable)
        self.down_btn.Enable(enable)
        
    def apply_theme(self, bg_color, fg_color):
        """应用主题颜色"""
        self._bg_color = bg_color
        self._fg_color = fg_color
        
        # 应用到面板自身
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        
        # 应用到文本框
        self.text_ctrl.SetBackgroundColour(bg_color)
        self.text_ctrl.SetForegroundColour(fg_color)
        self.text_ctrl.Refresh()
        
        # 应用到按钮（如果是ThemedButton）
        try:
            if hasattr(self.up_btn, 'apply_theme'):
                self.up_btn.apply_theme(bg_color, fg_color)
            else:
                self.up_btn.SetForegroundColour(fg_color)
                
            if hasattr(self.down_btn, 'apply_theme'):
                self.down_btn.apply_theme(bg_color, fg_color)
            else:
                self.down_btn.SetForegroundColour(fg_color)
        except:
            pass
        
        self.Refresh()


class ThemedNotebook(fnb.FlatNotebook):
    """支持主题的Notebook - 使用FlatNotebook实现完整主题支持"""
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, name='notebook'):
        # FlatNotebook的样式
        fnb_style = (fnb.FNB_NO_X_BUTTON |  # 不显示Tab上的关闭按钮
                     fnb.FNB_NODRAG |  # 禁用Tab拖动
                     fnb.FNB_FANCY_TABS)  # 使用漂亮的Tab样式
        
        super().__init__(parent, id, pos, size, agwStyle=fnb_style, name=name)
        
        self._bg_color = None
        self._fg_color = None
        
    def apply_theme(self, bg_color, fg_color, tab_bg_color=None, active_tab_bg_color=None):
        """应用主题颜色"""
        self._bg_color = bg_color
        self._fg_color = fg_color
        
        # 设置Tab区域颜色
        if tab_bg_color is None:
            # 计算稍微不同的Tab背景色
            r, g, b = bg_color.Red(), bg_color.Green(), bg_color.Blue()
            tab_bg_color = wx.Colour(max(r - 10, 0), max(g - 10, 0), max(b - 10, 0))
        
        if active_tab_bg_color is None:
            active_tab_bg_color = bg_color
        
        # 应用FlatNotebook的颜色
        self.SetTabAreaColour(tab_bg_color)  # Tab区域背景色
        self.SetActiveTabColour(active_tab_bg_color)  # 激活Tab的背景色
        self.SetNonActiveTabTextColour(fg_color)  # 非激活Tab的文字颜色
        self.SetActiveTabTextColour(fg_color)  # 激活Tab的文字颜色
        
        # 设置Notebook本身的颜色
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        
        # 更新所有Page的背景色
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            if page:
                page.SetBackgroundColour(bg_color)
                page.SetForegroundColour(fg_color)
        
        self.Refresh()


class ThemedComboBox(wx.adv.OwnerDrawnComboBox):
    """支持主题的下拉框 - 使用OwnerDrawnComboBox实现完整主题支持"""
    
    def __init__(self, parent, id=wx.ID_ANY, value='', pos=wx.DefaultPosition,
                 size=wx.DefaultSize, choices=[], style=0, name='comboBox'):
        super().__init__(parent, id, value, pos, size, choices, style, name=name)
        
        self._bg_color = wx.WHITE
        self._fg_color = wx.BLACK
        self._sel_bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        self._sel_fg_color = wx.WHITE
        
        # 尝试设置文本控件的颜色（针对可编辑ComboBox）
        try:
            text_ctrl = self.GetTextCtrl()
            if text_ctrl:
                text_ctrl.SetBackgroundColour(self._bg_color)
                text_ctrl.SetForegroundColour(self._fg_color)
        except:
            pass
        
    def apply_theme(self, bg_color, fg_color, sel_bg_color=None, sel_fg_color=None):
        """应用主题颜色"""
        self._bg_color = bg_color
        self._fg_color = fg_color
        
        if sel_bg_color:
            self._sel_bg_color = sel_bg_color
        if sel_fg_color:
            self._sel_fg_color = sel_fg_color
            
        # 设置控件本身的颜色
        self.SetBackgroundColour(bg_color)
        self.SetForegroundColour(fg_color)
        
        # 更新文本控件的颜色（针对可编辑ComboBox）
        try:
            text_ctrl = self.GetTextCtrl()
            if text_ctrl:
                text_ctrl.SetBackgroundColour(bg_color)
                text_ctrl.SetForegroundColour(fg_color)
                text_ctrl.Refresh()
        except:
            pass
        
        self.Refresh()
        
    def OnDrawBackground(self, dc, rect, item, flags):
        """绘制背景"""
        # 设置背景色
        if flags & wx.adv.ODCB_PAINTING_CONTROL:
            # 绘制控件本身（未展开时）
            dc.SetBrush(wx.Brush(self._bg_color))
        elif flags & wx.adv.ODCB_PAINTING_SELECTED:
            # 绘制选中项
            dc.SetBrush(wx.Brush(self._sel_bg_color))
        else:
            # 绘制普通列表项
            dc.SetBrush(wx.Brush(self._bg_color))
        
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
        
    def OnDrawItem(self, dc, rect, item, flags):
        """绘制列表项"""
        if item == wx.NOT_FOUND:
            return
        
        # 先绘制背景
        self.OnDrawBackground(dc, rect, item, flags)
        
        # 设置文本颜色
        if flags & wx.adv.ODCB_PAINTING_SELECTED:
            dc.SetTextForeground(self._sel_fg_color)
        else:
            dc.SetTextForeground(self._fg_color)
        
        # 绘制文本
        text = self.GetString(item)
        dc.DrawText(text, rect.x + 3, rect.y + 2)
    
    def OnMeasureItem(self, item):
        """测量项目高度"""
        return 24
    
    def OnMeasureItemWidth(self, item):
        """测量项目宽度"""
        return -1  # 使用默认宽度



