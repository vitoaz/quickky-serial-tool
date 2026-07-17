"""
串口通信管理工具类

Author: Aaz
Email: vitoaaazzz@gmail.com
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
        self.last_config = {}
        self.operation_timeout = 1.0  # 操作超时时间（秒）
        self.check_interval = 0.5  # 串口状态检查间隔（秒）
        self.last_check_time = 0  # 上次检查时间
    
    @staticmethod
    def get_available_ports():
        """
        获取可用串口列表
        
        Returns:
            list: 串口名称列表
        """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def _is_port_available(self, port_name):
        """
        检查串口是否仍然可用（物理存在）
        
        Args:
            port_name (str): 串口名称
            
        Returns:
            bool: 串口是否存在
        """
        available_ports = self.get_available_ports()
        return port_name in available_ports
    
    def _check_port_health(self):
        """
        综合检查串口健康状态
        
        Returns:
            tuple: (is_healthy, error_message)
        """
        if not self.serial_port:
            return False, "串口对象不存在"
        
        try:
            # 检查1: 串口是否处于打开状态
            if not self.serial_port.is_open:
                return False, "串口未打开"
            
            # 检查2: 串口是否仍然物理存在
            port_name = self.serial_port.port
            if not self._is_port_available(port_name):
                return False, f"串口 {port_name} 已被移除"
            
            # 检查3: 尝试获取串口状态（某些断开情况下会失败）
            try:
                # 检查CTS（Clear To Send）信号状态
                _ = self.serial_port.cts
                # 检查DSR（Data Set Ready）信号状态
                _ = self.serial_port.dsr
                # 检查输入缓冲区大小
                _ = self.serial_port.in_waiting
            except (OSError, AttributeError) as e:
                return False, f"串口状态异常: {e}"
            
            return True, None
            
        except Exception as e:
            return False, f"串口健康检查失败: {e}"
    
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
        """关闭串口（主动关闭不触发回调）"""
        self.is_running = False
        
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
                # 定期检查串口健康状态
                current_time = time.time()
                if current_time - self.last_check_time > self.check_interval:
                    self.last_check_time = current_time
                    is_healthy, error_msg = self._check_port_health()
                    if not is_healthy:
                        print(f"串口健康检查失败: {error_msg}")
                        raise serial.SerialException(error_msg)
                
                # 读取数据
                if self.serial_port and self.serial_port.is_open:
                    try:
                        # 检查是否有数据可读
                        if self.serial_port.in_waiting:
                            data = self.serial_port.read(self.serial_port.in_waiting)
                            if self.receive_callback and data:
                                self.receive_callback(data)
                        else:
                            # 短暂休眠，避免CPU占用过高
                            time.sleep(0.01)
                    except serial.SerialTimeoutException:
                        print("读取数据超时")
                        continue
                    except (OSError, serial.SerialException) as e:
                        # 串口读取错误，可能已断开
                        print(f"读取数据错误: {e}")
                        raise
                else:
                    # 串口对象无效
                    if self.is_running:
                        print("检测到串口对象无效")
                        raise serial.SerialException("串口对象无效")
                    break
                    
            except Exception as e:
                # 只有在运行状态下才触发断开回调（避免主动关闭时触发）
                if self.is_running:
                    print(f"串口异常断开: {e}")
                    self.is_running = False
                    
                    # 清理串口对象
                    if self.serial_port:
                        try:
                            self.serial_port.close()
                        except:
                            pass
                        self.serial_port = None
                    
                    # 触发断开回调
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
    
    def is_open(self):
        """检查串口是否打开"""
        return self.serial_port and self.serial_port.is_open

