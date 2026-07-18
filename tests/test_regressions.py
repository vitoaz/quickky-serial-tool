"""串口收发与配置健壮性回归测试。"""

import io
import json
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from components.work_tab_qt import WorkTab
from utils.config_manager import ConfigManager
from utils.log_writer import LogWriter
from utils.receive_data_utils import ReceiveLogFormatter, ReceiveTextDecoder, ReceiveTextSegmenter
from utils.send_data_utils import SendDataUtils
from utils.serial_manager import SerialManager


class ReceiveAndSendDataTests(unittest.TestCase):
    def test_incremental_utf8_and_empty_line_filtering(self):
        decoder = ReceiveTextDecoder()
        encoded = "中".encode("utf-8")
        self.assertEqual(decoder.decode(encoded[:2], "UTF-8"), "")
        self.assertEqual(decoder.decode(encoded[2:], "UTF-8"), "中")
        self.assertEqual(list(ReceiveTextSegmenter().iter_segments("A\n\nB")), ["A\n", "B"])

    def test_log_mode_splits_continuous_data_by_timestamp_duration(self):
        formatter = ReceiveLogFormatter()
        started = datetime(2026, 1, 1, 12, 0, 0)
        self.assertEqual(formatter.format("A", True, started), "[12:00:00.000] A")
        self.assertEqual(formatter.format("B", True, started + timedelta(milliseconds=50)), "B")
        self.assertEqual(formatter.format("C", True, started + timedelta(milliseconds=101)), "\n[12:00:00.101] C")

    def test_hex_separators_and_invalid_text_conversion(self):
        self.assertEqual(SendDataUtils.parse_hex("0x01, 0x02:03-04\n"), b"\x01\x02\x03\x04")
        self.assertEqual(SendDataUtils.hex_to_text("FF 41"), "\ufffdA")

    def test_text_and_hex_conversion_follow_selected_line_ending(self):
        self.assertEqual(SendDataUtils.encode_text("A\nB", "UTF-8", "CR")[2], b"A\rB")
        self.assertEqual(SendDataUtils.encode_text("A\r\nB", "UTF-8", "LF")[2], b"A\nB")
        self.assertEqual(SendDataUtils.text_to_hex("A\nB", line_ending="CR"), "41 0D 42")
        self.assertEqual(SendDataUtils.hex_to_text("41 0D 42", line_ending="CR"), "A\r\nB")


