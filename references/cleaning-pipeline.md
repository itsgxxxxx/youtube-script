# Cleaning Pipeline

## Goal

文稿质量的基础不是“总结能力”，而是先把自动字幕底稿清理干净。

## Required Cleaning Order

1. 先解析为连续 transcript
2. 清理自动字幕的渐进重复和半句回卷
3. 去掉 `>>`、破折号轮次等转写痕迹
4. 合并过短、过碎的片段
5. 识别 sponsor/read 或明显广告段
6. 再进入文章化整理

## What Must Be Removed Early

- 单词或短语重复两次以上
- 自动字幕的 progressive reveal 重复
- `>>`、`-`、HTML 转义残留
- 对正文无价值的 sponsor/read 口播

## What Must Be Preserved

- 原始讨论顺序
- 重要铺垫和上下文
- 问答关系和发言推进
- 可支持后续生成章节标题的主题边界
