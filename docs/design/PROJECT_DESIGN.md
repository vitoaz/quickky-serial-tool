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
tests/           按功能拆分的标准库回归测试
```

`src/main/app_qt.py` 是 `run.bat` 与 `build.bat` 使用的应用入口。

## 模块划分

- `src/main/app_qt.py`：创建 `QApplication`、Qt 主窗口并启动事件循环。
- `src/pages/main_window_qt.py`：组装菜单、工作区、命令面板，处理主题、配置导入导出和窗口关闭。
- `src/pages/settings_dialog_qt.py`：编辑接收缓冲、历史数量、字体和自动重连间隔。
- `src/components/work_panel_qt.py`：管理单栏或双栏工作区、当前激活栏及隐藏副栏会话暂停。
- `src/components/work_column_qt.py`：管理单个工作栏的 Tab 创建、切换与关闭。
- `src/components/work_tab_qt.py`：管理一个串口会话的连接、批量接收显示、发送、循环发送、日志和自动重连。
- `src/components/*_settings_panel_qt.py`：分别编辑串口、接收和发送设置。
- `src/components/command_panel_qt.py`、`quick_commands_panel_qt.py`、`quick_command_dialog_qt.py`、`send_history_panel_qt.py`：提供快捷指令和发送历史功能。
- `src/utils/serial_manager_qt.py`：串行执行有超时保护的后台串口操作，将结果与有界待显示缓冲适配给 Qt。
- `src/utils/log_writer.py`：在后台线程批量写入有界日志队列，并回传打开或写入失败状态。
- `src/utils/theme_manager_qt.py`：加载主题并生成 Qt 样式表。
- `src/utils/config_manager.py`：读取、规范化、更新、导入导出并持久化运行目录中的 `config.json`。
- `src/utils/serial_manager.py`：以互斥操作封装 pyserial 打开、关闭、收发、按会话隔离的接收线程和断线检测。
- `src/utils/hex_utils.py`：提供 HEX 数据格式校验。
- `src/utils/receive_data_utils.py`：提供跨批次文本增量解码、接收格式化与日志模式时间戳拼接。
- `src/utils/send_data_utils.py`：统一发送文本的 CRLF 换行、HEX 转换、HEX 解析与编码选择。
- `scripts/release_gitee.py`：读取 `.gitee` 与用户目录令牌，推送全部本地分支和标签到 Gitee，创建或补齐 Release 并上传 ZIP 发布包。
- `VERSION`：保存当前版本号；版本生成和发布包脚本均从此文件读取版本。
- `tests/test_receive_and_send_data.py`：覆盖接收解码、日志时间戳和 TEXT/HEX 转换。
- `tests/test_config_manager.py`、`tests/test_log_writer.py`：覆盖配置持久化与日志写入。
- `tests/test_serial_manager.py`：覆盖串口操作超时和接收会话隔离。
- `tests/test_work_tab_behavior.py`、`tests/test_work_panel_and_commands.py`：覆盖 Qt 工作页、工作区与快捷指令关键行为。

## 数据模型

配置由 `ConfigManager` 以 JSON 形式保存至 EXE 运行目录（开发模式为项目根目录）的 `config.json`，主要结构如下：

```text
config
├── last_port_main / last_port_secondary / last_log_directory
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
2. `SerialManagerQt` 在后台执行串口打开、关闭、发送和接收；底层接收线程持有独立的串口引用、会话代次和停止事件，关闭或超时后不会读取新会话串口。接收数据进入有最大字节数限制的队列，并在串口会话切换时清空未显示的旧数据。
3. `WorkTab` 每 25ms 最多消费 256 KiB 数据；接收工具按编码增量解码跨批次的多字节字符、保留有效空白字符与跨包行结束符、过滤真正的空行并处理日志时间戳，随后批量写入 `QPlainTextEdit`；接收区禁用自动换行并限制最大行数。日志模式对持续超过 100ms 的连续数据插入换行和新时间戳。RX 统计包含显示缓冲丢弃的字节；日志写入缓冲溢出或当前日志会话的后台打开、写入失败时，接收区会显示原因并停止保存日志。
4. 用户通过发送框或快捷指令发送数据时，发送工具将 TEXT 编辑器与快捷指令换行规范化为内部 `\r\n`；每个串口的 `send_settings.line_ending` 可选 `CR`、`LF` 或 `CRLF`，仅将用户主动输入的每一个逻辑换行转换为指定字节，不会在发送末尾自动追加换行。该规则也用于 TEXT/HEX 相互转换；HEX 模式直接发送时不改写字节，HEX 转 TEXT 后恢复为内部 `\r\n`。成功发送的数据写入发送历史。
5. 日志文件由后台日志写入器保持打开直到会话清理，避免在接收路径执行文件 I/O；每次打开使用独立会话代次，旧文件关闭失败不会影响新日志。清理时写入器有界等待已入队内容写入、刷新和关闭，超过 1 秒会在关闭 Tab 或退出前提示用户。切换串口时关闭当前日志文件，避免将新会话数据写入旧路径。选择日志文件后仅保存其目录，下一次保存默认打开该目录。串口打开、关闭和发送均在后台串行执行，并受 1 秒操作超时保护；关闭或发送失败、超时时界面显示错误。超时打开的晚到结果会被关闭，不会覆盖当前会话，且原打开或接收线程结束前会拒绝新的打开请求。用户主动关闭串口会取消已排队的自动重连。

### 配置与主题

1. 用户调整界面、串口、收发、快捷指令或历史数据。
2. `ConfigManager` 在启动加载和导入 JSON 时将缺失、类型错误或不合法的字段恢复为默认值（主题仅允许 `light`、`dark`），丢弃未知结构并按历史上限裁剪发送历史；深层或损坏 JSON 按无效配置处理。配置先写入同目录临时文件并通过原子替换更新运行目录 `config.json`，导入写入失败时保留当前内存配置。
3. 用户选择主题时，主窗口加载 `themes/` 中对应 JSON 并重新应用 Qt 样式表。
4. 切换回单栏模式时，副栏保留其 Tab 和配置，但暂停串口、循环发送、自动重连与日志会话；重新进入双栏模式后可继续使用这些 Tab。
