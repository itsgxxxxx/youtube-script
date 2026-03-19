#!/usr/bin/env python3
"""Parse VTT/SRT subtitle files into structured text with timestamps."""

import argparse
import json
import re
import sys


def parse_timestamp(ts: str) -> float:
    """Convert timestamp string (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    ts = ts.strip()
    parts = ts.replace(",", ".").split(":")

    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(parts[0])


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS or HH:MM:SS format."""
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"


def parse_vtt(file_path: str) -> list[dict]:
    """Parse a VTT subtitle file into a list of subtitle entries."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove VTT header and metadata
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    # Remove style blocks
    content = re.sub(r"STYLE\n.*?\n\n", "", content, flags=re.DOTALL)
    # Remove NOTE blocks
    content = re.sub(r"NOTE\n.*?\n\n", "", content, flags=re.DOTALL)

    entries = []
    blocks = re.split(r"\n\n+", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue

        # Find timestamp line
        timestamp_line = None
        text_lines = []

        for line in lines:
            if "-->" in line:
                timestamp_line = line
            elif timestamp_line is not None:
                # Remove VTT tags like <c>, </c>, <00:00:01.000>, etc.
                clean = re.sub(r"<[^>]+>", "", line)
                clean = clean.strip()
                if clean:
                    text_lines.append(clean)

        if timestamp_line and text_lines:
            parts = timestamp_line.split("-->")
            start = parse_timestamp(parts[0].strip().split(" ")[0])
            end = parse_timestamp(parts[1].strip().split(" ")[0])
            text = " ".join(text_lines)

            # Skip duplicate entries (common in auto-generated subtitles)
            if entries and entries[-1]["text"] == text:
                entries[-1]["end"] = end
                continue

            entries.append({
                "start": start,
                "end": end,
                "text": text,
            })

    return entries


def parse_srt(file_path: str) -> list[dict]:
    """Parse an SRT subtitle file into a list of subtitle entries."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = re.split(r"\n\n+", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # Skip sequence number (first line)
        timestamp_line = lines[1]
        text_lines = lines[2:]

        if "-->" in timestamp_line:
            parts = timestamp_line.split("-->")
            start = parse_timestamp(parts[0].strip())
            end = parse_timestamp(parts[1].strip())
            text = " ".join(line.strip() for line in text_lines if line.strip())

            if entries and entries[-1]["text"] == text:
                entries[-1]["end"] = end
                continue

            entries.append({
                "start": start,
                "end": end,
                "text": text,
            })

    return entries


def merge_short_entries(entries: list[dict], min_gap: float = 1.0) -> list[dict]:
    """Merge entries that are very close together into sentences."""
    if not entries:
        return []

    merged = [entries[0].copy()]

    for entry in entries[1:]:
        prev = merged[-1]
        gap = entry["start"] - prev["end"]

        # Merge if gap is small and previous doesn't end with sentence-ending punctuation
        if gap < min_gap and not re.search(r"[.!?。！？]$", prev["text"]):
            prev["text"] += " " + entry["text"]
            prev["end"] = entry["end"]
        else:
            merged.append(entry.copy())

    return merged


def deduplicate_entries(entries: list[dict]) -> list[dict]:
    """Remove duplicate or near-duplicate subtitle entries."""
    if not entries:
        return []

    result = [entries[0]]

    for entry in entries[1:]:
        prev = result[-1]
        # Skip if text is identical or if current text is a substring of previous
        if entry["text"] == prev["text"]:
            prev["end"] = entry["end"]
            continue
        if entry["text"] in prev["text"]:
            prev["end"] = entry["end"]
            continue
        # Skip if previous text is a substring of current (auto-subs progressive reveal)
        if prev["text"] in entry["text"]:
            prev["text"] = entry["text"]
            prev["end"] = entry["end"]
            continue
        result.append(entry)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a VTT/SRT subtitle file into structured transcript JSON."
    )
    parser.add_argument("subtitle_file", help="Path to a .vtt or .srt subtitle file")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path to save the parsed JSON. Defaults to stdout only.",
    )
    args = parser.parse_args()

    file_path = args.subtitle_file

    if file_path.endswith(".vtt"):
        entries = parse_vtt(file_path)
    elif file_path.endswith(".srt"):
        entries = parse_srt(file_path)
    else:
        print(json.dumps({"error": f"Unsupported format: {file_path}"}))
        sys.exit(1)

    # Clean up entries
    entries = deduplicate_entries(entries)
    entries = merge_short_entries(entries)

    output = {
        "total_entries": len(entries),
        "total_duration": format_timestamp(entries[-1]["end"]) if entries else "0:00",
        "total_duration_seconds": int(entries[-1]["end"]) if entries else 0,
        "entries": entries,
        "full_text": " ".join(e["text"] for e in entries),
    }

    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.write("\n")

    print(rendered)


if __name__ == "__main__":
    main()
