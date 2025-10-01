"""
版本号生成脚本

Author: Aaz
Email: vitoyuz@foxmail.com
"""

from datetime import datetime
import os

VERSION = "1.0.0"

def generate_version_file():
    """生成version.py文件"""
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f'''"""
版本信息（自动生成，请勿手动编辑）

Author: Aaz
Email: vitoyuz@foxmail.com
"""

VERSION = "{VERSION}"
BUILD_TIME = "{build_time}"
'''
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    version_file = os.path.join(root_dir, 'version.py')
    
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"版本文件已生成: {version_file}")
    print(f"版本号: {VERSION}")
    print(f"构建时间: {build_time}")

if __name__ == '__main__':
    generate_version_file()

