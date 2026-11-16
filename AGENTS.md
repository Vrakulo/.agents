# Skill overrides

When grilling, ask one question at a time.

When a skill puts `GLOSSARY.md` or `GLOSSARY-MAP.md` at the repo root, use `docs/` instead.

In-progress artifacts go under `.scratch/` in the project root, not the OS temp dir. Keep each artifact directory out of git by listing it in `.scratch/.gitignore`.

- **handoff**: save the handoff document to `.scratch/handoff/`.

# 语言

1. **对话输出**：与用户的对话结果使用中文回复。
2. **保留原文**：代码中的标识符、命令、文件路径、技术术语、库名、API 名称等保持原文，不做翻译。
3. **开发者文档**：代码注释、ADR、CONTEXT、plan、spec、git commit message、issue 等面向开发者的内容，遵循仓库内既有的语言约定；若仓库内不存在既有约定，则优先使用中文。
4. **界面与日志**：
   - 显示在 UI 上的文字优先做国际化处理（提取为资源文件，使用 i18n key 而非硬编码字符串）。
   - 打印到控制台或日志中的内容优先使用英文。

# 运行环境

运行项目时优先使用容器，尽可能不使用本地工具链（如 Rust、Java、Node.js 等）：

1. 默认使用对应语言的官方镜像（如 `rust`、`eclipse-temurin`、`node`），将项目目录挂载进容器运行，包括依赖安装、构建、测试和启动。
2. 仅当容器无法满足需求时才退回本地工具链，例如没有可用的容器运行时、需要访问宿主机特有资源（GPU、硬件设备、桌面环境等），或项目自身已明确要求使用本地环境。
3. 容器运行产生的临时文件放在 `.scratch/` 下，避免污染项目目录。
