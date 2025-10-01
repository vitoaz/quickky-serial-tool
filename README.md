# QSerial (Quickky Serial Tool)

一个功能强大的串口调试工具，基于Python + Tkinter开发。

## 🚀 核心特性

### 🔥 双栏模式
- **主栏 + 副栏**：同时操作两个串口，支持独立配置
- **一键切换**：点击任意区域激活对应栏目
- **独立配置**：每个栏目保存独立的串口设置和历史记录

### 📑 多Tab工作区
- **无限Tab**：支持创建多个工作Tab，每个Tab独立工作
- **独立配置**：每个Tab保存独立的串口参数和设置
- **快速切换**：Tab之间快速切换，提高工作效率

### 💡 智能功能
- **TEXT/HEX双模式**：支持文本和十六进制数据收发
- **自动保存配置**：按串口号自动保存和加载配置
- **配置导入导出**：支持配置文件的导入和导出
- **快捷指令管理**：保存常用指令，一键发送
- **发送历史记录**：自动记录发送历史，支持搜索和重发

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

生成的可执行文件位于 `dist/QSerial.exe`，同时生成发布包 `dist/QSerial_v1.0.0.zip`

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


## 技术栈

- **Python 3.x**: 主开发语言
- **Tkinter**: GUI界面框架
- **pyserial**: 串口通信库
- **PyInstaller**: 打包工具

## 开发者信息

- **作者**: Aaz
- **邮箱**: vitoyuz@foxmail.com

## 许可证

MIT License

