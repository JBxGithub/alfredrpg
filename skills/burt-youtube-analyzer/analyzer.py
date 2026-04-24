#!/usr/bin/env python3
"""
Burt's YouTube Analyzer v2.0 - Private Skill with Communication Protocol
Extracts and analyzes YouTube video metadata for discussion
Protocol: Share → Analyze → Discuss → Output
"""

import json
import subprocess
import sys
from typing import Dict, Optional

def extract_video_info(url: str) -> Optional[Dict]:
    """Extract video metadata using yt-dlp."""
    cmd = [
        "yt-dlp", "--dump-json", "--skip-download",
        "--no-warnings", url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout.strip().split('\n')[0])
    return None

def analyze_video(url: str, content_summary: str = "") -> Dict:
    """
    Analyze a YouTube video and return structured data.
    
    Args:
        url: YouTube video URL (supports shorts, watch, youtu.be)
        content_summary: Burt's brief description of the content
    
    Returns:
        Dict with video metadata and analysis
    """
    info = extract_video_info(url)
    if not info:
        return {"error": "Could not extract video info", "url": url}
    
    # Extract key information
    result = {
        "success": True,
        "protocol_version": "2.0",
        "url": url,
        "title": info.get("title"),
        "author": info.get("uploader"),
        "channel": info.get("channel"),
        "duration_seconds": info.get("duration"),
        "duration_formatted": info.get("duration_string"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "upload_date": info.get("upload_date"),
        "description": info.get("description", "")[:800] + "..." if len(info.get("description", "")) > 800 else info.get("description", ""),
        "categories": info.get("categories", []),
        "tags": info.get("tags", [])[:15],
        "is_short": info.get("media_type") == "short" or "/shorts/" in url,
        "thumbnail": info.get("thumbnail"),
        "content_summary": content_summary,  # Burt's input
    }
    
    # Generate discussion prompts
    result["discussion_prompts"] = generate_discussion_prompts(result)
    
    # Generate curation analysis (v2.0)
    result["curation_analysis"] = analyze_curation_pattern(result)
    
    return result

def generate_discussion_prompts(video_data: Dict) -> list:
    """Generate discussion prompts based on video data."""
    prompts = []
    
    if video_data.get("is_short"):
        prompts.append("這是 YouTube Shorts，適合快速消費內容")
    
    view_count = video_data.get("view_count", 0)
    if view_count > 100000:
        prompts.append(f"熱門影片（{view_count:,} 觀看），值得關注")
    elif view_count > 10000:
        prompts.append(f"有一定熱度（{view_count:,} 觀看）")
    
    categories = video_data.get("categories", [])
    if "Education" in categories:
        prompts.append("教育類內容，可能有學習價值")
    if "Music" in categories:
        prompts.append("音樂類內容")
    if "Entertainment" in categories:
        prompts.append("娛樂類內容")
    
    # Add protocol prompt
    prompts.append("💡 Burt 請簡述內容，我們開始討論")
    
    return prompts

def analyze_curation_pattern(video_data: Dict) -> Dict:
    """Analyze if this is a curation/repost pattern."""
    description = video_data.get("description", "")
    
    # Check for repost indicators
    is_repost = any(keyword in description.lower() for keyword in [
        "原片", "出處", "轉載", "original", "source", "repost"
    ])
    
    analysis = {
        "is_curation": is_repost,
        "pattern": "內容策展" if is_repost else "原創內容",
        "value_add": "轉載者加入自身觀點/社群導流" if is_repost else "原創者直接輸出",
    }
    
    return analysis

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: analyze_youtube.py <url> [content_summary]"}))
        sys.exit(1)
    
    url = sys.argv[1]
    content_summary = sys.argv[2] if len(sys.argv) > 2 else ""
    
    result = analyze_video(url, content_summary)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
