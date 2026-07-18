# Python 开发规范

## 技术约束

- 使用 Python 3、PySide6 + Qt Widgets、pyserial 和 PyInstaller。
- 使用 PySide6 + Qt Widgets，不引入其他 GUI 框架实现。
- 不新增未确认依赖；需要新增依赖时，同步更新 `requirements.txt`、`README.md` 和设计文档。

## 代码约定

- Python 文件使用 UTF-8 编码，类名使用 `CamelCase`，函数、变量使用 `snake_case`，常量使用 `UPPER_CASE`。
- 导入顺序为标准库、第三方库、本地模块，各组之间保留空行。
- 为公开类、复杂逻辑和非直观实现补充简洁文档字符串或注释。
- 捕获具体异常，避免裸 `except`；错误信息应能说明失败原因。
- 保持界面线程不执行串口阻塞读取或日志文件 I/O。高频接收显示继续使用现有的有界队列与批量写入机制。

## 一致性约束

- 界面实现以 PySide6 版本和 `docs/design/PROJECT_DESIGN.md` 为准。
- 变更配置、串口收发或界面核心行为时，必须同步更新设计文档与受影响的用户说明。
