"""接收与发送数据转换回归测试。"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils.receive_data_utils import ReceiveLogFormatter, ReceiveTextDecoder, ReceiveTextSegmenter
from utils.send_data_utils import SendDataUtils


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
