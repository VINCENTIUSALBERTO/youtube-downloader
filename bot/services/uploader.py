"""
Uploader service for YouTube Downloader Bot.

Handles uploading files to Telegram and Google Drive.
"""

import asyncio
import logging
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from telegram import Bot

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    """Result of an upload operation."""
    
    success: bool
    delivery_method: str
    drive_link: Optional[str] = None
    error: Optional[str] = None


class UploaderService:
    """Service for uploading files."""
    
    def __init__(self, rclone_remote: str):
        """
        Initialize uploader service.
        
        Args:
            rclone_remote: rclone remote destination
        """
        self.rclone_remote = rclone_remote
    
    async def upload_to_telegram(
        self,
        bot: Bot,
        chat_id: int,
        file_path: Path,
        caption: str = "",
        is_audio: bool = False,
    ) -> UploadResult:
        """
        Upload file to Telegram.
        
        Args:
            bot: Telegram Bot instance
            chat_id: Target chat ID
            file_path: Path to file to upload
            caption: Optional caption
            is_audio: Whether to send as audio (MP3)
            
        Returns:
            UploadResult
        """
        try:
            file_size = file_path.stat().st_size
            max_size = 500 * 1024 * 1024  # 500MB Telegram Bot API limit for bots
            
            if file_size > max_size:
                return UploadResult(
                    success=False,
                    delivery_method="telegram",
                    error=f"File terlalu besar untuk Telegram ({file_size / (1024*1024):.1f}MB). "
                          f"Maksimal 500MB. Silakan pilih Google Drive.",
                )
            
            with open(file_path, "rb") as f:
                if is_audio:
                    await bot.send_audio(
                        chat_id=chat_id,
                        audio=f,
                        caption=caption[:1024] if caption else None,
                        parse_mode="Markdown",
                        read_timeout=120,
                        write_timeout=120,
                    )
                else:
                    await bot.send_video(
                        chat_id=chat_id,
                        video=f,
                        caption=caption[:1024] if caption else None,
                        parse_mode="Markdown",
                        read_timeout=120,
                        write_timeout=120,
                        supports_streaming=True,
                    )
            
            logger.info(f"Uploaded to Telegram: {file_path}")
            return UploadResult(
                success=True,
                delivery_method="telegram",
            )
            
        except Exception as e:
            logger.error(f"Telegram upload error: {e}")
            return UploadResult(
                success=False,
                delivery_method="telegram",
                error=str(e),
            )
    
    async def upload_to_drive(
        self,
        file_path: Path,
        subfolder: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload file to Google Drive using rclone.
        
        Args:
            file_path: Path to file to upload
            subfolder: Optional subfolder in remote
            
        Returns:
            UploadResult with drive link
        """
        try:
            remote_path = self.rclone_remote
            if subfolder:
                remote_path = f"{self.rclone_remote}/{subfolder}"
            
            # Upload file
            cmd = [
                "rclone",
                "copy",
                str(file_path),
                remote_path,
                "--progress",
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()[:500] if stderr else "Unknown error"
                logger.error(f"rclone error: {error_msg}")
                return UploadResult(
                    success=False,
                    delivery_method="drive",
                    error=f"Upload ke Drive gagal: {error_msg}",
                )
            
            # Generate shareable link
            drive_link = await self._get_drive_link(file_path.name, remote_path)
            
            logger.info(f"Uploaded to Drive: {file_path} -> {remote_path}")
            
            return UploadResult(
                success=True,
                delivery_method="drive",
                drive_link=drive_link,
            )
            
        except Exception as e:
            logger.error(f"Drive upload error: {e}")
            return UploadResult(
                success=False,
                delivery_method="drive",
                error=str(e),
            )
    
    async def _get_drive_link(self, filename: str, remote_path: str) -> Optional[str]:
        """
        Get Google Drive shareable link for uploaded file.
        
        Args:
            filename: Name of the file
            remote_path: rclone remote path
            
        Returns:
            Shareable link or None
        """
        try:
            # Get file link using rclone
            cmd = [
                "rclone",
                "link",
                f"{remote_path}/{filename}",
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                link = stdout.decode().strip()
                if link:
                    return link
            
            # Fallback: construct link manually if rclone link fails
            logger.warning("Could not generate direct link, using folder path")
            return f"File tersimpan di: {remote_path}/{filename}"
            
        except Exception as e:
            logger.error(f"Error getting drive link: {e}")
            return None
