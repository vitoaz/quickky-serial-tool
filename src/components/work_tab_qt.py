"""Qt 串口工作标签页，针对高频接收采用有界缓冲和批量 UI 刷新。"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor, QTextFormat
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QSplitter, QTabWidget, QVBoxLayout, QWidget)

from components.receive_settings_panel_qt import ReceiveSettingsPanel
from components.send_settings_panel_qt import SendSettingsPanel
from components.serial_settings_panel_qt import SerialSettingsPanel
from utils.log_writer import LogWriter
from utils.receive_data_utils import ReceiveDataUtils, ReceiveLogFormatter, ReceiveTextDecoder, ReceiveTextSegmenter
from utils.serial_manager_qt import SerialManagerQt
from utils.send_data_utils import SendDataUtils


class WorkTab(QWidget):
    """一个独立串口会话；UI 线程仅周期性消费后台收取的有界数据。"""

    FLUSH_INTERVAL_MS = 25
    MAX_FLUSH_BYTES = 256 * 1024
    MAX_DISPLAY_CHARS = 4 * 1024 * 1024
    LOG_LEVEL_PROPERTY = int(QTextFormat.UserProperty) + 1

    def __init__(self, config_manager, tab_name="New Tab", is_first_tab=False,
                 on_data_sent=None, panel_type="main", parent=None):
        super().__init__(parent)
        self.config_manager, self.tab_name, self.on_data_sent, self.panel_type = config_manager, tab_name, on_data_sent, panel_type
        self.is_first_tab = is_first_tab
        self.serial_manager = SerialManagerQt(); self.serial_manager.disconnected.connect(self._on_disconnected)
        self.serial_manager.operation_completed.connect(self._on_operation_completed)
        self.log_writer = LogWriter(); self.log_file_path = None; self._log_enabled = False; self.rx_count = self.tx_count = 0
        self._theme_manager = None
        self.receive_decoder = ReceiveTextDecoder(); self.receive_text_segmenter = ReceiveTextSegmenter(); self.receive_log_formatter = ReceiveLogFormatter(); self._send_in_flight = False; self._connection_in_flight = False; self._pending_send = None; self._loop_send_cancelled = False; self._scroll_pending = False
        self.flush_timer = QTimer(self); self.flush_timer.timeout.connect(self._flush_receive)
        self.loop_timer = QTimer(self); self.loop_timer.timeout.connect(lambda: self._send_data(from_timer=True))
        self.reconnect_timer = QTimer(self); self.reconnect_timer.setSingleShot(True); self.reconnect_timer.timeout.connect(self._try_reconnect)
        self._build_ui()
        self.flush_timer.start(self.FLUSH_INTERVAL_MS)

    def _build_ui(self):
        self.serial_settings = SerialSettingsPanel(self.config_manager, self._serial_changed, self.panel_type, self)
        self.receive_settings = ReceiveSettingsPanel(self.config_manager, self._receive_changed, self._choose_log_file, self)
        self.send_settings = SendSettingsPanel(self.config_manager, self._send_settings_changed, self._on_send_mode_changed, self)
        self.connect_btn = QPushButton("打开串口"); self.connect_btn.clicked.connect(self._toggle_connection)
        left = QWidget(); left.setFixedWidth(180); left_layout = QVBoxLayout(left); left_layout.setContentsMargins(4, 4, 4, 4)
        for widget in (self.serial_settings, self.connect_btn, self.receive_settings, self.send_settings): left_layout.addWidget(widget)
        left_layout.addStretch()
        self.receive_text = QPlainTextEdit(); self.receive_text.setReadOnly(True); self.receive_text.setLineWrapMode(QPlainTextEdit.NoWrap); self.receive_text.document().setMaximumBlockCount(self.config_manager.get_global_settings().get("receive_buffer_size", 10000)); self.receive_text.setFont(QFont("Consolas", self.config_manager.get_font_size()))
        self.send_text = QPlainTextEdit(); self.send_text.setFont(QFont("Consolas", self.config_manager.get_font_size())); self.send_text.textChanged.connect(self._save_send_draft)
        self.send_btn = QPushButton("发送"); self.send_btn.setEnabled(False); self.send_btn.clicked.connect(lambda: self._send_data())
        self.clear_receive_btn, self.clear_send_btn, self.reset_count_btn = self._link_button("清除接收"), self._link_button("清除发送"), self._link_button("复位计数")
        self.clear_receive_btn.clicked.connect(self._clear_receive); self.clear_send_btn.clicked.connect(self.send_text.clear); self.reset_count_btn.clicked.connect(self._reset_counts)
        self.count_label = QLabel("RX: 0  TX: 0")
        right = QWidget(); right_layout = QVBoxLayout(right); right_layout.setContentsMargins(4, 4, 4, 4)
        receive_actions = QHBoxLayout(); receive_actions.addWidget(self.clear_receive_btn); receive_actions.addStretch()
        send_actions = QHBoxLayout(); send_actions.addWidget(self.clear_send_btn); send_actions.addStretch(); send_actions.addWidget(self.send_btn)
        status_actions = QHBoxLayout(); status_actions.addWidget(self.count_label); status_actions.addStretch(); status_actions.addWidget(self.reset_count_btn)
        right_layout.addWidget(QLabel("接收数据")); right_layout.addWidget(self.receive_text, 3); right_layout.addLayout(receive_actions); right_layout.addWidget(QLabel("发送数据")); right_layout.addWidget(self.send_text, 1); right_layout.addLayout(send_actions); right_layout.addLayout(status_actions)
        splitter = QSplitter(Qt.Horizontal); splitter.setChildrenCollapsible(False); splitter.addWidget(left); splitter.addWidget(right); splitter.setCollapsible(0, False); splitter.setCollapsible(1, False); splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.addWidget(splitter)
        # 与 wx 版一致：首个 Tab 恢复上次串口，其余通过“+”创建的 Tab 保持未选择。
        if self.is_first_tab:
            port = self.config_manager.get_last_port(self.panel_type)
            if port:
                self.serial_settings.set_current_port(port)
            elif self.serial_settings.port_combo.count() > 0:
                self.serial_settings.set_current_port(self.serial_settings.port_combo.itemText(0))

    @staticmethod
    def _link_button(text):
        button = QPushButton(text); button.setFlat(True); button.setProperty("linkButton", True); button.setCursor(Qt.PointingHandCursor); font = button.font(); font.setUnderline(True); button.setFont(font); return button

    def _serial_changed(self, kind, value):
        if kind == "port":
            self._reset_receive_session()
            self._close_log_writer()
            config = self.config_manager.get_port_config(value)
            self.receive_settings.load_config(value, config["receive_settings"])
            self.send_settings.load_config(value, config["send_settings"])
            self.send_text.blockSignals(True); self.send_text.setPlainText(config.get("send_text", "")); self.send_text.blockSignals(False)
            self._update_tab_title(value)

    def _receive_changed(self, settings):
        if not settings["save_log"] and self._log_enabled:
            self._close_log_writer()
        if not settings["auto_reconnect"]:
            self.reconnect_timer.stop()

    def _close_log_writer(self):
        """关闭当前日志文件，避免串口会话之间复用旧路径。"""
        self._log_enabled = False
        self.log_file_path = None
        self.log_writer.close()
    def _send_settings_changed(self, settings):
        if not settings["loop_send"]:
            self._loop_send_cancelled = True
            if self.loop_timer.isActive(): self.loop_timer.stop(); self.send_btn.setText("发送")
        elif settings["loop_send"] and self.loop_timer.isActive():
            self.loop_timer.start(settings["loop_period_ms"])
    def _on_send_mode_changed(self, old_mode, new_mode):
        text = self.send_text.toPlainText()
        if not text: return
        line_ending = self.send_settings.get_settings()["line_ending"]
        encoding = self.receive_settings.get_settings()["encoding"].replace("-", "").lower()
        try:
            if old_mode == "TEXT" and new_mode == "HEX":
                converted = SendDataUtils.text_to_hex(text, encoding, line_ending)
            elif old_mode == "HEX" and new_mode == "TEXT":
                converted = SendDataUtils.hex_to_text(text, encoding, line_ending)
            else: return
        except ValueError:
            return
        self.send_text.setPlainText(converted)

    def _toggle_connection(self):
        if self._connection_in_flight: return
        if self.serial_manager.is_open(): self._close_connection(); return
        port = self.serial_settings.get_current_port()
        if not port: self._append_system("[错误] 请先选择串口\n", "error"); return
        self._open_connection(port)

    def _open_connection(self, port):
        self._reset_receive_session()
        self._connection_in_flight = True
        self.connect_btn.setEnabled(False); self.serial_settings.set_enabled(False); self.serial_manager.open_async(port=port, **self.serial_settings.get_settings())

    def _close_connection(self):
        self._stop_loop_send(); self.reconnect_timer.stop(); self._reset_receive_session(); self.connect_btn.setEnabled(False); self.serial_manager.close_async()

    def _reset_receive_session(self):
        """清除会话残留接收状态，不清空用户可见的历史内容。"""
        self.serial_manager.clear_pending()
        self.receive_decoder.reset()
        self.receive_text_segmenter.reset()
        self.receive_log_formatter.reset()

    def _stop_loop_send(self):
        self._loop_send_cancelled = True
        self.loop_timer.stop()
        self.send_btn.setText("发送")

    def _set_connection_state(self, opened):
        self.connect_btn.setText("关闭串口" if opened else "打开串口"); self.send_btn.setEnabled(opened); self.serial_settings.set_enabled(not opened)

    def _update_tab_title(self, port):
        parent = self.parentWidget()
        while parent:
            if isinstance(parent, QTabWidget):
                index = parent.indexOf(self)
                if index >= 0: parent.setTabText(index, port)
                return
            parent = parent.parentWidget()

    def _on_disconnected(self):
        self._connection_in_flight = False; self._stop_loop_send(); self._reset_receive_session(); self._set_connection_state(False); self._append_system("[警告] 串口异常断开\n", "warning")
        if self.receive_settings.get_settings()["auto_reconnect"]: self._schedule_reconnect()

    def _schedule_reconnect(self):
        interval = self.config_manager.get_global_settings().get("reconnect_interval", 5)
        self.reconnect_timer.start(int(interval * 1000))

    def _try_reconnect(self):
        if not self.receive_settings.get_settings()["auto_reconnect"] or self.serial_manager.is_open() or self._connection_in_flight: return
        port = self.serial_settings.get_current_port()
        if port:
            self._open_connection(port)
        else:
            self._append_system("[警告] 自动重连失败，稍后重试\n", "warning"); self._schedule_reconnect()

    def _flush_receive(self):
        data, dropped = self.serial_manager.drain(self.MAX_FLUSH_BYTES)
        if dropped: self.rx_count += dropped; self._update_counts()
        if dropped: self._append_text(f"[警告] 接收缓冲已满，丢弃 {dropped} 字节\n", force=True, level="warning")
        log_dropped = self.log_writer.take_dropped_bytes()
        if log_dropped: self._append_text(f"[警告] 日志写入缓冲已满，丢弃 {log_dropped} 字节\n", force=True, level="warning", write_log=False)
        log_errors = self.log_writer.take_errors()
        if log_errors:
            self._disable_logging("；".join(dict.fromkeys(log_errors)))
        if not data: return
        max_blocks = self.config_manager.get_global_settings().get("receive_buffer_size", 10000)
        if self.receive_text.document().maximumBlockCount() != max_blocks:
            self.receive_text.document().setMaximumBlockCount(max_blocks)
        self.rx_count += len(data); self._update_counts()
        settings = self.receive_settings.get_settings()
        if settings["mode"] == "TEXT":
            # wx 版按保留换行的文本段逐段追加；日志模式下每个新行会获得独立时间戳。
            text = self.receive_decoder.decode(data, settings["encoding"])
            for segment in self.receive_text_segmenter.iter_segments(text):
                self._append_text(segment)
        else:
            self.receive_decoder.reset()
            self.receive_text_segmenter.reset()
            self._append_text(ReceiveDataUtils.format_hex(data))

    def _append_system(self, text, level="info"): self._append_text(text, force=True, level=level)

    def _disable_logging(self, error):
        """后台日志失败后同步界面状态，避免继续显示保存已启用。"""
        self._close_log_writer()
        checkbox = self.receive_settings.save_log_check
        if checkbox.isChecked(): checkbox.setChecked(False)
        self._append_text(f"[错误] {error}\n", force=True, level="error", write_log=False)

    def _append_text(self, text, force=False, level="normal", write_log=True):
        if not text: return
        settings = self.receive_settings.get_settings()
        text = self.receive_log_formatter.format(text, settings["log_mode"])
        if force and self.receive_text.document().characterCount() > 1 and not self.receive_text.toPlainText().endswith("\n") and not text.startswith("\n"):
            # wx 版会在系统消息前补换行，避免与未结束的接收数据粘连。
            text = "\n" + text
        if write_log and self._log_enabled: self.log_writer.write(text)
        cursor = self.receive_text.textCursor(); cursor.movePosition(QTextCursor.End); cursor.insertText(text, self._receive_text_format(level))
        excess = self.receive_text.document().characterCount() - self.MAX_DISPLAY_CHARS
        if excess > 0:
            trim = self.receive_text.textCursor(); trim.movePosition(QTextCursor.Start); trim.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, excess); trim.removeSelectedText()
        if settings["auto_scroll"] and not self._scroll_pending:
            self._scroll_pending = True; QTimer.singleShot(0, self._scroll_receive_to_bottom)

    def _scroll_receive_to_bottom(self):
        self._scroll_pending = False
        if self.receive_settings.get_settings()["auto_scroll"]:
            scrollbar = self.receive_text.verticalScrollBar(); scrollbar.setValue(scrollbar.maximum())

    def _receive_text_format(self, level):
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(self._receive_color(level)))
        text_format.setProperty(self.LOG_LEVEL_PROPERTY, level)
        return text_format

    def _receive_color(self, level):
        defaults = {"normal": "#000000", "info": "#0066CC", "error": "#D32F2F", "success": "#388E3C", "warning": "#D32F2F"}
        colors = self._theme_manager.get_theme_colors() if self._theme_manager else {}
        return colors.get("text_fg" if level == "normal" else f"log_{level}_color", defaults[level])

    def _refresh_receive_colors(self):
        document = self.receive_text.document()
        block = document.begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                level = fragment.charFormat().property(self.LOG_LEVEL_PROPERTY)
                if level:
                    cursor = QTextCursor(document)
                    cursor.setPosition(fragment.position())
                    cursor.setPosition(fragment.position() + fragment.length(), QTextCursor.KeepAnchor)
                    text_format = fragment.charFormat()
                    text_format.setForeground(QColor(self._receive_color(level)))
                    cursor.setCharFormat(text_format)
                iterator += 1
            block = block.next()

    def _send_data(self, override_mode=None, add_to_history=True, from_timer=False):
        if from_timer and self._loop_send_cancelled: return
        if self.loop_timer.isActive() and not from_timer and override_mode is None:
            self._loop_send_cancelled = True; self.loop_timer.stop(); self.send_btn.setText("发送"); return
        if not from_timer and override_mode is None: self._loop_send_cancelled = False
        if self._send_in_flight: return
        data = self.send_text.toPlainText(); settings = self.send_settings.get_settings(); mode = override_mode or settings["mode"]
        if not data: return
        if not self.serial_manager.is_open(): self._stop_loop_send(); self._append_system("[错误] 串口未打开，无法发送\n", "error"); return
        encoding = self.receive_settings.get_settings()["encoding"]
        try:
            if mode == "HEX":
                byte_count = len(SendDataUtils.parse_hex(data))
            else:
                send_data, encoding, encoded = SendDataUtils.encode_text(data, encoding, settings["line_ending"])
                byte_count = len(encoded)
        except (ValueError, UnicodeEncodeError): self._append_system("[错误] 发送内容无效\n", "error"); return
        self._send_in_flight = True; self._pending_send = (data, mode, byte_count, add_to_history, settings, override_mode)
        self.serial_manager.send_async(send_data if mode == "TEXT" else data, mode, encoding)

    def send_data(self, data, mode, add_to_history=True): self.send_text.setPlainText(data); self._send_data(mode, add_to_history=add_to_history)
    def _save_send_draft(self):
        port = self.serial_settings.get_current_port()
        if port: self.config_manager.set_send_text(port, self.send_text.toPlainText())
    def _on_operation_completed(self, operation, success):
        if operation == "open":
            self._connection_in_flight = False
            self.connect_btn.setEnabled(True)
            if success: self._set_connection_state(True); self._append_system(f"[信息] 已打开串口: {self.serial_settings.get_current_port()}\n", "success")
            else:
                self._set_connection_state(False); self._append_system("[错误] 无法打开串口\n", "error")
                if self.receive_settings.get_settings()["auto_reconnect"]: self._schedule_reconnect()
        elif operation == "close":
            self._connection_in_flight = False
            self._reset_receive_session()
            self.connect_btn.setEnabled(True)
            self._set_connection_state(False)
            if success:
                self._append_system("[信息] 串口已关闭\n", "info")
            else:
                self._append_system("[错误] 关闭串口失败或超时\n", "error")
        elif operation == "send":
            self._send_in_flight = False
            if not self._pending_send: return
            data, mode, byte_count, add_to_history, settings, override_mode = self._pending_send; self._pending_send = None
            if success:
                self.tx_count += byte_count; self._update_counts()
                if add_to_history: self.config_manager.add_send_history(data, mode)
                if self.on_data_sent: self.on_data_sent()
                if not override_mode and settings["loop_send"] and not self._loop_send_cancelled and not self.loop_timer.isActive(): self.loop_timer.start(settings["loop_period_ms"]); self.send_btn.setText("取消发送")
            else: self._stop_loop_send(); self._append_system("[错误] 发送失败\n", "error")
    def _choose_log_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "保存日志文件", f"{self.serial_settings.get_current_port()}-{datetime.now():%Y%m%d%H%M%S}.log", "日志文件 (*.log);;文本文件 (*.txt);;所有文件 (*.*)")
        if not filename: return False
        try:
            # 与 wx 版一致：选择后立即验证文件可创建，失败时不启用保存日志。
            with Path(filename).open("a", encoding="utf-8"):
                pass
        except OSError as error:
            self._append_system(f"[错误] 创建日志文件失败: {error}\n", "error")
            return False
        self.log_file_path = filename; self._log_enabled = self.log_writer.open(filename); self._append_system(f"[信息] 日志文件: {filename}\n", "info"); return self._log_enabled
    def _clear_receive(self): self.receive_text.clear(); self.receive_decoder.reset(); self.receive_text_segmenter.reset(); self.receive_log_formatter.reset()
    def _reset_counts(self): self.rx_count = self.tx_count = 0; self._update_counts()
    def _update_counts(self): self.count_label.setText(f"RX: {self.rx_count}  TX: {self.tx_count}")
    def apply_theme(self, theme_manager, font_size=9):
        self._theme_manager = theme_manager
        self.receive_text.setFont(QFont("Consolas", font_size)); self.send_text.setFont(QFont("Consolas", font_size)); self._refresh_receive_colors()
    def cleanup(self):
        self.flush_timer.stop(); self.loop_timer.stop(); self.reconnect_timer.stop(); self._reset_receive_session(); self.serial_manager.close_async(); self._log_enabled = False; self.log_writer.stop()
