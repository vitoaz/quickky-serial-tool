"""串口接收数据的通用格式化与日志模式辅助逻辑。"""

import codecs
from datetime import datetime


class ReceiveTextDecoder:
    """按当前接收编码增量解码串口字节，保留跨批次的多字节字符。"""

    def __init__(self):
        self._encoding = None
        self._decoder = None

    def reset(self):
        """清除已缓存的未完成多字节序列。"""
        self._encoding = None
        self._decoder = None

    def decode(self, data, encoding):
        """解码数据；ASCII 失败时按既有规则尝试 GB2312 与 GBK。"""
        candidates = ReceiveDataUtils.get_encoding_candidates(encoding)
        if self._encoding not in candidates:
            self.reset()
        if self._decoder:
            try:
                return self._decoder.decode(data)
            except UnicodeDecodeError:
                self.reset()
        for candidate in candidates:
            try:
                decoder = codecs.getincrementaldecoder(candidate)(errors="strict")
                text = decoder.decode(data)
            except (LookupError, UnicodeDecodeError):
                continue
            self._encoding = candidate
            self._decoder = decoder
            return text
        return str(data)


class ReceiveTextSegmenter:
    """按跨批次文本状态过滤空行，同时保留有效空白字符与行结束符。"""

    def __init__(self):
        self._line_has_content = False

    def reset(self):
        """重置当前行状态。"""
        self._line_has_content = False

    def iter_segments(self, text):
        """返回待显示文本段；只忽略真正的空行。"""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        for segment in normalized.splitlines(True):
            if segment.endswith("\n"):
                content = segment[:-1]
                if content:
                    yield segment
                elif self._line_has_content:
                    # 独立到达的换行仍需结束上一条文本，不能因过滤空行而丢失。
                    yield "\n"
                self._line_has_content = False
            elif segment:
                # 空格和 Tab 可能是协议有效数据，必须原样保留。
                self._line_has_content = True
                yield segment


class ReceiveLogFormatter:
    """维护日志模式的时间戳拼接状态，不依赖界面框架。"""

    def __init__(self):
        self.reset()

    def reset(self):
        """使下一条日志内容重新添加时间戳。"""
        self.last_append_time = None
        self.last_line_ended = True

    def format(self, text, log_mode, now=None):
        """按日志模式为文本添加时间戳，并返回应显示和写入日志的内容。"""
        now = now or datetime.now()
        if not log_mode:
            self.last_line_ended = text.endswith("\n")
            self.last_append_time = now
            return text
        needs_timestamp = (
            self.last_line_ended
            or self.last_append_time is None
            or (now - self.last_append_time).total_seconds() > 0.1
        )
        if needs_timestamp:
            timestamp = now.strftime("[%H:%M:%S.%f")[:-3] + "] "
            prefix = "" if self.last_line_ended or text.startswith("\n") else "\n"
            text = prefix + timestamp + text
        self.last_line_ended = text.endswith("\n")
        self.last_append_time = now
        return text


class ReceiveDataUtils:
    """提供 Qt 与 wx 共享的接收数据格式化方法。"""

    @staticmethod
    def get_encoding_candidates(encoding):
        normalized = encoding.replace("-", "").lower()
        return (normalized, "gb2312", "gbk") if normalized == "ascii" else (normalized,)

    @staticmethod
    def format_hex(data):
        """将字节格式化为连续 HEX 显示文本。"""
        return data.hex(" ").upper() + (" " if data else "")
