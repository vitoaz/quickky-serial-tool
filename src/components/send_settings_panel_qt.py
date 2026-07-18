"""Qt 发送设置面板。"""

from PySide6.QtWidgets import QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QRadioButton, QSpinBox, QVBoxLayout


class SendSettingsPanel(QGroupBox):
    def __init__(self, config_manager, on_change_callback=None, on_mode_change_callback=None, parent=None):
        super().__init__("发送设置", parent); self.config_manager, self.on_change_callback, self.on_mode_change_callback, self.current_port, self.old_mode = config_manager, on_change_callback, on_mode_change_callback, None, "TEXT"
        self.text_radio, self.hex_radio = QRadioButton("TEXT"), QRadioButton("HEX"); self.text_radio.setChecked(True); self.line_ending_combo = QComboBox(); self.line_ending_combo.addItem("CR（\\r）", "CR"); self.line_ending_combo.addItem("LF（\\n）", "LF"); self.line_ending_combo.addItem("CRLF（\\r\\n）", "CRLF"); self.line_ending_combo.setCurrentIndex(2); self.loop_send_check = QCheckBox("循环发送"); self.period_spin = QSpinBox(); self.period_spin.setRange(1, 3600000); self.period_spin.setValue(1000); self.period_spin.setSuffix(" ms"); self.period_spin.setEnabled(False)
        layout = QVBoxLayout(self); modes = QHBoxLayout(); modes.addWidget(self.text_radio); modes.addWidget(self.hex_radio); line_ending = QHBoxLayout(); line_ending.addWidget(QLabel("换行符:")); line_ending.addWidget(self.line_ending_combo); period = QHBoxLayout(); period.addWidget(QLabel("周期:")); period.addWidget(self.period_spin); layout.addLayout(modes); layout.addLayout(line_ending); layout.addWidget(self.loop_send_check); layout.addLayout(period)
        self.text_radio.toggled.connect(self._mode_changed); self.hex_radio.toggled.connect(self._mode_changed); self.line_ending_combo.currentIndexChanged.connect(self._save); self.loop_send_check.toggled.connect(self._loop_changed); self.period_spin.valueChanged.connect(self._save)
    def _mode_changed(self):
        new_mode = "HEX" if self.hex_radio.isChecked() else "TEXT"
        if new_mode == self.old_mode: return
        old_mode, self.old_mode = self.old_mode, new_mode
        self.line_ending_combo.setEnabled(new_mode == "TEXT")
        self._save()
        if self.on_mode_change_callback: self.on_mode_change_callback(old_mode, new_mode)
    def _loop_changed(self, checked):
        self.period_spin.setEnabled(checked)
        self._save()
    def _save(self):
        if self.current_port:
            settings = self.get_settings(); self.config_manager.update_send_settings(self.current_port, settings)
            if self.on_change_callback: self.on_change_callback(settings)
    def get_settings(self): return {"mode": "HEX" if self.hex_radio.isChecked() else "TEXT", "line_ending": self.line_ending_combo.currentData(), "loop_send": self.loop_send_check.isChecked(), "loop_period_ms": self.period_spin.value()}
    def load_config(self, port, config):
        self.current_port = port
        widgets = (self.text_radio, self.hex_radio, self.line_ending_combo, self.loop_send_check, self.period_spin)
        for widget in widgets: widget.blockSignals(True)
        try:
            self.hex_radio.setChecked(config.get("mode") == "HEX"); self.text_radio.setChecked(config.get("mode", "TEXT") != "HEX"); line_ending_index = self.line_ending_combo.findData(config.get("line_ending", "CRLF")); self.line_ending_combo.setCurrentIndex(line_ending_index if line_ending_index >= 0 else 2)
            self.loop_send_check.setChecked(config.get("loop_send", False)); self.period_spin.setValue(config.get("loop_period_ms", 1000))
        finally:
            for widget in widgets: widget.blockSignals(False)
        self.old_mode = "HEX" if self.hex_radio.isChecked() else "TEXT"
        self.line_ending_combo.setEnabled(not self.hex_radio.isChecked())
        self.period_spin.setEnabled(self.loop_send_check.isChecked())
