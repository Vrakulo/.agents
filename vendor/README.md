# vendor

第三方 skill 仓库，以 git submodule 引入。本目录只保存 submodule 的 commit 指针和
`.gitmodules` 配置，不包含第三方内容本身。

| 子模块 | 上游 | 许可证 |
| --- | --- | --- |
| `mattpocock-skills` | [mattpocock/skills](https://github.com/mattpocock/skills) | MIT |
| `addyosmani-agent-skills` | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | MIT |
| `wondelai-skills` | [wondelai/skills](https://github.com/wondelai/skills) | MIT |
| `cloudflare-skills` | [cloudflare/skills](https://github.com/cloudflare/skills) | Apache-2.0 |
| `midscene-skills` | [web-infra-dev/midscene-skills](https://github.com/web-infra-dev/midscene-skills) | MIT |
| `phuryn-pm-skills` | [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | MIT |

每个上游的许可证全文保留在其 submodule 根目录的 `LICENSE` 中。仓库根目录的 MIT 许可
不覆盖本目录，第三方内容遵循各自上游的许可证。

## 约定

- 不要修改本目录下的任何文件。需要调整时，在 `skills/` 下写自己的 wrapper skill，并
  在其中注明来源。
- 不要把这里的文件复制进仓库其他位置。submodule 只保存指针，这是本仓库避免再分发
  第三方内容的前提。
- skill 通过 `scripts/link-skills.sh` 软链到 `~/.agents/skills` 或
  `~/.config/opencode/skills`，不复制内容。

## 更新

```bash
git submodule update --init --recursive                    # 初始化/补齐
git submodule update --remote vendor/<name>                # 更新到上游最新
git diff --submodule=log vendor/<name>                     # 先 review SKILL.md 的变化
git add vendor/<name>                                      # 提交新的 commit 指针
```

skill 是会被 agent 执行的指令，更新前先读 diff，再决定是否提交。
