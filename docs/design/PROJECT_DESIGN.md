# QSerial 项目设计文档

## 项目概述

QSerial（Quickky Serial Tool）是面向开发和测试人员的 Windows 串口调试工具。默认启动入口为 PySide6 / Qt Widgets 界面，用户可在多个工作 Tab 中配置串口并收发 TEXT 或 HEX 数据。应用将串口配置、界面设置、快捷指令、发送历史和主题选择保存至 EXE 运行目录的 `config.json`。

## 技术栈

- Python 3
- PySide6 + Qt Widgets
- pyserial
- PyInstaller（Windows 单文件发布）

## 项目结构

```text
src/
  main/          PySide6 启动入口
  pages/         主窗口与全局设置页面
  components/    Qt 界面组件
  utils/         串口、配置、主题和辅助工具
themes/          Light、Dark 主题配置
scripts/         版本信息、发布许可证与 PyInstaller 裁剪钩子
licenses/        Qt/PySide6 发布声明
docs/design/     设计文档
docs/guides/     Python 开发与版本发布指南
```

`src/main/app_qt.py` 是 `run.bat` 与 `build.bat` 使用的应用入口。

## 模块划分

- `src/main/app_qt.py`：创建 `QApplication`、Qt 主窗口并启动事件循环。
- `src/pages/main_window_qt.py`：组装菜单、工作区、命令面板，处理主题、配置导入导出和窗口关闭。
- `src/pages/settings_dialog_qt.py`：编辑接收缓冲、历史数量、字体和自动重连间隔。
- `src/components/work_panel_qt.py`：管理单栏或双栏工作区及当前激活栏。
- `src/components/work_column_qt.py`：管理单个工作栏的 Tab 创建、切换与关闭。
- `src/components/work_tab_qt.py`：管理一个串口会话的连接、批量接收显示、发送、循环发送、日志和自动重连。
- `src/components/*_settings_panel_qt.py`：分别编辑串口、接收和发送设置。
- `src/components/command_panel_qt.py`、`quick_commands_panel_qt.py`、`quick_command_dialog_qt.py`、`send_history_panel_qt.py`：提供快捷指令和发送历史功能。
- `src/utils/serial_manager_qt.py`：将串口打开、关闭、发送和后台接收适配为 Qt 可用的异步操作与有界待显示缓冲。
- `src/utils/log_writer_qt.py`：在后台线程批量写入有界日志队列，避免日志 I/O 阻塞界面线程。
- `src/utils/theme_manager_qt.py` 与 `custom_controls_qt.py`：加载主题并提供 Qt 样式与通用控件。
- `src/utils/config_manager.py`：读取、更新、导入导出并持久化运行目录中的 `config.json`。
- `src/utils/serial_manager.py`：封装 pyserial 打开、关闭、收发、接收线程和断线检测。
- `src/utils/hex_utils.py`：提供 HEX 数据转换与校验。

## 数据模型

配置由 `ConfigManager` 以 JSON 形式保存至 EXE 运行目录（开发模式为项目根目录）的 `config.json`，主要结构如下：

```text
config
├── last_port_main / last_port_secondary
├── port_configs
│   └── <串口名>
│       ├── serial_settings
│       ├── receive_settings
│       ├── send_settings
│       └── send_text
├── quick_command_groups
├── send_history
├── command_panel_visible
├── dual_panel_mode
├── theme
└── global_settings
```

## 关键流程

### 应用启动

1. `app_qt.py` 创建 `QApplication` 和 `MainWindow`。
2. `MainWindow` 创建 `ConfigManager`、Qt 主题管理器、工作区和命令面板。
3. 主窗口读取主题 JSON，生成 Qt 样式表并进入事件循环。

### 串口收发与高吞吐显示

1. 用户在工作 Tab 中选择串口和通信参数，触发连接操作。
2. `SerialManagerQt` 在后台执行串口打开、关闭、发送和接收；接收数据进入有最大字节数限制的队列。
3. `WorkTab` 每 25ms 最多消费 256 KiB 数据，并批量写入 `QPlainTextEdit`；接收区禁用自动换行并限制最大行数。
4. 用户发送数据时，工作 Tab 按 TEXT 或 HEX 设置转换后写入串口；成功发送的数据写入发送历史。
5. 日志文件由后台日志写入器保持打开直到会话清理，避免在接收路径执行文件 I/O。

### 配置与主题

1. 用户调整界面、串口、收发、快捷指令或历史数据。
2. 相应组件调用 `ConfigManager` 更新内存中的配置并写入运行目录 `config.json`。
3. 用户选择主题时，主窗口加载 `themes/` 中对应 JSON 并重新应用 Qt 样式表。
