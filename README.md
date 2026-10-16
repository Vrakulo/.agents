# .agents

个人 agent 配置仓库，做三件事：

- 发布自维护的 skills，`npx skills add xezzon/.agents` 即可装到 Claude Code、Codex、Cursor 等受支持的编码 Agent。
- 版本化本机在用的 agent 定义与全局 `AGENTS.md` 覆盖。
- 存放跨项目、跨 session 复用的记忆文档。

## 目录结构

```
.agents/
├── skills/                     # 发布目录，npx skills add 安装这里的内容
├── agents/                     # agent 定义，各自限定可加载的 skill
├── deprecated-skills/          # 已退役的 skill，仅供查阅，不再发布
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

每个 agent 只放行自己清单内的 skill。

## Memory

`memory/` 用来放跨项目、跨 session 复用的记忆文档。约定做法：文档在本仓库内版本化，再以 symlink 挂到 `~/.agents/memory/`，供全局 `AGENTS.md` 用固定路径引用。

它不在 `skills/` 下，`npx skills add` 不会安装。

## 许可证

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
