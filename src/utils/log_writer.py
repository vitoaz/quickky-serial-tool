"""异步、有界日志写入器。"""

import threading
from collections import deque
from pathlib import Path


class LogWriter:
    """在后台线程写入日志文件，并限制待写入日志数量。"""

    def __init__(self, max_pending_bytes=4 * 1024 * 1024):
        self._queue = deque()
        self._condition = threading.Condition()
        self._pending_bytes = 0
        self._max_pending_bytes = max_pending_bytes
        self._dropped_bytes = 0
        self._errors = deque()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _put_control(self, command, value=None):
        with self._condition:
            self._queue.append((command, value, 0))
            self._condition.notify()

    def open(self, path):
        self._put_control("open", path)
        return True

    def write(self, text):
        size = len(text.encode("utf-8"))
        with self._condition:
            if self._pending_bytes + size > self._max_pending_bytes:
                self._dropped_bytes += size
                return False
            self._queue.append(("write", text, size))
            self._pending_bytes += size
            self._condition.notify()
            return True

    def close(self):
        self._put_control("close")

    def stop(self):
        self._put_control("stop")

    def take_dropped_bytes(self):
        with self._condition:
            dropped, self._dropped_bytes = self._dropped_bytes, 0
            return dropped

    def take_errors(self):
        """返回并清空后台日志操作失败信息。"""
        with self._condition:
            errors = list(self._errors)
            self._errors.clear()
            return errors

    def _record_error(self, message):
        with self._condition:
            self._errors.append(message)

    def _close_stream(self, stream):
        if not stream:
            return None
        try:
            stream.flush()
        except OSError as error:
            self._record_error(f"关闭日志文件失败: {error}")
        try:
            stream.close()
        except OSError as error:
            self._record_error(f"关闭日志文件失败: {error}")
        return None

    def _run(self):
        stream = None
        while True:
            with self._condition:
                while not self._queue:
                    self._condition.wait()
                command, value, size = self._queue.popleft()
                self._pending_bytes -= size
            if command == "open":
                if stream:
                    stream = self._close_stream(stream)
                try:
                    stream = Path(value).open("a", encoding="utf-8")
                except OSError as error:
                    stream = None
                    self._record_error(f"无法打开日志文件: {error}")
            elif command == "write" and stream:
                try:
                    stream.write(value)
                except OSError as error:
                    stream = self._close_stream(stream)
                    self._record_error(f"写入日志文件失败: {error}")
            elif command == "close" and stream:
                stream = self._close_stream(stream)
            elif command == "stop":
                if stream:
                    self._close_stream(stream)
                return
