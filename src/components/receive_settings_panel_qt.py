"""Qt 接收设置面板。"""

from PySide6.QtWidgets import QButtonGroup, QCheckBox, QGroupBox, QHBoxLayout, QRadioButton, QVBoxLayout


class ReceiveSettingsPanel(QGroupBox):
    def __init__(self, config_manager, on_change_callback=None, on_save_log_callback=None, parent=None):
        super().__init__("接收设置", parent); self.config_manager, self.on_change_callback, self.on_save_log_callback, self.current_port = config_manager, on_change_callback, on_save_log_callback, None
        self.text_radio, self.hex_radio = QRadioButton("TEXT"), QRadioButton("HEX"); self.text_radio.setChecked(True)
        self.encoding_utf8, self.encoding_ascii = QRadioButton("UTF-8"), QRadioButton("ASCII"); self.encoding_utf8.setChecked(True)
        self.mode_group, self.encoding_group = QButtonGroup(self), QButtonGroup(self)
        self.mode_group.addButton(self.text_radio); self.mode_group.addButton(self.hex_radio)
        self.encoding_group.addButton(self.encoding_utf8); self.encoding_group.addButton(self.encoding_ascii)
        self.log_mode_check, self.save_log_check = QCheckBox("日志模式（添加时间戳）"), QCheckBox("保存日志文件")
        self.auto_reconnect_check, self.auto_scroll_check = QCheckBox("串口自动重连"), QCheckBox("接收自动滚屏"); self.auto_scroll_check.setChecked(True)
        layout = QVBoxLayout(self); modes = QHBoxLayout(); modes.addWidget(self.text_radio); modes.addWidget(self.hex_radio); layout.addLayout(modes); encodings = QHBoxLayout(); encodings.addWidget(self.encoding_utf8); encodings.addWidget(self.encoding_ascii); layout.addLayout(encodings)
        for widget in (self.log_mode_check, self.save_log_check, self.auto_reconnect_check, self.auto_scroll_check): layout.addWidget(widget)
        self.text_radio.toggled.connect(self._mode_changed); self.hex_radio.toggled.connect(self._mode_changed); self.save_log_check.toggled.connect(self._save_log_changed)
        for widget in (self.encoding_utf8, self.encoding_ascii, self.log_mode_check, self.auto_reconnect_check, self.auto_scroll_check): widget.toggled.connect(self._save)

    def _mode_changed(self):
        is_text = self.text_radio.isChecked(); self.encoding_utf8.setEnabled(is_text); self.encoding_ascii.setEnabled(is_text); self._save()
    def _save_log_changed(self, checked):
        if checked and self.on_save_log_callback and not self.on_save_log_callback(): self.save_log_check.setChecked(False); return
        self._save()
    def _save(self):
        if self.current_port:
            settings = self.get_settings(); self.config_manager.update_receive_settings(self.current_port, settings)
            if self.on_change_callback: self.on_change_callback(settings)
    def get_settings(self): return {"mode": "HEX" if self.hex_radio.isChecked() else "TEXT", "encoding": "UTF-8" if self.encoding_utf8.isChecked() else "ASCII", "log_mode": self.log_mode_check.isChecked(), "save_log": self.save_log_check.isChecked(), "auto_reconnect": self.auto_reconnect_check.isChecked(), "auto_scroll": self.auto_scroll_check.isChecked()}
    def load_config(self, port, config):
        self.current_port = port
        for widget, value in ((self.hex_radio, config.get("mode") == "HEX"), (self.text_radio, config.get("mode", "TEXT") != "HEX"), (self.encoding_utf8, config.get("encoding", "UTF-8") == "UTF-8"), (self.encoding_ascii, config.get("encoding") == "ASCII"), (self.log_mode_check, config.get("log_mode", False)), (self.save_log_check, config.get("save_log", False)), (self.auto_reconnect_check, config.get("auto_reconnect", False)), (self.auto_scroll_check, config.get("auto_scroll", True))): widget.setChecked(value)
        self._mode_changed()
