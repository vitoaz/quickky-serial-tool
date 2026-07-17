# 版本发布流程

本指南用于从 `develop` 发布 QSerial 的 Windows 版本。发布、合并、打标签和推送均需用户明确授权后执行。

## 发布前检查

1. 确认当前位于 `develop` 分支，且代码已完成测试。
2. 执行 `git status --short`，确保工作区没有无关修改。
3. 确认目标版本符合语义化版本格式 `主版本号.次版本号.修订号`。
4. 确认 `README.md`、`AGENTS.md` 与 `docs/design/PROJECT_DESIGN.md` 已反映本次功能或结构变更。

## 更新版本与构建

1. 在 `scripts/generate_version.py` 中将 `VERSION` 更新为目标版本。
2. 执行：

   ```powershell
   .\build.bat
   ```

3. 启动 `dist/QSerial.exe`，至少验证应用可启动、版本号正确、主题可加载及主要串口收发流程可用。
4. 确认发布目录包含 `QSerial.exe`、`LICENSE` 和 `licenses/` 的许可证文件。

## 提交、合并和标签

1. 检查版本改动和工作区状态后，使用中文 Conventional Commits 提交版本号，例如：

   ```text
   chore: 升级版本号至2.0.1
   ```

2. 推送 `develop`。
3. 切换到 `master`，拉取远程最新状态，并使用快进合并将 `develop` 合入：

   ```powershell
   git switch master
   git pull --ff-only origin master
   git merge --ff-only develop
   ```

   若无法快进合并，停止操作并先确认分支差异与合并方案。

4. 在 `master` 创建带注释标签，标签格式为 `v<版本号>`，例如：

   ```powershell
   git tag -a v2.0.1 -m "发布 v2.0.1"
   ```

5. 推送 `master` 和标签，然后切回 `develop`：

   ```powershell
   git push origin master
   git push origin v2.0.1
   git switch develop
   ```

## 发布约束

- 只基于当前实际构建产物发布；`build.bat` 不自动生成 ZIP、发布说明或 GitHub Release。
- 需要 ZIP、发布说明或远程 Release 时，必须由用户单独提出需求，并基于本次实际功能改动生成。
- 发布完成后，确认 `master`、`develop` 和版本标签均已推送。
