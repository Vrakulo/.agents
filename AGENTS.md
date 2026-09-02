# Karpathy behavioral guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Agent Instructions

## 语言

1. **对话输出**：与用户的对话结果使用中文回复。
2. **保留原文**：代码中的标识符、命令、文件路径、技术术语、库名、API 名称等保持原文，不做翻译。
3. **开发者文档**：代码注释、ADR、CONTEXT、plan、spec、git commit message、issue 等面向开发者的内容，遵循仓库内既有的语言约定；若仓库内不存在既有约定，则优先使用中文。
4. **界面与日志**：
   - 显示在 UI 上的文字优先做国际化处理（提取为资源文件，使用 i18n key 而非硬编码字符串）。
   - 打印到控制台或日志中的内容优先使用英文。

## Git 分支命名

分支名格式：`xezzon/<issue-id>`。

创建分支前：
1. 在 Multica 中查找对应 issue，取其 ID。
2. 若该 issue 不存在，先与用户确认后再在 Multica 新建 issue，然后取
新 issue 的 ID。
3. 按 `xezzon/<issue-id>` 创建分支。
