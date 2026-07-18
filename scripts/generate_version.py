"""
版本号生成脚本

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT_DIR / "VERSION"


def load_version() -> str:
    """读取项目根目录中的唯一版本号来源。"""
    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(f"未找到版本号文件：{VERSION_FILE}") from error

    if not version:
        raise RuntimeError(f"版本号文件为空：{VERSION_FILE}")
    return version

def generate_version_file():
    """生成version.py文件"""
    version = load_version()
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f'''"""
版本信息（自动生成，请勿手动编辑）

Author: Aaz
Email: vitoaaazzz@gmail.com
"""

VERSION = "{version}"
BUILD_TIME = "{build_time}"
'''
    
    # 获取项目根目录
    version_file = ROOT_DIR / "version.py"
    
    with version_file.open('w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"版本文件已生成: {version_file}")
    print(f"版本号: {version}")
    print(f"构建时间: {build_time}")

if __name__ == '__main__':
    generate_version_file()
