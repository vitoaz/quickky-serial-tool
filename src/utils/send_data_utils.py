"""发送数据处理的共享辅助方法。"""


class SendDataUtils:
    """统一处理发送文本的换行格式。"""

    @staticmethod
    def normalize_text_newlines(text):
        """将逻辑换行统一转换为串口文本发送使用的 CRLF。"""
        return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
