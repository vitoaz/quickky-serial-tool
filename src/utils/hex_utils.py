"""
HEX格式处理工具类

Author: Aaz
Email: vitoyuz@foxmail.com
"""


class HexUtils:
    """HEX格式处理工具类"""
    
    @staticmethod
    def validate_hex_format(hex_string):
        """
        验证HEX字符串格式
        
        Args:
            hex_string: 要验证的HEX字符串
            
        Returns:
            bool: 格式是否正确
        """
        if not hex_string:
            return False
        
        try:
            # 移除常见的分隔符和前缀
            cleaned = hex_string.upper()
            cleaned = cleaned.replace('0X', '')  # 移除0x前缀
            cleaned = cleaned.replace(' ', '')   # 移除空格
            cleaned = cleaned.replace(',', '')   # 移除逗号
            cleaned = cleaned.replace('-', '')   # 移除横线
            cleaned = cleaned.replace(':', '')   # 移除冒号
            cleaned = cleaned.replace('\n', '')  # 移除换行
            cleaned = cleaned.replace('\r', '')  # 移除回车
            
            # 检查是否为空
            if not cleaned:
                return False
            
            # 检查长度是否为偶数（每个字节需要2个字符）
            if len(cleaned) % 2 != 0:
                return False
            
            # 检查是否只包含有效的十六进制字符
            valid_chars = set('0123456789ABCDEF')
            if not all(c in valid_chars for c in cleaned):
                return False
            
            # 尝试转换为字节数组验证
            bytes.fromhex(cleaned)
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_format_error_message():
        """
        获取HEX格式错误提示信息
        
        Returns:
            str: 错误提示信息
        """
        return 'HEX格式错误'
    
    @staticmethod
    def get_format_examples():
        """
        获取HEX格式示例
        
        Returns:
            str: 格式示例文本
        """
        return """HEX格式错误！

正确格式示例：
• 01 02 03 FF
• 01,02,03,FF
• 010203FF
• 0x01 0x02 0x03 0xFF"""
    
    @staticmethod
    def clean_hex_string(hex_string):
        """
        清理HEX字符串，移除分隔符和前缀
        
        Args:
            hex_string: 原始HEX字符串
            
        Returns:
            str: 清理后的HEX字符串
        """
        if not hex_string:
            return ''
        
        cleaned = hex_string.upper()
        cleaned = cleaned.replace('0X', '')
        cleaned = cleaned.replace(' ', '')
        cleaned = cleaned.replace(',', '')
        cleaned = cleaned.replace('-', '')
        cleaned = cleaned.replace(':', '')
        cleaned = cleaned.replace('\n', '')
        cleaned = cleaned.replace('\r', '')
        
        return cleaned
