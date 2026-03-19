#!/usr/bin/env python3
"""Clean parsed transcript JSON for manuscript-style generation."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path


COMMON_FILLERS = {
    "uh",
    "um",
    "you know",
    "like",
}

SPONSOR_PATTERNS = [
    re.compile(r"\bpresenting sponsor\b", re.IGNORECASE),
    re.compile(r"\bsponsor of this podcast\b", re.IGNORECASE),
    re.compile(r"\bthis episode is brought to you by\b", re.IGNORECASE),
    re.compile(r"\bgo to [a-z0-9.-]+\.(com|ai|io)\b", re.IGNORECASE),
    re.compile(r"\blearn how they can help\b", re.IGNORECASE),
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def decode_entities(text: str) -> str:
    return html.unescape(text)


def strip_speaker_markers(text: str) -> str:
    cleaned = re.sub(r"(?:^|\s)>>\s*", " ", text)
    cleaned = re.sub(r"(?:^|\s)-\s+", " ", cleaned)
    return normalize_whitespace(cleaned)


def remove_filler_runs(text: str) -> str:
    cleaned = text
    for filler in COMMON_FILLERS:
        pattern = re.compile(rf"\b{re.escape(filler)}\b(?:\s+\b{re.escape(filler)}\b)+", re.IGNORECASE)
        cleaned = pattern.sub(filler, cleaned)
    return cleaned


def dedupe_adjacent_word_runs(text: str) -> str:
    words = text.split()
    if not words:
        return text

    result: list[str] = []
    index = 0
    while index < len(words):
        matched = False
        max_window = min(12, (len(words) - index) // 2)
        for window in range(max_window, 1, -1):
            left = words[index:index + window]
            right = words[index + window:index + 2 * window]
            if left == right:
                result.extend(left)
                index += 2 * window
                matched = True
                break
        if matched:
            continue
        result.append(words[index])
        index += 1

    return " ".join(result)


def remove_stutter_repeats(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"\b([A-Za-z]+)\s+\1\b", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b([A-Za-z]+\s+[A-Za-z]+)\s+\1\b", r"\1", cleaned, flags=re.IGNORECASE)
    return cleaned


def dedupe_repeated_phrases(text: str) -> str:
    cleaned = text
    patterns = [
        re.compile(r"\b(.{8,120}?)\s+\1\b", re.IGNORECASE),
        re.compile(r"\b([A-Za-z][^.!?]{6,120}?)\s+\1(?=[,.!?])", re.IGNORECASE),
    ]
    changed = True
    while changed:
        changed = False
        for pattern in patterns:
            new_text = pattern.sub(r"\1", cleaned)
            if new_text != cleaned:
                cleaned = new_text
                changed = True
    return cleaned


def clean_entry_text(text: str) -> str:
    cleaned = decode_entities(text)
    cleaned = strip_speaker_markers(cleaned)
    cleaned = remove_filler_runs(cleaned)
    cleaned = dedupe_adjacent_word_runs(cleaned)
    cleaned = remove_stutter_repeats(cleaned)
    cleaned = dedupe_repeated_phrases(cleaned)
    cleaned = re.sub(r"\b([A-Za-z]+)(?:\s+\1\b)+", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.!?;:])", r"\1", cleaned)
    return normalize_whitespace(cleaned)


def is_probable_sponsor(entry_text: str) -> bool:
    lowered = entry_text.lower()
    return any(pattern.search(lowered) for pattern in SPONSOR_PATTERNS)


def merge_entries(entries: list[dict], min_gap: float = 1.2) -> list[dict]:
    if not entries:
        return []

    merged: list[dict] = [entries[0].copy()]
    for entry in entries[1:]:
        previous = merged[-1]
        entry_text = remove_leading_overlap(previous["text"], entry["text"])
        if not entry_text:
            previous["end"] = entry["end"]
            continue
        gap = entry["start"] - previous["end"]
        if gap <= min_gap and not re.search(r"[.!?。！？]$", previous["text"]):
            previous["text"] = normalize_whitespace(f'{previous["text"]} {entry_text}')
            previous["end"] = entry["end"]
            continue
        merged.append(
            {
                "start": entry["start"],
                "end": entry["end"],
                "text": entry_text,
            }
        )
    return merged


def remove_leading_overlap(previous_text: str, current_text: str) -> str:
    previous_words = previous_text.split()
    current_words = current_text.split()
    max_overlap = min(12, len(previous_words), len(current_words))
    for size in range(max_overlap, 1, -1):
        if previous_words[-size:] == current_words[:size]:
            return " ".join(current_words[size:])
    return current_text


def remove_near_duplicate_entries(entries: list[dict]) -> list[dict]:
    if not entries:
        return []

    result: list[dict] = []
    for entry in entries:
        if not entry["text"]:
            continue
        if result:
            previous = result[-1]
            if entry["text"] == previous["text"]:
                previous["end"] = entry["end"]
                continue
            if entry["text"] in previous["text"]:
                previous["end"] = entry["end"]
                continue
            if previous["text"] in entry["text"] and len(entry["text"]) > len(previous["text"]):
                previous["text"] = entry["text"]
                previous["end"] = entry["end"]
                continue
        result.append(entry.copy())
    return result


def clean_entries(entries: list[dict], drop_sponsor_segments: bool) -> list[dict]:
    cleaned_entries: list[dict] = []
    for entry in entries:
        cleaned_text = clean_entry_text(entry["text"])
        if not cleaned_text:
            continue
        if drop_sponsor_segments and is_probable_sponsor(cleaned_text):
            continue
        cleaned_entries.append(
            {
                "start": entry["start"],
                "end": entry["end"],
                "text": cleaned_text,
            }
        )

    cleaned_entries = remove_near_duplicate_entries(cleaned_entries)
    cleaned_entries = merge_entries(cleaned_entries)
    return cleaned_entries


def build_output(parsed: dict, cleaned_entries: list[dict]) -> dict:
    return {
        "total_entries": len(cleaned_entries),
        "total_duration": parsed.get("total_duration", "0:00"),
        "total_duration_seconds": parsed.get("total_duration_seconds", 0),
        "entries": cleaned_entries,
        "full_text": " ".join(entry["text"] for entry in cleaned_entries),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean parsed transcript JSON for manuscript generation.")
    parser.add_argument("parsed_json", help="Path to parsed transcript JSON")
    parser.add_argument("-o", "--output", help="Optional output path")
    parser.add_argument(
        "--drop-sponsor-segments",
        action="store_true",
        help="Drop likely sponsor/read segments from the cleaned transcript",
    )
    args = parser.parse_args()

    parsed = json.loads(Path(args.parsed_json).read_text(encoding="utf-8"))
    entries = parsed.get("entries", [])
    cleaned_entries = clean_entries(entries, drop_sponsor_segments=args.drop_sponsor_segments)
    output = build_output(parsed, cleaned_entries)

    rendered = json.dumps(output, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
