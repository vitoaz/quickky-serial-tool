"""Qt 主窗口：菜单、工作区、命令栏、主题和配置导入导出。"""

from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QFileDialog,
                               QLabel, QMainWindow, QMessageBox, QSplitter, QVBoxLayout)

from components.command_panel_qt import CommandPanel
from components.work_panel_qt import WorkPanel
from pages.settings_dialog_qt import SettingsDialog
from utils.app_info import AppInfo
from utils.config_manager import ConfigManager
from utils.file_utils import resource_path
from utils.theme_manager_qt import ThemeManagerQt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); QApplication.setStyle("Windows"); self.setWindowTitle(AppInfo.get_window_title()); self.resize(1200, 720)
        icon = Path(resource_path("icon.png"))
        if icon.exists(): self.setWindowIcon(QIcon(str(icon)))
        self.config_manager, self.theme_manager = ConfigManager(), ThemeManagerQt(); self._create_widgets(); self._create_menu(); self.apply_theme()
    def _create_widgets(self):
        self.work_panel = WorkPanel(self.config_manager, self.theme_manager, self._on_data_sent, self); self.command_panel = CommandPanel(self.config_manager, self, self)
        self.splitter = QSplitter(); self.splitter.setChildrenCollapsible(False); self.splitter.addWidget(self.work_panel); self.splitter.addWidget(self.command_panel); self.splitter.setCollapsible(0, False); self.splitter.setCollapsible(1, False); self.splitter.setStretchFactor(0, 1); self.command_panel.setVisible(self.config_manager.get_command_panel_visible()); self.setCentralWidget(self.splitter); QTimer.singleShot(0, self._sync_command_panel_width)
    def _create_menu(self):
        file_menu = self.menuBar().addMenu("文件")
        self._action(file_menu, "导出配置", self._export_config); self._action(file_menu, "导入配置", self._import_config); file_menu.addSeparator(); self._action(file_menu, "设置", self._settings); file_menu.addSeparator(); self._action(file_menu, "退出", self.close)
        view_menu = self.menuBar().addMenu("视图"); self.dual_action = self._action(view_menu, "双栏模式", self._toggle_dual, checkable=True); self.dual_action.setChecked(self.config_manager.get_dual_panel_mode()); self.command_action = self._action(view_menu, "命令面板", self._toggle_command, checkable=True); self.command_action.setChecked(self.config_manager.get_command_panel_visible())
        theme_menu = self.menuBar().addMenu("主题"); self.theme_actions = []
        for name in self.theme_manager.get_available_themes():
            action = self._action(theme_menu, name.capitalize(), lambda checked=False, value=name: self._change_theme(value), checkable=True); self.theme_actions.append(action)
        help_menu = self.menuBar().addMenu("帮助"); self._action(help_menu, "关于", self._about)
    @staticmethod
    def _action(menu, title, callback, checkable=False):
        action = QAction(title, menu); action.setCheckable(checkable); action.triggered.connect(callback); menu.addAction(action); return action
    def _on_data_sent(self): self.command_panel.refresh_history()
    def _toggle_dual(self, checked): self.work_panel.toggle_dual_panel_mode(checked)
    def _toggle_command(self, checked): self.command_panel.setVisible(checked); self.config_manager.set_command_panel_visible(checked); QTimer.singleShot(0, self._sync_command_panel_width)
    def _sync_command_panel_width(self):
        if not self.command_panel.isVisible() or self.splitter.width() <= 0: return
        command_width = self.command_panel.width(); work_width = max(0, self.splitter.width() - command_width - self.splitter.handleWidth())
        self.splitter.setSizes([work_width, command_width])
    def _change_theme(self, name): self.config_manager.set_theme(name); self.apply_theme()
    def apply_theme(self):
        name = self.config_manager.get_theme(); self.theme_manager.load_theme(name); QApplication.instance().setPalette(self.theme_manager.palette()); self.setStyleSheet(self.theme_manager.stylesheet()); self.work_panel.apply_theme()
        for action in self.theme_actions: action.setChecked(action.text().lower() == self.theme_manager._theme_name.lower())
    def _export_config(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出配置", "config.json", "JSON 文件 (*.json)")
        if path: QMessageBox.information(self, "导出配置", "配置导出成功！" if self.config_manager.export_config(path) else "配置导出失败！")
    def _import_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入配置", "", "JSON 文件 (*.json)")
        if path: QMessageBox.information(self, "导入配置", "配置导入成功，请重启应用以应用配置。" if self.config_manager.import_config(path) else "配置导入失败！")
    def _settings(self): SettingsDialog(self, self.config_manager).exec()
    def _about(self):
        dialog = QDialog(self); dialog.setWindowTitle("关于")
        layout = QVBoxLayout(dialog)
        label = QLabel(AppInfo.get_about_html() + "<br><br>Qt/PySide6 按 LGPLv3 使用。")
        label.setTextFormat(Qt.RichText); label.setTextInteractionFlags(Qt.TextBrowserInteraction); label.setOpenExternalLinks(True)
        layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok); buttons.button(QDialogButtonBox.Ok).setText("确定"); buttons.accepted.connect(dialog.accept); layout.addWidget(buttons)
        dialog.exec()
    def closeEvent(self, event): self.work_panel.cleanup(); event.accept()
