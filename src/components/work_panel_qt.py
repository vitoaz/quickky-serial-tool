"""Qt 单栏 / 双栏工作区。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QVBoxLayout, QWidget

from .work_column_qt import WorkColumn


class WorkPanel(QWidget):
    def __init__(self, config_manager, theme_manager, on_tab_data_sent=None, parent=None):
        super().__init__(parent); self.config_manager, self.theme_manager, self.on_tab_data_sent = config_manager, theme_manager, on_tab_data_sent; self.active_column = None
        self.main_column = WorkColumn(config_manager, theme_manager, "main", self._activate, on_tab_data_sent, self); self.secondary_column = WorkColumn(config_manager, theme_manager, "secondary", self._activate, on_tab_data_sent, self); self.active_column = self.main_column
        self.splitter = QSplitter(Qt.Horizontal); self.splitter.setChildrenCollapsible(False); self.splitter.addWidget(self.main_column); self.splitter.addWidget(self.secondary_column); self.splitter.setCollapsible(0, False); self.splitter.setCollapsible(1, False); self.secondary_column.setVisible(config_manager.get_dual_panel_mode())
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(self.splitter)
    def _activate(self, column): self.active_column = column
    def toggle_dual_panel_mode(self, enabled):
        self.secondary_column.setVisible(enabled)
        if not enabled:
            self.secondary_column.cleanup()
            self.active_column = self.main_column
        self.config_manager.set_dual_panel_mode(enabled)
    def get_current_work_tab(self): return self.active_column.get_current_tab() if self.active_column else self.main_column.get_current_tab()
    def get_all_work_tabs(self): return self.main_column.get_all_tabs() + (self.secondary_column.get_all_tabs() if self.secondary_column.isVisible() else [])
    def send_data(self, data, mode):
        tab = self.get_current_work_tab()
        if not tab: return False
        tab.send_data(data, mode); return True
    def apply_theme(self): self.main_column.apply_theme(self.theme_manager); self.secondary_column.apply_theme(self.theme_manager)
    def cleanup(self): self.main_column.cleanup(); self.secondary_column.cleanup()
