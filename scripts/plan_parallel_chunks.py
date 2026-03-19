#!/usr/bin/env python3
"""Plan transcript chunking for long-form videos and emit chunk JSON files."""

import argparse
import json
import math
import os
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def choose_strategy(total_seconds: float, prefer_parallel: bool = False) -> dict:
    if total_seconds <= 30 * 60:
        if prefer_parallel and total_seconds > 20 * 60:
            chunk_count = 2
            chunk_seconds = math.ceil(total_seconds / chunk_count)
            return {
                "mode": "parallel_optional",
                "reason": "Video is near 30 minutes; optional 2-way split improves latency.",
                "chunk_count": chunk_count,
                "chunk_seconds": chunk_seconds,
            }
        return {
            "mode": "single",
            "reason": "Video is short enough for a single agent pass.",
            "chunk_count": 1,
            "chunk_seconds": math.ceil(total_seconds),
        }

    if total_seconds <= 60 * 60:
        return {
            "mode": "parallel",
            "reason": "Use 4 chunks of about 15 minutes for hour-long videos.",
            "chunk_count": 4,
            "chunk_seconds": 15 * 60,
        }

    if total_seconds <= 120 * 60:
        return {
            "mode": "parallel",
            "reason": "Use 4 chunks of about 30 minutes for 1-2 hour videos.",
            "chunk_count": 4,
            "chunk_seconds": math.ceil(total_seconds / 4),
        }

    chunk_seconds = 30 * 60
    chunk_count = math.ceil(total_seconds / chunk_seconds)
    return {
        "mode": "parallel",
        "reason": "Use about 30-minute chunks for very long videos.",
        "chunk_count": chunk_count,
        "chunk_seconds": math.ceil(total_seconds / chunk_count),
    }


def build_chunk(
    entries: list[dict],
    chunk_id: int,
    core_start: float,
    core_end: float,
    overlap_seconds: int,
    total_seconds: float,
) -> dict:
    context_start = max(0, core_start - overlap_seconds)
    context_end = min(total_seconds, core_end + overlap_seconds)

    chunk_entries = [
        entry
        for entry in entries
        if entry["end"] > context_start and entry["start"] < context_end
    ]
    core_entries = [
        entry
        for entry in entries
        if entry["end"] > core_start and entry["start"] < core_end
    ]

    return {
        "chunk_id": chunk_id,
        "core_range": {
            "start_seconds": int(core_start),
            "end_seconds": int(core_end),
            "start": format_timestamp(core_start),
            "end": format_timestamp(core_end),
        },
        "context_range": {
            "start_seconds": int(context_start),
            "end_seconds": int(context_end),
            "start": format_timestamp(context_start),
            "end": format_timestamp(context_end),
        },
        "instructions": {
            "use_context_only_for_continuity": True,
            "authoritative_output_range": f"{format_timestamp(core_start)} - {format_timestamp(core_end)}",
            "do_not_duplicate_content_outside_core_range": True,
        },
        "total_entries": len(chunk_entries),
        "core_entries": core_entries,
        "context_entries": chunk_entries,
        "core_text": " ".join(entry["text"] for entry in core_entries),
        "context_text": " ".join(entry["text"] for entry in chunk_entries),
    }


def plan_chunks(parsed_data: dict, output_dir: Path, overlap_seconds: int, prefer_parallel: bool) -> dict:
    entries = parsed_data.get("entries", [])
    total_seconds = parsed_data.get("total_duration_seconds")
    if total_seconds is None:
        total_seconds = int(entries[-1]["end"]) if entries else 0

    strategy = choose_strategy(total_seconds, prefer_parallel=prefer_parallel)
    chunk_seconds = strategy["chunk_seconds"]
    chunk_count = strategy["chunk_count"]

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir = output_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    chunks = []
    if chunk_count == 1:
        chunks.append(build_chunk(entries, 1, 0, total_seconds, overlap_seconds, total_seconds))
    else:
        for index in range(chunk_count):
            core_start = index * chunk_seconds
            core_end = total_seconds if index == chunk_count - 1 else min(total_seconds, (index + 1) * chunk_seconds)
            if core_start >= total_seconds:
                break
            chunks.append(
                build_chunk(
                    entries,
                    index + 1,
                    core_start,
                    core_end,
                    overlap_seconds,
                    total_seconds,
                )
            )

    for chunk in chunks:
        chunk_name = f"chunk_{chunk['chunk_id']:02d}_{chunk['core_range']['start_seconds']:05d}_{chunk['core_range']['end_seconds']:05d}.json"
        chunk_path = chunks_dir / chunk_name
        with open(chunk_path, "w", encoding="utf-8") as handle:
            json.dump(chunk, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        chunk["file"] = str(chunk_path)

    plan = {
        "total_duration_seconds": int(total_seconds),
        "total_duration": format_timestamp(total_seconds),
        "strategy": strategy,
        "overlap_seconds": overlap_seconds,
        "chunks": [
            {
                "chunk_id": chunk["chunk_id"],
                "file": chunk["file"],
                "core_range": chunk["core_range"],
                "context_range": chunk["context_range"],
                "total_entries": chunk["total_entries"],
            }
            for chunk in chunks
        ],
    }

    plan_path = output_dir / "plan.json"
    with open(plan_path, "w", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return plan


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan chunked transcript processing for long-form YouTube videos."
    )
    parser.add_argument("parsed_json", help="Path to parsed transcript JSON")
    parser.add_argument(
        "-o",
        "--output-dir",
        help="Directory to write plan.json and chunk files",
    )
    parser.add_argument(
        "--overlap-seconds",
        type=int,
        default=45,
        help="Overlap to include before/after each chunk for continuity",
    )
    parser.add_argument(
        "--prefer-parallel",
        action="store_true",
        help="Split near-30-minute videos into 2 chunks when helpful",
    )
    args = parser.parse_args()

    with open(args.parsed_json, "r", encoding="utf-8") as handle:
        parsed_data = json.load(handle)

    output_dir = Path(args.output_dir) if args.output_dir else Path(args.parsed_json).with_suffix("")
    plan = plan_chunks(parsed_data, output_dir, args.overlap_seconds, args.prefer_parallel)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