class ConfigManagerTests(unittest.TestCase):
    def test_send_settings_persist_loop_and_period_with_line_ending(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ConfigManager(str(Path(directory) / "config.json"))
            manager.update_send_settings("COM1", {
                "mode": "TEXT",
                "line_ending": "LF",
                "loop_send": True,
                "loop_period_ms": 250,
            })
            self.assertEqual(manager.get_port_config("COM1")["send_settings"], {
                "mode": "TEXT",
                "line_ending": "LF",
                "loop_send": True,
                "loop_period_ms": 250,
            })

    def test_load_and_import_normalize_partial_or_invalid_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text(json.dumps({
                "last_port_main": "COM1",
                "port_configs": {"COM1": {"serial_settings": {"baudrate": "bad"}}},
                "global_settings": {"fontSize": "large"},
                "send_history": ["legacy", {"data": 1}],
            }), encoding="utf-8")
            manager = ConfigManager(str(config_path))
            self.assertEqual(manager.get_last_port(), "COM1")
            manager.set_last_log_directory(str(Path(directory)))
            self.assertEqual(manager.get_last_log_directory(), str(Path(directory)))
            self.assertEqual(manager.get_port_config("COM1")["serial_settings"]["baudrate"], 115200)
            self.assertEqual(manager.get_global_settings()["fontSize"], 9)
            self.assertEqual(manager.get_send_history(), [{"data": "legacy", "mode": "TEXT", "time": ""}])
            self.assertEqual(manager.get_port_config("COM1")["send_settings"]["line_ending"], "CRLF")
            self.assertEqual(json.loads(config_path.read_text(encoding="utf-8")), manager.config)

            imported_path = Path(directory) / "import.json"
            imported_path.write_text(json.dumps({"global_settings": {"send_history_max": 50}}), encoding="utf-8")
            self.assertTrue(manager.import_config(str(imported_path)))
            self.assertEqual(manager.get_global_settings()["send_history_max"], 50)
            self.assertEqual(manager.get_global_settings()["fontSize"], 9)

            imported_path.write_text(json.dumps({"theme": "unknown"}), encoding="utf-8")
            self.assertTrue(manager.import_config(str(imported_path)))
            self.assertEqual(manager.get_theme(), "light")

            invalid_path = Path(directory) / "invalid.json"
            invalid_path.write_text("[]", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertFalse(manager.import_config(str(invalid_path)))

            broken_path = Path(directory) / "broken.json"
            broken_path.write_text("[]", encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                ConfigManager(str(broken_path))
            self.assertEqual(broken_path.read_text(encoding="utf-8"), "[]")


class LogWriterTests(unittest.TestCase):
    def test_background_open_failure_is_reported(self):
        writer = LogWriter()
        try:
            with patch("utils.log_writer.Path.open", side_effect=OSError("denied")):
                writer.open("unwritable.log")
                deadline = time.monotonic() + 1
                errors = []
                while time.monotonic() < deadline and not errors:
                    errors = writer.take_errors()
                    time.sleep(0.01)
            self.assertEqual(len(errors), 1)
            self.assertIn("无法打开日志文件", errors[0])
        finally:
            writer.stop()

    def test_background_write_failure_is_reported(self):
        class BrokenStream:
            def write(self, _text):
                raise OSError("disk full")

            def flush(self):
                pass

            def close(self):
                pass

        writer = LogWriter()
        try:
            with patch("utils.log_writer.Path.open", return_value=BrokenStream()):
                writer.open("writable.log")
                writer.write("日志内容")
                deadline = time.monotonic() + 1
                errors = []
                while time.monotonic() < deadline and not errors:
                    errors = writer.take_errors()
                    time.sleep(0.01)
            self.assertEqual(len(errors), 1)
            self.assertIn("写入日志文件失败", errors[0])
        finally:
            writer.stop()

    def test_background_close_failure_is_reported(self):
        class BrokenCloseStream:
            def write(self, _text):
                pass

            def flush(self):
                raise OSError("device removed")

            def close(self):
                pass

        writer = LogWriter()
        try:
            with patch("utils.log_writer.Path.open", return_value=BrokenCloseStream()):
                writer.open("closing.log")
                writer.close()
                deadline = time.monotonic() + 1
                errors = []
                while time.monotonic() < deadline and not errors:
                    errors = writer.take_errors()
                    time.sleep(0.01)
            self.assertEqual(len(errors), 1)
            self.assertIn("关闭日志文件失败", errors[0])
        finally:
            writer.stop()


class SerialManagerTests(unittest.TestCase):
    class _SlowPort:
        def __init__(self, delay=0):
            self.delay = delay
            self.is_open = True
            self.written = b""

        def write(self, data):
            time.sleep(self.delay)
            self.written = data

        def close(self):
            self.is_open = False

    def test_open_times_out_and_closes_late_result(self):
        manager = SerialManager()
        manager._receive_loop = lambda: None
        created_ports = []

        def create_port(**_settings):
            time.sleep(1.05)
            port = self._SlowPort()
            created_ports.append(port)
            return port

        with patch("utils.serial_manager.serial.Serial", side_effect=create_port):
            started = time.monotonic()
            with redirect_stdout(io.StringIO()):
                self.assertFalse(manager.open("COM1"))
            self.assertGreaterEqual(time.monotonic() - started, 0.95)
            time.sleep(0.15)
        self.assertFalse(manager.is_open())
        self.assertFalse(created_ports[0].is_open)

    def test_open_timeout_rejects_parallel_retry(self):
        manager = SerialManager()
        manager._receive_loop = lambda: None
        open_calls = []

        def create_port(**_settings):
            open_calls.append(time.monotonic())
            time.sleep(1.2)
            return self._SlowPort()

        with patch("utils.serial_manager.serial.Serial", side_effect=create_port):
            with redirect_stdout(io.StringIO()):
                self.assertFalse(manager.open("COM1"))
                self.assertFalse(manager.open("COM1"))
            self.assertEqual(len(open_calls), 1)
            time.sleep(0.25)
        self.assertFalse(manager._open_in_flight)

    def test_send_times_out_without_allowing_concurrent_write(self):
        manager = SerialManager()
        manager.serial_port = self._SlowPort(delay=1.05)
        started = time.monotonic()
        with redirect_stdout(io.StringIO()):
            self.assertFalse(manager.send("01", "HEX"))
        self.assertGreaterEqual(time.monotonic() - started, 0.95)
        self.assertFalse(manager.send("02", "HEX"))
        time.sleep(0.15)
        self.assertEqual(manager.serial_port.written, b"\x01")

    def test_text_send_does_not_override_selected_line_ending(self):
        manager = SerialManager()
        manager.serial_port = self._SlowPort()
        self.assertTrue(manager.send("A\rB", "TEXT"))
        self.assertEqual(manager.serial_port.written, b"A\rB")

    def test_close_times_out_without_allowing_new_open(self):
        class SlowClosePort(self._SlowPort):
            def close(self):
                time.sleep(1.05)
                super().close()

        manager = SerialManager()
        manager.serial_port = SlowClosePort()
        started = time.monotonic()
        with redirect_stdout(io.StringIO()):
            self.assertFalse(manager.close())
            self.assertFalse(manager.open("COM1"))
        self.assertGreaterEqual(time.monotonic() - started, 0.95)
        time.sleep(0.15)
        self.assertFalse(manager._close_in_flight)


class WorkTabBehaviorTests(unittest.TestCase):
    def test_external_send_records_history_by_default(self):
        tab = WorkTab.__new__(WorkTab)
        tab.send_text = Mock()
        tab._send_data = Mock()
        WorkTab.send_data(tab, "快捷指令", "TEXT")
        tab.send_text.setPlainText.assert_called_once_with("快捷指令")
        tab._send_data.assert_called_once_with("TEXT", add_to_history=True)

    def test_rx_count_includes_dropped_display_bytes(self):
        tab = WorkTab.__new__(WorkTab)
        tab.serial_manager = Mock(drain=Mock(return_value=(b"", 7)))
        tab.log_writer = Mock(take_dropped_bytes=Mock(return_value=0), take_errors=Mock(return_value=[]))
        tab.rx_count = 0
        tab._update_counts = Mock()
        tab._append_text = Mock()
        WorkTab._flush_receive(tab)
        self.assertEqual(tab.rx_count, 7)
        tab._update_counts.assert_called_once()

    def test_close_failure_is_shown_to_user(self):
        tab = WorkTab.__new__(WorkTab)
        tab._connection_in_flight = True
        tab._reset_receive_session = Mock()
        tab.connect_btn = Mock()
        tab._set_connection_state = Mock()
        tab._append_system = Mock()

        WorkTab._on_operation_completed(tab, "close", False)

        self.assertFalse(tab._connection_in_flight)
        tab._reset_receive_session.assert_called_once()
        tab.connect_btn.setEnabled.assert_called_once_with(True)
        tab._set_connection_state.assert_called_once_with(False)
        tab._append_system.assert_called_once_with("[错误] 关闭串口失败或超时\n", "error")

    def test_log_file_dialog_reuses_last_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            selected_file = str(Path(directory) / "serial.log")
            tab = WorkTab.__new__(WorkTab)
            tab.serial_settings = Mock(get_current_port=Mock(return_value="COM1"))
            tab.config_manager = Mock(get_last_log_directory=Mock(return_value=directory))
            tab.log_writer = Mock(open=Mock(return_value=True))
            tab._append_system = Mock()

            with patch("components.work_tab_qt.QFileDialog.getSaveFileName", return_value=(selected_file, "")) as dialog:
                self.assertTrue(WorkTab._choose_log_file(tab))

            self.assertTrue(dialog.call_args.args[2].startswith(directory))
            tab.config_manager.set_last_log_directory.assert_called_once_with(directory)
            tab.log_writer.open.assert_called_once_with(selected_file)



if __name__ == "__main__":
    unittest.main()
