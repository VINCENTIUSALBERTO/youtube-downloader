"""
URL validators for YouTube Downloader Bot.

Provides YouTube URL validation and video info extraction.
"""

import re
import asyncio
import json
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# YouTube URL patterns
YOUTUBE_VIDEO_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)"
    r"([a-zA-Z0-9_-]+)"
)

YOUTUBE_PLAYLIST_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)"
)


@dataclass
class VideoInfo:
    """Video information extracted from URL."""
    
    video_id: str
    title: str
    duration: str
    duration_seconds: int
    thumbnail: str
    channel: str
    view_count: int
    upload_date: str
    description: str
    url: str
    is_playlist: bool = False
    playlist_count: int = 0


def validate_youtube_url(url: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate if URL is a valid YouTube URL.
    
    Returns:
        Tuple of (is_valid, url_type, video_id_or_playlist_id)
        url_type: 'video', 'playlist', or 'invalid'
    """
    # Check for playlist
    playlist_match = YOUTUBE_PLAYLIST_PATTERN.search(url)
    if playlist_match:
        return True, "playlist", playlist_match.group(1)
    
    # Check for video
    video_match = YOUTUBE_VIDEO_PATTERN.search(url)
    if video_match:
        return True, "video", video_match.group(1)
    
    return False, "invalid", None


async def get_video_info(url: str, cookies_file: Optional[str] = None) -> Optional[VideoInfo]:
    """
    Get video information using yt-dlp.
    
    Args:
        url: YouTube URL
        cookies_file: Optional path to cookies file
        
    Returns:
        VideoInfo object or None if failed
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--no-warnings",
        "--no-check-certificate",
        "--extractor-args", "youtube:player_client=web,default",
    ]
    
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(url)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30,
        )
        
        if process.returncode != 0:
            logger.error(f"yt-dlp error: {stderr.decode()[:200]}")
            return None
        
        data = json.loads(stdout.decode())
        
        # Format duration
        duration_seconds = data.get("duration", 0) or 0
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        duration_str = f"{minutes}:{seconds:02d}"
        
        # Format upload date
        upload_date = data.get("upload_date", "")
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        
        return VideoInfo(
            video_id=data.get("id", ""),
            title=data.get("title", "Unknown Title"),
            duration=duration_str,
            duration_seconds=duration_seconds,
            thumbnail=data.get("thumbnail", ""),
            channel=data.get("channel", data.get("uploader", "Unknown")),
            view_count=data.get("view_count", 0) or 0,
            upload_date=upload_date,
            description=data.get("description", "")[:500],
            url=url,
        )
        
    except asyncio.TimeoutError:
        logger.error("Timeout getting video info")
        return None
    except json.JSONDecodeError:
        logger.error("Failed to parse video info JSON")
        return None
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None


async def get_playlist_info(url: str, cookies_file: Optional[str] = None) -> Optional[dict]:
    """
    Get playlist information using yt-dlp.
    
    Args:
        url: YouTube playlist URL
        cookies_file: Optional path to cookies file
        
    Returns:
        Dict with playlist info or None if failed
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--no-download",
        "--no-warnings",
        "--no-check-certificate",
        "--extractor-args", "youtube:player_client=web,default",
    ]
    
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    
    cmd.append(url)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=60,
        )
        
        if process.returncode != 0:
            logger.error(f"yt-dlp error: {stderr.decode()[:200]}")
            return None
        
        # Parse each line as JSON (one per video in playlist)
        lines = stdout.decode().strip().split("\n")
        videos = []
        playlist_title = "Unknown Playlist"
        
        for line in lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get("_type") == "playlist":
                        playlist_title = data.get("title", playlist_title)
                    else:
                        videos.append({
                            "id": data.get("id", ""),
                            "title": data.get("title", "Unknown"),
                            "duration": data.get("duration", 0),
                        })
                except json.JSONDecodeError:
                    continue
        
        return {
            "title": playlist_title,
            "count": len(videos),
            "videos": videos[:50],  # Limit to first 50 for display
            "url": url,
        }
        
    except asyncio.TimeoutError:
        logger.error("Timeout getting playlist info")
        return None
    except Exception as e:
        logger.error(f"Error getting playlist info: {e}")
        return None
