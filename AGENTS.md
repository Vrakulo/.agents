# Mattpocock skills patch

When grilling, ask one question at a time.

When implement, DO NOT commit until confimed.

When a skill references `GLOSSARY.md` or `GLOSSARY-MAP.md`, it lives in `docs/`, not the repo root.

# Agent Instruction

## 语言

1. **对话输出**：与用户的对话结果使用中文回复。
2. **保留原文**：代码中的标识符、命令、文件路径、技术术语、库名、API 名称等保持原文，不做翻译。
3. **开发者文档**：代码注释、ADR、CONTEXT、plan、spec、git commit message、issue 等面向开发者的内容，遵循仓库内既有的语言约定；若仓库内不存在既有约定，则优先使用中文。
4. **界面与日志**：
   - 显示在 UI 上的文字优先做国际化处理（提取为资源文件，使用 i18n key 而非硬编码字符串）。
   - 打印到控制台或日志中的内容优先使用英文。
