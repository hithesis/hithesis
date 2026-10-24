# dev 下载与 QQ 更新通知

## 版本和发布记录

页面显示 `v3.2b-dev.1024`：版本号根据正式 Release、源码及开发发布历史计算，月日取北京时间的开发构建日期。
模板压缩包的文件名保持不变，解压目录带完整的显示版本，每份模板包含 `BUILD-INFO.json`。
同日多次成功构建由提交 SHA、完整日期和 CI 运行号组成的 `build_id` 区分；这是构建号，不是 Git tag。
只有正式版才打 tag、创建正式 Release 并上传 CTAN。开发版不创建 tag 或 GitHub prerelease，也不上传 CTAN。
CI 可以构建 CTAN/TDS 包做内容验证，但不会将它们作为开发版下载包发布，更不会调用 CTAN 上传。

`scripts/dev-release.py` 从 `\changes` 收集新条目，按本次 dev 发布日期写入：

- `dev.json`：当前可下载开发版及每个附件的 SHA256。
- `dev-history.json`：各次 dev 发布收录的增量变更及其发布日期。
- `DEV_CHANGELOG.md`：按发布日期归档的用户更新记录。

已有历史条目不重新标日期。相同版本、相同变更正文即使调整了源码日期，也不重复通知。
正式基准只使用 GitHub 上已发布的正式 Release 对应 tag，排除草稿、prerelease、开发版与裸 Git tag。
普通开发版取正式版的下一字母；遇到明确的破坏性变更后，进入下一小版本的 `a`。

| 正式版 | 普通开发版 | 有破坏性变更 |
|---|---|---|
| `v3.2a` | `v3.2b-dev.1025` | `v3.3a-dev.1025` |
| `v3.2b` | `v3.2c-dev.1025` | `v3.3a-dev.1025` |
| `v3.3a` | `v3.3b-dev.1025` | `v3.4a-dev.1025` |

每日发布不递增字母。在正式版仍为 `3.2` 系列时，开发版第二位最多为 `3`；再遇到破坏性变更也不会进入 `3.4`。
已有源码或开发发布记录若已到 `3.3c`，也不会退回 `3.3a`。超出上限的已有版本会报错，要求先核实正式 Release，不自动降级。
版本解析来自 `scripts/dev-version.py`；`build/dev-version-plan.json` 记录正式基准、上限和触发升级的提交。
源码中的 `\changes` 保留，历史正式版本记录不改写；开发者新增条目统一使用待发布日期：

```latex
% \changes{v3.2b}{0000/00/00}{修正英文内封长字段折行。}
```

默认分支 `master` 上的 `scheduled_dev.yml` 每日北京时间 08:00 派发 `dev` 发布流程，计算版本、填写待发布日期，生成版本/日期元信息提交并回写 `dev`。实际构建使用 `dev`，调度入口不修改正式模板版本。
版本变化时同步源码和六个运行文件的声明，只调整尚未发布条目的版本号；历史版本与日期保持不变。
`dev-date-stamp.json` 记录来源提交、元信息提交、版本计划和逐条替换，发布记录关联构建号与运行记录。
代码维护、文档等未写 `\changes` 的提交也会纳入下一次开发版，消息提供提交差异链接。

### 破坏性标记与 PR 校验

破坏性变更只指旧命令、参数、配置等原有用法失效或不再支持原功能。字号、间距、默认对齐、换行等纯外观变化不算；新增写法但旧用法仍有效也不算。本次关键词默认续行对齐的调整是兼容更新。

兼容性由维护者审核，程序不根据代码差异猜测。例如，将来若删除现有的 `\bicaption`，使旧调用无法使用，才应写成下面的形式（本次仍保留该命令）：

```text
feat(caption)!: remove legacy bicaption

BREAKING CHANGE: 不再提供旧 bicaption 命令，原有调用无法使用。
Impact: 仍使用旧双语题注命令的论文。
Migration: 按文档将旧调用改为 caption 的双语写法。
Validation: 填写实际执行的迁移与回归测试结果。
```

`!` 或 `BREAKING CHANGE:`（也支持 Conventional Commits 的 `BREAKING-CHANGE:`）均会触发升级。
扫描范围为正式 Release 至当前源码提交；因此已进入下一小版本后不会因重复标记再升一级。
GitHub 普通合并和 squash 合并会同时读取经合并 SHA 核实的 PR 正文，避免只在 PR 正文写标记时漏判，并保留迁移说明。

