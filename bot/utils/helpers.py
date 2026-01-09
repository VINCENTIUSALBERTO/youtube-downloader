"""
Helper functions for YouTube Downloader Bot.

Provides utility functions for formatting and string manipulation.
"""

import re
from datetime import datetime
from typing import Optional


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be compatible with filesystems.
    
    Removes or replaces characters that could cause issues.
    """
    # Remove null bytes and control characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    # Replace problematic characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Replace multiple underscores with single underscore
    filename = re.sub(r"_+", "_", filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")
    # Limit filename length (leaving room for extension)
    if len(filename) > 200:
        filename = filename[:200]
    return filename if filename else "download"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS format."""
    if seconds < 0:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_number(number: int) -> str:
    """Format number with thousand separators."""
    if number < 1000:
        return str(number)
    elif number < 1000000:
        return f"{number / 1000:.1f}K"
    elif number < 1000000000:
        return f"{number / 1000000:.1f}M"
    else:
        return f"{number / 1000000000:.1f}B"


def format_price(price: int) -> str:
    """Format price in IDR."""
    return f"Rp {price:,}".replace(",", ".")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram Markdown."""
    special_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def get_quality_emoji(quality: str) -> str:
    """Get emoji for quality label."""
    quality_map = {
        "mp3": "🎵",
        "360p": "📹",
        "720p": "📺",
        "1080p": "🎬",
        "best": "⭐",
    }
    return quality_map.get(quality, "📁")


def format_download_result(
    title: str,
    quality: str,
    file_size: Optional[int],
    duration: str,
    delivery_method: str,
    drive_link: Optional[str] = None,
) -> str:
    """Format download completion message."""
    emoji = get_quality_emoji(quality)
    size_str = format_file_size(file_size) if file_size else "Unknown"
    
    result = (
        f"✅ *Download Berhasil!*\n\n"
        f"📌 *Judul:*\n`{truncate_text(title, 60)}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Detail File:*\n"
        f"├ {emoji} Kualitas: `{quality.upper()}`\n"
        f"├ 📦 Ukuran: `{size_str}`\n"
        f"├ ⏱️ Durasi: `{duration}`\n"
        f"└ 📤 Pengiriman: `{delivery_method.title()}`\n"
    )
    
    if drive_link:
        result += (
            f"\n━━━━━━━━━━━━━━━━━━\n"
            f"🔗 *Link Google Drive:*\n"
            f"`{drive_link}`\n"
        )
    
    result += (
        f"\n━━━━━━━━━━━━━━━━━━\n"
        f"⏰ Selesai pada: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n"
        f"\nTerima kasih telah menggunakan layanan kami! 🙏"
    )
    
    return result
