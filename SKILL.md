---
name: youtube-script
description: 将 YouTube URL 或原始 transcript 整理成文章化完整文稿，适合访谈、播客、演讲与对谈内容。支持中文、英文、双语输出，以及 Markdown/Word 交付。
---

# YouTube Script

将 YouTube 视频或现成 transcript 转换为可阅读、可归档的完整文稿。

## When to Use

在用户希望进行以下任务时使用本 skill：

- 根据 YouTube URL 生成文章化完整文稿
- 将原始 transcript / 字幕文本整理成更易读的正式稿件
- 输出中文、英文或双语版本的访谈稿、播客稿、演讲稿
- 先得到轻量化 Markdown，再按需导出 Word
- 追求类似杂志访谈稿、整理稿、长文文稿的阅读体验

## Inputs

开始处理前先确认以下输入：

- `youtube_url`：YouTube 视频链接，可选
- `raw_transcript`：用户直接提供的 transcript / 字幕文本，可选
- `output_language`：`zh`、`bilingual`、`source`
- `output_format`：`markdown`、`word`
- `output_directory`：输出目录

如果宿主环境支持结构化提问或交互式偏好收集，优先用这种方式确认用户偏好；否则通过普通对话逐项确认。

除非用户已经在当前请求中明确指定了 `output_language` 或 `output_format`，否则必须先询问这两个偏好，再开始处理；在偏好未确认前，不要直接套用默认值并跳过提问。

当用户只给了 YouTube URL 或只说“帮我生成文稿”时，也必须先问偏好，不能默认按中文或 Markdown 直接开跑。

当需要询问用户偏好时，推荐这样引导：

- `output_language`：默认推荐 `zh`。
- `output_format`：默认推荐 `markdown`，理由是“轻量化”。

只有在完成偏好询问、但用户明确表示“你决定 / 用默认 / 随便”时，才使用默认值：

- `output_language`: `zh`
- `output_format`: `markdown`
- `output_directory`: `./youtube-scripts/`

`timestamp_mode` 不作为默认必问偏好；它属于文稿排版细节，内部默认按 `sparse` 处理。只有用户明确提出“不要时间点”或“保留时间点”时，才覆盖这一内部默认。

## Workflow

1. 若用户直接提供 `raw_transcript`，优先使用它作为底稿；否则检查 `yt-dlp` 是否可用并获取 YouTube transcript。
2. 如果需要从 YouTube 获取内容，运行 `scripts/download_transcript.py <youtube_url>` 下载可用 transcript/captions 与元数据。
3. 运行 `scripts/parse_subtitle.py <subtitle_file>` 将字幕文件转成连续 transcript；这里的目标是得到可整理的连续底稿，而不是保留字幕展示形式。
4. 运行 `scripts/clean_transcript.py <parsed_json>` 做文稿级清洗：去除自动字幕的渐进重复、清理 `>>` 等轮次痕迹、合并短碎片，并在需要时剔除明显 sponsor/read 段。
5. 默认优先单 agent 直出文稿；仅当视频极长或上下文明显不足时，才使用 `scripts/plan_parallel_chunks.py <parsed_json>` 做切块，且各块输出必须服务于最终“文章化文稿”，而不是各自生成一套 transcript 页面。
6. 先按原始顺序理解讨论推进、主题切换和发言主体变化，再将碎片化口语重组为自然段和主题段。
7. 最终文稿应由宿主模型基于 cleaned transcript 直接生成，不依赖脚本规则拼接；脚本只负责底稿清洗、切分和导出。
8. 生成文稿时，必须遵守 `references/manuscript-generation.md` 中的写作提示词与输出约束。
9. 输出应优先像整理后的文稿：合并短句、移除明显语气词、修正标点和语法、增强段落连贯性，但不得增加原视频没有的新事实或评论。
10. 使用 `H1/H2/H3` 组织全文；章节标题应体现主题，不应只是时间轴导航。
11. 说话人切换清晰时，可通过分段体现对话关系；除非身份非常可靠，否则不要强行补真实姓名。
12. `timestamp_mode=sparse` 时，只在章节或较大段落入口保留少量时间点；`timestamp_mode=none` 时不输出时间戳。
13. 默认只输出文章化完整文稿，不附加核心要点、章节目录、元数据区块或完整逐字稿附录，除非用户明确要求。
14. 按用户选择生成 Markdown，若需要 Word，再基于 Markdown 运行 `scripts/convert_to_docx.py` 导出为 `.docx`。
15. 文稿必须覆盖整个可用 transcript，对应完整视频流程；除非源 transcript 本身残缺，否则不能只整理前半段或只挑重点段落。
16. 向用户返回输出路径、语言模式，以及任何降级处理说明；只有用户明确要求时间点处理时，才额外说明时间戳模式。

