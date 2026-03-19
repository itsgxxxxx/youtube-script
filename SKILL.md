---
name: youtube-transcript
description: 将 YouTube 视频字幕提取、清洗并整理为结构化文字稿，支持生成摘要、章节目录、翻译后的中文或双语版本，以及 Markdown/Word 输出。适用于视频笔记、课程整理、访谈归档、内容摘要和学习资料沉淀。
---

# YouTube Transcript

将 YouTube 视频转换为结构化、可阅读、可归档的文字稿。

## When to Use

在用户希望进行以下任务时使用本 skill：

- 提取 YouTube 视频字幕或自动字幕
- 生成整理后的完整文字稿
- 输出中文、双语或原文版本
- 把视频内容保存为 Markdown 或 Word 文档
- 整理教程、访谈、播客或学习笔记

## Inputs

开始处理前先确认以下输入：

- `youtube_url`：YouTube 视频链接
- `output_language`：`zh`、`bilingual`、`source`
- `output_format`：`markdown`、`word`
- `output_style`：`verbatim_transcript`、`transcript`、`summary`
- `output_directory`：输出目录

如果宿主环境支持结构化提问或交互式偏好收集，优先用这种方式确认用户偏好；否则通过普通对话逐项确认。

除非用户已经在当前请求中明确指定了 `output_language`、`output_format` 或 `output_style`，否则必须先询问这些偏好，再开始下载和处理 transcript；在偏好未确认前，不要直接套用默认值并跳过提问。

当需要询问用户偏好时，推荐这样引导：

- `output_language`：默认推荐 `zh`。
- `output_format`：默认推荐 `markdown`，理由是“轻量化”。
- `output_style`：如用户未特别说明，建议继续使用高保真的 `verbatim_transcript`。

只有在完成偏好询问、但用户明确表示“你决定 / 用默认 / 随便”时，才使用默认值：

- `output_language`: `zh`
- `output_format`: `markdown`
- `output_style`: `verbatim_transcript`
- `output_directory`: `./youtube-transcripts/`

## Workflow

1. 检查 `yt-dlp` 是否可用；如需导出 Word，再检查 `python-docx` 是否已安装。
2. 运行 `scripts/download_transcript.py <youtube_url>` 下载视频元数据和字幕。
3. 运行 `scripts/parse_subtitle.py <subtitle_file>` 解析字幕并生成带时间戳的结构化文本；长视频场景建议保存 JSON 文件以便后续分块。
4. 对时长超过约 30 分钟的视频，运行 `scripts/plan_parallel_chunks.py <parsed_json>` 生成时间块和处理计划。
5. 如果运行环境支持 subagent 且计划包含多个 chunk，由主 agent 负责分发 chunk，subagent 并行处理各自时间段；如果不支持，就按 chunk 顺序串行处理。
6. 先保证信息不丢失，再根据字幕和上下文判断是否存在明确的发言切换；只有在此之后，才把“教程/单人讲解”与“对话/访谈”分类作为排版层面的辅助判断。
7. 在不添加新观点的前提下清洗字幕、合并碎片、去除重复和无意义填充词。
8. `output_style=verbatim_transcript` 时，严格以 transcript/captions 为权威底稿，只做最小必要清洗，不得总结、改写或稀释信息密度。
9. 若字幕中含有 `>>`、`-`、连续冒号等转写轮次标记，应把它们视为“可能发生发言切换或语气切换”的弱信号，用于帮助分段；除非用户明确要求保留原始转写符号，否则不要把这些标记原样输出到最终文稿。
10. 当无法可靠识别真实说话人身份时，不要强行标注 `Speaker A/B`；优先输出“不写姓名、但按发言主体变化换段”的中性 transcript。
11. “教程/对话”分类只影响分段风格、章节命名和是否尝试识别说话人，不得作为压缩内容或省略信息的依据。
12. `output_style=transcript` 时，可在不改变原意的前提下做适度清洗和可读性整理，但仍应保留高密度时间戳和发言顺序；`output_style=summary` 时，才允许生成更压缩的整理段落。
13. 若宿主支持为 subagent 单独选择模型，则把 chunk 翻译、最小清洗、格式规整这类低推理任务路由到更便宜的小模型；把主控编排、说话人消歧、跨 chunk 去重、最终合并和质检留给更强模型。
14. 按用户选择生成 Markdown，或先生成 Markdown 再用 `scripts/convert_to_docx.py` 导出为 Word。
15. 向用户返回输出路径、语言模式、输出风格、章节数和任何降级处理说明。

