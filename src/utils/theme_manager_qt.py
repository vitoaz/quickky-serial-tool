"""Qt Widgets 主题加载与样式表生成。"""

import json
from pathlib import Path

from PySide6.QtGui import QColor, QPalette

from .file_utils import resource_path


class ThemeManagerQt:
    """复用 themes/ 中的颜色定义，为 Qt Widgets 生成样式表。"""

    def __init__(self):
        self._theme_name = "light"
        self._colors = {}

    def get_available_themes(self):
        theme_dir = Path(resource_path("themes"))
        return sorted(path.stem for path in theme_dir.glob("*.json"))

    def load_theme(self, theme_name):
        path = Path(resource_path("themes")) / f"{theme_name}.json"
        if not path.exists():
            path = Path(resource_path("themes")) / "light.json"
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        self._theme_name = path.stem
        self._colors = data.get("colors", {})
        return self._colors

    def get_theme_colors(self):
        return self._colors

    def palette(self):
        """将当前主题颜色映射到 Qt 标准控件使用的调色板。"""
        colors = self._colors
        background = QColor(colors.get("background", "#FFFFFF"))
        border = QColor(colors.get("border", "#D0D0D0"))
        control_border = border.lighter(180) if background.lightness() < 128 else border.darker(180)
        palette = QPalette()
        palette.setColor(QPalette.Window, background)
        palette.setColor(QPalette.WindowText, QColor(colors.get("foreground", "#000000")))
        palette.setColor(QPalette.Base, QColor(colors.get("text_bg", "#FFFFFF")))
        palette.setColor(QPalette.AlternateBase, QColor(colors.get("button_bg", "#F0F0F0")))
        palette.setColor(QPalette.Text, QColor(colors.get("text_fg", "#000000")))
        palette.setColor(QPalette.Button, QColor(colors.get("button_bg", "#F0F0F0")))
        palette.setColor(QPalette.ButtonText, QColor(colors.get("button_fg", "#000000")))
        palette.setColor(QPalette.Highlight, QColor(colors.get("selectbackground", "#0078D7")))
        palette.setColor(QPalette.HighlightedText, QColor(colors.get("selectforeground", "#FFFFFF")))
        palette.setColor(QPalette.Light, control_border.lighter(125))
        palette.setColor(QPalette.Midlight, control_border)
        palette.setColor(QPalette.Mid, control_border)
        palette.setColor(QPalette.Dark, control_border)
        palette.setColor(QPalette.Shadow, control_border.darker(130))
        disabled = control_border
        palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
        palette.setColor(QPalette.Disabled, QPalette.Text, disabled)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
        return palette

    def stylesheet(self):
        colors = self._colors
        bg = colors.get("background", "#FFFFFF")
        fg = colors.get("foreground", "#000000")
        text_bg = colors.get("text_bg", bg)
        text_fg = colors.get("text_fg", fg)
        button_bg = colors.get("button_bg", "#F0F0F0")
        button_fg = colors.get("button_fg", fg)
        border = colors.get("border", "#D0D0D0")
        selected = colors.get("selectbackground", "#0078D7")
        selected_fg = colors.get("selectforeground", "#FFFFFF")
        active = colors.get("active_border", selected)
        return f"""
            QWidget {{ background: {bg}; color: {fg}; }}
            QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QTableWidget, QTreeWidget {{
                background: {text_bg}; color: {text_fg}; border: 1px solid {border};
            }}
            QPushButton {{ background: {button_bg}; color: {button_fg}; border: 1px solid {border}; padding: 5px; }}
            QPushButton:hover {{ border-color: {active}; }}
            QTabBar::tab {{ background: {colors.get('inactive_tab', bg)}; padding: 7px 10px; border: 1px solid {border}; }}
            QTabBar::tab:selected {{ background: {colors.get('active_tab', text_bg)}; border-top: 2px solid {active}; }}
            QTableWidget {{ gridline-color: {border}; alternate-background-color: {button_bg}; }}
            QTableWidget::item {{ padding: 3px 5px; }}
            QHeaderView::section {{ background: {button_bg}; color: {button_fg}; border: 1px solid {border}; padding: 4px; }}
            QMenu::item:selected, QTableWidget::item:selected {{ background: {selected}; color: {selected_fg}; }}
        """
