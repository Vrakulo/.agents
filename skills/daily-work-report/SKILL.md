---
name: daily-work-report
description: 生成当日/指定日期的工作汇报，聚合飞书会议记录（vc +search，非日历）、GitHub 提交与本人发布过审查意见的 PR、Multica issue 三类数据源，输出 `[issue-id 或 项目名称] 完成了哪些事项。(用时h)` 格式的条目列表。当用户要求"整理今日工作汇报""写日报/周报草稿""总结今天做了什么""汇总今天的会议、提交和 issue"时使用。严格限定检索范围：只查用户明确授权的 GitHub 仓库/组织和 Multica 工作区，绝不擅自遍历本地文件系统寻找无关仓库，绝不汇报未发现的空类别。
version: 1.0.0
metadata:
  opencode/slash: true
---

# 日报生成

把飞书会议、GitHub 提交、Multica issue 三类零散记录，收敛成一份用时可核对的工作汇报。核心难点不是"怎么调 API"，而是**知道该查哪、不该查哪、查到之后怎么去重和归类**。下面按这个顺序展开。

## 第一步：确定范围，而不是自己猜

在检索任何数据源之前，先确认三件事。范围错了，后面查得再准也是白费——擅自扩大范围（比如翻遍本地磁盘找 `.git` 目录）是比查漏更严重的问题，宁可先问用户，也不要自作主张。

1. **身份**：用户的飞书身份（默认走 user 身份即可）、GitHub 账号/邮箱、Multica 邮箱。这些通常能从 `mcp__agent-memory__memory` 里的 FACT.md、`gh auth status`、`multica user profile get` 直接拿到，不必每次都问。
2. **GitHub 仓库范围**：只检查用户明确说过在做的仓库/组织，或者是此前对话、记忆中出现过的仓库。用户已加入的 GitHub 组织（`gh api user/orgs --jq '.[].login'`）也算已授权范围，可直接作为 `--owner` 候选；个人账号下的仓库用 `--author` 检索即可。**不要**用 `find / -iname ".git"` 或类似命令扫描整个文件系统——本地磁盘上可能有大量与当前工作无关的个人项目、开源仓库、第三方代码，把它们纳入日报是严重的越界。如果不确定该查哪些仓库，直接问用户"今天在哪些仓库/组织下有提交？"或使用下面"GitHub 提交"一节里限定范围的检索方法。
3. **Multica 工作区范围**：`multica workspace list` 列出用户所属的全部工作区，通常需要逐个检查（工作区之间数据不互通，且 `--assignee-id` 等过滤是按当前 `multica workspace switch` 的工作区生效的）。

如果用户已经在对话中指定了仓库或工作区，直接复用，不必重新问一遍。

## 第二步：分源检索

### 会议（飞书会议记录，不走日历）

不使用 `lark-cli calendar +agenda`/日历日程接口获取会议列表（该路径需要 calendar 域授权，默认视为不可用）。改用 [lark-meeting](../lark-meeting/SKILL.md) 的 `vc +search` 查询目标日期已结束的历史会议：

```bash
lark-cli vc +search --start <YYYY-MM-DD> --end <YYYY-MM-DD> --format json --as user
```

单日查询时 `--start`/`--end` 必须填同一天（`--end` 为纯日期时会被解释为当天 23:59:59）。若返回 `has_more=true`，按 `page_token` 翻页取全当天结果。

每条结果里的会议起止时间相减得到时长（小时，保留到 0.5h 粒度即可），会议主题用于后续归类到项目，而不是直接当作汇报里的方括号内容。相同 `meeting_id` 或明显重复的记录只算一次。

`vc +search` 返回的条目不含起止时间，只有 `display_info`。要算时长，必须再用 `vc +detail --meeting-ids <id1,id2> --as user` 取 `start_time`/`end_time`。

**授权过期的处理**：若返回 `need_user_authorization` / `token_missing`（`refresh_token` 过期），按下面流程重新授权，不要退回日历接口，也不要跳过会议：

