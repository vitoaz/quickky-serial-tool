"""
TTK PanedWindow 最小尺寸支持工具
提供TTK PanedWindow的最小尺寸约束功能

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import tkinter as tk
from tkinter import ttk


class TTKPanedWindowMinSize:
    """TTK PanedWindow 最小尺寸管理器"""
    
    def __init__(self, paned_window, orientation='horizontal'):
        """
        初始化最小尺寸管理器
        
        Args:
            paned_window: ttk.PanedWindow 实例
            orientation: 方向 ('horizontal' 或 'vertical')
        """
        self.paned_window = paned_window
        self.orientation = orientation
        self.min_sizes = {}  # 存储每个面板的最小尺寸
        self.panels = []     # 存储面板引用
        
        # 绑定配置事件
        self.paned_window.bind('<Configure>', self._on_configure)
        # 绑定按钮释放事件（分割线拖拽结束）
        self.paned_window.bind('<ButtonRelease-1>', self._on_sash_drag_end)
        # 绑定映射事件（窗口显示完成）
        self.paned_window.bind('<Map>', self._on_map)
    
    def add_panel(self, panel, min_size=None, **kwargs):
        """
        添加面板到PanedWindow并设置最小尺寸
        
        Args:
            panel: 要添加的面板控件
            min_size: 最小尺寸（像素）
            **kwargs: 传递给PanedWindow.add()的其他参数
        """
        # 添加面板到PanedWindow
        self.paned_window.add(panel, **kwargs)
        
        # 记录面板和最小尺寸
        panel_index = len(self.panels)
        self.panels.append(panel)
        
        if min_size is not None:
            self.min_sizes[panel_index] = min_size
    
    def set_min_size(self, panel_index, min_size):
        """
        设置指定面板的最小尺寸
        
        Args:
            panel_index: 面板索引
            min_size: 最小尺寸（像素）
        """
        if 0 <= panel_index < len(self.panels):
            self.min_sizes[panel_index] = min_size
    
    def remove_panel(self, panel):
        """
        从PanedWindow中移除面板
        
        Args:
            panel: 要移除的面板控件
        """
        try:
            # 找到面板在列表中的索引
            if panel in self.panels:
                panel_index = self.panels.index(panel)
                
                # 从PanedWindow中移除
                self.paned_window.remove(panel)
                
                # 保存要移除面板之后的面板的最小尺寸设置
                panels_after = []
                min_sizes_after = {}
                
                for i in range(panel_index + 1, len(self.panels)):
                    panels_after.append(self.panels[i])
                    if i in self.min_sizes:
                        min_sizes_after[i - panel_index - 1] = self.min_sizes[i]
                
                # 从管理器中移除面板
                self.panels.remove(panel)
                
                # 移除该面板的最小尺寸设置
                if panel_index in self.min_sizes:
                    del self.min_sizes[panel_index]
                
                # 重新调整后续面板的索引
                new_min_sizes = {}
                for old_index, min_size in self.min_sizes.items():
                    if old_index < panel_index:
                        # 在移除面板之前的面板，索引不变
                        new_min_sizes[old_index] = min_size
                    elif old_index > panel_index:
                        # 在移除面板之后的面板，索引减1
                        new_min_sizes[old_index - 1] = min_size
                
                self.min_sizes = new_min_sizes
                
        except Exception:
            pass
    
    def _on_sash_drag_end(self, event):
        """分割线拖拽结束事件处理"""
        # 延迟检查，确保尺寸已经更新
        self.paned_window.after(50, self._check_constraints)
    
    def _on_map(self, event):
        """窗口映射完成事件处理"""
        if event.widget == self.paned_window:
            # 窗口显示完成后检查约束
            self.paned_window.after(100, self._check_constraints)
    
    def _check_constraints(self):
        """检查并应用最小尺寸约束"""
        if not self.min_sizes:
            return
            
        try:
            # 获取PanedWindow的总尺寸
            if self.orientation == 'horizontal':
                total_size = self.paned_window.winfo_width()
            else:
                total_size = self.paned_window.winfo_height()
                
            if total_size <= 1:  # 避免初始化时的无效值
                return
            
            # 检查每个面板的尺寸
            self._check_and_adjust_panels(total_size)
            
        except Exception:
            # 忽略所有异常，确保程序稳定性
            pass
    
    def _on_configure(self, event):
        """配置变化事件处理"""
        # 只处理PanedWindow本身的配置事件
        if event.widget != self.paned_window:
            return
        
        # 延迟检查，避免频繁调用
        self.paned_window.after_idle(self._check_constraints)
    
    def _check_and_adjust_panels(self, total_size):
        """检查并调整面板尺寸"""
        panel_count = len(self.panels)
        if panel_count == 0:
            return
        
        # 获取当前所有面板的尺寸
        current_sizes = []
        for i, panel in enumerate(self.panels):
            try:
                if self.orientation == 'horizontal':
                    size = panel.winfo_width()
                else:
                    size = panel.winfo_height()
                current_sizes.append(size)
            except:
                current_sizes.append(0)
        
        # 检查是否需要调整
        needs_adjustment = False
        adjusted_sizes = current_sizes.copy()
        
        # 计算分割线占用的空间（估算）
        sash_space = (panel_count - 1) * 5  # 假设每个分割线占用5像素
        available_space = total_size - sash_space
        
        # 第一轮：确保所有面板都满足最小尺寸要求
        for i, size in enumerate(current_sizes):
            min_size = self.min_sizes.get(i, 0)
            if size < min_size:
                adjusted_sizes[i] = min_size
                needs_adjustment = True
        
        # 第二轮：如果总尺寸超出可用空间，按比例缩减非最小尺寸面板
        total_adjusted = sum(adjusted_sizes)
        if total_adjusted > available_space:
            # 计算可压缩的空间
            compressible_space = 0
            min_total = 0
            
            for i in range(panel_count):
                min_size = self.min_sizes.get(i, 0)
                min_total += min_size
                if adjusted_sizes[i] > min_size:
                    compressible_space += adjusted_sizes[i] - min_size
            
            if available_space >= min_total and compressible_space > 0:
                # 按比例压缩超出最小尺寸的部分
                excess = total_adjusted - available_space
                compression_ratio = min(1.0, excess / compressible_space)
                
                for i in range(panel_count):
                    min_size = self.min_sizes.get(i, 0)
                    if adjusted_sizes[i] > min_size:
                        compressible = adjusted_sizes[i] - min_size
                        reduction = compressible * compression_ratio
                        adjusted_sizes[i] = max(min_size, adjusted_sizes[i] - reduction)
                        needs_adjustment = True
        
        # 应用调整
        if needs_adjustment:
            self._apply_size_adjustments(adjusted_sizes)
    
    def _apply_size_adjustments(self, target_sizes):
        """应用尺寸调整"""
        try:
            # 使用after_idle确保在空闲时执行
            self.paned_window.after_idle(
                lambda: self._do_apply_adjustments(target_sizes)
            )
        except:
            pass
    
    def _do_apply_adjustments(self, target_sizes):
        """执行尺寸调整"""
        try:
            # 确保所有面板都已经映射到屏幕
            for panel in self.panels:
                if not panel.winfo_ismapped():
                    return  # 如果有面板还没有映射，延迟执行
            
            # 逐个设置分割线位置
            cumulative_size = 0
            for i in range(len(target_sizes) - 1):  # 最后一个面板不需要设置分割线
                cumulative_size += int(target_sizes[i])
                try:
                    # 获取当前分割线位置
                    current_pos = self.paned_window.sashpos(i)
                    if current_pos != cumulative_size:
                        # TTK PanedWindow使用sashpos方法
                        self.paned_window.sashpos(i, cumulative_size)
                        # 强制刷新界面
                        self.paned_window.update_idletasks()
                        pass
                except Exception:
                    pass
        except Exception:
            pass
    
    def _verify_adjustments(self):
        """验证调整是否生效"""
        # 暂时禁用验证，防止无限循环
        pass


def ttk_panedwindow_minsize(paned_window, orientation='horizontal'):
    """
    为TTK PanedWindow添加最小尺寸支持
    
    Args:
        paned_window: ttk.PanedWindow 实例
        orientation: 方向 ('horizontal' 或 'vertical')
    
    Returns:
        TTKPanedWindowMinSize: 最小尺寸管理器实例
    
    Example:
        # 创建PanedWindow
        paned = ttk.PanedWindow(parent, orient='horizontal')
        
        # 添加最小尺寸支持
        minsize_manager = ttk_panedwindow_minsize(paned, 'horizontal')
        
        # 添加面板并设置最小宽度
        minsize_manager.add_panel(left_panel, min_size=400, weight=1)
        minsize_manager.add_panel(right_panel, min_size=250, weight=0)
    """
    return TTKPanedWindowMinSize(paned_window, orientation)


def create_resizable_paned_window(parent, orientation='horizontal', **kwargs):
    """
    创建支持最小尺寸的可调整PanedWindow
    
    Args:
        parent: 父控件
        orientation: 方向 ('horizontal' 或 'vertical')
        **kwargs: 传递给ttk.PanedWindow的参数
    
    Returns:
        tuple: (paned_window, minsize_manager)
    """
    # 设置默认方向参数
    if 'orient' not in kwargs:
        kwargs['orient'] = orientation
    
    # 创建PanedWindow
    paned_window = ttk.PanedWindow(parent, **kwargs)
    
    # 创建最小尺寸管理器
    minsize_manager = ttk_panedwindow_minsize(paned_window, orientation)
    
    return paned_window, minsize_manager
