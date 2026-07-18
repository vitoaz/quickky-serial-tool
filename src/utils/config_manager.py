"""配置管理工具类。"""

import json
import os
import tempfile
from copy import deepcopy
from datetime import datetime

from .file_utils import get_base_path


class ConfigManager:
    """读取、校验并持久化运行目录中的配置。"""

    SERIAL_PARITIES = {"None", "Even", "Odd", "Mark", "Space"}
    FLOW_CONTROLS = {"None", "Hardware", "Software"}
    MODES = {"TEXT", "HEX"}
    ENCODINGS = {"UTF-8", "ASCII"}
    LINE_ENDINGS = {"CR", "LF", "CRLF"}
    THEMES = {"light", "dark"}

    def __init__(self, config_file="config.json"):
        self.config_file = os.path.join(get_base_path(), config_file)
        self.config = self._load_config()
        self._last_saved_config = deepcopy(self.config)

    def _get_default_config(self):
        return {
            "last_port_main": "",
            "last_port_secondary": "",
            "last_log_directory": "",
            "port_configs": {},
            "quick_command_groups": [],
            "send_history": [],
            "command_panel_visible": True,
            "dual_panel_mode": False,
            "theme": "light",
            "global_settings": {
                "receive_buffer_size": 10000,
                "send_history_max": 200,
                "fontSize": 9,
                "reconnect_interval": 5,
            },
        }

    def _get_default_port_config(self):
        return {
            "serial_settings": {
                "baudrate": 115200,
                "parity": "None",
                "bytesize": 8,
                "stopbits": 1,
                "flow_control": "None",
            },
            "receive_settings": {
                "mode": "TEXT",
                "encoding": "UTF-8",
                "log_mode": False,
                "save_log": False,
                "auto_reconnect": False,
                "auto_scroll": True,
            },
            "send_settings": {
                "mode": "TEXT",
                "line_ending": "CRLF",
                "loop_send": False,
                "loop_period_ms": 1000,
            },
            "send_text": "",
        }

    @staticmethod
    def _valid_int(value, minimum, maximum):
        return type(value) is int and minimum <= value <= maximum

    @staticmethod
    def _valid_number(value, allowed):
        return type(value) in (int, float) and value in allowed

    @staticmethod
    def _valid_bool(value):
        return type(value) is bool

    def _normalize_port_config(self, raw):
        defaults = self._get_default_port_config()
        if not isinstance(raw, dict):
            return defaults

        serial_raw = raw.get("serial_settings", {})
        if not isinstance(serial_raw, dict):
            serial_raw = {}
        serial = defaults["serial_settings"]
        if self._valid_int(serial_raw.get("baudrate"), 1, 4_000_000):
            serial["baudrate"] = serial_raw["baudrate"]
        if serial_raw.get("parity") in self.SERIAL_PARITIES:
            serial["parity"] = serial_raw["parity"]
        if serial_raw.get("bytesize") in {5, 6, 7, 8} and type(serial_raw["bytesize"]) is int:
            serial["bytesize"] = serial_raw["bytesize"]
        if self._valid_number(serial_raw.get("stopbits"), {1, 1.5, 2}):
            serial["stopbits"] = serial_raw["stopbits"]
        if serial_raw.get("flow_control") in self.FLOW_CONTROLS:
            serial["flow_control"] = serial_raw["flow_control"]

        receive_raw = raw.get("receive_settings", {})
        if not isinstance(receive_raw, dict):
            receive_raw = {}
        receive = defaults["receive_settings"]
        if receive_raw.get("mode") in self.MODES:
            receive["mode"] = receive_raw["mode"]
        if receive_raw.get("encoding") in self.ENCODINGS:
            receive["encoding"] = receive_raw["encoding"]
        for key in ("log_mode", "auto_reconnect", "auto_scroll"):
            if self._valid_bool(receive_raw.get(key)):
                receive[key] = receive_raw[key]
        # 日志文件路径不持久化，重启和导入后必须重新选择文件。
        receive["save_log"] = False

        send_raw = raw.get("send_settings", {})
        if not isinstance(send_raw, dict):
            send_raw = {}
        send = defaults["send_settings"]
        if send_raw.get("mode") in self.MODES:
            send["mode"] = send_raw["mode"]
        if send_raw.get("line_ending") in self.LINE_ENDINGS:
            send["line_ending"] = send_raw["line_ending"]
        if self._valid_bool(send_raw.get("loop_send")):
            send["loop_send"] = send_raw["loop_send"]
        if self._valid_int(send_raw.get("loop_period_ms"), 1, 3_600_000):
            send["loop_period_ms"] = send_raw["loop_period_ms"]

        if isinstance(raw.get("send_text"), str):
            defaults["send_text"] = raw["send_text"]
        return defaults

    def _normalize_quick_command_groups(self, raw):
        if not isinstance(raw, list):
            return []
        groups = []
        for group in raw:
            if not isinstance(group, dict) or not isinstance(group.get("name"), str):
                continue
            commands_raw = group.get("commands", [])
            if not isinstance(commands_raw, list):
                commands_raw = []
            commands = []
            for command in commands_raw:
                if not isinstance(command, dict):
                    continue
                data = command.get("data", command.get("command"))
                if not isinstance(data, str):
                    continue
                mode = command.get("mode", "TEXT")
                commands.append({
                    "name": command.get("name", "") if isinstance(command.get("name", ""), str) else "",
                    "data": data,
                    "command": data,
                    "mode": mode if mode in self.MODES else "TEXT",
                })
            groups.append({"name": group["name"], "commands": commands})
        return groups

    def _normalize_send_history(self, raw):
        if not isinstance(raw, list):
            return []
        history = []
        for item in raw:
            if isinstance(item, str):
                history.append({"data": item, "mode": "TEXT", "time": ""})
                continue
            if not isinstance(item, dict) or not isinstance(item.get("data"), str):
                continue
            mode = item.get("mode", "TEXT")
            time_text = item.get("time", "")
            history.append({
                "data": item["data"],
                "mode": mode if mode in self.MODES else "TEXT",
                "time": time_text if isinstance(time_text, str) else "",
            })
        return history

    def _normalize_config(self, raw):
        """将外部 JSON 归一化为当前配置结构，未知字段不保留。"""
        if not isinstance(raw, dict):
            raise ValueError("配置根节点必须是 JSON 对象")
        config = self._get_default_config()
        for key in ("last_port_main", "last_port_secondary", "last_log_directory"):
            if isinstance(raw.get(key), str):
                config[key] = raw[key]
        for key in ("command_panel_visible", "dual_panel_mode"):
            if self._valid_bool(raw.get(key)):
                config[key] = raw[key]
        if raw.get("theme") in self.THEMES:
            config["theme"] = raw["theme"]

        settings_raw = raw.get("global_settings", {})
        if isinstance(settings_raw, dict):
            settings = config["global_settings"]
            if self._valid_int(settings_raw.get("receive_buffer_size"), 1000, 100000):
                settings["receive_buffer_size"] = settings_raw["receive_buffer_size"]
            if self._valid_int(settings_raw.get("send_history_max"), 50, 1000):
                settings["send_history_max"] = settings_raw["send_history_max"]
            if self._valid_int(settings_raw.get("fontSize"), 6, 20):
                settings["fontSize"] = settings_raw["fontSize"]
            if self._valid_int(settings_raw.get("reconnect_interval"), 1, 30):
                settings["reconnect_interval"] = settings_raw["reconnect_interval"]

        port_configs = raw.get("port_configs", {})
        if isinstance(port_configs, dict):
            config["port_configs"] = {
                port: self._normalize_port_config(value)
                for port, value in port_configs.items()
                if isinstance(port, str) and port
            }
        config["quick_command_groups"] = self._normalize_quick_command_groups(raw.get("quick_command_groups", []))
        history = self._normalize_send_history(raw.get("send_history", []))
        config["send_history"] = history[:config["global_settings"]["send_history_max"]]
        return config

    def _write_config(self, config):
        directory = os.path.dirname(os.path.abspath(self.config_file))
        file_descriptor, temporary_path = tempfile.mkstemp(
            prefix=".config-", suffix=".tmp", dir=directory, text=True,
        )
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as stream:
                json.dump(config, stream, indent=2, ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.config_file)
        except OSError:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
            raise

    def _load_config(self):
        if not os.path.exists(self.config_file):
            return self._get_default_config()
        try:
            with open(self.config_file, "r", encoding="utf-8") as stream:
                raw = json.load(stream)
            config = self._normalize_config(raw)
            if config != raw:
                self._write_config(config)
            return config
        except (OSError, ValueError, json.JSONDecodeError, RecursionError) as error:
            print(f"加载配置文件失败: {error}")
            # 损坏的运行配置可由用户修复；不要用默认值覆盖原文件。
            return self._get_default_config()

    def save_config(self):
        """仅在配置实际变化时执行原子写入；失败后保留旧快照以便下次重试。"""
        if self.config == self._last_saved_config:
            return True
        try:
            self._write_config(self.config)
            self._last_saved_config = deepcopy(self.config)
            return True
        except OSError as error:
            print(f"保存配置文件失败: {error}")
            return False

    def get_last_port(self, panel="main"):
        return self.config["last_port_secondary" if panel == "secondary" else "last_port_main"]

    def set_last_port(self, port, panel="main"):
        self.config["last_port_secondary" if panel == "secondary" else "last_port_main"] = port
        self.save_config()

    def get_last_log_directory(self):
        """获取上次选择日志文件时所在的目录。"""
        return self.config["last_log_directory"]

    def set_last_log_directory(self, directory):
        """保存日志文件选择目录，不保存具体日志文件路径。"""
        self.config["last_log_directory"] = directory if isinstance(directory, str) else ""
        self.save_config()

    def get_port_config(self, port):
        if port not in self.config["port_configs"]:
            self.config["port_configs"][port] = self._get_default_port_config()
            self.save_config()
        config = self.config["port_configs"][port]
        config["receive_settings"]["save_log"] = False
        return config

    def save_port_config(self, port, config):
        self.config["port_configs"][port] = self._normalize_port_config(config)
        self.save_config()

    def update_serial_settings(self, port, settings):
        port_config = self.get_port_config(port)
        port_config["serial_settings"].update(settings)
        self.save_port_config(port, port_config)

    def update_receive_settings(self, port, settings):
        port_config = self.get_port_config(port)
        port_config["receive_settings"].update(settings)
        self.save_port_config(port, port_config)

    def update_send_settings(self, port, settings):
        port_config = self.get_port_config(port)
        port_config["send_settings"].update(settings)
        self.save_port_config(port, port_config)

    def export_config(self, file_path):
        try:
            with open(file_path, "w", encoding="utf-8") as stream:
                json.dump(self.config, stream, indent=2, ensure_ascii=False)
            return True
        except OSError as error:
            print(f"导出配置失败: {error}")
            return False

    def import_config(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as stream:
                raw = json.load(stream)
            config = self._normalize_config(raw)
            self._write_config(config)
            self.config = config
            self._last_saved_config = deepcopy(config)
            return True
        except (OSError, ValueError, json.JSONDecodeError, RecursionError) as error:
            print(f"导入配置失败: {error}")
            return False

    def get_quick_command_groups(self):
        return self.config["quick_command_groups"]

    def set_quick_command_groups(self, groups):
        self.config["quick_command_groups"] = self._normalize_quick_command_groups(groups)
        self.save_config()

    def add_send_history(self, data, mode="TEXT"):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history = self.config["send_history"]
        if history and history[0]["data"] == data and history[0]["mode"] == mode:
            history[0]["time"] = current_time
        else:
            history.insert(0, {"data": data, "mode": mode, "time": current_time})
        max_history = self.get_global_settings()["send_history_max"]
        del history[max_history:]
        self.save_config()

    def get_send_history(self):
        return self.config["send_history"]

    def clear_send_history(self):
        self.config["send_history"] = []
        self.save_config()

    def get_command_panel_visible(self):
        return self.config["command_panel_visible"]

    def set_command_panel_visible(self, visible):
        self.config["command_panel_visible"] = bool(visible)
        self.save_config()

    def get_send_text(self, port):
        return self.get_port_config(port)["send_text"]

    def set_send_text(self, port, text):
        port_config = self.get_port_config(port)
        port_config["send_text"] = text if isinstance(text, str) else ""
        self.save_port_config(port, port_config)

    def get_dual_panel_mode(self):
        return self.config["dual_panel_mode"]

    def set_dual_panel_mode(self, enabled):
        self.config["dual_panel_mode"] = bool(enabled)
        self.save_config()

    def get_global_settings(self):
        return self.config["global_settings"]

    def set_global_settings(self, settings):
        raw = dict(self.config)
        raw["global_settings"] = settings
        self.config = self._normalize_config(raw)
        self.save_config()

    def get_theme(self):
        return self.config["theme"]

    def set_theme(self, theme_name):
        self.config["theme"] = theme_name if theme_name in self.THEMES else "light"
        self.save_config()

    def get_font_size(self):
        return self.get_global_settings()["fontSize"]

    def set_font_size(self, size):
        settings = dict(self.get_global_settings())
        settings["fontSize"] = size
        self.set_global_settings(settings)
