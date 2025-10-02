# 版本发布流程

本文档描述QSerial项目的版本发布完整流程。

## 📋 发布前准备

在开始版本发布前，确保：
1. 所有功能已开发完成并测试通过
2. 代码已提交到develop分支
3. 工作区是干净的状态（无未提交的修改）

## 🚀 发布流程

### 步骤1: 输入目标版本号

用户提供要发布的版本号，例如：`1.0.1`

版本号规则遵循语义化版本（Semantic Versioning）：
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 步骤2: 检查版本号是否需要更新

读取 `scripts/generate_version.py` 中的当前版本号，与目标版本号对比：

- **版本号一致**: 跳过修改和提交，直接进入构建步骤
- **版本号不一致**: 需要修改版本号

#### 2.1 修改版本号（如需要）

编辑 `scripts/generate_version.py` 文件，更新版本号：

```python
VERSION = "x.y.z"  # 修改为新版本号
```

### 步骤3: 构建项目

执行构建脚本：

```bash
cmd /c build.bat
```

构建脚本会自动：
1. 生成version.py文件
2. 生成图标文件
3. 检查并安装依赖
4. 清理旧的构建文件
5. 使用PyInstaller打包应用
6. 复制themes资源目录
7. 生成发布包（zip文件）

构建产物位于：
- `dist/QSerial.exe` - 可执行文件
- `dist/QSerial_vx.y.z.zip` - 发布包
- `dist/themes/` - 主题资源目录

### 步骤4: 提交版本号修改（如有修改）

**注意**: 只有在步骤2中修改了版本号时才执行此步骤，否则跳过。

#### 4.1 设置UTF-8编码

```bash
chcp 65001
```

#### 4.2 检查工作区状态

```bash
git status
```

#### 4.3 查看修改内容

```bash
git diff scripts/generate_version.py
```

#### 4.4 添加到暂存区

```bash
git add scripts/generate_version.py
```

#### 4.5 创建提交信息文件

创建临时文件 `commit_msg.txt`，内容：

```
chore: 升级版本号至x.y.z

- 更新generate_version.py中的版本号
- 准备发布vx.y.z版本
```

#### 4.6 提交

```bash
git commit -F commit_msg.txt
```

#### 4.7 删除临时文件

```bash
del commit_msg.txt
```

#### 4.8 验证提交

```bash
git log -1
```

### 步骤5: 创建版本标签

#### 5.1 创建带注释的标签

```bash
git tag -a vx.y.z -m "Release vx.y.z"
```

#### 5.2 验证标签

```bash
git tag -l vx.y.z
```

### 步骤6: 生成发布说明

#### 6.1 查看版本间的提交记录

```bash
git log v上一版本..vx.y.z --pretty=format:"%s%n%b" --reverse
```

#### 6.2 创建release_notes.md

在 `dist/release_notes.md` 创建发布说明文档，包含：

- 版本信息（发布日期、版本号、构建时间）
- 更新内容（仅包含程序功能改进）

**重要要求**：
- 只需要 `## ✨ 更新内容` 部分
- 使用数字列表简要说明程序功能（如 1.2.3.4.5...）
- **非程序功能的代码改动不需要提及**（如重构、架构调整、文档更新等）

**模板示例**：

```markdown
# QSerial vx.y.z Release Notes

**发布日期**: YYYY年MM月DD日  
**版本号**: vx.y.z  
**构建时间**: YYYY-MM-DD HH:MM:SS

## ✨ 更新内容

1. 新增功能描述1
2. 优化功能描述2
3. 修复问题描述3
4. 增强功能描述4
5. 改进功能描述5
```

### 步骤7: 合并到master分支

#### 7.1 切换到master分支

```bash
git checkout master
```

#### 7.2 拉取最新代码

```bash
git pull origin master
```

#### 7.3 合并develop分支

```bash
git merge develop
```

#### 7.4 切换回develop分支

```bash
git checkout develop
```

### 步骤8: 推送到远程仓库

```bash
# 推送develop分支（如果有版本号提交）
git push origin develop

# 推送master分支
git push origin master

# 推送标签
git push origin vx.y.z
```

## 📝 注意事项

1. **版本号检查**: 自动检查当前版本号，只有不一致时才修改和提交
2. **版本号规范**: 严格遵循语义化版本规范
3. **提交信息**: 使用文件方式提交避免中文乱码
4. **标签命名**: 使用 `vx.y.z` 格式（带v前缀）
5. **发布说明**: 仅包含程序功能改进，使用数字列表简要说明，忽略代码重构等非功能性改动
6. **构建验证**: 构建后测试exe文件是否正常运行
7. **分支管理**: 发布后必须合并到master分支

## 🔍 发布后检查

1. 在本地运行 `dist/QSerial.exe` 验证功能
2. 检查主题切换是否正常
3. 验证版本号显示是否正确
4. 测试主要功能是否工作正常
5. 确认master和develop分支都已更新