## Output Requirements

- 所有输出都必须保留时间信息，便于回看原视频。
- 默认输出风格应为 `verbatim_transcript`。
- `verbatim_transcript` 模式下，目标是尽量贴近原视频说法，只清理明显重复、`uh`/`um`/`you know` 之类口头禅、基础标点和明显 ASR 错误。
- `verbatim_transcript` 与 `transcript` 模式下，尤其在长视频和自动字幕场景中，不要把 2-5 分钟内容压缩成 1-2 句。
- “教程/对话”判断只用于决定分段风格、章节命名和是否尝试识别说话人，不用于决定删减力度或摘要程度。
- 在 `verbatim_transcript` 与 `transcript` 模式下，应优先保留原始信息密度；即使判断为教程类内容，也不能因为是单人连续讲解就更激进地压缩。
- 若存在明确发言切换，应优先根据发言切换组织段落；只有在没有明显多人来回时，才更偏向按主题或步骤组织。
- 如果不输出说话人姓名，仍要根据明显的发言切换、语气转折、问答往返和语义单元主动换段，不要把多轮来回对话堆进同一长段。
- 默认不要把 `>>`、破折号轮次标记等自动字幕提示符直接留在最终正文里；它们应用于辅助判断换段，而不是作为最终展示格式。
- `verbatim_transcript` 模式下，尽量不要省略背景铺垫、引语引入句、举例前置说明和承上启下的上下文句；即使这些句子看起来像“引子”，只要原视频说了，通常就应保留。
- 只清洗表达，不改写事实，不补充原视频中没有的新信息。
- Word 输出使用 `.docx`；当前不支持 PDF。
- 如果用户要求 PDF，明确说明当前 skill 只支持 Markdown 和 Word，并建议先导出 Word 再自行转换。

## Scripts

- `scripts/download_transcript.py`
  下载视频元数据和可用字幕，优先使用人工字幕，其次自动字幕。
- `scripts/parse_subtitle.py`
  将 VTT/SRT 解析为结构化字幕条目和全文文本。
- `scripts/plan_parallel_chunks.py`
  按视频时长生成单 agent 或多 chunk 处理计划，并输出带重叠上下文的 chunk 文件。
- `scripts/convert_to_docx.py`
  将整理后的 Markdown 文字稿导出为 Word 文档。

## References

按需读取以下参考文件，不要一次性全部加载：

- `references/language-modes.md`
  各语言输出模式的选择和翻译约束。
- `references/cleaning-and-segmentation.md`
  清洗、说话人识别、教程/对话分段和章节生成规则。
- `references/output-format.md`
  Markdown/Word 的文档结构、命名规范和交付要求。
- `references/parallel-processing.md`
  长视频的 chunk 策略、subagent 分工和主 agent 合并规则。
- `references/verbatim-transcript.md`
  高保真 transcript 的允许修改项、禁止修改项和输出密度标准。
- `references/model-routing.md`
  不同任务的模型分配建议；仅在宿主支持子 agent 模型选择时启用。

## Failure Handling

- 如果视频没有任何字幕，明确告知用户该视频无可用字幕。
- 如果只存在自动字幕，继续处理，但在结果中注明来源为自动字幕。
- 如果 Word 导出依赖缺失，保留 Markdown 输出并告诉用户缺少什么依赖。
- 如果视频较长，不要把整段全文一次性交给单个 agent；优先按时间块处理，再由主 agent 合并。
- 如果运行环境不支持 subagent，仍然使用 chunk 计划串行处理，避免单次上下文过大。
