# QSerial 主题配置说明

## 主题文件格式

主题配置文件使用JSON格式，包含以下结构：

```json
{
  "name": "主题名称",
  "description": "主题描述",
  "colors": {
    "background": "#FFFFFF",
    "foreground": "#000000",
    "text_bg": "#FFFFFF",
    "text_fg": "#000000",
    "button_bg": "#F0F0F0",
    "button_fg": "#000000",
    "frame_bg": "#F5F5F5",
    "labelframe_bg": "#EFEFEF",
    "entry_bg": "#FFFFFF",
    "entry_fg": "#000000",
    "selectbackground": "#0078D7",
    "selectforeground": "#FFFFFF",
    "border": "#D0D0D0",
    "scrollbar_bg": "#F0F0F0",
    "scrollbar_fg": "#C0C0C0",
    "terminal_bg": "#FFFFFF",
    "terminal_fg": "#000000",
    "active_tab": "#E0E0E0",
    "inactive_tab": "#F5F5F5"
  }
}
```

## 颜色说明

- `background`: 主窗口背景色
- `foreground`: 主窗口前景色（文字颜色）
- `text_bg`: 文本框背景色
- `text_fg`: 文本框前景色
- `button_bg`: 按钮背景色
- `button_fg`: 按钮前景色
- `frame_bg`: 框架背景色
- `labelframe_bg`: 标签框架背景色
- `entry_bg`: 输入框背景色
- `entry_fg`: 输入框前景色
- `selectbackground`: 选中文本的背景色
- `selectforeground`: 选中文本的前景色
- `border`: 边框颜色
- `scrollbar_bg`: 滚动条背景色
- `scrollbar_fg`: 滚动条前景色
- `terminal_bg`: 终端背景色
- `terminal_fg`: 终端前景色
- `active_tab`: 激活标签页颜色
- `inactive_tab`: 未激活标签页颜色

## 创建自定义主题

1. 复制 `light.json` 或 `dark.json` 为新文件，如 `mytheme.json`
2. 修改 `name` 和 `description` 字段
3. 根据需要修改 `colors` 中的颜色值（使用十六进制格式，如 `#RRGGBB`）
4. 保存文件
5. 重启程序，在 **视图 -> 主题** 菜单中选择新主题

## 内置主题

### Light（明亮主题）
适合白天使用，背景为白色，文字为黑色。

### Dark（暗黑主题）
适合夜间使用，背景为深色，文字为浅色。参考VSCode的Dark主题设计。

## 颜色推荐工具

- [Coolors](https://coolors.co/) - 配色方案生成器
- [Adobe Color](https://color.adobe.com/) - Adobe 配色工具
- [Material Design Colors](https://materialui.co/colors) - Material Design 配色参考

