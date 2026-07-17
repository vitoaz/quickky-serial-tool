"""Qt 全局设置对话框。"""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QSpinBox


class SettingsDialog(QDialog):
    def __init__(self, parent, config_manager):
        super().__init__(parent); self.setWindowTitle("设置"); self.config_manager = config_manager; settings = config_manager.get_global_settings()
        self.buffer_size_spin = self._spin(1000, 100000, settings.get("receive_buffer_size", 10000)); self.history_max_spin = self._spin(50, 1000, settings.get("send_history_max", 200)); self.font_size_spin = self._spin(6, 20, settings.get("fontSize", 9)); self.reconnect_interval_spin = self._spin(1, 30, settings.get("reconnect_interval", 5))
        layout = QFormLayout(self); layout.addRow("数据接收缓冲区大小:", self.buffer_size_spin); layout.addRow("发送历史最大条数:", self.history_max_spin); layout.addRow("接收区域字体大小:", self.font_size_spin); layout.addRow("自动重连间隔（秒）:", self.reconnect_interval_spin)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Ok).setText("确定"); buttons.button(QDialogButtonBox.Cancel).setText("取消"); buttons.accepted.connect(self._save); buttons.rejected.connect(self.reject); layout.addRow(buttons)
    @staticmethod
    def _spin(minimum, maximum, value):
        spin = QSpinBox(); spin.setRange(minimum, maximum); spin.setValue(value); return spin
    def _save(self):
        self.config_manager.set_global_settings({"receive_buffer_size": self.buffer_size_spin.value(), "send_history_max": self.history_max_spin.value(), "fontSize": self.font_size_spin.value(), "reconnect_interval": self.reconnect_interval_spin.value()})
        if hasattr(self.parent(), "apply_theme"): self.parent().apply_theme()
        self.accept()
