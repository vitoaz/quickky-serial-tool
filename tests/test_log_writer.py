"""异步日志写入回归测试。"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils.log_writer import LogWriter


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

    def test_stop_flushes_queued_log_content(self):
        class Stream:
            def __init__(self):
                self.content = ""

            def write(self, text):
                self.content += text

            def flush(self):
                pass

            def close(self):
                pass

        stream = Stream()
        writer = LogWriter()
        with patch("utils.log_writer.Path.open", return_value=stream):
            writer.open("closing.log")
            writer.write("日志尾部")
            self.assertTrue(writer.stop())
        self.assertEqual(stream.content, "日志尾部")

    def test_log_errors_are_isolated_by_generation(self):
        writer = LogWriter()
        try:
            writer._record_error("旧会话错误", 1)
            writer._record_error("当前会话错误", 2)
            self.assertEqual(writer.take_errors(2), ["当前会话错误"])
            self.assertEqual(writer.take_errors(), ["旧会话错误"])
        finally:
            writer.stop()

    def test_log_writer_rejects_new_work_after_stop(self):
        writer = LogWriter()
        self.assertTrue(writer.stop())
        self.assertFalse(writer.open("stopped.log"))
        self.assertFalse(writer.write("日志内容"))
        self.assertFalse(writer.close())
