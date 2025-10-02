# Git 代码提交指令

当用户请求执行代码提交时，按照以下流程自动完成：

## 执行步骤

### 1. 检查工作区状态

首先使用 `git status` 检查当前工作区状态，确认有待提交的修改。

### 2. 查看修改内容

使用 `git diff` 查看已修改文件的具体改动内容，理解本次修改的范围和目的。

### 3. 分析修改类型

根据修改内容，确定提交类型（type）：

- **feat**: 新增功能或特性
- **fix**: 修复bug
- **refactor**: 代码重构（不改变功能）
- **style**: 代码格式调整、UI样式优化
- **docs**: 文档更新
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建/工具变动

### 4. 生成提交信息

根据修改内容自动生成简明扼要的提交信息，格式：

```
<type>: <简明描述>

[可选的详细说明]
- 改动点1
- 改动点2
```

### 5. 检查文档同步

如果代码修改涉及以下内容，必须更新相应文档：

- 新增功能 → 更新 [README.md](mdc:README.md) 和 [PROJECT_DESIGN.md](mdc:PROJECT_DESIGN.md)
- 修改用户界面 → 更新 [README.md](mdc:README.md)
- 变更配置方式 → 更新文档
- 修改使用方法 → 更新 [README.md](mdc:README.md)
- 更新依赖项 → 更新 [requirements.txt](mdc:requirements.txt)

### 6. 执行 git add

添加所有修改的文件到暂存区：

```bash
git add <file1> <file2> ...
```

### 7. 创建提交

**推荐方式：使用文件方式提交**

```bash
# 1. 创建并编辑临时提交信息文件 commit_msg.txt
# 2. 在文件中写入提交信息（格式如下）：
#    <type>: <简明描述>
#    
#    [可选的详细说明]
#    - 改动点1
#    - 改动点2

# 使用文件提交
git commit -F commit_msg.txt

# 删除临时文件
del commit_msg.txt
```

**备选方式：单行提交**

```bash
git commit -m "<type>: <简明描述>"
```

### 8. 验证提交

使用 `git log -1` 验证提交信息显示正常。

## Windows PowerShell 环境配置

### PowerShell UTF-8 编码设置

每次在 PowerShell 中使用 Git 前执行：

```bash
# 设置 PowerShell 使用 UTF-8 编码
chcp 65001
```

此设置确保中文提交信息正确显示，避免乱码问题。

## 注意事项

1. **中文编码处理**：在 PowerShell 中使用文件方式提交可避免中文乱码
2. **自动执行**：无需向用户确认每个步骤，直接执行完整流程
3. **错误处理**：如果某步骤失败，及时报告并停止流程
4. **简洁信息**：提交信息应简明扼要，突出核心改动

## 示例

```bash
# 检查状态
git status

# 查看改动
git diff

# 添加文件
git add src/components/custom_menubar.py src/main/app.py

# 创建提交信息文件 commit_msg.txt 并写入：
# feat: 实现自定义菜单栏组件
# 
# - 新增CustomMenuBar自定义菜单栏控件
# - 替换原生菜单为自定义菜单
# - 优化主题切换和样式应用

# 提交
git commit -F commit_msg.txt

# 删除临时文件
del commit_msg.txt

# 验证
git log -1
```
