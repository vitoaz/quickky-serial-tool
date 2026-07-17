# QSerial 项目设计文档

## 项目概述

QSerial（Quickky Serial Tool）是一个 Python 桌面串口调试工具。默认启动入口为 wxPython 界面，用户可在多个工作 Tab 中配置串口并收发 TEXT 或 HEX 数据。应用将串口配置、界面设置、快捷指令和发送历史保存至本地 `config.json`。

## 技术栈

- Python 3
- wxPython 4.2 及其 `wx.stc`、AGW 控件
- pyserial
- PyInstaller（构建发布）

## 项目结构

```text
src/
  main/          应用启动入口
  pages/         主窗口与设置对话框
  components/    工作区及各类界面组件
  utils/         串口、配置、主题和辅助工具
themes/          Light、Dark 主题配置
scripts/         版本信息生成脚本
docs/design/     设计文档
```

`src/main/app_wx.py` 是 `run.bat` 使用的 wxPython 启动入口。`src/main/app.py` 及同名的非 `_wx` 界面模块为仓库中保留的 Tkinter 实现。

## 模块划分

- `src/main/app_wx.py`：创建 wxPython 应用、主窗口并启动事件循环。
- `src/pages/main_window_wx.py`：组装菜单、工作区、命令面板，处理主题、配置导入导出与窗口关闭。
- `src/pages/settings_dialog_wx.py`：编辑全局设置。
- `src/components/work_panel_wx.py`：管理主栏和副栏的显示及激活状态。
- `src/components/work_column_wx.py`：管理单个工作栏的 Tab 创建、切换与关闭。
- `src/components/work_tab_wx.py`：管理一个串口会话的连接、接收显示、发送、循环发送、日志和自动重连。
- `src/components/*_settings_panel_wx.py`：分别编辑串口、接收和发送设置。
- `src/components/command_panel_wx.py`：承载快捷指令与发送历史面板。
- `src/components/quick_commands_panel_wx.py`：管理并发送快捷指令。
- `src/components/send_history_panel_wx.py`：显示、筛选和重发发送历史。
- `src/utils/serial_manager.py`：封装 pyserial 串口打开、关闭、收发、接收线程和断线检测。
- `src/utils/config_manager.py`：读取、更新、导入导出并持久化 `config.json`。
- `src/utils/theme_manager_wx.py` 与 `src/utils/custom_controls_wx.py`：加载主题并提供带主题的 wxPython 控件。
- `src/utils/hex_utils.py`：提供 HEX 数据转换与校验。
- 无 `_wx` 后缀的 `src/pages/`、`src/components/` 与部分 `src/utils/` 模块：为 Tkinter 实现提供对应界面与辅助功能。

## 数据模型

配置由 `ConfigManager` 以 JSON 形式保存至根目录 `config.json`，主要结构如下：

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

`serial_settings` 保存波特率、校验位、数据位、停止位和流控；`receive_settings` 保存接收模式、编码、日志、保存日志、自动重连和自动滚屏设置；`send_settings` 保存发送模式、循环发送状态和发送周期。

## 关键流程

### 应用启动

1. `app_wx.py` 创建 `wx.App` 与 `MainWindow`。
2. `MainWindow` 创建 `ConfigManager` 和主题管理器，并按配置创建菜单、工作区和命令面板。
3. 应用当前主题，显示窗口并进入 wxPython 事件循环。

### 串口收发

1. 用户在工作 Tab 中选择串口和通信参数，触发连接操作。
2. `WorkTab` 调用 `SerialManager.open()` 打开串口并启动接收线程。
3. 接收线程通过回调将数据放入工作 Tab 的队列，界面定时将队列内容写入接收区。
4. 用户发送数据时，工作 Tab 按 TEXT 或 HEX 设置转换内容并调用串口写入。
5. 成功发送的数据写入发送历史；相关设置通过 `ConfigManager` 保存。

### 配置与主题

1. 用户调整界面、串口、收发、快捷指令或历史数据。
2. 相应组件调用 `ConfigManager` 更新内存中的配置并写入 `config.json`。
3. 用户选择主题时，主窗口加载 `themes/` 中对应 JSON 并重新应用控件样式。
