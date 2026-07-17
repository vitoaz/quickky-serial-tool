"""Qt 多 Tab 工作栏。"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QMenu, QTabWidget, QToolButton, QVBoxLayout, QWidget

from .work_tab_qt import WorkTab


class WorkColumn(QWidget):
    def __init__(self, config_manager, theme_manager=None, panel_type="main", on_column_activated=None, on_tab_data_sent=None, parent=None):
        super().__init__(parent); self.config_manager, self.theme_manager, self.panel_type, self.on_column_activated, self.on_tab_data_sent = config_manager, theme_manager, panel_type, on_column_activated, on_tab_data_sent
        self.notebook = QTabWidget(); self.notebook.setTabsClosable(True); self.notebook.tabCloseRequested.connect(self._close_tab); self.notebook.currentChanged.connect(self._on_changed); self.notebook.tabBar().setContextMenuPolicy(Qt.CustomContextMenu); self.notebook.tabBar().customContextMenuRequested.connect(self._tab_menu)
        self.add_tab_button = QToolButton(); self.add_tab_button.setText("+"); self.add_tab_button.setToolTip("新建标签"); self.add_tab_button.setAutoRaise(True); self.add_tab_button.setFixedSize(32, 32); self.add_tab_button.clicked.connect(self._add_new_tab); self.notebook.setCornerWidget(self.add_tab_button, Qt.TopRightCorner)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(self.notebook); self._add_new_tab(True)
    def _add_new_tab(self, first=False):
        tab = WorkTab(self.config_manager, "New Tab", first, self.on_tab_data_sent, self.panel_type, self); self._watch_activation(tab); index = self.notebook.addTab(tab, "New Tab"); self.notebook.setCurrentIndex(index); return tab
    def _watch_activation(self, widget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget): child.installEventFilter(self)
    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress and self.on_column_activated: self.on_column_activated(self)
        return super().eventFilter(watched, event)
    def _on_changed(self, _index):
        if self.on_column_activated: self.on_column_activated(self)
    def _close_tab(self, index):
        if self.notebook.count() <= 1: return
        tab = self.notebook.widget(index); tab.cleanup(); self.notebook.removeTab(index); tab.deleteLater()
    def _tab_menu(self, pos):
        index = self.notebook.tabBar().tabAt(pos); menu = QMenu(self); add = menu.addAction("新建标签"); add.triggered.connect(self._add_new_tab)
        if index >= 0 and self.notebook.count() > 1:
            close = menu.addAction("关闭标签"); close.triggered.connect(lambda: self._close_tab(index))
        menu.exec(self.notebook.tabBar().mapToGlobal(pos))
    def get_current_tab(self): return self.notebook.currentWidget()
    def get_all_tabs(self): return [self.notebook.widget(index) for index in range(self.notebook.count())]
    def apply_theme(self, theme_manager):
        for tab in self.get_all_tabs(): tab.apply_theme(theme_manager, self.config_manager.get_font_size())
    def cleanup(self):
        for tab in self.get_all_tabs(): tab.cleanup()
