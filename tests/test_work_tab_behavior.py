"""Qt 工作 Tab 关键行为回归测试。"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from components.work_tab_qt import WorkTab


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
        tab._log_generation = 0
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
            tab._log_generation = 0
            tab._append_system = Mock()

            with patch("components.work_tab_qt.QFileDialog.getSaveFileName", return_value=(selected_file, "")) as dialog:
                self.assertTrue(WorkTab._choose_log_file(tab))

            self.assertTrue(dialog.call_args.args[2].startswith(directory))
            tab.config_manager.set_last_log_directory.assert_called_once_with(directory)
            tab.log_writer.open.assert_called_once_with(selected_file, 0)

    def test_manual_close_blocks_queued_auto_reconnect(self):
        tab = WorkTab.__new__(WorkTab)
        tab._manual_close = True
        tab.receive_settings = Mock(get_settings=Mock(return_value={"auto_reconnect": True}))
        tab.serial_manager = Mock(is_open=Mock(return_value=False))
        tab._connection_in_flight = False
        tab._open_connection = Mock()
        WorkTab._try_reconnect(tab)
        tab._open_connection.assert_not_called()

    def test_suspend_disables_log_checkbox_after_closing_log_session(self):
        tab = WorkTab.__new__(WorkTab)
        tab._stop_loop_send = Mock()
        tab.reconnect_timer = Mock()
        tab._reset_receive_session = Mock()
        tab._close_log_writer = Mock()
        tab.receive_settings = Mock()
        tab.receive_settings.save_log_check.isChecked.return_value = True
        tab.serial_manager = Mock(is_open=Mock(return_value=False))
        tab._connection_in_flight = False
        tab._set_connection_state = Mock()

        WorkTab.suspend(tab)

        self.assertTrue(tab._manual_close)
        tab.receive_settings.save_log_check.setChecked.assert_called_once_with(False)
        tab._set_connection_state.assert_called_once_with(False)