PR 标题使用 `feat:`、`fix(scope):`、`docs:` 等 Conventional Commits 格式。
PR 正文必须有一行 `Compatibility: compatible` 或 `Compatibility: breaking`，以及 `Validation:`。
破坏性 PR 还须填写 `BREAKING CHANGE:` 和 `Migration:`，声明与标记冲突会使检查失败。

工作流提供 **Compatibility declaration** 检查。仓库管理员应在 `dev`/`master` 的分支规则中将它设为 required status check，并要求审核；仅添加工作流不会自动开启禁止合并。
本地 Git hook 可以绕过，不作为主要约束。破坏性标记不会跳过测试，受影响的接口测试需随变更一起更新并审核。

### 每日详细更新说明

每日开发构建附带 `DEV_UPDATE.pdf` 和 `DEV_UPDATE.md`，面向论文使用者说明实际功能与修复、哪些论文受影响、旧写法怎么改，并给出可直接使用的示例。
08:00 任务自动比对上次发布与当前源码，用 DeepSeek V4.1 Flash 写稿，再由固定程序编译 PDF。API 使用官方地址 `https://api.deepseek.com/chat/completions`，模型 ID 为 `deepseek-flash`。
人工维护的 `release-notes/notes.json`、`\changes` 与提交 `Release-Notes:` 是输入依据；模型同时读取有上限的模板差异和实际编译的样例对照图。
PDF 不放 CI 规则、版本算法、测试数量、提交 SHA 或原始提交日志；不自动编造影响范围或迁移方法。
PDF 用现有 TeX Live/XeLaTeX 和 Fandol 字体编译，并原样标注 **此预览由 AI 比对生成**。
PDF 和 Markdown 进入 `dev.json` 的文件摘要及 `SHA256SUMS`，按构建号保存到 `gh-pages` 的 `dev-builds/<build_id>/`，通知消息附对应 PDF 的公开直链。
ZIP 存放在 `dev-downloads/`，发布步骤先提交附件，取得该提交 SHA，再将 ZIP 下载地址绑定到这个 Git 提交的原始文件地址。随后提交下载指针并一次性推送 `gh-pages`，不创建标签。
站点只需保存一份当前 ZIP 文件，Git 提交历史保留旧构建的原始内容；打开旧构建的下载地址仍得到原来那一版，不依赖可变分支地址。每次 PDF 和说明分别保留，不覆盖已有构建目录。

**没有 PDF 不许发布。** 准备附件和实际发布时分别校验 PDF 可解析、页数正常、含本次版本/日期/AI 标注、内嵌源码与构建标识相符，且 SHA256 匹配。bot 发群前再次下载并校验公开 PDF；失败不发送、不更新通知状态。

### AI 的输入与权限限制

- 正常只做一次非流式稿件调用；JSON 或内容校验失败时，最多带校验结果追加一次纠错，两次都没有 tools、命令执行、仓库写入或发布能力。两次均不合格则停止，不无限重试。
- 文本输入最多 120 KB；仅包含公开模板源码及示例的差异、人工说明和限量提交正文，不读取 `.env`、密钥或私人文件。
- 最多提供两张受控对照图；图像来自上次版本和本次版本真实编译的同一示例。关键词使用并排图，英文内封使用上下局部图；不让模型生成效果图。
- 每次输出上限 7000 tokens，累计最多两次；包含纠错上下文的文本也须在 120 KB 内。必须匹配固定 JSON 结构，每节引用已登记证据，代码和图片只能引用已有 ID。有变化的对照不能漏掉，未在人工说明中确认的命令/选项不能加入稿件。只规范化等号空白和单值花括号，不放行新的名称或取值。
- 模型输出按普通文本转义，不作为 TeX 程序执行。API 密钥不会传入 TeX 子进程；请求失败、输出截断、结构错误、越权引用或 PDF 校验失败都阻止发布。
- `DEV_AI_DRAFT.json` 记录模型、输入摘要、用量与稿件，便于追查；不包含 API 密钥。
- 不合格原稿和原因只保存在 Actions 调试附件的 `report-build/AI_REJECTED.json` 中，不进入下载站；发布门槛始终不变。

## GitHub 上启用开发版下载

需要先将下载页改动发布到 `gh-pages`，再启用开发版附件发布。

