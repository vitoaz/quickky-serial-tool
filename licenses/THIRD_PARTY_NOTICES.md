# 第三方组件与许可证声明

QSerial 项目代码采用 MIT 许可证。

发布的 Windows 单文件版本使用 PySide6（Qt for Python）及 Qt 运行时。PySide6/Qt 以 LGPLv3 方式使用；发行目录的 `licenses/LGPL-3.0.txt` 和 `licenses/GPL-3.0.txt` 包含完整许可证文本。用户可从 Qt 官方获取对应源码和许可证信息：<https://download.qt.io/official_releases/qt/>、<https://code.qt.io/cgit/pyside/pyside-setup.git/>。

本项目未修改 PySide6 或 Qt 的源码。Windows 单文件构建会将 Qt/PySide6 运行时打包并在运行时解压；发布前必须针对具体 PyInstaller、Qt/PySide6 版本确认 LGPLv3 的重新链接、调试修改和安装信息义务。项目提供完整源码及 `build_qt.bat` 以支持从源码重建发行物。

pyserial 使用 BSD 许可证；其许可证与源码信息见：<https://github.com/pyserial/pyserial>。
