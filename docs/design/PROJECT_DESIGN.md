# QSerial 项目设计文档

## 项目概述

QSerial（Quickky Serial Tool）是面向开发和测试人员的 Windows 串口调试工具。默认启动入口为 PySide6 / Qt Widgets 界面，用户可在多个工作 Tab 中配置串口并收发 TEXT 或 HEX 数据。应用将串口配置、界面设置、快捷指令、发送历史和主题选择保存至 EXE 运行目录的 `config.json`。

## 技术栈

- Python 3
- PySide6 + Qt Widgets
- pyserial
- PyInstaller（Windows 单文件与 ZIP 发布包）

## 项目结构

```text
src/
  main/          PySide6 启动入口
  pages/         主窗口与全局设置页面
  components/    Qt 界面组件
  utils/         串口、配置、主题和辅助工具
themes/          Light、Dark 主题配置
scripts/         版本信息、发布许可证、发布包、Gitee Release 与 PyInstaller 裁剪钩子
.gitee           Gitee 发布仓库与 Git 远程配置（不含令牌）
VERSION           项目当前版本号的唯一来源
licenses/        Qt/PySide6 发布声明
docs/design/     设计文档
docs/guides/     Python 开发与版本发布指南
tests/           标准库回归测试
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
- `src/utils/serial_manager_qt.py`：串行执行有超时保护的后台串口操作，将结果与有界待显示缓冲适配给 Qt。
- `src/utils/log_writer.py`：在后台线程批量写入有界日志队列，并回传打开或写入失败状态。
- `src/utils/theme_manager_qt.py`：加载主题并生成 Qt 样式表。
- `src/utils/config_manager.py`：读取、规范化、更新、导入导出并持久化运行目录中的 `config.json`。
- `src/utils/serial_manager.py`：以互斥操作封装 pyserial 打开、关闭、收发、接收线程和断线检测。
- `src/utils/hex_utils.py`：提供 HEX 数据格式校验。
- `src/utils/receive_data_utils.py`：提供跨批次文本增量解码、接收格式化与日志模式时间戳拼接。
- `src/utils/send_data_utils.py`：统一发送文本的 CRLF 换行、HEX 转换、HEX 解析与编码选择。
- `scripts/release_gitee.py`：读取 `.gitee` 与用户目录令牌，推送全部本地分支和标签到 Gitee，创建或补齐 Release 并上传 ZIP 发布包。
- `VERSION`：保存当前版本号；版本生成和发布包脚本均从此文件读取版本。
- `tests/`：覆盖配置、串口通信辅助逻辑和 Qt 工作页关键行为的回归测试。

## 数据模型

配置由 `ConfigManager` 以 JSON 形式保存至 EXE 运行目录（开发模式为项目根目录）的 `config.json`，主要结构如下：

```text
config
├── last_port_main / last_port_secondary
├── port_configs
│   └── <串口名>
│       ├── serial_settings
│       ├── receive_settings
│       ├── send_settings（含 TEXT 换行符）
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
2. `SerialManagerQt` 在后台执行串口打开、关闭、发送和接收；接收数据进入有最大字节数限制的队列，并在串口会话切换时清空未显示的旧数据。
3. `WorkTab` 每 25ms 最多消费 256 KiB 数据；接收工具按编码增量解码跨批次的多字节字符、保留有效空白字符与跨包行结束符、过滤真正的空行并处理日志时间戳，随后批量写入 `QPlainTextEdit`；接收区禁用自动换行并限制最大行数。日志模式对持续超过 100ms 的连续数据插入换行和新时间戳。RX 统计包含显示缓冲丢弃的字节；日志写入缓冲溢出或后台打开、写入失败时，接收区会显示原因并停止保存日志。
4. 用户通过发送框或快捷指令发送数据时，发送工具将 TEXT 编辑器与快捷指令换行规范化为内部 `\r\n`；每个串口的 `send_settings.line_ending` 可选 `CR`、`LF` 或 `CRLF`，仅将用户主动输入的每一个逻辑换行转换为指定字节，不会在发送末尾自动追加换行。该规则也用于 TEXT/HEX 相互转换；HEX 模式直接发送时不改写字节，HEX 转 TEXT 后恢复为内部 `\r\n`。成功发送的数据写入发送历史。
5. 日志文件由后台日志写入器保持打开直到会话清理，避免在接收路径执行文件 I/O；切换串口时关闭当前日志文件，避免将新会话数据写入旧路径。串口打开、关闭和发送均在后台串行执行，并受 1 秒操作超时保护；关闭或发送失败、超时时界面显示错误。超时打开的晚到结果会被关闭，不会覆盖当前会话，且原打开线程结束前会拒绝新的打开请求。

### 配置与主题

1. 用户调整界面、串口、收发、快捷指令或历史数据。
2. `ConfigManager` 在启动加载和导入 JSON 时将缺失、类型错误或不合法的字段恢复为默认值（主题仅允许 `light`、`dark`），丢弃未知结构；相应组件再更新内存中的规范化配置并写入运行目录 `config.json`。
3. 用户选择主题时，主窗口加载 `themes/` 中对应 JSON 并重新应用 Qt 样式表。
