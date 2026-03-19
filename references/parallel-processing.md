# Parallel Processing

## Goal

长视频不要把完整字幕一次性交给单个 agent。主 agent 负责编排，subagent 负责时间块处理，最后再由主 agent 合并结果。

## Chunk Strategy

默认按总时长选择策略：

- `<= 30 分钟`
  默认单 agent。若视频接近 30 分钟且更关注速度，可选 2 个约 15 分钟 chunk。
- `> 30 分钟 且 <= 60 分钟`
  使用 4 个约 15 分钟 chunk。
- `> 60 分钟 且 <= 120 分钟`
  使用 4 个约 30 分钟 chunk。
- `> 120 分钟`
  使用约 30 分钟一个 chunk，自动计算 chunk 数量。

所有 chunk 默认加 `45 秒` 上下文重叠，避免在分界处丢失语义。

## Processing Order

1. 主 agent 下载字幕并解析为结构化 JSON。
2. 主 agent 运行 `scripts/plan_parallel_chunks.py` 生成 `plan.json` 和每个 chunk 的 JSON 文件。
3. 若环境支持 subagent：
   每个 subagent 处理一个 chunk。
4. 若环境不支持 subagent：
   主 agent 仍按 chunk 顺序逐个处理。
5. 主 agent 合并各 chunk 输出，统一章节目录、全局核心要点和最终文稿。
6. 若宿主支持子任务模型选择，则 chunk 翻译和轻清洗优先路由给更省成本的小模型，主控合并和质检留给强模型。

## Subagent Responsibilities

每个 subagent 只负责自己的 `core_range`：

- 清洗和整理该时间段的文本
- 生成局部章节标题和段落
- 标识说话人或教程步骤
- 保留时间戳
- 在 transcript 模式下产出高保真、可合并的 Markdown 片段，优先保留发言顺序与内容密度
- 在 `verbatim_transcript` 模式下，只做最小必要清洗，禁止摘要

每个 chunk 文件里还会带 `context_range`，仅用于连续性判断，不应把上下文重复写入最终正文。

## Main Agent Responsibilities

主 agent 负责：

- 决定是否启用并行
- 分发 chunk
- 去重边界处内容
- 统一章节风格
- 汇总全局核心要点
- 拼接最终 Markdown/Word 输出

## Merge Rules

- 相邻 chunk 的重叠区域只能保留一份。
- 目录由主 agent 统一生成，不让各 subagent 各写一套全局目录。
- 全局核心要点最后统一提炼，不直接拼接各 chunk 的要点列表。
- 对话类视频要确保 chunk 边界不把同一轮发言拆成重复内容。
- 不要在合并时把 transcript 重新压缩成摘要式短段落，除非用户明确要求 summary 风格。
- 如果使用了小模型做 chunk 处理，主 agent 必须抽查时间戳密度、内容遗漏和边界重复，必要时回退为强模型重做。
