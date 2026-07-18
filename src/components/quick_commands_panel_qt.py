"""Qt 快捷指令分组、编辑和发送面板。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QHeaderView, QInputDialog, QMenu, QMessageBox, QTabWidget,
                               QAbstractItemView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .quick_command_dialog_qt import QuickCommandDialog


class CommandTable(QTableWidget):
    rows_reordered = Signal()

    def __init__(self, parent=None):
        super().__init__(0, 2, parent)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True); self.setAcceptDrops(True); self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def dropEvent(self, event):
        if event.source() is not self:
            super().dropEvent(event)
            return
        selected = self.selectionModel().selectedRows()
        if len(selected) != 1:
            event.ignore()
            return
        source = selected[0].row()
        target = self.indexAt(event.position().toPoint()).row()
        if target < 0:
            target = self.rowCount()
        if target == source or target == source + 1:
            event.acceptProposedAction()
            return
        self._move_row(source, target)
        event.acceptProposedAction()
        self.rows_reordered.emit()

    def _move_row(self, source, target):
        items = [self.takeItem(source, column) for column in range(self.columnCount())]
        self.removeRow(source)
        if target > source:
            target -= 1
        self.insertRow(target)
        for column, item in enumerate(items):
            self.setItem(target, column, item)
        self.selectRow(target)


class QuickCommandsPanel(QWidget):
    def __init__(self, config_manager, main_window=None, parent=None):
        super().__init__(parent); self.config_manager, self.main_window = config_manager, main_window; self.group_notebook = QTabWidget(); self.group_notebook.setDocumentMode(True); self.group_notebook.setFont(QFont(self.font().family(), 7)); self.group_notebook.setMovable(True); self.group_notebook.tabBar().setContextMenuPolicy(Qt.CustomContextMenu); self.group_notebook.tabBar().customContextMenuRequested.connect(self._group_menu); self.group_notebook.tabBar().tabMoved.connect(self._save_group_order)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(self.group_notebook); self._load_groups()
    def _groups(self): return self.config_manager.get_quick_command_groups()
    def _load_groups(self):
        while self.group_notebook.count():
            page = self.group_notebook.widget(0)
            self.group_notebook.removeTab(0)
            page.deleteLater()
        groups = self._groups()
        if not groups: groups = [{"name": "默认", "commands": []}]; self.config_manager.set_quick_command_groups(groups)
        for index, group in enumerate(groups): self._create_group_tab(index, group)
    def _create_group_tab(self, index, group):
        table = CommandTable(); compact_font = QFont(table.font().family(), 7); table.setFont(compact_font); table.horizontalHeader().setFont(compact_font); table.verticalHeader().setDefaultSectionSize(22); table.setHorizontalHeaderLabels(["名称", "数据"]); table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed); table.setColumnWidth(0, 75); table.horizontalHeader().setStretchLastSection(True); table.verticalHeader().setVisible(False); table.setSelectionBehavior(QTableWidget.SelectRows); table.setEditTriggers(QTableWidget.NoEditTriggers); table.itemDoubleClicked.connect(lambda _item, table=table: self._send_command(table)); table.setContextMenuPolicy(Qt.CustomContextMenu); table.customContextMenuRequested.connect(lambda pos, table=table: self._command_menu(table, pos)); table.rows_reordered.connect(lambda table=table: self._save_command_order(table)); self._fill_table(table, group)
        self.group_notebook.addTab(table, group.get("name", "默认"))
    def _fill_table(self, table, group):
        table.setRowCount(0)
        for command in group.get("commands", []):
            row = table.rowCount(); table.insertRow(row); data = str(command.get("data", command.get("command", ""))); prefix = "[H] " if command.get("mode") == "HEX" else "[T] "; name_item = QTableWidgetItem(command.get("name", "")); name_item.setData(Qt.UserRole, command); table.setItem(row, 0, name_item); table.setItem(row, 1, QTableWidgetItem(prefix + data.replace("\n", "\\n").replace("\r", "\\r")))
    def _current_index(self): return self.group_notebook.currentIndex()
    def _current_table(self): return self.group_notebook.currentWidget()
    def _save_group_order(self, source, target):
        """按页签索引移动，允许历史配置中存在同名分组。"""
        groups = self._groups()
        if not (0 <= source < len(groups) and 0 <= target < len(groups)):
            return
        group = groups.pop(source)
        groups.insert(target, group)
        self.config_manager.set_quick_command_groups(groups)
    def _save_command_order(self, table):
        index = self.group_notebook.indexOf(table)
        if index < 0: return
        groups = self._groups()
        groups[index]["commands"] = [table.item(row, 0).data(Qt.UserRole) for row in range(table.rowCount())]
        self.config_manager.set_quick_command_groups(groups)
    def _group_menu(self, pos):
        index = self.group_notebook.tabBar().tabAt(pos); menu = QMenu(self); add = menu.addAction("新建分组"); add.triggered.connect(self._add_group)
        if index >= 0:
            rename = menu.addAction("编辑分组"); rename.triggered.connect(lambda: self._rename_group(index)); delete = menu.addAction("删除分组"); delete.triggered.connect(lambda: self._delete_group(index))
        menu.exec(self.group_notebook.tabBar().mapToGlobal(pos))
    def _add_group(self):
        name, ok = QInputDialog.getText(self, "新建分组", "分组名称:")
        if ok and name.strip(): groups = self._groups(); groups.append({"name": name.strip(), "commands": []}); self.config_manager.set_quick_command_groups(groups); self._load_groups(); self.group_notebook.setCurrentIndex(len(groups)-1)
    def _rename_group(self, index):
        groups = self._groups(); name, ok = QInputDialog.getText(self, "编辑分组", "分组名称:", text=groups[index]["name"])
        if ok and name.strip(): groups[index]["name"] = name.strip(); self.config_manager.set_quick_command_groups(groups); self.group_notebook.setTabText(index, name.strip())
    def _delete_group(self, index):
        groups = self._groups()
        if len(groups) <= 1: QMessageBox.warning(self, "提示", "至少需要保留一个分组"); return
        if QMessageBox.question(self, "确认", f'确定删除分组“{groups[index]["name"]}”？') == QMessageBox.Yes: groups.pop(index); self.config_manager.set_quick_command_groups(groups); self._load_groups()
    def _command_menu(self, table, pos):
        item = table.itemAt(pos)
        if item: table.selectRow(item.row())
        else: table.clearSelection(); table.setCurrentItem(None)
        menu = QMenu(self); row = table.currentRow()
        add = menu.addAction("添加指令"); add.triggered.connect(self._add_command)
        if row >= 0:
            send = menu.addAction("发送"); send.triggered.connect(lambda: self._send_command(table)); edit = menu.addAction("编辑指令"); edit.triggered.connect(lambda: self._edit_command(row)); delete = menu.addAction("删除指令"); delete.triggered.connect(lambda: self._delete_command(row))
        menu.exec(table.viewport().mapToGlobal(pos))
    def _add_command(self):
        dialog = QuickCommandDialog(self)
        if dialog.exec(): groups = self._groups(); groups[self._current_index()]["commands"].append(dialog.get_command()); self.config_manager.set_quick_command_groups(groups); self._fill_table(self._current_table(), groups[self._current_index()])
    def _edit_command(self, row):
        groups = self._groups(); group = groups[self._current_index()]; dialog = QuickCommandDialog(self, group["commands"][row])
        if dialog.exec(): group["commands"][row] = dialog.get_command(); self.config_manager.set_quick_command_groups(groups); self._fill_table(self._current_table(), group)
    def _delete_command(self, row):
        if QMessageBox.question(self, "确认", "确定删除选中指令？") == QMessageBox.Yes: groups = self._groups(); group = groups[self._current_index()]; group["commands"].pop(row); self.config_manager.set_quick_command_groups(groups); self._fill_table(self._current_table(), group)
    def _send_command(self, table):
        row = table.currentRow()
        if row < 0 or not self.main_window: return
        command = self._groups()[self._current_index()]["commands"][row]; self.main_window.work_panel.send_data(str(command.get("data", command.get("command", ""))), command.get("mode", "TEXT")); self.main_window.command_panel.refresh_history()
