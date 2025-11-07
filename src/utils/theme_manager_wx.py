"""
主题管理器 (wxPython版本)

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import json
import os
import wx
from typing import Dict, List
from .file_utils import get_base_path


class ThemeManagerWx:
    """wxPython主题管理类"""
    
    def __init__(self):
        """初始化主题管理器"""
        # 获取主题目录路径
        base_path = get_base_path()
        self.themes_dir = os.path.join(base_path, 'themes')
        self.current_theme = None
        self._current_theme_name = 'light'
        self._ensure_themes_dir()
    
    def _ensure_themes_dir(self):
        """确保主题目录存在"""
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir)
    
    def get_available_themes(self) -> List[str]:
        """
        获取可用的主题列表
        
        Returns:
            List[str]: 主题名称列表
        """
        themes = []
        try:
            if os.path.exists(self.themes_dir):
                for filename in os.listdir(self.themes_dir):
                    if filename.endswith('.json'):
                        theme_name = filename[:-5]  # 移除.json后缀
                        themes.append(theme_name)
        except Exception as e:
            print(f"获取主题列表失败: {e}")
        
        return sorted(themes)
    
    def load_theme(self, theme_name: str) -> Dict:
        """
        加载指定主题
        
        Args:
            theme_name: 主题名称
            
        Returns:
            Dict: 主题配置字典
        """
        theme_file = os.path.join(self.themes_dir, f"{theme_name}.json")
        
        try:
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    self.current_theme = theme_data
                    self._current_theme_name = theme_name
                    return theme_data
            else:
                print(f"主题文件不存在: {theme_file}")
                return self._get_default_theme()
        except Exception as e:
            print(f"加载主题失败: {e}")
            return self._get_default_theme()
    
    def _get_default_theme(self) -> Dict:
        """获取默认主题（Light主题）"""
        return {
            "name": "Light",
            "description": "明亮主题",
            "colors": {
                "background": "#FFFFFF",
                "foreground": "#000000",
                "text_bg": "#FFFFFF",
                "text_fg": "#000000",
                "button_bg": "#F0F0F0",
                "button_fg": "#000000",
                "frame_bg": "#F5F5F5",
                "labelframe_bg": "#EFEFEF",
                "entry_bg": "#FFFFFF",
                "entry_fg": "#000000",
                "selectbackground": "#0078D7",
                "selectforeground": "#FFFFFF",
                "border": "#D0D0D0",
                "scrollbar_bg": "#F0F0F0",
                "scrollbar_fg": "#C0C0C0",
                "terminal_bg": "#FFFFFF",
                "terminal_fg": "#000000",
                "active_tab": "#E0E0E0",
                "inactive_tab": "#F5F5F5",
                "link_color": "#0066CC",
                "log_info_color": "#0066CC",
                "log_error_color": "#D32F2F",
                "log_success_color": "#388E3C",
                "log_warning_color": "#D32F2F"
            }
        }
    
    def get_color(self, color_key: str, default: str = "#000000") -> str:
        """
        获取当前主题的颜色值
        
        Args:
            color_key: 颜色键名
            default: 默认颜色值
            
        Returns:
            str: 颜色值（十六进制格式）
        """
        if self.current_theme and 'colors' in self.current_theme:
            return self.current_theme['colors'].get(color_key, default)
        return default
    
    def get_theme_colors(self) -> Dict[str, str]:
        """
        获取当前主题的所有颜色
        
        Returns:
            Dict[str, str]: 颜色字典
        """
        if self.current_theme and 'colors' in self.current_theme:
            return self.current_theme['colors']
        return {}
    
    def hex_to_wx_colour(self, hex_color: str) -> wx.Colour:
        """
        将十六进制颜色转换为wx.Colour
        
        Args:
            hex_color: 十六进制颜色字符串（如 "#FFFFFF"）
            
        Returns:
            wx.Colour对象
        """
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return wx.Colour(r, g, b)
        except:
            return wx.Colour(255, 255, 255)  # 默认白色
    
    def apply_theme_to_widget(self, widget, widget_type: str = 'panel'):
        """
        应用主题到控件
        
        Args:
            widget: wx控件
            widget_type: 控件类型 ('panel', 'text', 'button', 'static')
        """
        if not self.current_theme:
            return
        
        try:
            colors = self.current_theme.get('colors', {})
            
            if widget_type == 'panel':
                bg_color = self.hex_to_wx_colour(colors.get('frame_bg', '#F5F5F5'))
                widget.SetBackgroundColour(bg_color)
            
            elif widget_type == 'text':
                bg_color = self.hex_to_wx_colour(colors.get('text_bg', '#FFFFFF'))
                fg_color = self.hex_to_wx_colour(colors.get('text_fg', '#000000'))
                widget.SetBackgroundColour(bg_color)
                widget.SetForegroundColour(fg_color)
            
            elif widget_type == 'button':
                bg_color = self.hex_to_wx_colour(colors.get('button_bg', '#F0F0F0'))
                fg_color = self.hex_to_wx_colour(colors.get('button_fg', '#000000'))
                widget.SetBackgroundColour(bg_color)
                widget.SetForegroundColour(fg_color)
            
            elif widget_type == 'static':
                bg_color = self.hex_to_wx_colour(colors.get('labelframe_bg', '#EFEFEF'))
                fg_color = self.hex_to_wx_colour(colors.get('foreground', '#000000'))
                widget.SetBackgroundColour(bg_color)
                widget.SetForegroundColour(fg_color)
            
        except Exception as e:
            print(f"应用主题到控件失败: {e}")

