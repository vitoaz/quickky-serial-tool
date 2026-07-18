"""串口操作超时与会话隔离回归测试。"""

import io
import sys
import threading
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils.serial_manager import SerialManager


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
        manager._receive_loop = lambda *_args: None
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
        manager._receive_loop = lambda *_args: None
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

    def test_close_prevents_old_receive_thread_from_becoming_new_session_reader(self):
        class BlockedReadPort(self._SlowPort):
            port = "COM1"
            cts = False
            dsr = False

            def __init__(self, entered, release):
                super().__init__()
                self.entered, self.release = entered, release

            @property
            def in_waiting(self):
                self.entered.set()
                self.release.wait()
                return 0

        manager = SerialManager()
        entered, release = threading.Event(), threading.Event()
        old_port = BlockedReadPort(entered, release)
        stop_event = threading.Event()
        manager.serial_port = old_port
        manager.is_running = True
        manager._open_generation = 1
        manager._receive_stop_event = stop_event
        with patch.object(manager, "_check_port_health", return_value=(True, None)):
            receive_thread = threading.Thread(target=manager._receive_loop, args=(old_port, stop_event, 1), daemon=True)
            manager.receive_thread = receive_thread
            receive_thread.start()
            self.assertTrue(entered.wait(0.2))
            with redirect_stdout(io.StringIO()):
                self.assertFalse(manager.close())
                self.assertFalse(manager.open("COM2"))
            release.set()
            receive_thread.join(0.5)
            deadline = time.monotonic() + 0.5
            while manager._close_in_flight and time.monotonic() < deadline:
                time.sleep(0.01)
        self.assertFalse(manager._close_in_flight)
        self.assertFalse(manager.is_open())

    def test_late_read_after_close_is_not_delivered_to_callback(self):
        class LateReadPort(self._SlowPort):
            port = "COM1"
            cts = False
            dsr = False

            def __init__(self, entered, release):
                super().__init__()
                self.entered, self.release = entered, release

            @property
            def in_waiting(self):
                return 1

            def read(self, _size):
                self.entered.set()
                self.release.wait()
                return b"late"

        manager = SerialManager()
        entered, release = threading.Event(), threading.Event()
        port = LateReadPort(entered, release)
        stop_event = threading.Event()
        callback = Mock()
        manager.serial_port = port
        manager._open_generation = 1
        manager.set_receive_callback(callback)
        with patch.object(manager, "_check_port_health", return_value=(True, None)):
            thread = threading.Thread(target=manager._receive_loop, args=(port, stop_event, 1), daemon=True)
            manager.receive_thread = thread
            thread.start()
            self.assertTrue(entered.wait(0.2))
            stop_event.set()
            manager._open_generation = 2
            manager.serial_port = None
            release.set()
            thread.join(0.5)
        callback.assert_not_called()
