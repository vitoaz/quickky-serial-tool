"""仅保留 Windows Qt Widgets 应用运行所需的平台插件。"""

from pathlib import Path

from PyInstaller.utils.hooks import get_module_file_attribute


_pyside_dir = Path(get_module_file_attribute("PySide6.QtGui")).parent

hiddenimports = ["PySide6.QtCore"]
binaries = [
    (
        str(_pyside_dir / "plugins" / "platforms" / "qwindows.dll"),
        "PySide6/plugins/platforms",
    ),
]
datas = []
