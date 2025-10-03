"""
串口通信管理工具类

Author: Aaz
Email: vitoyuz@foxmail.com
"""

import serial
import serial.tools.list_ports
import threading
from datetime import datetime
import time

# 串口参数映射
PARITY_MAP = {
    'None': serial.PARITY_NONE,
    'Even': serial.PARITY_EVEN,
    'Odd': serial.PARITY_ODD,
    'Mark': serial.PARITY_MARK,
    'Space': serial.PARITY_SPACE
}

STOPBITS_MAP = {
    1: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2: serial.STOPBITS_TWO
}

FLOW_CONTROL_MAP = {
    'None': (False, False),
    'Hardware': (True, False),
    'Software': (False, True)
}

class SerialManager:
    """串口管理类"""
    
    def __init__(self):
        self.serial_port = None
        self.receive_thread = None
        self.is_running = False
        self.receive_callback = None
        self.disconnect_callback = None
        self.auto_reconnect = False
        self.last_config = {}
        self.operation_timeout = 1.0  # 操作超时时间（秒）
    
    @staticmethod
    def get_available_ports():
        """
        获取可用串口列表
        
        Returns:
            list: 串口名称列表
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def open(self, port, baudrate=115200, parity='None', bytesize=8, 
             stopbits=1, flow_control='None'):
        """
        打开串口
        
        Args:
            port (str): 串口名称
            baudrate (int): 波特率
            parity (str): 校验位
            bytesize (int): 数据位
            stopbits (float): 停止位
            flow_control (str): 流控
            
        Returns:
            bool: 是否成功打开
        """
        # 使用线程执行打开操作，避免阻塞
        result = {'success': False, 'error': None}
        
        def _open_thread():
            try:
                # 保存配置用于重连
                self.last_config = {
                    'port': port,
                    'baudrate': baudrate,
                    'parity': parity,
                    'bytesize': bytesize,
                    'stopbits': stopbits,
                    'flow_control': flow_control
                }
                
                rtscts, xonxoff = FLOW_CONTROL_MAP.get(flow_control, (False, False))
                
                self.serial_port = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=PARITY_MAP.get(parity, serial.PARITY_NONE),
                    stopbits=STOPBITS_MAP.get(stopbits, serial.STOPBITS_ONE),
                    timeout=0.1,
                    write_timeout=self.operation_timeout,  # 写超时
                    rtscts=rtscts,
                    xonxoff=xonxoff
                )
                
                # 启动接收线程
                self.is_running = True
                self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
                self.receive_thread.start()
                
                result['success'] = True
            except Exception as e:
                result['error'] = str(e)
        
        # 在独立线程中执行打开操作
        thread = threading.Thread(target=_open_thread, daemon=True)
        thread.start()
        thread.join(timeout=self.operation_timeout)
        
        if thread.is_alive():
            # 超时，操作仍在执行
            print(f"打开串口超时（{self.operation_timeout}秒）")
            return False
        
        if not result['success']:
            print(f"打开串口失败: {result['error']}")
            return False
        
        return True
    
    def close(self):
        """关闭串口"""
        self.is_running = False
        self.auto_reconnect = False
        
        # 等待接收线程结束
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
        
        # 使用线程执行关闭操作，避免阻塞
        def _close_thread():
            try:
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.close()
            except Exception as e:
                print(f"关闭串口时出错: {e}")
            finally:
                self.serial_port = None
        
        thread = threading.Thread(target=_close_thread, daemon=True)
        thread.start()
        thread.join(timeout=self.operation_timeout)
        
        if thread.is_alive():
            # 超时，强制置空
            print(f"关闭串口超时，强制释放")
            self.serial_port = None
    
    def _receive_loop(self):
        """接收数据循环"""
        while self.is_running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    # 使用超时读取，避免阻塞
                    if self.serial_port.in_waiting:
                        try:
                            data = self.serial_port.read(self.serial_port.in_waiting)
                            if self.receive_callback and data:
                                self.receive_callback(data)
                        except serial.SerialTimeoutException:
                            print("读取数据超时")
                            continue
                        except Exception as e:
                            print(f"读取数据错误: {e}")
                            raise
                    else:
                        # 短暂休眠，避免CPU占用过高
                        time.sleep(0.01)
                else:
                    # 串口断开
                    if self.disconnect_callback:
                        self.disconnect_callback()
                    
                    if self.auto_reconnect and self.last_config:
                        # 尝试重连
                        time.sleep(1)  # 等待1秒
                        self.open(**self.last_config)
                    else:
                        break
            except Exception as e:
                print(f"接收数据错误: {e}")
                if self.disconnect_callback:
                    self.disconnect_callback()
                break
    
    def send(self, data, mode='TEXT', encoding='UTF-8'):
        """
        发送数据
        
        Args:
            data (str): 要发送的数据
            mode (str): 发送模式（TEXT/HEX）
            encoding (str): 编码格式（仅TEXT模式）
            
        Returns:
            bool: 是否发送成功
        """
        if not self.serial_port or not self.serial_port.is_open:
            return False
        
        result = {'success': False, 'error': None}
        
        def _send_thread():
            try:
                if mode == 'HEX':
                    # HEX模式：将十六进制字符串转为字节
                    hex_str = data.replace(' ', '').replace('\n', '')
                    send_data = bytes.fromhex(hex_str)
                else:
                    # TEXT模式：按编码转换
                    send_data = data.encode(encoding.lower().replace('-', ''))
                
                self.serial_port.write(send_data)
                result['success'] = True
            except serial.SerialTimeoutException:
                result['error'] = "发送超时"
            except Exception as e:
                result['error'] = str(e)
        
        # 在独立线程中执行发送操作
        thread = threading.Thread(target=_send_thread, daemon=True)
        thread.start()
        thread.join(timeout=self.operation_timeout)
        
        if thread.is_alive():
            # 超时
            print(f"发送数据超时（{self.operation_timeout}秒）")
            return False
        
        if not result['success']:
            print(f"发送数据失败: {result['error']}")
            return False
        
        return True
    
    def set_receive_callback(self, callback):
        """设置接收回调函数"""
        self.receive_callback = callback
    
    def set_disconnect_callback(self, callback):
        """设置断开连接回调函数"""
        self.disconnect_callback = callback
    
    def set_auto_reconnect(self, enable):
        """设置自动重连"""
        self.auto_reconnect = enable
    
    def is_open(self):
        """检查串口是否打开"""
        return self.serial_port and self.serial_port.is_open

