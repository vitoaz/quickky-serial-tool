"""发送数据处理的共享辅助方法。"""

from utils.hex_utils import HexUtils


class SendDataUtils:
    """统一处理发送文本换行、HEX 转换与编码选择。"""

    LINE_ENDINGS = {"CR": "\r", "LF": "\n", "CRLF": "\r\n"}

    @staticmethod
    def normalize_text_newlines(text):
        """将编辑器中的逻辑换行统一为内部保存使用的 CRLF。"""
        return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")

    @classmethod
    def apply_line_ending(cls, text, line_ending="CRLF"):
        """将内部 CRLF 规范文本转换为当前串口的实际行尾。"""
        if line_ending not in cls.LINE_ENDINGS:
            raise ValueError("不支持的发送行尾")
        return cls.normalize_text_newlines(text).replace("\r\n", cls.LINE_ENDINGS[line_ending])

    @classmethod
    def restore_line_ending(cls, text, line_ending="CRLF"):
        """将 HEX 解码得到的当前行尾还原为编辑器使用的 CRLF。"""
        if line_ending not in cls.LINE_ENDINGS:
            raise ValueError("不支持的发送行尾")
        return cls.normalize_text_newlines(text.replace(cls.LINE_ENDINGS[line_ending], "\n"))

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
    def text_to_hex(cls, text, encoding="utf-8", line_ending="CRLF"):
        """将文本按指定行尾和编码转换为 HEX 显示文本。"""
        return cls.apply_line_ending(text, line_ending).encode(encoding).hex(" ").upper()

    @classmethod
    def hex_to_text(cls, text, encoding="utf-8", line_ending="CRLF"):
        """将 HEX 文本转换为规范 CRLF 文本，并以替换字符保留无法解码的字节。"""
        return cls.restore_line_ending(cls.parse_hex(text).decode(encoding, errors="replace"), line_ending)

    @classmethod
    def encode_text(cls, text, encoding, line_ending="CRLF"):
        """按指定行尾和可用编码编码，返回实际发送文本、编码和字节数据。"""
        normalized = cls.apply_line_ending(text, line_ending)
        for candidate in cls.get_encoding_candidates(encoding):
            try:
                return normalized, candidate, normalized.encode(candidate.replace("-", "").lower())
            except (LookupError, UnicodeEncodeError):
                continue
        raise UnicodeEncodeError(encoding, text, 0, len(text), "无法使用任何编码发送数据")
