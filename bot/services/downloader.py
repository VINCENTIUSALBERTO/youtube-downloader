"""
Downloader service for YouTube Downloader Bot.

Handles downloading YouTube videos and audio using yt-dlp.
"""

import asyncio
import logging
import os
import uuid
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Callable, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of a download operation."""
    
    success: bool
    file_path: Optional[Path]
    title: str
    duration: str
    file_size: int
    error: Optional[str] = None


# Format configurations
FORMAT_OPTIONS = {
    "mp3": {
        "format": "bestaudio/best",
        "extract_audio": True,
        "audio_format": "mp3",
        "audio_quality": "192K",
        "label": "🎵 MP3 (Audio Only)",
    },
    "360p": {
        "format": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "label": "📹 Video 360p",
    },
    "720p": {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "label": "📺 Video 720p",
    },
    "1080p": {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "label": "🎬 Video 1080p",
    },
    "best": {
        "format": "bestvideo+bestaudio/best",
        "label": "⭐ Best Quality",
    },
}


class DownloaderService:
    """Service for downloading YouTube videos."""
    
    def __init__(self, download_dir: str, cookies_file: Optional[str] = None):
        """
        Initialize downloader service.
        
        Args:
            download_dir: Base directory for downloads
            cookies_file: Optional path to cookies file
        """
        self.download_dir = download_dir
        self.cookies_file = cookies_file
        Path(download_dir).mkdir(parents=True, exist_ok=True)
    
    async def download(
        self,
        url: str,
        format_key: str,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> DownloadResult:
        """
        Download video/audio from YouTube.
        
        Args:
            url: YouTube URL
            format_key: Format option key (mp3, 360p, etc.)
            progress_callback: Optional async callback for progress updates
            
        Returns:
            DownloadResult with file path and metadata
        """
        format_opts = FORMAT_OPTIONS.get(format_key, FORMAT_OPTIONS["720p"])
        
        # Create unique download directory
        unique_id = str(uuid.uuid4())[:8]
        download_path = Path(self.download_dir) / unique_id
        download_path.mkdir(parents=True, exist_ok=True)
        
        # Build yt-dlp command
        output_template = str(download_path / "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--format", format_opts["format"],
            "--output", output_template,
            "--restrict-filenames",
            "--no-playlist",
            "--progress",
            "--newline",
            "--no-check-certificate",
            "--extractor-args", "youtube:player_client=default,mweb",
            "--retries", "3",
            "--extractor-retries", "3",
        ]
        
        # Add cookies if available
        if self.cookies_file and os.path.exists(self.cookies_file):
            cmd.extend(["--cookies", self.cookies_file])
            logger.info(f"Using cookies file: {self.cookies_file}")
        
        # Add audio extraction for MP3
        if format_opts.get("extract_audio"):
            cmd.extend([
                "--extract-audio",
                "--audio-format", format_opts.get("audio_format", "mp3"),
                "--audio-quality", format_opts.get("audio_quality", "192K"),
            ])
        
        cmd.append(url)
        
        try:
            if progress_callback:
                await progress_callback("⬇️ Memulai download...")
            
            # Run download
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()[:500] if stderr else "Unknown error"
                logger.error(f"Download failed: {error_msg}")
                return DownloadResult(
                    success=False,
                    file_path=None,
                    title="",
                    duration="",
                    file_size=0,
                    error=self._parse_error(error_msg),
                )
            
            # Find downloaded file
            files = list(download_path.iterdir())
            if not files:
                return DownloadResult(
                    success=False,
                    file_path=None,
                    title="",
                    duration="",
                    file_size=0,
                    error="Tidak ada file yang terdownload",
                )
            
            downloaded_file = files[0]
            file_size = downloaded_file.stat().st_size
            title = downloaded_file.stem
            
            # Get duration from filename or estimate
            duration = await self._get_duration(str(downloaded_file))
            
            logger.info(f"Downloaded: {downloaded_file} ({file_size} bytes)")
            
            return DownloadResult(
                success=True,
                file_path=downloaded_file,
                title=title,
                duration=duration,
                file_size=file_size,
            )
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            # Cleanup on error
            self._cleanup_directory(download_path)
            return DownloadResult(
                success=False,
                file_path=None,
                title="",
                duration="",
                file_size=0,
                error=str(e),
            )
    
    async def download_playlist(
        self,
        url: str,
        format_key: str,
        progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> List[DownloadResult]:
        """
        Download all videos from a playlist.
        
        Args:
            url: YouTube playlist URL
            format_key: Format option key
            progress_callback: Optional async callback for progress updates
            
        Returns:
            List of DownloadResult for each video
        """
        results = []
        
        # Get playlist videos
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s",
            "--no-check-certificate",
            "--extractor-args", "youtube:player_client=default,mweb",
            "--retries", "3",
            "--extractor-retries", "3",
            url,
        ]
        
        if self.cookies_file and os.path.exists(self.cookies_file):
            cmd.insert(1, "--cookies")
            cmd.insert(2, self.cookies_file)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            
            video_ids = stdout.decode().strip().split("\n")
            video_ids = [vid for vid in video_ids if vid.strip()]
            
            if progress_callback:
                await progress_callback(f"📋 Playlist berisi {len(video_ids)} video")
            
            for i, video_id in enumerate(video_ids):
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                if progress_callback:
                    await progress_callback(f"⬇️ Download {i+1}/{len(video_ids)}...")
                
                result = await self.download(video_url, format_key)
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Playlist download error: {e}")
            return results
    
    async def _get_duration(self, file_path: str) -> str:
        """Get duration of media file using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path,
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            
            duration_seconds = float(stdout.decode().strip())
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            return f"{minutes}:{seconds:02d}"
        except Exception:
            return "Unknown"
    
    def _parse_error(self, error_msg: str) -> str:
        """Parse yt-dlp error message to user-friendly message."""
        if "Video unavailable" in error_msg or "not available" in error_msg:
            return "Video tidak tersedia atau telah dihapus."
        elif "age" in error_msg.lower():
            return "Video memerlukan verifikasi umur. Silakan konfigurasi cookies."
        elif "private" in error_msg.lower():
            return "Video bersifat private dan tidak dapat diakses."
        elif "copyright" in error_msg.lower():
            return "Video diblokir karena hak cipta."
        elif "Sign in" in error_msg:
            return "Video memerlukan login. Silakan konfigurasi cookies."
        elif "HTTP Error 403" in error_msg or "403: Forbidden" in error_msg:
            return "Gagal mengunduh video (HTTP 403). Silakan coba lagi atau konfigurasi cookies."
        else:
            return f"Terjadi kesalahan: {error_msg[:200]}"
    
    def _cleanup_directory(self, path: Path) -> None:
        """Clean up download directory."""
        try:
            if path.exists():
                for file in path.iterdir():
                    file.unlink()
                path.rmdir()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def cleanup_file(self, file_path: Path) -> None:
        """Clean up downloaded file and its directory."""
        try:
            if file_path and file_path.exists():
                parent = file_path.parent
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
                
                # Try to remove parent directory if empty
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
