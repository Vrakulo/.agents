# .agents

个人 agent 配置仓库，做三件事：

- 发布自维护的 skills，`npx skills add xezzon/.agents` 即可装到 Claude Code、Codex、Cursor 等受支持的编码 Agent。
- 版本化本机在用的 agent 定义、MCP 配置与全局 `AGENTS.md` 覆盖。
- 存放跨项目、跨 session 复用的记忆文档。

## 目录结构

```
.agents/
├── skills/                     # 发布目录，npx skills add 安装这里的内容
├── agents/                     # agent 定义，各自限定可加载的 skill
├── deprecated-skills/          # 已退役的 skill，仅供查阅，不再发布
├── mcp.json                    # 各 harness 通用的 MCP server 记录
├── AGENTS.md                   # 全局覆盖指令，symlink 到 ~/.agents/AGENTS.md
├── .skill-lock.json            # npx skills 的安装记录，勿手改
├── LICENSE
└── README.md
```

## 安装

```bash
npx skills add xezzon/.agents                       # 全部
npx skills add xezzon/.agents@pull-request-rules    # 指定单个
npx skills add xezzon/.agents -g                    # 安装到用户级作用域
```

## Skills

`skills/<name>/SKILL.md` 是一个发布单元：YAML frontmatter 加 Markdown 指令，目录名即 skill 名。这是 `npx skills` 的 catalog 布局。

- [`pull-request-rules`](./skills/pull-request-rules)：创建 GitHub Issue 或 Pull Request 前先查重、读目标仓库的模板和必填元数据，确认无相似项后才创建。

## Agents

- [`mattpocock`](./agents/mattpocock.md)：grilling → spec → tickets → implement → review → PR 的端到端工程流程。
- [`wondelai`](./agents/wondelai.md)：clean code、重构、遗留代码、文档等代码工艺与架构。
- [`device-pilot`](./agents/device-pilot.md)：操作浏览器与桌面完成任务，并做 UI 自动化与端到端测试。`mode: all`，既能当主 agent，也能被别的 agent 派活。

每个 agent 只放行自己清单内的 skill 和 MCP。

## MCP

`mcp.json` 记录本机在用的 MCP server，采用通用的 `mcpServers` 结构，与具体 harness 无关。

- `context7`：Upstash Context7，远程 HTTP 服务，按库名拉取最新文档和代码示例。匿名访问有速率限制，设置 `CONTEXT7_API_KEY` 可提高额度。
- `playwright`：`@playwright/mcp`，本地 stdio 服务，以 DOM / 可访问性树驱动浏览器。当前配置为 headless + isolated + `1440x900` 视口 + `vision,devtools` caps，因此只能操作它自己拉起的浏览器实例，接触不到本机 Chrome 的登录态。

### Midscene 不走 MCP

Midscene 自 `1.10` 起[下线了全部 MCP server](https://midscenejs.com/zh/mcp.html)（`@midscene/mcp`、`@midscene/web-bridge-mcp`、`@midscene/computer-mcp` 等），官方推荐改用 Skills + 平台 CLI。最后一个含 MCP 支持的版本是 `1.9.8`。

本仓库不记录任何 Midscene MCP 包。`device-pilot` 通过以下 skills 调用对应 CLI：

| Skill | CLI | 平台 |
| --- | --- | --- |
| `browser-automation` | `npx @midscene/web` | 浏览器（Puppeteer / CDP / Bridge） |
| `computer-automation` | `npx @midscene/computer` | macOS / Windows / Linux 桌面 |
| `vitest-midscene-e2e` | — | E2E 测试工程 |

Midscene 需要多模态模型才能运行，配置 `MIDSCENE_MODEL_API_KEY`、`MIDSCENE_MODEL_NAME`、`MIDSCENE_MODEL_BASE_URL`、`MIDSCENE_MODEL_FAMILY` 四个环境变量。推荐写进项目根目录的 `.env`（Midscene 会自动加载），记得确认 `.env` 已被 git 忽略。详见 [Midscene 模型配置](https://midscenejs.com/zh/skills.html#模型配置)。

## Memory

`memory/` 用来放跨项目、跨 session 复用的记忆文档。约定做法：文档在本仓库内版本化，再以 symlink 挂到 `~/.agents/memory/`，供全局 `AGENTS.md` 用固定路径引用。

它不在 `skills/` 下，`npx skills add` 不会安装。

## 许可证

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