## Output Requirements

- 输出目标是“完整文稿”，不是“字幕清洗版”。
- 输出目标是“覆盖全程的完整文稿”，不是节选稿、提纲稿或摘要稿。
- 输出长度应尽量接近原始讨论密度；默认不做明显压缩，不把长段讨论改写成短摘要。
- 默认不省略正常正文内容；除非是明显噪音、重复或 sponsor/read，否则不要主动删减有效讨论。
- 保持原始讨论顺序，不打乱论证推进。
- 允许口语书面化，但不允许补充事实、评论、解释或结论。
- 只允许删除明显语气词、卡顿重复、自动字幕渐进重复和 sponsor/read 等非正文噪音。
- 删除明显的语气词、字幕断裂感、重复性填充片段。
- 自动字幕中的渐进重复、半句重复、词组回卷必须先清掉，再进行文稿化整理。
- sponsor/read、广告口播、站内导流等明显偏离正文主题的段落，应在整理前识别并按用户意图决定是否剔除；默认可剔除明显 sponsor/read。
- 段落应按主题与语义推进组织，而不是按每条字幕机械换行。
- 标题应是主题标题，如“创始人与内省”“技术作为进步引擎”，而不是“00:00 开场”。
- 默认不输出密集时间戳。
- 默认不输出元数据、核心要点、章节目录。
- 最终 Markdown 不应在正文前后插入解释性说明、系统提示或处理过程注释。
- 如果某一节原始内容很长，生成结果也应保持相近的信息量，而不是压缩成几段总结。
- 如果视频时长较长，章节可以变多，但正文覆盖范围不能缩短；“完整”优先于“简洁”。
- 只有在 transcript 源文件本身缺段、损坏或不可得时，才允许生成不完整文稿，并需明确标注为底稿不完整。
- 如果用户明确要求高保真、可核验、密集时间戳 transcript，应改用 `youtube-transcript`。
- Word 输出使用 `.docx`；当前不支持 PDF。

## Scripts

- `scripts/download_transcript.py`
  获取视频元数据和可用 transcript/captions。
- `scripts/parse_subtitle.py`
  将 VTT/SRT 解析为连续 transcript 与结构化条目。
- `scripts/clean_transcript.py`
  对解析后的 transcript 做去重、轮次痕迹清理、碎片合并和 sponsor/read 段识别。
- `scripts/plan_parallel_chunks.py`
  为长视频生成 chunk 计划，供文章化整理时并行处理。
- `scripts/convert_to_docx.py`
  将整理后的 Markdown 文稿导出为 Word 文档。

## References

按需读取以下参考文件，不要一次性全部加载：

- `references/language-modes.md`
  各语言输出模式与翻译约束。
- `references/manuscript-style.md`
  文章化文稿的写法、允许修改项与禁止项。
- `references/manuscript-generation.md`
  供宿主模型直接使用的文稿生成提示词与输出规则。
- `references/output-format.md`
  Markdown/Word 文稿的结构、标题和时间戳要求。
- `references/source-strategy.md`
  transcript 与字幕的处理优先级、输入降级策略。
- `references/legacy-notes.md`
  与旧版 `youtube-transcript` 的边界，以及旧方案不适合文稿化目标的原因。

## Failure Handling

- 如果视频没有任何可用 transcript/captions，明确告知用户该视频无可用底稿。
- 如果只有自动字幕，继续处理，但说明底稿来自自动转写。
- 如果 Word 导出依赖缺失，保留 Markdown 输出并说明缺少的依赖。
- 如果 transcript 质量较差，应优先保持原意并保守整理，不要为了“更像文章”而编写不存在的连接句。
- 如果用户真正想要的是逐字核验稿，应明确建议切换到 `youtube-transcript`。
