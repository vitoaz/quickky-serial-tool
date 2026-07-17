"""面向 Qt 界面的串口适配层；串口 I/O 始终运行在后台线程。"""

from collections import deque
import threading

from PySide6.QtCore import QObject, Signal

from .serial_manager import SerialManager


class SerialManagerQt(QObject):
    """将后台串口回调转换为 Qt 信号，并限制待显示数据的内存占用。"""

    disconnected = Signal()
    operation_completed = Signal(str, bool)

    def __init__(self, max_pending_bytes=4 * 1024 * 1024):
        super().__init__()
        self._manager = SerialManager()
        self._pending = deque()
        self._pending_bytes = 0
        self._max_pending_bytes = max_pending_bytes
        self._lock = threading.Lock()
        self._dropped_bytes = 0
        self._manager.set_receive_callback(self._enqueue)
        self._manager.set_disconnect_callback(self.disconnected.emit)

    @staticmethod
    def get_available_ports():
        return SerialManager.get_available_ports()

    def _enqueue(self, data):
        with self._lock:
            if self._pending_bytes + len(data) > self._max_pending_bytes:
                self._dropped_bytes += len(data)
                return
            self._pending.append(data)
            self._pending_bytes += len(data)

    def drain(self, max_bytes=256 * 1024):
        """由 UI 线程周期调用；返回一批数据及本批之前丢弃的字节数。"""
        chunks, total = [], 0
        with self._lock:
            while self._pending and total < max_bytes:
                chunk = self._pending.popleft()
                remaining = max_bytes - total
                if len(chunk) > remaining:
                    chunks.append(chunk[:remaining])
                    self._pending.appendleft(chunk[remaining:])
                    self._pending_bytes -= remaining
                    total += remaining
                    break
                chunks.append(chunk)
                total += len(chunk)
                self._pending_bytes -= len(chunk)
        with self._lock:
            dropped, self._dropped_bytes = self._dropped_bytes, 0
        return b"".join(chunks), dropped

    def _run_async(self, operation, callback):
        def runner():
            try:
                result = callback()
                self.operation_completed.emit(operation, bool(result) if result is not None else True)
            except Exception:
                self.operation_completed.emit(operation, False)
        threading.Thread(target=runner, daemon=True).start()

    def open_async(self, **settings):
        self._run_async("open", lambda: self._manager.open(**settings))

    def close_async(self):
        self._run_async("close", self._manager.close)

    def send_async(self, data, mode="TEXT", encoding="UTF-8"):
        self._run_async("send", lambda: self._manager.send(data, mode, encoding)
        )

    def is_open(self):
        return self._manager.is_open()
