# 架构评审（improve-codebase-architecture）产物跟踪

## 判据

未定稿的诊断会在 grilling 中被否决、合并、重塑——它是工作草稿，不是待办（issue tracker）、不是长期知识（docs/）、也不该放难维护且默认不可见的 Gist。

问题：内容是否会在敲定前大幅改变？会 → 本地草稿；定稿后按去向分流。

## 流程

1. 首次查看：HTML 报告照旧写 OS temp。
2. 需要跨 session / 逐个 grilling 时，原始 HTML 原样移入 `.scratch/architecture-review/report.html`（保留图示，不转 markdown）；忽略规则放 `.scratch/.gitignore`（内容 `*`），不动仓库根 `.gitignore`。
3. `.scratch/architecture-review/backlog.md` 是纯表格状态追踪：候选表（编号、候选、强度、状态、依赖、去向）。决策细节不写进这里——留在会话中，候选敲定时写进 issue 或 ADR。诊断与 before/after 图只在 `report.html`，表格按编号引用（卡片锚点 `#c1`–`#c8`）。
4. 每轮 grilling 只更新 `backlog.md` 表格里该候选的「状态」列；推进项敲定 seam 形状与验收标准后才开正式 issue（编号回填「去向」列）；否决且理由有承载价值的写 ADR 的「曾考虑并否决」一节。
5. 全部候选落地后删除整个目录。

## 教训来源

2026-10，agent-maestro：HTML 报告曾直接发成 GitHub issue + secret Gist，因 issue「没有实际内容」、Gist 难维护且不可见而关闭撤回，最终改为 `.scratch/` 本地跟踪。
