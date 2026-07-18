"""发送数据处理的共享辅助方法。"""

from utils.hex_utils import HexUtils


class SendDataUtils:
    """统一处理发送文本换行、HEX 转换与编码选择。"""

    @staticmethod
    def normalize_text_newlines(text):
        """将逻辑换行统一转换为串口文本发送使用的 CRLF。"""
        return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")

    @staticmethod
    def get_encoding_candidates(encoding):
        """返回发送时按既有规则尝试的编码列表。"""
        return (encoding, "GB2312", "GBK") if encoding.upper() == "ASCII" else (encoding,)

    @staticmethod
    def parse_hex(text):
        """按项目支持的分隔符和 0x 前缀将 HEX 文本解析为字节。"""
        cleaned = HexUtils.clean_hex_string(text)
        if not cleaned:
            raise ValueError("HEX 内容不能为空")
        return bytes.fromhex(cleaned)

    @classmethod
    def text_to_hex(cls, text, encoding="utf-8"):
        """将文本按 CRLF 和指定编码转换为 HEX 显示文本。"""
        return cls.normalize_text_newlines(text).encode(encoding).hex(" ").upper()

    @classmethod
    def hex_to_text(cls, text, encoding="utf-8"):
        """将 HEX 文本转换为文本，保留既有的忽略无效字符策略。"""
        return cls.parse_hex(text).decode(encoding, errors="ignore")

    @classmethod
    def encode_text(cls, text, encoding):
        """规范化换行并按可用编码编码，返回文本、实际编码和字节数据。"""
        normalized = cls.normalize_text_newlines(text)
        for candidate in cls.get_encoding_candidates(encoding):
            try:
                return normalized, candidate, normalized.encode(candidate.replace("-", "").lower())
            except (LookupError, UnicodeEncodeError):
                continue
        raise UnicodeEncodeError(encoding, text, 0, len(text), "无法使用任何编码发送数据")
