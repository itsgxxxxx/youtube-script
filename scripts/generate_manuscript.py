#!/usr/bin/env python3
"""Generate manuscript-style Markdown from cleaned transcript JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TOPIC_KEYWORDS = [
    ("caffeine", "关于咖啡因与心跳"),
    ("introspection", "零内省的心态"),
    ("psychedelic", "迷幻药与创始人"),
    ("happiness", "优化影响力而非幸福"),
    ("technology", "技术作为进步的引擎"),
    ("founder", "创始人与管理者"),
    ("manager", "创始人与管理者"),
    ("venture", "为什么要创办这家公司"),
    ("hewlett", "惠普与英特尔的创始人传统"),
    ("intel", "惠普与英特尔的创始人传统"),
    ("mosaic", "Mosaic 与浏览器时代"),
    ("netscape", "Netscape 的商业与时代背景"),
    ("internet", "互联网扩张与争议"),
    ("elon", "Elon Musk 的管理方法"),
    ("spacex", "Elon Musk 的管理方法"),
    ("tesla", "Elon Musk 的管理方法"),
    ("starlink", "Starlink 与侧项目逻辑"),
]

AD_PATTERNS = [
    re.compile(r"\bsponsor\b", re.IGNORECASE),
    re.compile(r"\bramp\b", re.IGNORECASE),
    re.compile(r"\bgo to [a-z0-9.-]+\.(com|ai|io)\b", re.IGNORECASE),
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def remove_ad_entries(entries: list[dict]) -> list[dict]:
    result = []
    for entry in entries:
        text = entry["text"]
        if any(pattern.search(text) for pattern in AD_PATTERNS):
            continue
        result.append(entry)
    return result


def sentence_cleanup(text: str) -> str:
    cleaned = text
    replacements = [
        (r"\bI don't I don't\b", "I don't"),
        (r"\bit's it's\b", "it's"),
        (r"\bthey they\b", "they"),
        (r"\bwhat what\b", "what"),
        (r"\bthe the\b", "the"),
        (r"\bkind of\b", ""),
        (r"\byou know\b", ""),
        (r"\bum\b", ""),
        (r"\buh\b", ""),
    ]
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\s+([,.!?;:])", r"\1", cleaned)
    return cleaned


def choose_heading(text: str, index: int) -> str:
    lowered = text.lower()
    for keyword, heading in TOPIC_KEYWORDS:
        if keyword in lowered:
            return heading
    return f"章节 {index}"


def timestamp_label(seconds: float) -> str:
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def split_sections(entries: list[dict], target_span: int = 480) -> list[list[dict]]:
    sections: list[list[dict]] = []
    current: list[dict] = []
    start = None

    for entry in entries:
        if start is None:
            start = entry["start"]
        current.append(entry)
        span = entry["end"] - start
        text = entry["text"].lower()
        should_break = False
        if span >= target_span and len(current) >= 6:
            should_break = True
        if any(marker in text for marker in ["when you started", "another thing", "i want to tell you", "so when you", "the question is"]):
            if span >= 180 and len(current) >= 4:
                should_break = True
        if should_break:
            sections.append(current)
            current = []
            start = None

    if current:
        sections.append(current)

    return sections


def build_paragraphs(entries: list[dict], target_chars: int = 700) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []

    for entry in entries:
        text = sentence_cleanup(entry["text"])
        if not text:
            continue
        current.append(text)
        joined = " ".join(current)
        if len(joined) >= target_chars or re.search(r"[.!?]$", text):
            paragraphs.append(joined.strip())
            current = []

    if current:
        paragraphs.append(" ".join(current).strip())

    return paragraphs


def render_markdown(title: str, entries: list[dict], sparse_timestamps: bool) -> str:
    sections = split_sections(entries)
    parts = [f"# {title}"]

    for index, section in enumerate(sections, 1):
        section_text = " ".join(item["text"] for item in section)
        heading = choose_heading(section_text, index)
        if sparse_timestamps:
            parts.append(f"\n## [{timestamp_label(section[0]['start'])}] {heading}\n")
        else:
            parts.append(f"\n## {heading}\n")

        for paragraph in build_paragraphs(section):
            parts.append(paragraph)

    return "\n\n".join(parts).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate manuscript Markdown from cleaned transcript JSON.")
    parser.add_argument("cleaned_json", help="Path to cleaned transcript JSON")
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument("-o", "--output", required=True, help="Output Markdown file")
    parser.add_argument("--timestamp-mode", choices=["sparse", "none"], default="sparse")
    args = parser.parse_args()

    data = load_json(Path(args.cleaned_json))
    entries = remove_ad_entries(data.get("entries", []))
    markdown = render_markdown(
        title=args.title,
        entries=entries,
        sparse_timestamps=args.timestamp_mode == "sparse",
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
