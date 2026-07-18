# 版本发布 SOP

QSerial 发布分为两个独立 SOP。第一阶段只在本地准备并等待用户确认；第二阶段仅在用户明确要求“提交”后执行提交、分支、标签以及 GitHub、Gitee Release 操作。

## 前置条件

- 版本使用语义化版本格式：稳定版为 `主版本号.次版本号.修订号`，日常开发版为 `主版本号.次版本号.修订号-snapshot`，测试候选版为 `主版本号.次版本号.修订号-rc.N`。
- 发布前位于 `develop` 分支，且没有无关修改。
- 执行第二阶段前，GitHub CLI 已登录并可通过 `gh auth status` 校验。
- 仓库根目录 `.gitee` 已配置 Gitee `owner`、`repo`、`remote` 和 SSH `url`，且用户目录 `~/.gitee/TOKEN` 已保存目标仓库 Release 写入令牌；令牌不得提交到仓库或输出到日志。
- Gitee 发布脚本使用 SSH `StrictHostKeyChecking=no` 忽略 Gitee 主机密钥校验；执行环境仍须具备 `git@gitee.com` 的 SSH 认证权限。
- `README.md`、`AGENTS.md` 与 `docs/design/PROJECT_DESIGN.md` 已反映本次功能或结构变更。

## SOP 1：预发布准备与确认

此阶段不执行 Git 提交、合并、打标签、推送或创建 GitHub Release。

1. 在根目录 `VERSION` 文件中更新目标版本号；该文件是项目版本号的唯一来源。
2. 执行 `build.bat`，生成并验证 `dist/QSerial.exe` 和 `dist/QSerial_v<版本号>.zip`。ZIP 仅包含 EXE、`LICENSE` 与 `licenses/`，不包含 `config.json` 和发布说明。
3. Agent 使用 `git log <上一次正式发布标签>..develop` 和对应代码改动读取实际功能变化，手动生成 `dist/release_notes.md` 草稿。无论本次为正式发布还是 RC 预发布，发布说明始终以最近一次正式版为基线，不以先前 RC 标签为基线。该文件仅作为 GitHub 与 Gitee Release 正文，不打入 ZIP，也不提交到仓库。
4. 发布说明必须使用简洁的数字列表，只记录用户可感知的功能新增、优化或修复。例如：

   ```markdown
   # QSerial v2.0.1

   ## 更新内容

   1. 优化高频串口数据接收时的界面流畅度。
   2. 修复串口切换后配置未正确恢复的问题。
   ```

   不记录重构、构建脚本、文档调整、内部模块名、TODO 或原始提交信息。
5. Agent 向用户展示版本号、ZIP 路径与大小、发布说明全文，以及拟创建的类型：正式发布或 RC 预发布。
6. 用户确认发布内容和类型。若选择 RC 预发布，Agent 必须再次明确询问“是否确认创建预发布版本”，得到肯定答复后才可进入第二阶段。
7. 用户确认后，仍须明确要求 Agent“提交”，才进入 SOP 2。

## 版本状态规则

| 场景 | 版本示例 | GitHub Release 类型 |
|---|---|---|
| 日常开发 | `2.0.2-snapshot` | 不创建 |
| 测试候选 | `2.0.2-rc.1` | 预发布 |
| 正式发布 | `2.0.2` | 正式发布 |
| 正式发布后 | `2.0.3-snapshot` | 不创建 |

- 正式发布后，`develop` 自动改为下一补丁 Snapshot 版本，避免后续开发沿用已发布版本号。
- 需要新增功能并改发次版本或主版本时，在下一次 SOP 1 将 Snapshot 版本调整为对应目标，例如从 `2.0.3-snapshot` 调整为 `2.1.0-snapshot`。
- RC 预发布完成后不自动修改版本号；后续继续开发或准备下一 RC 时，在下一次 SOP 1 按实际目标版本更新。

## SOP 2：提交与多平台 Release

仅在用户已确认发布内容、发布类型，并明确要求“提交”后执行。

1. 检查工作区，仅暂存本次版本发布相关改动；使用中文 Conventional Commits 提交版本号与必要文档更新。
2. 推送 `develop`：

   ```powershell
   git push origin develop
   ```

3. 切换到 `master`，拉取远程状态并快进合并 `develop`：

   ```powershell
   git switch master
   git pull --ff-only origin master
   git merge --ff-only develop
   ```

   无法快进合并时停止操作，向用户报告分支差异并等待确认。

4. 在 `master` 创建带注释标签 `v<版本号>`，并推送 `master` 与该标签：

   ```powershell
   git tag -a v2.0.1 -m "发布 v2.0.1"
   git push origin master
   git push origin v2.0.1
   ```

5. 使用 GitHub CLI 创建 Release，上传 ZIP，并以 `dist/release_notes.md` 作为正文：

   ```powershell
   gh release create v2.0.1 dist/QSerial_v2.0.1.zip --title "QSerial v2.0.1" --notes-file dist/release_notes.md
   ```

   正式发布与 RC 预发布使用相同流程；仅 RC 预发布追加 `--prerelease`。

6. 使用 `gh release view v<版本号>` 验证 GitHub Release、说明和附件。
7. 执行 Gitee 发布脚本。脚本会自动添加或校验 `gitee` 远程，推送全部本地分支和标签到 Gitee，确认 `v<版本号>` 标签到位后再继续；远程地址不一致或标签不可用时停止操作。
8. 脚本创建或补齐同名 Gitee Release，上传同一个 ZIP，并使用 `dist/release_notes.md` 作为正文。正式发布与 RC 预发布均同步到 Gitee；RC 预发布追加 `--prerelease`。

   ```powershell
   python3 scripts/release_gitee.py
   # RC 预发布示例：python3 scripts/release_gitee.py --prerelease
   ```

9. 在 Gitee Release 页面验证标签、标题、说明和 ZIP 附件，再切回 `develop`。
10. 根据发布类型更新根目录 `VERSION` 中的开发版本，并使用中文 Conventional Commits 单独提交和推送：

   - 正式发布 `2.0.2` 后，更新为 `2.0.3-snapshot`，提交信息为 `chore: 开启2.0.3开发`。
   - RC 预发布不自动更新版本号，也不创建额外版本提交。

## 发布约束

- `build.bat` 只生成本地 EXE 和 ZIP，不创建 GitHub Release。
- GitHub Release 必须在 `master` 与版本标签推送成功后创建。
- Gitee Release 必须由发布脚本完成全部本地分支和标签推送后创建，且标签、发布说明和 ZIP 必须与 GitHub Release 一致。
- Gitee 发布脚本运行时从 `.gitee` 读取仓库与 Git 远程配置、从 `~/.gitee/TOKEN` 读取令牌；脚本同步全部本地分支和标签后再创建 Release，令牌不被输出。
- 若 Release 创建失败，保留已推送的分支和标签，仅重试 Release 创建步骤；不得擅自重建标签或覆盖已发布版本。
- 自动开启下一开发版本属于正式发布 SOP 2 的收尾步骤，仅在用户已明确要求“提交”后执行。
