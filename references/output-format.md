# Output Format

## Required Structure

Markdown 和 Word 输出都应遵循这一结构：

1. 缩略图链接或说明
2. 视频标题
3. 来源、时长、语言、字幕来源
4. 核心要点
5. 章节目录
6. 完整文稿

默认应输出 `verbatim_transcript` 风格的完整文稿；只有用户明确要求更易读的整理版时，才切换为 `transcript` 或 `summary` 风格。

## Metadata Fields

建议至少包含：

- `来源`: YouTube URL
- `时长`: 视频时长
- `语言`: `中文`、`中英双语` 或原始语言
- `字幕来源`: `人工字幕` 或 `自动字幕`
- `输出格式`: `Markdown` 或 `Word`

## Timestamp Rules

- 所有正文都应尽量保留时间信息。
- 对话格式示例：
  `**[00:12] Speaker A**: 内容`
- 教程格式示例：
  `**[01:35]** 这里是整理后的正文`
- 无说话人标签的对话 transcript 也合法，示例：
  `**[00:12]** 这里是一段问句`
  `**[00:18]** 这里是另一位发言者的回答`
- transcript 风格下，时间戳应足够密集，便于用户对照视频回看。
- `verbatim_transcript` 风格下，时间戳应更密集，并且正文应尽量保持原始说话顺序与信息密度。
- 不要出现“04:01 一句，07:20 一句”这种跨度很大但内容极少的情况。
- 默认不要把 `>>`、轮次破折号等自动字幕标记直接显示在正文中；它们应在清洗阶段转化为更自然的换段。

## File Naming

- 文件名格式建议：`<sanitized_title>_<video_id>.<ext>`
- 删除文件名中的特殊字符和路径分隔符。
- Markdown 使用 `.md`
- Word 使用 `.docx`

## Word Export

- Word 导出以 Markdown 为中间表示。
- 如需 `.docx`，先生成完整 Markdown，再运行 `scripts/convert_to_docx.py`。
- 当前 skill 不提供 PDF 导出。

## Delivery

返回结果时至少说明：

- 输出文件路径
- 输出语言模式
- 输出风格
- 输出格式
- 章节数量或核心要点数量
- 如果有降级处理，也要明确说明