1. 在仓库 Actions Secrets 配置 `DEV_REPORT_API_KEY`，填写 DeepSeek API 密钥；密钥只交给每日发布任务。模型固定为 `deepseek-flash`，普通 PR 测试不调用付费接口。
   发布使用 Actions 自带的短期仓库令牌 `GITHUB_TOKEN`，job 显式授予 Contents 和 Pages 写权限。无需创建个人 `DEV_DOWNLOADS_TOKEN`，不需要组织 PAT 审批或 Workflows 写权限。
2. 仓库 Pages 使用 `gh-pages` 根目录作为发布源，保留现有域名设置。
3. `dev` 提交触发测试；Actions 定时入口每日北京时间 08:00 请求开发版发布，现有测试、示例编译及打包全部成功后才发布附件。平台可能排队延迟，群通知在构建和 PDF 就绪后发送。
   手动发布时，`workflow_dispatch` 选择 `dev`，设置 `publish_only=true`、`notify_only=false`。
4. 未配置 DeepSeek 密钥或仓库不允许令牌写入时，发布会失败并保留调试附件，不会降级为纯文字发布。

只检查下载站写权限、不编译或调用 AI 时，可在 `dev` 运行工作流并勾选 `preflight_only`，也可执行：

```sh
gh workflow run test_dev.yml --repo hithesis/hithesis --ref dev -f preflight_only=true
```

发布程序在 `gh-pages` 提交完整附件快照，再提交三个下载数据文件和构建目录索引，最后推送；不覆盖首页、CSS、脚本或 `editor/`。遇到并发页面更新采用合并，不能 rebase 附件快照，否则会改变已绑定的下载提交 SHA。
`GITHUB_TOKEN` 推送本身不会触发分支式 Pages 部署，因此发布程序会显式调用 Pages build API，并等待公开 PDF 可下载且校验通过。服务器的定时派发凭据 `DEV_PUBLISH_TOKEN` 与此仓库内发布令牌职责不同。
`gh-pages` 不再触发模板编译工作流。
开发版只更新下载站，不创建 Release 或 tag；正式版的最新 Release 和 CTAN 流程独立。

## Ubuntu / Debian 部署机器人

服务器需安装 Git、Docker Engine 和 Docker Compose 插件。先按 Docker 对应发行版的安装文档安装，确认：

```sh
docker version
docker compose version
```

以下以 `/opt/hithesis-notify` 为部署目录。执行账号需要该目录写权限和 Docker 使用权限。

```sh
git clone --branch dev https://github.com/hithesis/hithesis.git /opt/hithesis-notify
cd /opt/hithesis-notify/deploy/qq-notify
cp .env.example .env
chmod 600 .env
```

编辑 `.env`：

| 变量 | 内容 |
|---|---|
| `NAPCAT_WEBUI_TOKEN` | 自行生成的 NapCat 管理界面口令 |
| `ONEBOT_ACCESS_TOKEN` | 另一个自行生成的发消息接口口令 |
| `QQ_GROUP_ID` | 接收通知的 QQ 群号 |
| `DEV_PUBLISH_TOKEN` | 可选，仅手动使用 `notify.sh --publish` 时需要；默认每日调度与通知不使用它 |
| `NAPCAT_IMAGE` | NapCat 镜像，部署验证后可固定版本或 digest |

### 首次登录

```sh
docker compose up -d napcat
docker compose logs -f napcat
```

从自己的电脑建立 SSH 转发：

```sh
ssh -L 6099:127.0.0.1:6099 用户名@服务器地址
```

打开本机 `http://127.0.0.1:6099/webui`，输入管理口令，用机器人 QQ 扫码登录，再把它拉进目标群。

在 NapCat WebUI 的 OneBot 网络配置中**新增 HTTP 服务端**：

- 监听地址：`0.0.0.0`（容器内部）。
- 端口：`3000`。
- Access Token：与 `.env` 的 `ONEBOT_ACCESS_TOKEN` 一致。
- 启用并保存；按界面提示重新加载。

