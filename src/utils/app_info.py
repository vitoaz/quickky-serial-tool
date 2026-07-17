"""
应用信息工具类

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

import sys
import os
from html import escape
from .file_utils import get_base_path


class AppInfo:
    """应用信息管理类"""
    
    # 应用基本信息
    APP_NAME = "QSerial"
    APP_FULL_NAME = "Quickky Serial Tool"
    AUTHOR = "Aaz"
    EMAIL = "vitoaaazzz@gmail.com"
    
    # 开源地址
    GITEE_URL = "https://gitee.com/vitoaaazzz/quickky-serial-tool"
    GITHUB_URL = "https://github.com/vitoaz/quickky-serial-tool"
    
    # 应用描述
    DESCRIPTION = "一个功能强大的串口调试工具"
    
    @classmethod
    def _get_version_info(cls):
        """
        获取版本信息
        
        Returns:
            tuple: (version, build_time)
        """
        try:
            # 添加项目根目录到路径
            sys.path.insert(0, get_base_path())
            import version
            return version.VERSION, version.BUILD_TIME
        except:
            return "1.0.0", "未知"
    
    @classmethod
    def get_about_text(cls):
        """
        获取关于对话框的文本
        
        Returns:
            str: 格式化的关于文本
        """
        version, build_time = cls._get_version_info()
        
        return f"""{cls.APP_NAME} ({cls.APP_FULL_NAME})

版本: {version}
构建时间: {build_time}

作者: {cls.AUTHOR}
邮箱: {cls.EMAIL}

{cls.DESCRIPTION}

开源地址:
Gitee: {cls.GITEE_URL}
GitHub: {cls.GITHUB_URL}"""

    @classmethod
    def get_about_html(cls):
        """获取 Qt 关于对话框使用的可点击链接内容。"""
        version, build_time = cls._get_version_info()
        return f"""<b>{escape(cls.APP_NAME)} ({escape(cls.APP_FULL_NAME)})</b><br><br>
版本: {escape(version)}<br>
构建时间: {escape(build_time)}<br><br>
作者: {escape(cls.AUTHOR)}<br>
邮箱: {escape(cls.EMAIL)}<br><br>
{escape(cls.DESCRIPTION)}<br><br>
开源地址:<br>
Gitee: <a href=\"{escape(cls.GITEE_URL)}\">{escape(cls.GITEE_URL)}</a><br>
GitHub: <a href=\"{escape(cls.GITHUB_URL)}\">{escape(cls.GITHUB_URL)}</a>"""
    
    @classmethod
    def get_window_title(cls):
        """
        获取窗口标题
        
        Returns:
            str: 窗口标题
        """
        version, _ = cls._get_version_info()
        return f'{cls.APP_NAME} v{version} - by {cls.AUTHOR}'
    
    @classmethod
    def get_app_name(cls):
        """获取应用名称"""
        return cls.APP_NAME
    
    @classmethod
    def get_full_name(cls):
        """获取应用全名"""
        return cls.APP_FULL_NAME
    
    @classmethod
    def get_author(cls):
        """获取作者"""
        return cls.AUTHOR
    
    @classmethod
    def get_email(cls):
        """获取邮箱"""
        return cls.EMAIL
    
    @classmethod
    def get_description(cls):
        """获取应用描述"""
        return cls.DESCRIPTION
