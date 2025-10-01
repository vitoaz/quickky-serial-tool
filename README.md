# Quickky Serial Tool

一个功能强大的串口调试工具，基于Python + Tkinter开发。

## 功能特性

### 核心功能
- ✅ 多串口Tab支持，每个Tab独立配置
- ✅ 完整的串口参数配置（波特率、校验位、数据位、停止位、流控）
- ✅ TEXT/HEX双模式收发
- ✅ 自动保存配置（按串口号保存）
- ✅ 配置导入/导出
- ✅ 快捷指令管理
- ✅ 发送历史记录

### 串口设置
- 串口号自动刷新
- 波特率支持自定义输入
- 校验位：None、Even、Odd、Mark、Space
- 数据位：5、6、7、8
- 停止位：1、1.5、2
- 流控：None、Hardware、Software

### 接收设置
- 模式：TEXT、HEX
- 编码：UTF-8、ASCII（TEXT模式）
- 日志模式（附加时间戳）
- 保存日志到文件
- 自动重连
- 一键清除接收区

### 发送设置
- 模式：TEXT、HEX
- 循环发送（可设置周期ms）

### 命令面板
- 快捷指令：保存常用指令，双击发送
- 历史发送：记录所有发送历史，支持搜索

## 安装依赖

```bash
pip3 install -r requirements.txt
```

## 运行

### 开发调试

```bash
run.bat
```

或者：

```bash
python3 src/main/app.py
```

### 构建发布

```bash
build.bat
```

生成的可执行文件位于 `dist/QuickkySerialTool.exe`

## 项目结构

```
quickky-serial-tool/
├── src/                    # 源代码目录
│   ├── main/              # 主入口代码
│   │   └── app.py         # 启动代码
│   ├── utils/             # 工具类
│   │   ├── config_manager.py      # 配置管理
│   │   └── serial_manager.py      # 串口管理
│   ├── pages/             # 窗体页面
│   │   └── work_tab.py            # 工作Tab页面
│   └── components/        # 自定义控件
│       ├── serial_settings_panel.py    # 串口设置面板
│       ├── receive_settings_panel.py   # 接收设置面板
│       ├── send_settings_panel.py      # 发送设置面板
│       ├── quick_commands_panel.py     # 快捷指令面板
│       └── send_history_panel.py       # 历史发送面板
├── scripts/               # 脚本目录
│   └── generate_version.py        # 版本生成脚本
├── version.py             # 版本信息（自动生成）
├── run.bat               # 调试运行脚本
├── build.bat             # 构建脚本
├── requirements.txt      # 依赖列表
└── README.md            # 说明文档
```

## 配置文件

配置文件自动保存在程序同级目录下的 `config.json`，包含：

- 上次使用的串口
- 每个串口的独立配置（串口设置、接收设置、发送设置）
- 快捷指令列表
- 发送历史记录

### 配置文件格式

```json
{
  "last_port": "COM3",
  "port_configs": {
    "COM3": {
      "serial_settings": {
        "baudrate": 115200,
        "parity": "None",
        "bytesize": 8,
        "stopbits": 1,
        "flow_control": "None"
      },
      "receive_settings": {
        "mode": "TEXT",
        "encoding": "UTF-8",
        "log_mode": false,
        "save_log": false,
        "auto_reconnect": false
      },
      "send_settings": {
        "mode": "TEXT",
        "loop_send": false,
        "loop_period_ms": 1000
      }
    }
  },
  "quick_commands": [],
  "send_history": []
}
```

## 使用说明

### 1. 基本使用

1. 从串口号下拉框选择串口（下拉时自动刷新可用串口）
2. 配置串口参数（波特率、校验位等）
3. 点击"打开串口"按钮
4. 在发送区输入数据，点击"发送"按钮

### 2. 配置切换

- 切换串口号时，自动加载该串口保存的配置
- 修改任何配置后，自动保存到当前串口

### 3. 多Tab工作

- 点击工作面板上方的"+"按钮创建新Tab
- 每个Tab独立配置和工作

### 4. 快捷指令

1. 在命令面板切换到"快捷指令"Tab
2. 点击"添加"按钮添加常用指令
3. 双击指令即可发送

### 5. 历史发送

1. 在命令面板切换到"历史发送"Tab
2. 所有发送的数据自动记录
3. 支持搜索过滤
4. 双击历史记录可重新填充到发送区

### 6. 配置导入导出

- 菜单栏 -> 文件 -> 导出配置：将当前配置导出为JSON文件
- 菜单栏 -> 文件 -> 导入配置：从JSON文件导入配置

## 技术栈

- **Python 3.x**: 主开发语言
- **Tkinter**: GUI界面框架
- **pyserial**: 串口通信库
- **PyInstaller**: 打包工具

## 开发者信息

- **作者**: Aaz
- **邮箱**: vitoyuz@foxmail.com
- **版本**: 1.0.0

## 许可证

MIT License

