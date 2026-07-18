"""Qt 串口参数面板。"""

from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox

from utils.serial_manager_qt import SerialManagerQt


class PortComboBox(QComboBox):
    def __init__(self, refresh_callback, parent=None):
        super().__init__(parent)
        self._refresh_callback = refresh_callback

    def showPopup(self):
        self._refresh_callback()
        super().showPopup()


class SerialSettingsPanel(QGroupBox):
    BAUDRATES = ["300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "38400", "57600", "115200", "230400", "460800", "921600", "1000000", "1500000", "2000000"]

    def __init__(self, config_manager, on_change_callback=None, panel_type="main", parent=None):
        super().__init__("串口设置", parent)
        self.config_manager, self.on_change_callback, self.panel_type = config_manager, on_change_callback, panel_type
        self.port_combo = PortComboBox(self.refresh_ports); self.port_combo.setEditable(False)
        self.baudrate_combo = self._combo(self.BAUDRATES, "115200", editable=True)
        self.baudrate_combo.lineEdit().setValidator(QIntValidator(1, 4_000_000, self.baudrate_combo))
        self.parity_combo = self._combo(["None", "Even", "Odd", "Mark", "Space"], "None")
        self.bytesize_combo = self._combo(["5", "6", "7", "8"], "8")
        self.stopbits_combo = self._combo(["1", "1.5", "2"], "1")
        self.flow_control_combo = self._combo(["None", "Hardware", "Software"], "None")
        form = QFormLayout(self)
        form.addRow("串口号:", self.port_combo); form.addRow("波特率:", self.baudrate_combo)
        form.addRow("校验位:", self.parity_combo); form.addRow("数据位:", self.bytesize_combo)
        form.addRow("停止位:", self.stopbits_combo); form.addRow("流控:", self.flow_control_combo)
        self.port_combo.currentTextChanged.connect(self._on_port_changed)
        for widget in (self.parity_combo, self.bytesize_combo, self.stopbits_combo, self.flow_control_combo):
            widget.currentTextChanged.connect(self._save)
        self.baudrate_combo.currentTextChanged.connect(self._save_baudrate_if_valid)
        self.baudrate_combo.lineEdit().editingFinished.connect(self._normalize_baudrate_and_save)
        self.refresh_ports()

    @staticmethod
    def _combo(values, current, editable=False):
        combo = QComboBox(); combo.addItems(values); combo.setCurrentText(current); combo.setEditable(editable); return combo

    def refresh_ports(self):
        current = self.port_combo.currentText()
        def port_sort_key(value):
            name = value.upper()
            if name.startswith("COM"):
                try:
                    return (0, int(name[3:].strip()))
                except ValueError:
                    pass
            return (1, value)
        ports = sorted(SerialManagerQt.get_available_ports(), key=port_sort_key)
        self.port_combo.blockSignals(True); self.port_combo.clear(); self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
        else:
            self.port_combo.setCurrentIndex(-1)
        self.port_combo.blockSignals(False)

    def _on_port_changed(self, port):
        if port:
            config = self.config_manager.get_port_config(port)
            self.load_config(config["serial_settings"])
            self.config_manager.set_last_port(port, self.panel_type)
            if self.on_change_callback: self.on_change_callback("port", port)

    def _save(self):
        port = self.get_current_port()
        if port:
            settings = self.get_settings(); self.config_manager.update_serial_settings(port, settings)
            if self.on_change_callback: self.on_change_callback("settings", settings)

    def _normalize_baudrate_and_save(self):
        if self._baudrate_value() is None:
            self.baudrate_combo.setCurrentText("115200")
        self._save()

    def _save_baudrate_if_valid(self):
        if self._baudrate_value() is not None:
            self._save()

    def _baudrate_value(self):
        try:
            baudrate = int(self.baudrate_combo.currentText())
        except ValueError:
            return None
        return baudrate if 1 <= baudrate <= 4_000_000 else None

    def get_settings(self):
        baudrate = self._baudrate_value()
        if baudrate is None:
            baudrate = 115200
            self.baudrate_combo.setCurrentText(str(baudrate))
        try: stopbits = float(self.stopbits_combo.currentText())
        except ValueError: stopbits = 1
        return {"baudrate": baudrate, "parity": self.parity_combo.currentText(), "bytesize": int(self.bytesize_combo.currentText()), "stopbits": stopbits, "flow_control": self.flow_control_combo.currentText()}

    def load_config(self, config):
        combos = (self.baudrate_combo, self.parity_combo, self.bytesize_combo, self.stopbits_combo, self.flow_control_combo)
        for combo in combos: combo.blockSignals(True)
        try:
            for combo, value in ((self.baudrate_combo, config.get("baudrate", 115200)), (self.parity_combo, config.get("parity", "None")), (self.bytesize_combo, config.get("bytesize", 8)), (self.stopbits_combo, config.get("stopbits", 1)), (self.flow_control_combo, config.get("flow_control", "None"))): combo.setCurrentText(str(int(value) if combo is self.stopbits_combo and isinstance(value, float) and value.is_integer() else value))
        finally:
            for combo in combos: combo.blockSignals(False)

    def get_current_port(self): return self.port_combo.currentText()
    def set_current_port(self, port):
        if self.port_combo.findText(port) < 0: self.port_combo.addItem(port)
        self.port_combo.blockSignals(True); self.port_combo.setCurrentText(port); self.port_combo.blockSignals(False)
        self._on_port_changed(port)
    def set_enabled(self, enabled): self.setEnabled(enabled)
