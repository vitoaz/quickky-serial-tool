"""串口通信管理工具类。"""

import threading
import time

import serial
import serial.tools.list_ports

from .send_data_utils import SendDataUtils


PARITY_MAP = {
    "None": serial.PARITY_NONE,
    "Even": serial.PARITY_EVEN,
    "Odd": serial.PARITY_ODD,
    "Mark": serial.PARITY_MARK,
    "Space": serial.PARITY_SPACE,
}

STOPBITS_MAP = {
    1: serial.STOPBITS_ONE,
    1.5: serial.STOPBITS_ONE_POINT_FIVE,
    2: serial.STOPBITS_TWO,
}

FLOW_CONTROL_MAP = {
    "None": (False, False),
    "Hardware": (True, False),
    "Software": (False, True),
}


class SerialManager:
    """封装串口操作，并使超时后的晚到结果不会污染当前会话。"""

    def __init__(self):
        self.serial_port = None
        self.receive_thread = None
        self.is_running = False
        self.receive_callback = None
        self.disconnect_callback = None
        self.last_config = {}
        self.operation_timeout = 1.0
        self.check_interval = 0.5
        self.last_check_time = 0
        self._operation_lock = threading.RLock()
        self._open_generation = 0
        self._open_in_flight = False
        self._close_in_flight = False
        self._send_in_flight = False

    @staticmethod
    def get_available_ports():
        return [port.device for port in serial.tools.list_ports.comports()]

    def _is_port_available(self, port_name):
        return port_name in self.get_available_ports()

    def _check_port_health(self):
        if not self.serial_port:
            return False, "串口对象不存在"
        try:
            if not self.serial_port.is_open:
                return False, "串口未打开"
            port_name = self.serial_port.port
            if not self._is_port_available(port_name):
                return False, f"串口 {port_name} 已被移除"
            try:
                _ = self.serial_port.cts
                _ = self.serial_port.dsr
                _ = self.serial_port.in_waiting
            except (OSError, AttributeError) as error:
                return False, f"串口状态异常: {error}"
            return True, None
        except Exception as error:
            return False, f"串口健康检查失败: {error}"

    @staticmethod
    def _close_port(port):
        try:
            if port and port.is_open:
                port.close()
        except Exception as error:
            print(f"关闭串口时出错: {error}")

    def _invalidate_open(self, generation):
        """使尚未完成的打开操作失效，并释放恰好在超时边界完成的串口。"""
        port = None
        with self._operation_lock:
            if generation != self._open_generation:
                return
            self._open_generation += 1
            self.is_running = False
            port, self.serial_port = self.serial_port, None
        self._close_port(port)

    def open(self, port, baudrate=115200, parity="None", bytesize=8,
             stopbits=1, flow_control="None"):
        """在限定时间内打开串口；超时后的晚到连接会立即关闭。"""
        with self._operation_lock:
            # 超时仅结束调用方等待，不能安全终止底层串口打开线程；在线程收尾前
            # 保持该标记以拒绝重试，避免并发打开同一串口。
            if self._open_in_flight or self._close_in_flight:
                print("打开串口失败: 串口操作仍在进行")
                return False
            if self.serial_port and self.serial_port.is_open:
                print("打开串口失败: 串口已打开")
                return False
            self._open_generation += 1
            generation = self._open_generation
            self._open_in_flight = True
            self.last_config = {
                "port": port,
                "baudrate": baudrate,
                "parity": parity,
                "bytesize": bytesize,
                "stopbits": stopbits,
                "flow_control": flow_control,
            }

        completed = threading.Event()
        result = {"success": False, "error": None}

        def open_worker():
            opened_port = None
            try:
                rtscts, xonxoff = FLOW_CONTROL_MAP.get(flow_control, (False, False))
                opened_port = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=PARITY_MAP.get(parity, serial.PARITY_NONE),
                    stopbits=STOPBITS_MAP.get(stopbits, serial.STOPBITS_ONE),
                    timeout=0.1,
                    write_timeout=self.operation_timeout,
                    rtscts=rtscts,
                    xonxoff=xonxoff,
                )
                with self._operation_lock:
                    if generation != self._open_generation:
                        self._close_port(opened_port)
                        return
                    self.serial_port = opened_port
                    self.is_running = True
                    self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
                    self.receive_thread.start()
                    result["success"] = True
            except Exception as error:
                result["error"] = str(error)
                self._close_port(opened_port)
            finally:
                with self._operation_lock:
                    self._open_in_flight = False
                completed.set()

        threading.Thread(target=open_worker, daemon=True).start()
        if completed.wait(self.operation_timeout):
            if not result["success"]:
                print(f"打开串口失败: {result['error']}")
            return result["success"]
        self._invalidate_open(generation)
        print(f"打开串口超时（{self.operation_timeout}秒）")
        return False

    def close(self):
        """在限定时间内关闭串口，并取消仍在进行的打开操作。"""
        with self._operation_lock:
            if self._close_in_flight:
                print("关闭串口失败: 关闭操作仍在进行")
                return False
            self._open_generation += 1
            self.is_running = False
            self.receive_thread = None
            port, self.serial_port = self.serial_port, None
            if not port:
                return True
            self._close_in_flight = True

        completed = threading.Event()
        result = {"success": False, "error": None}

        def close_worker():
            try:
                if port.is_open:
                    port.close()
                result["success"] = True
            except Exception as error:
                result["error"] = str(error)
            finally:
                with self._operation_lock:
                    self._close_in_flight = False
                completed.set()

        threading.Thread(target=close_worker, daemon=True).start()
        if completed.wait(self.operation_timeout):
            if not result["success"]:
                print(f"关闭串口失败: {result['error']}")
            return result["success"]
        print(f"关闭串口超时（{self.operation_timeout}秒）")
        return False

    def _receive_loop(self):
        while self.is_running:
            try:
                current_time = time.time()
                if current_time - self.last_check_time > self.check_interval:
                    self.last_check_time = current_time
                    is_healthy, error_message = self._check_port_health()
                    if not is_healthy:
                        print(f"串口健康检查失败: {error_message}")
                        raise serial.SerialException(error_message)
                if self.serial_port and self.serial_port.is_open:
                    try:
                        if self.serial_port.in_waiting:
                            data = self.serial_port.read(self.serial_port.in_waiting)
                            if self.receive_callback and data:
                                self.receive_callback(data)
                        else:
                            time.sleep(0.01)
                    except serial.SerialTimeoutException:
                        continue
                    except (OSError, serial.SerialException) as error:
                        print(f"读取数据错误: {error}")
                        raise
                elif self.is_running:
                    raise serial.SerialException("串口对象无效")
                else:
                    break
            except Exception as error:
                if self.is_running:
                    print(f"串口异常断开: {error}")
                    self.is_running = False
                    port, self.serial_port = self.serial_port, None
                    self._close_port(port)
                    if self.disconnect_callback:
                        self.disconnect_callback()
                break

    def send(self, data, mode="TEXT", encoding="UTF-8"):
        """在限定时间内写入，超时时拒绝后续并发写入直到原操作结束。"""
        with self._operation_lock:
            if not self.serial_port or not self.serial_port.is_open or self._send_in_flight:
                return False
            self._send_in_flight = True
            port = self.serial_port

        completed = threading.Event()
        result = {"success": False, "error": None}

        def send_worker():
            try:
                if mode == "HEX":
                    send_data = SendDataUtils.parse_hex(data)
                else:
                    send_data = data.encode(encoding.lower().replace("-", ""))
                port.write(send_data)
                result["success"] = True
            except serial.SerialTimeoutException:
                result["error"] = "发送超时"
            except Exception as error:
                result["error"] = str(error)
            finally:
                with self._operation_lock:
                    self._send_in_flight = False
                completed.set()

        threading.Thread(target=send_worker, daemon=True).start()
        if completed.wait(self.operation_timeout):
            if not result["success"]:
                print(f"发送数据失败: {result['error']}")
            return result["success"]
        print(f"发送数据超时（{self.operation_timeout}秒）")
        return False

    def set_receive_callback(self, callback):
        self.receive_callback = callback

    def set_disconnect_callback(self, callback):
        self.disconnect_callback = callback

    def is_open(self):
        return self.serial_port and self.serial_port.is_open
