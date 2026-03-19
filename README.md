# youtube-script

一个根据 YouTube URL 或原始 transcript 生成覆盖全程完整文稿的 skill，skill 名称为 `youtube-script`。

支持 Claude Code、Codex 等 CLI Agent，直接使用其模型进行文稿清理、重组和格式化工作。

## 功能

- 根据 YouTube URL 或原始 transcript 生成完整文稿
- 将口语化 transcript 整理成可阅读的文章式稿件
- 默认不做摘要化压缩，保留接近原始讨论的信息密度
- 支持中文、英文、双语输出
- 支持轻量化 Markdown 和 Word 输出

## 安装

可以直接对你的 Claude Code 或 Codex 说：

```text
帮我安装 `itsgxxxxx/youtube-transcript` 里面的 `youtube-script` skill。
```