1. 运行 `lark-cli auth login --scope "vc:meeting.search:read" --no-wait --json`，拿到 `device_code` 和 `verification_url`。
2. 用 `lark-cli auth qrcode "<verification_url>" --output ./lark-auth-qr.png` 生成二维码。输出目录用当前工作目录，`/tmp/opencode` 可能没有写权限。`verification_url` 原样使用，不要做任何编码或改动。
3. 把 URL 放在前面，二维码图片放在下面发给用户（可用 `openchamber` 的 `file.open` 在文件面板打开），然后结束本轮，提醒用户授权后回来告知。**不要在同一轮里阻塞执行 `--device-code`**，也不要重复生成链接，重新生成会让上一个失效。
4. 用户确认已授权后，再执行 `lark-cli auth login --device-code <device_code>` 完成登录，随后重新检索。
5. 授权完成后删除生成的二维码图片。

`vc +search` 只能查到已结束的会议，不含未来或正在进行的会议；如果目标日期包含尚未结束的会议且需要它，如实说明覆盖不到，不要退回日历接口兜底。

需要更详细信息（比如会议实际讨论了什么）时，用 `vc +detail` 取 `note_id`/`minute_token` 后进入 [查询会议及其产物](../lark-meeting/scenes/query-meeting-and-artifacts.md)；大多数日报场景，会议主题 + 参会人 + 时长已经够用，不必为了几句话去翻纪要正文。

### GitHub 提交

优先用限定范围的检索，按可靠性从高到低尝试：

1. `gh search commits --author <github-handle> --author-date <YYYY-MM-DD> --owner <组织> --limit 100 --json repository,commit,sha` —— 对 `gh api user/orgs` 列出的**每个**组织都跑一遍；必须加 `--limit 100`，默认只返回 30 条，一个大 PR 的提交就能把结果截断。`--author-date` 是提交者本地时区的日期，跨时区时注意边界。
2. GraphQL `viewer.contributionsCollection(from, to)` 的 `commitContributionsByRepository` 只作补充。**它返回空不代表当天没有提交**：对未开启"在个人资料中显示私有贡献"的账号，私有组织仓库不会被统计。这次 `totalCommitContributions` 为 0，而 `gh search commits` 实际找到 60 条提交，就是这个原因。不能仅凭 GraphQL 为空就得出"无提交"的结论。
3. 如果两种方式都为空，再回头确认一次：`gh pr list --author @me --search "updated:>=<日期>"`，或用 Multica 里 issue 的线索对照，不要直接下"无提交"结论；同样不要转去扫本地文件系统。
4. 只有当用户明确提供了本地仓库路径（或此前对话/记忆中出现过这些路径）时，才用 `git -C <指定路径> log --author=<email> --since=<today 00:00> --until=<tomorrow 00:00>` 兜底查当天提交，包括本地已提交但未推送的记录。**不要**主动用 `find`/`fd` 去发现新的本地仓库路径。

拿到 commit 列表后，用 `git show --stat` 或 PR 描述（`gh pr view <number> --json body,comments`）看一眼改了什么、有没有关联 issue（commit message 里的 `#123` 或 `Closes #55`），方便写清楚"完成了哪些事项"而不是简单复述 commit message。

一个 PR 常含几十个提交时，不要逐条列出，按 PR 合并成一条事项，用时按首尾提交时间跨度扣除会议等已单独计时的时间来估算，并在说明里标注是估算。

### 本人审查过的 PR

日报要包含用户**审查过**的 PR，但必须是用户**发布过审查意见**的，不能因为搜索结果里出现了就算。

