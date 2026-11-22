# ZenAI 公司 PDF 模板规范

## 1. 适用范围与封面决策

### 默认包含封面

- 技术文档、架构文档、设计文档
- 需求文档、产品规格、研究报告
- 实施方案、咨询方案、解决方案
- 投标、验收、交付、评审类正式文档
- 公司介绍、白皮书、对外报告

### 默认不包含封面

- 会议纪要、简短周报、通知、备忘录
- 单页说明、临时清单、内部快速记录

### 边界判断

满足任一条件即建议使用封面：需要正式发布、需要版本控制、需要标注密级、面向外部、超过约 5 页、需要审批/签署。用户明确指定时以用户要求为准。

## 2. 页面结构

### 封面

封面视觉对齐《ZenAI 公司简介》拼色结构：

1. 上半：深绿 `#26372f` 英雄区（Logo、标题、副标题、标签）
2. 水印大半在深绿区，底边在拼色线处截断
3. 下半：白底信息行（编制部门、版本、日期、密级；无分区标题/横线；封面右上不再重复）
4. 封面无页眉/页脚线，不计入正文页码

### 正文页眉

- 左：公司 Logo，高度约 7.5 mm（宽约 15 mm，保持 2:1）
- 右：文档简称，使用 Space Mono 或回退字体（约 7 pt）
- 下方：浅灰紫细分隔线；内容区顶边约在页顶下 14.5 mm

### 正文页脚

- 左：密级，颜色与封面徽标一致（约 7 pt）
- 右：正文页码，格式为 `当前页/总页数`（有封面时从 1 起且不含封面；无封面时首页即为 1）
- 上方：浅灰紫细分隔线；内容区底边约在页底下 13 mm

### 会议纪要 / 会议记录（`--mode meeting`）

默认**无封面**。正文按阅读优先级排列：

1. **会议信息表**：主题、时间、地点（可选）、组织部门、主持人、记录人、参会人、缺席（可选；空值不渲染）
2. **会议目的**：一段话说明为何开、要对齐什么
3. **纪要摘要**：分块结构——顶部「核心结论」横幅；主题块 3 列网格（标题 / 副标题 / 要点）；可选「后续推进」2 列。色条使用品牌紫/鼠尾草绿，无图标、无多色贴纸风。
4. **决议事项**：已拍板结论的短列表
5. **发言记录**（有则渲染）：完整发言流水，每条为「姓名头像 + 人名 + 内容」；头像按姓名稳定着色（中文取末字、英文取首字母）。排版偏紧凑，便于容纳较长逐字稿。

责任人与下一步写在「后续推进」分块或决议表述里即可；不单独做待办跟踪表（静态 PDF 无法维护状态）。

不纳入：AI 免责声明、妙记/相关链接、反馈收集等产品导出噪声。

示例：`examples/zenai-meeting-minutes.pdf`

## 3. 视觉系统

| Token | 色值 | 用途 |
|---|---|---|
| `--bg-white` | `#fcfdfd` | 主背景 |
| `--bg-soft-purple` | `#f7f5fa` | 信息块、弱背景 |
| `--deep-green` | `#1a2b24` | 主标题、深色竖条 |
| `--mid-green` | `#4a6358` | 正文 |
| `--light-green` | `#a8c8bd` | 强调与几何装饰 |
| `--deep-purple` | `#2d2844` | 关键强调、机密徽标 |
| `--mid-purple` | `#7a739c` | 技术标签、内部徽标 |
| `--light-purple` | `#dcd8eb` | 边框、分隔线 |

### 字体（OFL，可商用）

| 用途 | 字体 | 许可 | 文件 |
|---|---|---|---|
| 中文标题 / 正文 / 密级 / 表头 | **Noto Serif SC**（思源宋体系，正式衬线） | SIL OFL 1.1 | `assets/fonts/NotoSerifSC-{Regular,SemiBold,Bold}.ttf` |
| 拉丁 / 希腊 / 常用符号回退（如 μ、Ω、±） | **Noto Serif LGC** | SIL OFL 1.1 | `assets/fonts/NotoSerifLGC-{Regular,SemiBold}.ttf` |
| 英文标签、版本号、页码 | **Space Mono** | SIL OFL 1.1 | `assets/fonts/SpaceMono-{Regular,Bold}.ttf` |

- 许可全文：`assets/fonts/OFL-NotoSerifSC.txt`、`assets/fonts/OFL-SpaceMono.txt`
- 中文内容禁止使用 Mono / Helvetica（会导致方框缺字）
- 主字体缺字（如希腊字母 μ）时，渲染器自动回退到 Noto Serif LGC
- 无本地字体文件时，脚本回退到可嵌入的中文 CID 字体（STSong）与 Helvetica；英文在 CID 下可能字距异常，正式交付前请带上 `assets/fonts/`

### 图像

- 优先黑白、高对比度、欧洲建筑/工业/实景摄影
- 使用深绿或深紫叠色；不要直接放置杂乱彩色图
- 禁止通用图库式笑脸、虚假商务握手照
- Logo 源文件：`assets/zenai-logo.svg`（渲染时由脚本栅格化为 `zenai-logo.png`）

## 4. 密级

- **对外**：允许发送给客户、合作伙伴或公开发布
- **内部**：仅限公司员工及授权协作者
- **机密**：仅限明确授权人员；导出前再次确认接收范围

同一文档的封面、元数据和每页页脚必须保持同一密级。

## 5. 资产与命令

- Logo：`assets/zenai-logo.svg`（渲染产出 `assets/zenai-logo.png`）
- 字体：`assets/fonts/`（Noto Serif SC + Space Mono，OFL）
- 渲染脚本：`scripts/render_zenai_template.py`（`--mode doc|meeting`）
- 示例输出：`examples/zenai-cover-template.pdf`、`examples/zenai-meeting-minutes.pdf`

```bash
python scripts/render_zenai_template.py \
  --output output/方案.pdf \
  --title "项目实施方案" \
  --subtitle "客户名称 / 项目名称" \
  --version "V1.0" \
  --classification "内部" \
  --date "2026-09-08" \
  --department "解决方案部"
```

依赖：`reportlab`、`Pillow`、`fonttools`（字形覆盖检测与 LGC 回退）。推荐在虚拟环境中安装。

## 6. 导出验收

1. A4 纵向，页面背景为 `#fcfdfd`
2. 封面信息齐全且密级有效
3. 正文页眉 Logo 清楚、比例无变形
4. 正文页码从 1 开始并连续
5. 中文无缺字/方框，文本无溢出或重叠
6. 表格跨页时重复表头
7. 图片分辨率足够、色彩符合规范
8. PDF 标题、作者、主题元数据正确
9. 机密文档接收范围已经确认
