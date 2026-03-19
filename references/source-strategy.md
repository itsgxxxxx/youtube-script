# Source Strategy

## Priority

优先级如下：

1. 用户直接提供的完整 transcript
2. 可提取的连续 transcript / captions
3. 字幕文件解析后的连续文本

核心目标是获得“可整理的连续底稿”，而不是保留字幕展示形式。

## Transcript vs Subtitle

- transcript 适合做文稿化整理。
- 字幕只是一种底稿来源，不应决定最终输出形式。
- 即使底稿来自字幕文件，也应先转成连续 transcript，再进行文稿化处理。

## Degradation

- 如果只有自动字幕，也可以继续处理。
- 如果底稿质量一般，应保守整理，避免自作主张补句。
- 如果用户真正需要逐句核验，应该改用 `youtube-transcript`。
