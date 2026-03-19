# Model Routing

## Principle

如果宿主支持为 subagent 或子任务单独指定模型，则把低推理、重复性高、token 消耗大的工作路由到更便宜的小模型，把高判断力任务留给强模型。

如果宿主不支持按子任务选模型，则忽略本文件，仍按同一模型执行。

## Strong Model Tasks

以下任务应优先使用更强模型：

- 主 agent 编排
- 视频类型判断
- 说话人消歧
- 跨 chunk 去重与边界修复
- 全局目录与章节统一
- 最终质检

## Efficient Model Tasks

以下任务适合更便宜的小模型：

- chunk 级最小清洗
- chunk 级翻译
- 格式化为 mergeable Markdown
- 将已确定结构的内容转成 Word/Markdown

## Host-Specific Guidance

- Claude Code:
  若支持任务级模型选择，优先把 chunk 翻译/轻清洗路由到 Sonnet，一致性审校和合并保留给更强模型。
- Codex / OpenAI:
  若支持任务级模型选择，优先把 chunk 翻译/轻清洗路由到 GPT-5.4 mini 这类更省成本的小模型，主控合并与质检使用当前更强模型。

## Safety Rule

如果小模型输出开始出现明显漏译、过度摘要、时间戳稀疏或内容顺序错乱，应立即把该任务回退到强模型。
