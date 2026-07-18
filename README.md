# QSerial（Quickky Serial Tool）

QSerial 是面向开发和测试人员的 Windows 串口调试工具。默认界面基于 Python、PySide6 和 Qt Widgets，支持多 Tab、单栏/双栏串口会话、TEXT/HEX 收发、快捷指令、发送历史、日志和 Light/Dark 主题。

## 运行

```bash
pip3 install -r requirements.txt
run.bat
```

也可以直接执行 `python3 src/main/app_qt.py`。

## 构建 Windows 单文件

```bash
build.bat
```

构建版本由根目录 `VERSION` 文件确定，构建产物为 `dist/QSerial.exe` 和 `dist/QSerial_v<版本号>.zip`。ZIP 包含 EXE、`LICENSE` 与 `licenses/` 中的 LGPLv3/GPLv3、第三方声明；主题、图标和 Qt 运行时均被打入单文件，不包含开发环境的 `config.json`。用户配置仍与 EXE 放在同一运行目录。

## 技术栈

- Python 3
- PySide6 + Qt Widgets
- pyserial
- PyInstaller

## 许可证

项目代码采用 [MIT License](LICENSE)。PySide6/Qt 按 LGPLv3 使用；发布时须保留 `licenses/THIRD_PARTY_NOTICES.md`，并随发行物提供完整 LGPLv3/GPLv3 文本和 Qt/PySide6 源码获取方式。

## Agent 驱动开发

本项目采用 Agent 驱动开发方式。修改前必须先阅读 [AGENTS.md](AGENTS.md) 和 [docs/design/PROJECT_DESIGN.md](docs/design/PROJECT_DESIGN.md)，并同步维护实现与设计文档的一致性。