1. 候选：运行 `gh search prs --reviewed-by <handle> --updated ">=<日期>" --json repository,number,title,author,state,updatedAt --limit 100`，再运行 `gh search prs --commenter <handle> --updated ">=<日期>" ...`，两者取并集，再运行 `gh search prs --involves <handle> --updated ">=<日期>" ...` 补漏并排除用户自己作者的 PR。**不要加 `--owner`**：用户参与的仓库所属组织不一定出现在 `gh api user/orgs` 里（例如以外部协作者身份参与的 `TechWithU/fitwithu_client`），按组织限定会漏掉；而 `--reviewed-by`/`--commenter` 本身已经把范围限定在用户自己的动作上，不属于范围扩张。`--involves` 范围更宽，用来补漏（它能搜到只发过普通评论的 PR），但搜到本身不是证据，必须经过第 3 步核实。
2. 排除用户自己作者的 PR，这类已经算在"提交"里。
3. **逐个核实**用户确实发过意见、且发生在目标日期。对每个候选 PR，同时查三处，并按 `user.login == <handle>` 过滤：
   - `gh api --paginate repos/<owner>/<repo>/pulls/<n>/reviews`：正式审查，含 `APPROVED`、`CHANGES_REQUESTED`、`COMMENTED`，看 `submitted_at`
   - `gh api --paginate repos/<owner>/<repo>/pulls/<n>/comments`：行内评论，看 `created_at`
   - `gh api --paginate repos/<owner>/<repo>/issues/<n>/comments`：PR 对话区评论。很多人把 Code Review 写成普通评论，**只查 `reviews` 会漏掉**

   **关键陷阱：`reviews` 接口会漏掉普通评论形式的 Code Review。** 这次的 `fitwithu_client` #37，`gh pr view --json reviews` 返回空，用户的意见是 PR 对话区的一条评论，只有查 `issues/<n>/comments` 才能看到。`--reviewed-by` 和 `--commenter` 的搜索结果都没有它，只有 `--involves` 搜到了。所以候选必须再用 `--involves` 补一遍，并过滤掉用户自己作者的 PR，然后逐个核实。
4. 时间过滤：把时间戳换成用户所在时区（Asia/Shanghai，UTC+8）后再比较日期。`updated` 只说明 PR 在那天有任何更新，不说明用户那天发过意见。比如用户前一天的 Approve 不属于今天，别人的 PR 当天被合并也不算。
5. 无正文的小型审查（例如仅 `APPROVED` 且没有评论正文）直接忽略，不计入时间和汇报条目。
6. 读一眼评论正文，概括关键意见（结论、主要问题），不要只复述 PR 标题。
7. 用时计算：每轮审查按 10 分钟计算，以 0.5h 粒度向上取整（例如 1～3 轮计为 0.5h，4～6 轮计为 1h）。

### Multica issue

对每个候选工作区（来自第一步）：

1. `multica workspace switch <id或slug>`
2. `multica workspace member list --output json`，按邮箱匹配找到该用户在这个工作区里的 `user_id`（不同工作区里同一人的 `user_id` 一致，但工作区成员关系不同，没加入的工作区这一步会报错，跳过即可）。
3. `multica issue list --assignee-id <user_id> --fields identifier,title,status,updated_at,project_id --output json --limit 100`，翻页（`--offset`）直到 `has_more` 为 false，筛出 `updated_at` 落在目标日期内的条目。
4. 如果怀疑用户是通过评论/协作而非指派参与了某个 issue（例如已经从会议或 commit 里知道了具体 issue 号），可以用 `multica issue comment list <issue-id> --since <today 00:00Z>` 针对性核实，而不是对整个工作区做评论级别的全量扫描。

`assignee_id` 过滤拿到的是"分配给我"的 issue，这是绝大多数日报场景真正关心的范围；不要因为找不到就放宽到搜索全部 issue 标题关键词——那属于范围扩张，容易把无关的、别人负责的工作也算进来。

## 第三步：去重

三个数据源之间经常有重叠，写报告前先合并：

