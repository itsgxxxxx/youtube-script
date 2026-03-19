# Output Format

## Required Structure

默认 Markdown 和 Word 输出都遵循以下结构：

1. H1 标题
2. H2/H3 章节正文
3. 如无额外要求，可在章节或较大段落入口处保留少量时间点

默认不包含：

- 元数据区块
- 核心要点
- 章节目录
- 完整逐字稿附录

## Timepoint Rules

- 时间点属于内部排版细节，不作为默认必问偏好。
- 默认可只在章节或较大段落前保留少量时间点。
- 如果用户明确要求不要时间点，则整篇不输出时间点。
- 不要使用密集时间戳破坏阅读流。
- 不要把每条字幕的时间都保留下来。

## File Naming

- 文件名格式建议：`<sanitized_title>_<video_id>_manuscript.<ext>`
- Markdown 使用 `.md`
- Word 使用 `.docx`

## Word Export

- Word 导出以 Markdown 为中间表示。
- 如需 `.docx`，先生成 Markdown，再运行 `scripts/convert_to_docx.py`。
- 当前 skill 不提供 PDF 导出。
