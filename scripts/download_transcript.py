#!/usr/bin/env python3
"""Download YouTube video subtitles and metadata using yt-dlp."""

import json
import sys
import subprocess
import re


def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|\/v\/|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def download_transcript(url: str) -> dict:
    """Download subtitles and metadata for a YouTube video."""
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": f"Could not extract video ID from URL: {url}"}

    # Get video metadata
    try:
        metadata_cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            "--no-warnings",
            url,
        ]
        result = subprocess.run(
            metadata_cmd, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return {"error": f"Failed to get video metadata: {result.stderr}"}

        metadata = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "Timeout while fetching video metadata"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse video metadata"}

    # Determine available subtitle languages
    subtitles = metadata.get("subtitles", {})
    automatic_captions = metadata.get("automatic_captions", {})

    # Priority: manual subtitles > automatic captions
    # Prefer English, then other common languages
    preferred_langs = ["en", "en-US", "en-GB", "en-orig"]
    subtitle_source = None
    subtitle_lang = None

    # Check manual subtitles first (prefer English)
    for lang in preferred_langs:
        if lang in subtitles:
            subtitle_source = "manual"
            subtitle_lang = lang
            break

    # If no English manual subtitle, try any manual subtitle
    if not subtitle_lang:
        for lang in subtitles:
            subtitle_source = "manual"
            subtitle_lang = lang
            break

    # Fall back to automatic captions (prefer English)
    if not subtitle_lang:
        for lang in preferred_langs:
            if lang in automatic_captions:
                subtitle_source = "auto"
                subtitle_lang = lang
                break

    # If no English auto caption, try any auto caption
    if not subtitle_lang:
        for lang in automatic_captions:
            subtitle_source = "auto"
            subtitle_lang = lang
            break

    if not subtitle_lang:
        return {
            "error": "No subtitles available for this video",
            "video_id": video_id,
            "title": metadata.get("title", ""),
        }

    # Download subtitle file
    import tempfile
    import os

    temp_dir = tempfile.mkdtemp(prefix="yt_transcript_")

    sub_args = [
        "yt-dlp",
        "--no-download",
        "--no-warnings",
    ]

    if subtitle_source == "manual":
        sub_args.extend(["--write-subs", "--sub-langs", subtitle_lang])
    else:
        sub_args.extend(["--write-auto-subs", "--sub-langs", subtitle_lang])

    sub_args.extend([
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "-o", os.path.join(temp_dir, "%(id)s.%(ext)s"),
        url,
    ])

    try:
        result = subprocess.run(sub_args, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"error": "Timeout while downloading subtitles"}

    # Find the downloaded subtitle file
    subtitle_file = None
    for f in os.listdir(temp_dir):
        if f.endswith(".vtt"):
            subtitle_file = os.path.join(temp_dir, f)
            break

    if not subtitle_file:
        return {
            "error": "Subtitle file was not created",
            "video_id": video_id,
            "title": metadata.get("title", ""),
        }

    # Format duration
    duration_seconds = metadata.get("duration", 0)
    hours = duration_seconds // 3600
    minutes = (duration_seconds % 3600) // 60
    seconds = duration_seconds % 60
    if hours > 0:
        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        duration_str = f"{minutes}:{seconds:02d}"

    return {
        "video_id": video_id,
        "title": metadata.get("title", ""),
        "author": metadata.get("uploader", metadata.get("channel", "")),
        "duration": duration_seconds,
        "duration_str": duration_str,
        "description": metadata.get("description", ""),
        "subtitle_file": subtitle_file,
        "subtitle_language": subtitle_lang,
        "subtitle_source": subtitle_source,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: download_transcript.py <youtube_url>"}))
        sys.exit(1)

    result = download_transcript(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if "error" in result:
        sys.exit(1)
