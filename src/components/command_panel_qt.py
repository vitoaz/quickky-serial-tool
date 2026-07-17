"""Qt 命令侧栏。"""

from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .quick_commands_panel_qt import QuickCommandsPanel
from .send_history_panel_qt import SendHistoryPanel


class CommandPanel(QWidget):
    def __init__(self, config_manager, main_window=None, parent=None):
        super().__init__(parent); self.quick_commands_panel = QuickCommandsPanel(config_manager, main_window, self); self.send_history_panel = SendHistoryPanel(config_manager, main_window, self); self.notebook = QTabWidget(); self.notebook.addTab(self.quick_commands_panel, "快捷指令"); self.notebook.addTab(self.send_history_panel, "历史发送"); layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(self.notebook); self.setFixedWidth(180)
    def refresh_history(self): self.send_history_panel.refresh()