- 同一个 GitHub PR 关联同一个 Multica issue（commit message 或 PR 描述里出现 issue 标识）时，合并成一条，用 issue-id 作为方括号内容，事项描述里可以提一句"对应 PR #xx"。
- 用户自己作者的 PR 在"提交"里算一次，不要再在"审查过的 PR"里重复；同一个 PR 在多个提交里出现，也只算一条事项。
- 同一场会议如果在结果里出现多条记录（比如组织者视角和参与者视角），按 `meeting_id` 去重，只算一次时长。
- 同一天对同一个 issue 有多次状态更新（比如多次 commit 或多次评论），合并成一条描述，用时按整体工作时长估算，不要按更新次数重复计时。

## 第四步：归类到 `[issue-id 或 项目名称]`

方括号里写的是**项目名称或 issue-id，不是会议标题、commit message 或 issue 标题**。判断顺序：

1. 如果这项工作对应一个具体的 Multica issue，直接用它的 identifier（如 `GGB-431`）。
2. 如果没有具体 issue，但能确定所属项目（会议标题、commit 所在仓库、issue 的 `project_id` 都能提供线索），查 `multica project list --output json`（**按所在工作区分别查**，项目列表不跨工作区，需要先 `multica workspace switch`）拿到项目名称列表，用关键词/仓库名匹配到正确的项目名。同一件事优先用能查到的最具体项目，而不是笼统地写会议主题。
3. 如果既没有 issue 也确认不了项目归属（比如纯粹的对外沟通会议、探索性讨论），才退而用一个概括性的主题词，并在描述里如实说明这是临时归类，不要杜撰一个听起来像项目名但其实不存在的名字。

判断项目归属时同样遵守"不擅自扩大范围"的原则：找不到明确证据就如实使用主题词或注明"未确认项目归属"，不要为了凑一个好看的项目名而去检索与本次任务无关的仓库或工作区。

## 输出格式

严格使用：

```
[issue-id 或 项目名称] 完成了哪些事项。(用时h)
```

- **汇报条目必须整体放进一个代码块**（用 ``` 包裹），方便用户一键复制。代码块内只放汇报条目，不放标题、说明或其他文字。
- 每条一行，事项描述用陈述句概括做了什么（而不是逐字复制会议标题或 commit message）。
- 审查 PR 的条目写成"审查 <仓库> PR #<n>（<主题>），给出 <结论>：<关键意见>"。方括号里仍按第四步规则写 issue-id 或项目名称。
- 报告末尾可以附"说明"，放在代码块**之外**：
  - **用时汇总**：计算并列出总用时与各分类用时（代码、审查、会议），例如：`总计 Xh（代码 Xh、审查 Xh、会议 Xh）`。
  - **核对信息**：只写需要用户核对的估算依据、临时归类。不要写"今日无 XX"。
- 用时按 0.5h 粒度估算：会议直接用 `vc +search` 返回的起止时长；PR 审查按每轮 10 分钟、0.5h 粒度向上取整（无正文的小型审查不计入）；GitHub 提交与 Multica 工作按 commit 时间跨度、讨论跨度或改动量做合理估算，无法判断时如实标注为估算而不是精确到分钟。
- **不汇报不存在的内容**：某个数据源当天确实没有可汇报的条目（没有会议、没有提交、没有分配的 issue），直接跳过整段，不要写"今日无 XX""未发现相关内容"之类的说明性文字——用户只想看到确实发生的工作。
- 不要在方括号外再重复一遍方括号里的内容（比如 "[GGB-431] GGB-431 完成了..."），描述部分直接说事项本身。

## 示例

```
[GGB-431] 基于 AI GTM 调研结果完成实验方案设计与验证。(1.5h)
[Aero Operations] 与客户对接方沟通星源材质数据方案及技术框架细节。(1h)
[Soraka Facility] 参加项目敏捷站会，同步开发进度与阻塞项。(0.5h)
```

不要写成：

```
[GTM方案研讨] 参加了 GTM 方案研讨会议。(1h)          # 方括号用了会议标题而不是项目名称
[Multica] 今日未发现分配给本人的 issue。              # 汇报了不存在的内容
[agent-maestro] 修复了日志 promise 未捕获问题。(2h)   # 未经用户授权，擅自检索了范围外的仓库
```
