"""
主题管理器

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import json
import os
import sys
from typing import Dict, List
from tkinter import ttk


class ThemeManager:
    """主题管理类"""
    
    def __init__(self, root=None):
        """
        初始化主题管理器
        
        Args:
            root: Tkinter根窗口，用于设置ttk.Style
        """
        # 获取主题目录路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        self.themes_dir = os.path.join(base_path, 'themes')
        self.current_theme = None
        self.root = root
        self.style = ttk.Style(root) if root else None
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
                "inactive_tab": "#F5F5F5"
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
    
    def apply_theme_to_widget(self, widget, widget_type: str = 'text'):
        """
        应用主题到控件
        
        Args:
            widget: Tkinter控件
            widget_type: 控件类型 ('text', 'button', 'frame', 'entry', 'labelframe', 'terminal')
        """
        if not self.current_theme:
            return
        
        try:
            colors = self.current_theme.get('colors', {})
            
            if widget_type == 'text':
                widget.configure(
                    bg=colors.get('text_bg', '#FFFFFF'),
                    fg=colors.get('text_fg', '#000000'),
                    selectbackground=colors.get('selectbackground', '#0078D7'),
                    selectforeground=colors.get('selectforeground', '#FFFFFF'),
                    insertbackground=colors.get('text_fg', '#000000')
                )
            elif widget_type == 'button':
                widget.configure(
                    bg=colors.get('button_bg', '#F0F0F0'),
                    fg=colors.get('button_fg', '#000000')
                )
            elif widget_type == 'frame':
                widget.configure(
                    bg=colors.get('frame_bg', '#F5F5F5')
                )
            elif widget_type == 'entry':
                widget.configure(
                    bg=colors.get('entry_bg', '#FFFFFF'),
                    fg=colors.get('entry_fg', '#000000'),
                    selectbackground=colors.get('selectbackground', '#0078D7'),
                    selectforeground=colors.get('selectforeground', '#FFFFFF'),
                    insertbackground=colors.get('entry_fg', '#000000')
                )
            elif widget_type == 'labelframe':
                widget.configure(
                    bg=colors.get('labelframe_bg', '#EFEFEF')
                )
            elif widget_type == 'terminal':
                widget.configure(
                    bg=colors.get('terminal_bg', '#000000'),
                    fg=colors.get('terminal_fg', '#FFFFFF'),
                    selectbackground=colors.get('selectbackground', '#0078D7'),
                    selectforeground=colors.get('selectforeground', '#FFFFFF'),
                    insertbackground=colors.get('terminal_fg', '#FFFFFF')
                )
        except Exception as e:
            print(f"应用主题到控件失败: {e}")
    
    def get_theme_colors(self) -> Dict[str, str]:
        """
        获取当前主题的所有颜色
        
        Returns:
            Dict[str, str]: 颜色字典
        """
        if self.current_theme and 'colors' in self.current_theme:
            return self.current_theme['colors']
        return {}
    
    def apply_ttk_theme(self):
        """应用主题到ttk控件"""
        if not self.style or not self.current_theme:
            return
        
        colors = self.current_theme.get('colors', {})
        
        try:
            # 使用clam主题作为基础（现代化外观，边框最少，最干净）
            # 其他可选: 'vista'(Windows原生), 'default'(系统默认)
            # 避免使用: 'alt'(边框明显), 'classic'(老式风格)
            self.style.theme_use('clam')
            
            # 配置ttk.Frame样式
            self.style.configure('TFrame', 
                               background=colors.get('frame_bg', '#F5F5F5'))
            self.style.configure('WorkTab.TFrame', 
                               background=colors.get('background', '#FFFFFF'))
            
            # 配置ttk.LabelFrame样式
            self.style.configure('TLabelframe', 
                               background=colors.get('labelframe_bg', '#EFEFEF'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               relief='solid',
                               borderwidth=1)
            self.style.configure('TLabelframe.Label', 
                               background=colors.get('labelframe_bg', '#EFEFEF'),
                               foreground=colors.get('foreground', '#000000'))
            
            # 配置ttk.Button样式
            self.style.configure('TButton',
                               background=colors.get('button_bg', '#F0F0F0'),
                               foreground=colors.get('button_fg', '#000000'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               lightcolor=colors.get('button_bg', '#F0F0F0'),
                               darkcolor=colors.get('border', '#D0D0D0'),
                               borderwidth=1,
                               relief='raised',
                               focuscolor='',
                               cursor='hand2')
            self.style.map('TButton',
                         background=[('active', colors.get('border', '#D0D0D0')),
                                   ('pressed', colors.get('border', '#D0D0D0'))])
            
            # 配置ttk.Label样式
            self.style.configure('TLabel',
                               background=colors.get('labelframe_bg', '#EFEFEF'),
                               foreground=colors.get('foreground', '#000000'))
            
            # 配置ttk.Checkbutton样式
            self.style.configure('TCheckbutton',
                               background=colors.get('labelframe_bg', '#EFEFEF'),
                               foreground=colors.get('foreground', '#000000'),
                               indicatorbackground=colors.get('entry_bg', '#FFFFFF'),
                               indicatorforeground=colors.get('foreground', '#000000'),
                               focuscolor=colors.get('labelframe_bg', '#EFEFEF'))
            self.style.map('TCheckbutton',
                         background=[('active', colors.get('labelframe_bg', '#EFEFEF'))],
                         foreground=[('active', colors.get('foreground', '#000000'))],
                         indicatorcolor=[('selected', colors.get('checkbox_selected', colors.get('selectbackground', '#0078D7')))])
            
            # 配置ttk.Radiobutton样式
            # 现在frame_bg和labelframe_bg一致，使用labelframe_bg即可
            self.style.configure('TRadiobutton',
                               background=colors.get('labelframe_bg', '#F5F5F5'),
                               foreground=colors.get('foreground', '#000000'),
                               borderwidth=0,
                               relief='flat',
                               focuscolor=colors.get('labelframe_bg', '#F5F5F5'))
            
            self.style.map('TRadiobutton',
                         background=[('active', colors.get('labelframe_bg', '#F5F5F5'))],
                         indicatorcolor=[('selected', colors.get('checkbox_selected', colors.get('selectbackground', '#0078D7')))])
            
            # 配置ttk.Combobox样式
            self.style.configure('TCombobox',
                               fieldbackground=colors.get('entry_bg', '#FFFFFF'),
                               background=colors.get('button_bg', '#F0F0F0'),
                               foreground=colors.get('entry_fg', '#000000'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               arrowcolor=colors.get('foreground', '#000000'),
                               selectbackground=colors.get('selectbackground', '#0078D7'),
                               selectforeground=colors.get('selectforeground', '#FFFFFF'))
            self.style.map('TCombobox',
                         fieldbackground=[('readonly', colors.get('entry_bg', '#FFFFFF'))],
                         selectbackground=[('readonly', colors.get('entry_bg', '#FFFFFF'))],
                         selectforeground=[('readonly', colors.get('entry_fg', '#000000'))],
                         background=[('active', colors.get('button_bg', '#F0F0F0'))],
                         arrowcolor=[('active', colors.get('selectbackground', '#0078D7'))])
            
            # 配置ttk.Entry样式
            self.style.configure('TEntry',
                               fieldbackground=colors.get('entry_bg', '#FFFFFF'),
                               foreground=colors.get('entry_fg', '#000000'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               insertcolor=colors.get('entry_fg', '#000000'))
            
            # 配置ttk.Spinbox样式
            self.style.configure('TSpinbox',
                               fieldbackground=colors.get('entry_bg', '#FFFFFF'),
                               background=colors.get('button_bg', '#F0F0F0'),
                               foreground=colors.get('entry_fg', '#000000'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               arrowcolor=colors.get('foreground', '#000000'))
            
            # 配置ttk.Notebook样式
            self.style.configure('TNotebook',
                               background=colors.get('frame_bg', '#F5F5F5'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               tabmargins=[2, 5, 2, 0])
            self.style.configure('TNotebook.Tab',
                               background=colors.get('inactive_tab', '#F5F5F5'),
                               foreground=colors.get('foreground', '#000000'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               lightcolor=colors.get('inactive_tab', '#F5F5F5'),
                               padding=[10, 2],
                               focuscolor='')
            self.style.map('TNotebook.Tab',
                         background=[('selected', colors.get('active_tab', '#E0E0E0')),
                                   ('active', colors.get('active_tab', '#E0E0E0'))],
                         foreground=[('selected', colors.get('foreground', '#000000'))],
                         expand=[('selected', [1, 1, 1, 0])])
            
            # 配置ttk.PanedWindow样式
            self.style.configure('TPanedwindow',
                               background=colors.get('frame_bg', '#F5F5F5'))
            
            # 配置ttk.Treeview样式（用于快捷指令和历史面板）
            self.style.configure('Treeview',
                               background=colors.get('entry_bg', '#FFFFFF'),
                               foreground=colors.get('entry_fg', '#000000'),
                               fieldbackground=colors.get('entry_bg', '#FFFFFF'),
                               bordercolor=colors.get('border', '#D0D0D0'))
            self.style.map('Treeview',
                         background=[('selected', colors.get('selectbackground', '#0078D7')),
                                   ('active', colors.get('frame_bg', '#F5F5F5'))],
                         foreground=[('selected', colors.get('selectforeground', '#FFFFFF')),
                                   ('active', colors.get('foreground', '#000000'))])
            
            # 配置Treeview标题样式
            self.style.configure('Treeview.Heading',
                               background=colors.get('button_bg', '#F0F0F0'),
                               foreground=colors.get('foreground', '#000000'),
                               bordercolor=colors.get('border', '#D0D0D0'),
                               relief='raised')
            self.style.map('Treeview.Heading',
                         background=[('active', colors.get('button_bg', '#F0F0F0'))],
                         foreground=[('active', colors.get('foreground', '#000000'))])
            
            # 配置Combobox下拉列表颜色（使用option_add）
            if self.root:
                self.root.option_add('*TCombobox*Listbox.background', colors.get('entry_bg', '#FFFFFF'))
                self.root.option_add('*TCombobox*Listbox.foreground', colors.get('entry_fg', '#000000'))
                self.root.option_add('*TCombobox*Listbox.selectBackground', colors.get('selectbackground', '#0078D7'))
                self.root.option_add('*TCombobox*Listbox.selectForeground', colors.get('selectforeground', '#FFFFFF'))
            
            # 配置滚动条样式 - 现代扁平化设计
            self.style.configure('Vertical.TScrollbar',
                               background=colors.get('scrollbar_bg', '#F0F0F0'),
                               troughcolor=colors.get('text_bg', '#FFFFFF'),
                               bordercolor=colors.get('text_bg', '#FFFFFF'),
                               arrowcolor=colors.get('scrollbar_fg', '#686868'),
                               relief='flat',
                               borderwidth=0)
            self.style.map('Vertical.TScrollbar',
                         background=[('active', colors.get('scrollbar_fg', '#C0C0C0')),
                                   ('pressed', colors.get('scrollbar_fg', '#C0C0C0'))],
                         arrowcolor=[('active', colors.get('foreground', '#D4D4D4'))])
            
            self.style.configure('Horizontal.TScrollbar',
                               background=colors.get('scrollbar_bg', '#F0F0F0'),
                               troughcolor=colors.get('text_bg', '#FFFFFF'),
                               bordercolor=colors.get('text_bg', '#FFFFFF'),
                               arrowcolor=colors.get('scrollbar_fg', '#686868'),
                               relief='flat',
                               borderwidth=0)
            self.style.map('Horizontal.TScrollbar',
                         background=[('active', colors.get('scrollbar_fg', '#C0C0C0')),
                                   ('pressed', colors.get('scrollbar_fg', '#C0C0C0'))],
                         arrowcolor=[('active', colors.get('foreground', '#D4D4D4'))])
            
        except Exception as e:
            print(f"应用ttk主题失败: {e}")

