"""
配置管理工具类

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import json
import os
from pathlib import Path

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file='config.json'):
        """
        初始化配置管理器
        
        Args:
            config_file (str): 配置文件名
        """
        # 配置文件路径（与程序同级目录）
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), config_file)
        self.config = self._load_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "last_port": "",
            "port_configs": {},
            "quick_commands": [],
            "send_history": [],
            "command_panel_visible": True  # 命令面板显示状态
        }
    
    def _get_default_port_config(self):
        """获取默认串口配置"""
        return {
            "serial_settings": {
                "baudrate": 115200,
                "parity": "None",
                "bytesize": 8,
                "stopbits": 1,
                "flow_control": "None"
            },
            "receive_settings": {
                "mode": "TEXT",
                "encoding": "UTF-8",
                "log_mode": False,
                "save_log": False,
                "auto_reconnect": False
            },
            "send_settings": {
                "mode": "TEXT",
                "loop_send": False,
                "loop_period_ms": 1000
            },
            "send_text": ""  # 发送区域的文本内容
        }
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self._get_default_config()
        return self._get_default_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_last_port(self):
        """获取上次使用的串口"""
        return self.config.get('last_port', '')
    
    def set_last_port(self, port):
        """设置上次使用的串口"""
        self.config['last_port'] = port
        self.save_config()
    
    def get_port_config(self, port):
        """
        获取指定串口的配置
        
        Args:
            port (str): 串口名称
            
        Returns:
            dict: 串口配置
        """
        if port not in self.config['port_configs']:
            self.config['port_configs'][port] = self._get_default_port_config()
            self.save_config()
        return self.config['port_configs'][port]
    
    def save_port_config(self, port, config):
        """
        保存指定串口的配置
        
        Args:
            port (str): 串口名称
            config (dict): 配置数据
        """
        self.config['port_configs'][port] = config
        self.save_config()
    
    def update_serial_settings(self, port, settings):
        """更新串口设置"""
        port_config = self.get_port_config(port)
        port_config['serial_settings'].update(settings)
        self.save_port_config(port, port_config)
    
    def update_receive_settings(self, port, settings):
        """更新接收设置"""
        port_config = self.get_port_config(port)
        port_config['receive_settings'].update(settings)
        self.save_port_config(port, port_config)
    
    def update_send_settings(self, port, settings):
        """更新发送设置"""
        port_config = self.get_port_config(port)
        port_config['send_settings'].update(settings)
        self.save_port_config(port, port_config)
    
    def export_config(self, file_path):
        """
        导出配置到文件
        
        Args:
            file_path (str): 导出文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path):
        """
        从文件导入配置
        
        Args:
            file_path (str): 导入文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.save_config()
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def add_quick_command(self, name, command, mode='TEXT'):
        """添加快捷指令"""
        self.config['quick_commands'].append({
            'name': name,
            'mode': mode,
            'command': command
        })
        self.save_config()
    
    def remove_quick_command(self, index):
        """删除快捷指令"""
        if 0 <= index < len(self.config['quick_commands']):
            self.config['quick_commands'].pop(index)
            self.save_config()
    
    def get_quick_commands(self):
        """获取快捷指令列表"""
        return self.config.get('quick_commands', [])
    
    def add_send_history(self, data):
        """添加发送历史"""
        self.config['send_history'].insert(0, data)
        # 限制历史记录数量
        if len(self.config['send_history']) > 100:
            self.config['send_history'] = self.config['send_history'][:100]
        self.save_config()
    
    def get_send_history(self):
        """获取发送历史"""
        return self.config.get('send_history', [])
    
    def get_command_panel_visible(self):
        """获取命令面板显示状态"""
        return self.config.get('command_panel_visible', True)
    
    def set_command_panel_visible(self, visible):
        """设置命令面板显示状态"""
        self.config['command_panel_visible'] = visible
        self.save_config()
    
    def get_send_text(self, port):
        """获取指定串口的发送文本"""
        port_config = self.get_port_config(port)
        return port_config.get('send_text', '')
    
    def set_send_text(self, port, text):
        """设置指定串口的发送文本"""
        if port not in self.config['port_configs']:
            self.config['port_configs'][port] = self._get_default_port_config()
        self.config['port_configs'][port]['send_text'] = text
        self.save_config()

