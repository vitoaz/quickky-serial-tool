"""
配置管理工具类

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import json
import os
import sys
from pathlib import Path

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file='config.json'):
        """
        初始化配置管理器
        
        Args:
            config_file (str): 配置文件名
        """
        # 获取应用程序的基础路径
        if getattr(sys, 'frozen', False):
            # 打包后的exe环境
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # 配置文件路径（与程序同级目录）
        self.config_file = os.path.join(base_path, config_file)
        self.config = self._load_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "last_port_main": "",  # 主栏最后使用的串口
            "last_port_secondary": "",  # 副栏最后使用的串口
            "port_configs": {},
            "quick_command_groups": [],  # 快捷指令分组
            "send_history": [],
            "command_panel_visible": True,  # 命令面板显示状态
            "dual_panel_mode": False  # 双栏模式
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
                "auto_reconnect": False,
                "auto_scroll": True
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
    
    def get_last_port(self, panel='main'):
        """
        获取上次使用的串口
        
        Args:
            panel: 面板类型 ('main' 或 'secondary')
        """
        if panel == 'secondary':
            return self.config.get('last_port_secondary', '')
        else:
            return self.config.get('last_port_main', '')
    
    def set_last_port(self, port, panel='main'):
        """
        设置上次使用的串口
        
        Args:
            port: 串口名称
            panel: 面板类型 ('main' 或 'secondary')
        """
        if panel == 'secondary':
            self.config['last_port_secondary'] = port
        else:
            self.config['last_port_main'] = port
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
        
        # 强制将save_log设为False（每次都需要重新选择文件）
        config = self.config['port_configs'][port]
        if 'receive_settings' in config:
            config['receive_settings']['save_log'] = False
        
        return config
    
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
    
    def get_quick_command_groups(self):
        """获取快捷指令分组列表"""
        return self.config.get('quick_command_groups', [])
    
    def set_quick_command_groups(self, groups):
        """设置快捷指令分组列表"""
        self.config['quick_command_groups'] = groups
        self.save_config()
    
    def add_send_history(self, data, mode='TEXT'):
        """
        添加发送历史
        
        Args:
            data: 发送的数据
            mode: 发送模式(TEXT/HEX)
        """
        from datetime import datetime
        
        history_item = {
            'data': data,
            'mode': mode,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.config['send_history'].insert(0, history_item)
        # 限制历史记录数量为200条
        if len(self.config['send_history']) > 200:
            self.config['send_history'] = self.config['send_history'][:200]
        self.save_config()
    
    def get_send_history(self):
        """获取发送历史"""
        return self.config.get('send_history', [])
    
    def clear_send_history(self):
        """清空发送历史"""
        self.config['send_history'] = []
        self.save_config()
    
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
    
    def get_dual_panel_mode(self):
        """获取双栏模式状态"""
        return self.config.get('dual_panel_mode', False)
    
    def set_dual_panel_mode(self, enabled):
        """设置双栏模式状态"""
        self.config['dual_panel_mode'] = enabled
        self.save_config()