Compose 只把管理端口绑定到服务器 `127.0.0.1`，HTTP 3000 不发布到宿主机；通知容器经内部网络访问它。
`MODE=ws` 是镜像初始配置，不会自动创建上述 HTTP 服务，必须在首次登录后完成这一步。
镜像用法依据 [NapCat-Docker](https://github.com/NapNeko/NapCat-Docker)，消息接口使用 OneBot v11 `send_group_msg`。

### 检查并发送

```sh
docker compose build notifier
install -m 755 notify.sh /opt/hithesis-notify/notify.sh
/opt/hithesis-notify/notify.sh --dry-run
/opt/hithesis-notify/notify.sh
```

`--dry-run` 只显示消息，不发群消息、不更新通知状态。
首次发送仅通知当前最新开发版。后续检查合并尚未通知的构建，按变更 ID 去重。
同一提交重新构建不会自动再发；`--force` 可以重发。

```sh
/opt/hithesis-notify/notify.sh --force
```

发送获得 OneBot 成功响应和 message_id 后才保存状态；失败不会消耗更新。
定时和手动触发共用文件锁，避免同时发送。网络超时后无法判断对方是否已收消息，因此不会自动重试发送；先查群消息再决定重发。
通知状态在 `data/notifier/notified.json`，QQ 登录信息也在 `data/`，更新服务时保留该目录。
更新记录从 `https://hithesis.site/dev-history.json` 读取，不需要 GitHub 凭据，也不消耗 GitHub REST API 调用额度。
服务器每五分钟只检查已发布记录，未发现新构建就退出；不会运行 AI 或 GitHub Actions。首次安装仅发送最新构建，重复检查不会重复发群。
`--publish` 保留为需要另行授权的手动功能，不用于默认定时服务。

### 每日发布与五分钟通知检查

```sh
sudo install -m 644 hithesis-dev-notify.service hithesis-dev-notify.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hithesis-dev-notify.timer
systemctl list-timers hithesis-dev-notify.timer
journalctl -u hithesis-dev-notify.service
```

GitHub 定时工作流计划在北京时间 08:00 开始；systemd 定时器每五分钟读取免费更新索引，PDF 可下载且校验通过后才发送。轮询不会调用模型或派发构建。
没有更新不发消息。`Persistent=true` 会在服务器错过通知检查后补检查一次。

## 可选：GitHub 手动通知入口

在 Actions Secrets 设置：

| Secret | 内容 |
|---|---|
| `DEV_NOTIFY_ACCESS_KEY_ID` | 专用 RAM 用户的 AccessKey ID |
| `DEV_NOTIFY_ACCESS_KEY_SECRET` | 对应 AccessKey Secret |

在 Actions Variables 设置：

| Variable | 内容 |
|---|---|
| `DEV_NOTIFY_INSTANCE_ID` | 运行机器人的 ECS 实例 ID |
| `DEV_NOTIFY_REGION` | 实例地域，默认 `cn-beijing` |

手动任务通过官方 Workbench CLI 调用服务器，不依赖公网 SSH 通道。
该 RAM 用户需要目标实例的 Workbench 连接权限；首次使用应先在本机验证 `workbench exec` 能执行服务器通知脚本。
GitHub runner 使用独立的临时 Workbench 配置，权限为 0600，调用结束后删除。
QQ 接口口令仍只保存在服务器 `.env`。

进入 **Actions → Test development branches → Run workflow**：

- 分支选择 `dev`。
- 勾选 `notify_only`：立即检查并推送，不重新编译模板。
- 需要重发当前版本时再勾选 `force_notify`。

也可用已经登录的 GitHub CLI：

```sh
gh workflow run test_dev.yml --repo hithesis/hithesis --ref dev -f notify_only=true -f force_notify=false
```

这个入口用于手动请求服务器检查或重发通知；每日发布由默认分支调度，日常轮询不依赖这些 Workbench Secrets。

## 更新和本地验证

更新服务器代码后，重建通知容器、重新安装 wrapper；机器人数据不动：

以下 `git pull` 仅适用于 Git checkout 部署。当前 ECS 若记录为拷贝快照部署，应打包并上传指定源码文件，保留 `.env` 与 `data/`，不可直接在原目录执行 `git pull`；部署记录需注明来源提交。

```sh
git -C /opt/hithesis-notify pull --ff-only
cd /opt/hithesis-notify/deploy/qq-notify
docker compose build notifier
install -m 755 notify.sh /opt/hithesis-notify/notify.sh
```

本地工具测试只使用临时压缩包和本地模拟 OneBot，不向真实 QQ 群发送消息：

```sh
python3 -m unittest discover -s tests -p 'test_dev_*.py' -v
```
