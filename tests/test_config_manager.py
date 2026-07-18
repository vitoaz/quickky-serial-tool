"""配置加载、导入与持久化回归测试。"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from utils.config_manager import ConfigManager


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

    def test_history_is_capped_after_import_and_global_setting_change(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            history = [{"data": str(index), "mode": "TEXT", "time": ""} for index in range(60)]
            config_path.write_text(json.dumps({
                "global_settings": {"send_history_max": 50},
                "send_history": history,
            }), encoding="utf-8")
            manager = ConfigManager(str(config_path))
            self.assertEqual(len(manager.get_send_history()), 50)
            manager.set_global_settings({"send_history_max": 50})
            self.assertEqual(len(manager.get_send_history()), 50)
            manager.add_send_history(manager.get_send_history()[0]["data"], "TEXT")
            self.assertEqual(len(manager.get_send_history()), 50)

    def test_import_failure_keeps_current_memory_config(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ConfigManager(str(Path(directory) / "config.json"))
            manager.set_theme("dark")
            imported_path = Path(directory) / "import.json"
            imported_path.write_text(json.dumps({"theme": "light"}), encoding="utf-8")
            with patch.object(manager, "_write_config", side_effect=OSError("disk full")):
                self.assertFalse(manager.import_config(str(imported_path)))
            self.assertEqual(manager.get_theme(), "dark")

    def test_deep_json_is_handled_as_invalid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            config_path.write_text("[" * 2000 + "]" * 2000, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                manager = ConfigManager(str(config_path))
            self.assertEqual(manager.get_theme(), "light")

    def test_unchanged_config_skips_atomic_write_and_failed_write_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ConfigManager(str(Path(directory) / "config.json"))
            with patch.object(manager, "_write_config") as write_config:
                self.assertTrue(manager.save_config())
                manager.set_last_port("")
                self.assertEqual(write_config.call_count, 0)

                manager.set_last_port("COM1")
                self.assertEqual(write_config.call_count, 1)
                manager.set_last_port("COM1")
                self.assertEqual(write_config.call_count, 1)

            manager.set_theme("dark")
            with patch.object(manager, "_write_config", side_effect=OSError("disk full")):
                manager.set_theme("light")
            with patch.object(manager, "_write_config") as write_config:
                self.assertTrue(manager.save_config())
                write_config.assert_called_once_with(manager.config)
