# Legacy Notes

## Why This Skill Exists

旧版 `youtube-transcript` 的目标是高保真 transcript：

- 时间戳密集
- 可回看、可核验
- 更接近字幕/转录工作流

这与“完整文稿”目标不同。

## Why The Old Approach Felt Off

当目标是生成可阅读文稿时，旧方案容易出现这些问题：

- 过于强调时间戳和定位
- 结构更像 transcript，而不像文章
- 元数据、目录、要点等区块打断阅读流
- 以“字幕整理”为中心，而不是以“文稿化重组”为中心

## Boundary

- 想要高保真 transcript：使用 `youtube-transcript`
- 想要可读的整理稿、访谈稿、文章式文稿：使用 `youtube-manuscript`
