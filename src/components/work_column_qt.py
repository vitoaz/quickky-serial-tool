"""Qt 多 Tab 工作栏。"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFrame, QMenu, QMessageBox, QStyle, QTabBar, QTabWidget, QToolButton, QVBoxLayout, QWidget

from .work_tab_qt import WorkTab


class WorkColumn(QWidget):
    def __init__(self, config_manager, theme_manager=None, panel_type="main", on_column_activated=None, on_tab_data_sent=None, parent=None):
        super().__init__(parent); self.config_manager, self.theme_manager, self.panel_type, self.on_column_activated, self.on_tab_data_sent, self.is_active = config_manager, theme_manager, panel_type, on_column_activated, on_tab_data_sent, False
        self.notebook = QTabWidget(); self.notebook.setTabsClosable(False); self.notebook.currentChanged.connect(self._on_changed); self.notebook.tabBar().tabBarClicked.connect(self._on_tab_bar_clicked); self.notebook.tabBar().tabBarDoubleClicked.connect(self._close_tab_on_double_click); self.notebook.tabBar().setContextMenuPolicy(Qt.CustomContextMenu); self.notebook.tabBar().customContextMenuRequested.connect(self._tab_menu)
        self._add_tab_page = QWidget(self.notebook); self.notebook.blockSignals(True); self._add_tab_index = self.notebook.addTab(self._add_tab_page, "+"); self.notebook.blockSignals(False)
        for side in (QTabBar.LeftSide, QTabBar.RightSide): self.notebook.tabBar().setTabButton(self._add_tab_index, side, None)
        self.top_border = QFrame(); self.top_border.setFixedHeight(3)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0); layout.addWidget(self.top_border); layout.addWidget(self.notebook); self.set_active(False); self._add_new_tab(True)
    def _add_new_tab(self, first=False):
        tab = WorkTab(self.config_manager, "New Tab", first, self.on_tab_data_sent, self.panel_type, self); self._watch_activation(tab); index = self.notebook.insertTab(self.notebook.indexOf(self._add_tab_page), tab, "New Tab"); port = tab.serial_settings.get_current_port(); self.notebook.setTabText(index, port or "New Tab"); self.notebook.setCurrentIndex(index); self._refresh_close_buttons(); return tab
    def _is_add_tab(self, index): return self.notebook.widget(index) is self._add_tab_page
    def _refresh_close_buttons(self):
        can_close = len(self.get_all_tabs()) > 1
        for index, tab in enumerate(self.get_all_tabs()):
            button = self.notebook.tabBar().tabButton(self.notebook.indexOf(tab), QTabBar.RightSide)
            if not isinstance(button, QToolButton):
                button = QToolButton(self.notebook.tabBar()); button.setAutoRaise(True); button.setToolTip("关闭标签"); button.setIcon(self.style().standardIcon(QStyle.SP_TitleBarCloseButton)); button.setFixedSize(18, 18); button.clicked.connect(lambda _checked=False, target=tab: self._close_tab(self.notebook.indexOf(target))); self.notebook.tabBar().setTabButton(self.notebook.indexOf(tab), QTabBar.RightSide, button)
            button.setVisible(can_close)
    def _watch_activation(self, widget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget): child.installEventFilter(self)
    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress and self.on_column_activated: self.on_column_activated(self)
        return super().eventFilter(watched, event)
    def _on_changed(self, _index):
        if self._is_add_tab(_index): self._add_new_tab(); return
        if self.on_column_activated: self.on_column_activated(self)
    def _on_tab_bar_clicked(self, _index):
        """已选中的 Tab 不会触发 currentChanged，仍需切换活动工作栏。"""
        if self.on_column_activated: self.on_column_activated(self)
    def _close_tab(self, index):
        if self._is_add_tab(index) or len(self.get_all_tabs()) <= 1: return
        if self.notebook.currentIndex() == index:
            self.notebook.setCurrentIndex(index - 1 if index > 0 else index + 1)
        tab = self.notebook.widget(index)
        if not tab.cleanup():
            QMessageBox.warning(self, "日志写入未完成", "日志文件写入超过 1 秒仍未完成，关闭标签后剩余日志可能未写入。")
        self.notebook.removeTab(index); tab.deleteLater(); self._refresh_close_buttons()
    def _close_tab_on_double_click(self, index):
        if index >= 0: self._close_tab(index)
    def _tab_menu(self, pos):
        index = self.notebook.tabBar().tabAt(pos); menu = QMenu(self); add = menu.addAction("新建标签"); add.triggered.connect(self._add_new_tab)
        if index >= 0 and not self._is_add_tab(index) and len(self.get_all_tabs()) > 1:
            close = menu.addAction("关闭标签"); close.triggered.connect(lambda: self._close_tab(index))
        menu.exec(self.notebook.tabBar().mapToGlobal(pos))
    def get_current_tab(self): return self.notebook.currentWidget()
    def get_all_tabs(self): return [self.notebook.widget(index) for index in range(self.notebook.count()) if not self._is_add_tab(index)]
    def set_active(self, active):
        self.is_active = active
        colors = self.theme_manager.get_theme_colors() if self.theme_manager else {}
        color = colors.get("active_border", "#0E639C") if active else colors.get("background", "transparent")
        self.top_border.setStyleSheet(f"background-color: {color}; border: none;")
    def apply_theme(self, theme_manager):
        self.theme_manager = theme_manager
        for tab in self.get_all_tabs(): tab.apply_theme(theme_manager, self.config_manager.get_font_size())
        self.set_active(self.is_active)
    def cleanup(self):
        results = [tab.cleanup() for tab in self.get_all_tabs()]
        return all(results)
    def suspend(self):
        for tab in self.get_all_tabs(): tab.suspend()
