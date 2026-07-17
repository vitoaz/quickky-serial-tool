# Agent 开发约束

## 项目简述

QSerial（Quickky Serial Tool）是一个基于 Python 的 Windows 桌面串口调试工具，当前默认使用 PySide6 + Qt Widgets 图形界面。它用于配置串口参数、收发文本或十六进制数据，并管理快捷指令、发送历史、主题及本地配置。项目面向需要进行串口通信调试的开发和测试人员。本项目采用 Agent 驱动开发方式，Agent 必须以设计文档和当前代码为依据实施改动。

## 核心逻辑

1. 应用入口创建 PySide6 Qt 主窗口，并加载本地配置与主题。
2. 主窗口创建工作区和命令面板，工作区可切换单栏或双栏模式并管理多个 Tab。
3. 每个工作 Tab 读取串口、接收和发送设置，通过 `SerialManagerQt` 打开或关闭对应串口。
4. `SerialManager` 在后台线程接收串口数据，`SerialManagerQt` 将数据放入有界队列；工作 Tab 定时批量写入接收区，发送时按 TEXT 或 HEX 模式转换后写入串口。
5. 配置变更、快捷指令和发送历史由 `ConfigManager` 保存到运行目录的 `config.json`。

## 模块说明

- `src/main/`：提供 PySide6 应用启动入口，默认运行脚本使用该入口。
- `src/pages/`：实现 Qt 主窗口和设置对话框。
- `src/components/`：实现 Qt 工作区、串口设置、数据收发、快捷指令及发送历史等界面组件。
- `src/utils/`：提供串口通信、Qt 接收与日志写入适配、配置持久化、主题、HEX 转换和辅助功能。
- `themes/`：存放界面主题 JSON 配置。
- `scripts/`：存放版本信息生成、发布许可证和 PyInstaller 裁剪钩子。

## 项目目录说明

- `src/`：应用源代码目录。
- `src/main/`：应用启动入口目录。
- `src/pages/`：窗口与对话框页面目录。
- `src/components/`：可复用界面组件目录。
- `src/utils/`：串口、配置、主题及辅助工具目录。
- `themes/`：主题配置目录。
- `scripts/`：构建辅助脚本目录。
- `licenses/`：Qt/PySide6 发布许可证与第三方声明目录。
- `docs/design/`：项目设计文档目录。
- `README.md`：面向开发者的项目说明。
- `AGENTS.md`：Agent 开发约束文件。

## 唯一事实来源

- `docs/design/` 下的设计文档是项目结构与设计的唯一事实来源（SSOT）。
- `docs/design/PROJECT_DESIGN.md` 是核心设计文档。
- `AGENTS.md` 只保留项目上下文摘要和 Agent 行为规则。
- 如果 `AGENTS.md` 与 `PROJECT_DESIGN.md` 不一致，以 `PROJECT_DESIGN.md` 为准。
- Agent 必须优先阅读 `PROJECT_DESIGN.md`，再进行代码修改。
- 不允许发明未在设计文档或代码中出现的结构。
- 不允许引入未定义的模块、目录、技术栈或抽象层。
- 必须保持实现与设计文档一致。

@docs/design/PROJECT_DESIGN.md

## 开发行为规则

- 修改代码前，先理解 `docs/design/PROJECT_DESIGN.md`。
- 修改代码前，先阅读本文件中的项目简述、核心逻辑、模块说明和目录说明。
- 修改结构、模块职责、核心流程、数据模型时，必须同步更新 `docs/design/`。
- 不允许只改代码不改设计文档。
- 不允许只改设计文档但代码长期不一致。
- 如果代码与设计文档不一致，优先修正设计文档，再进行代码调整。
- 保持改动最小化。
- 不做无关重构。
- 不引入未要求的新依赖。
- 不新增无业务意义的抽象。
- git 的 commit message 始终使用中文，并必须包含 Conventional Commits 类型标签，例如 `feat:`、`fix:`、`docs:`、`refactor:`、`test:`、`chore:`。

## 文档更新规则

- 任何结构或逻辑变更，必须同步更新 `docs/design/PROJECT_DESIGN.md`。
- 如果 `AGENTS.md` 中的项目简述、核心逻辑、模块说明、目录说明受到影响，也必须同步更新 `AGENTS.md`。
- `PROJECT_DESIGN.md` 必须始终反映当前项目真实结构。
- `AGENTS.md` 必须保持与 `PROJECT_DESIGN.md` 的摘要一致。
- 文档只记录当前状态，不记录历史、不写规划、不写 TODO。
- 如果新增、删除、调整模块，必须同步更新 `PROJECT_DESIGN.md` 的“模块划分”章节。
- 如果新增或调整核心数据结构，必须同步更新 `PROJECT_DESIGN.md` 的“数据模型”章节。
- 如果新增或调整核心流程，必须同步更新 `PROJECT_DESIGN.md` 的“关键流程”章节。

## 禁止行为

- 禁止无需求重构。
- 禁止新增未定义模块。
- 禁止引入未确认依赖。
- 禁止为了兼容未来场景提前设计扩展点。
- 禁止在没有同步设计文档的情况下修改模块结构。
- 禁止把 `PROJECT_DESIGN.md` 中不存在的设计当成已确认事实。
- 禁止引入与当前需求无关的抽象层、封装层或通用框架。
