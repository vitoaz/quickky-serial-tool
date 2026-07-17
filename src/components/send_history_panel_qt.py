"""Qt 发送历史面板。"""

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class SendHistoryPanel(QWidget):
    def __init__(self, config_manager, main_window=None, parent=None):
        super().__init__(parent); self.config_manager, self.main_window, self.items = config_manager, main_window, []
        self.table = QTableWidget(0, 2); self.table.setHorizontalHeaderLabels(["时间", "数据"]); self.table.horizontalHeader().setStretchLastSection(True); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers); self.table.itemDoubleClicked.connect(lambda _item: self._send_selected()); self.table.setContextMenuPolicy(Qt.CustomContextMenu); self.table.customContextMenuRequested.connect(self._menu)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(self.table); self.refresh()
    def refresh(self):
        self.table.setRowCount(0); self.items = self.config_manager.get_send_history()
        for item in self.items:
            item = {"data": item, "mode": "TEXT", "time": ""} if isinstance(item, str) else item; row = self.table.rowCount(); self.table.insertRow(row); time = item.get("time", "")
            try: time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S").strftime("%m-%d %H:%M:%S")
            except ValueError: pass
            data = str(item.get("data", "")).replace("\n", "\\n"); data = ("[H] " if item.get("mode") == "HEX" else "[T] ") + (data[:50] + ("..." if len(data) > 50 else "")); self.table.setItem(row, 0, QTableWidgetItem(time)); self.table.setItem(row, 1, QTableWidgetItem(data))
    def _menu(self, pos):
        menu = QMenu(self); row = self.table.currentRow()
        if row >= 0: send = menu.addAction("发送"); send.triggered.connect(self._send_selected)
        clear = menu.addAction("清空历史"); clear.triggered.connect(self._clear); menu.exec(self.table.viewport().mapToGlobal(pos))
    def _send_selected(self):
        row = self.table.currentRow()
        if row < 0 or not self.main_window or row >= len(self.items): return
        item = self.items[row]; item = {"data": item, "mode": "TEXT"} if isinstance(item, str) else item; self.main_window.work_panel.send_data(str(item.get("data", "")), item.get("mode", "TEXT"))
    def _clear(self):
        if QMessageBox.question(self, "确认", "确定清空所有发送历史？") == QMessageBox.Yes: self.config_manager.clear_send_history(); self.refresh()
