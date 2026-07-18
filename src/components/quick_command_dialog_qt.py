"""Qt 快捷指令编辑对话框。"""

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
                               QPlainTextEdit, QComboBox, QMessageBox)

from utils.hex_utils import HexUtils
from utils.send_data_utils import SendDataUtils


class QuickCommandDialog(QDialog):
    def __init__(self, parent=None, command=None):
        super().__init__(parent); self.setWindowTitle("编辑指令" if command else "添加指令")
        self.name_text, self.data_text, self.mode_combo = QLineEdit(), QPlainTextEdit(), QComboBox(); self.mode_combo.addItems(["TEXT", "HEX"])
        layout = QFormLayout(self); layout.addRow("指令名称:", self.name_text); layout.addRow("指令内容:", self.data_text); layout.addRow("发送模式:", self.mode_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); buttons.button(QDialogButtonBox.Ok).setText("确定"); buttons.button(QDialogButtonBox.Cancel).setText("取消"); buttons.accepted.connect(self._accept); buttons.rejected.connect(self.reject); layout.addRow(buttons)
        if command: self.name_text.setText(command.get("name", "")); self.data_text.setPlainText(command.get("data", command.get("command", ""))); self.mode_combo.setCurrentText(command.get("mode", "TEXT"))
    def _accept(self):
        data = self.data_text.toPlainText()
        if not self.name_text.text().strip() or not data.strip(): QMessageBox.warning(self, "输入错误", "指令名称和内容不能为空"); return
        if self.mode_combo.currentText() == "HEX" and not HexUtils.validate_hex_format(data): QMessageBox.warning(self, "输入错误", HexUtils.get_format_error_message()); return
        self.accept()
    def get_command(self):
        data = self.data_text.toPlainText()
        mode = self.mode_combo.currentText()
        if mode == "TEXT":
            data = SendDataUtils.normalize_text_newlines(data)
        return {"name": self.name_text.text().strip(), "data": data, "command": data, "mode": mode}
