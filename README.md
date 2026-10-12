# agent-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

个人维护的 [Agent Skills](https://agentskills.io/) 集合。遵循 [`npx skills`](https://skills.sh/) 标准，可通过一条命令安装到任意受支持的编码 Agent（Claude Code、Cursor、Codex、Cline、Zed 等 70+）。

## 安装

```bash
# 安装全部 skills
npx skills add xezzon/agent-skills

# 安装指定 skill
npx skills add xezzon/agent-skills --skill plan-edit
npx skills add xezzon/agent-skills --skill plan-implement
npx skills add xezzon/agent-skills --skill pull-request-rules

# 安装到全局作用域
npx skills add xezzon/agent-skills -g
```

## Skills 列表

### [`plan-edit`](./skills/plan-edit)
创建或修订项目实施计划。当用户要求"写一个 plan""生成实施步骤""更新已有 plan"时触发。
- 输出至 `.agents/plans/${yyMMddHHmm}_${title}.plan.md`
- 包含完整章节：概述 / 目标 / 实施步骤（含 checkbox） / 关键文件 / 风险

### [`plan-implement`](./skills/plan-implement)
按编号执行 plan 文件中的实施步骤，并实时将 checkbox 标记为已完成。
- 支持通过 `steps` 参数指定执行部分步骤（如 `1,3,5`）
- 默认跳过已勾选的步骤；出错时立即停止

### [`pull-request-rules`](./skills/pull-request-rules)
处理 GitHub Issue 和 Pull Request 的创建流程：先查找相似项，再读取并遵循目标仓库的模板、标签和必填元数据。

## Memory

[`memory/`](./memory) 存放需要跨项目、跨 session 复用的 agent 记忆文档。文件在本仓库内版本化，并通过 symlink 挂载到 `~/.agents/memory/`，供个人 `AGENTS.md` 以固定路径引用，对所有项目的 agent 生效。

`memory/` 不属于 `npx skills` catalog，`npx skills add` 不会安装它。

## 目录结构

```
agent-skills/
├── skills/
│   ├── plan-edit/
│   │   └── SKILL.md
│   ├── plan-implement/
│   │   └── SKILL.md
│   └── pull-request-rules/
│   └── SKILL.md
├── memory/
│   └── architecture-review-flow.md
├── LICENSE
└── README.md
```

每个 skill 是一个自包含目录，仅需一个 `SKILL.md`（YAML frontmatter + Markdown 指令）。这是 `npx skills` 标准的 catalog 布局。

## 贡献

欢迎以 Issue / PR 形式新增或改进 skill。新增 skill 时，在 `skills/<name>/` 下创建目录，并参考已有 `SKILL.md` 填写 `name` 与 `description` frontmatter。

## 许可证

[MIT](./LICENSE)
