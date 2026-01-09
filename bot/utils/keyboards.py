"""
Keyboard utilities for YouTube Downloader Bot.

Provides inline keyboard builders for bot interactions.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard with download options."""
    keyboard = [
        [InlineKeyboardButton("🎵 YouTube Musik", callback_data="menu_music")],
        [InlineKeyboardButton("🎬 YouTube Video", callback_data="menu_video")],
        [InlineKeyboardButton("📋 YouTube Playlist", callback_data="menu_playlist")],
        [
            InlineKeyboardButton("💰 Token Saya", callback_data="my_tokens"),
            InlineKeyboardButton("📊 Riwayat", callback_data="my_history"),
        ],
        [InlineKeyboardButton("💎 Beli Token", callback_data="buy_tokens")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_format_keyboard(download_type: str) -> InlineKeyboardMarkup:
    """Get format selection keyboard based on download type."""
    if download_type == "music":
        keyboard = [
            [InlineKeyboardButton("🎵 MP3 (192kbps)", callback_data="format_mp3")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
        ]
    elif download_type == "video":
        keyboard = [
            [InlineKeyboardButton("📹 360p", callback_data="format_360p")],
            [InlineKeyboardButton("📺 720p (HD)", callback_data="format_720p")],
            [InlineKeyboardButton("🎬 1080p (Full HD)", callback_data="format_1080p")],
            [InlineKeyboardButton("⭐ Best Quality", callback_data="format_best")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
        ]
    else:  # playlist
        keyboard = [
            [InlineKeyboardButton("🎵 Semua MP3", callback_data="format_playlist_mp3")],
            [InlineKeyboardButton("📹 Semua Video 720p", callback_data="format_playlist_720p")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
        ]
    return InlineKeyboardMarkup(keyboard)


def get_delivery_keyboard() -> InlineKeyboardMarkup:
    """Get delivery method selection keyboard."""
    keyboard = [
        [InlineKeyboardButton("📲 Kirim via Telegram", callback_data="deliver_telegram")],
        [InlineKeyboardButton("☁️ Upload ke Google Drive", callback_data="deliver_drive")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_format")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_keyboard(download_id: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ya, Lanjutkan", callback_data=f"confirm_{download_id}"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel_download"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("👥 Daftar User", callback_data="admin_users")],
        [InlineKeyboardButton("➕ Tambah Token", callback_data="admin_add_token")],
        [InlineKeyboardButton("📊 Statistik", callback_data="admin_stats")],
        [InlineKeyboardButton("🚫 Ban/Unban User", callback_data="admin_ban")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_token_packages_keyboard() -> InlineKeyboardMarkup:
    """Get token purchase packages keyboard."""
    keyboard = [
        [InlineKeyboardButton("1️⃣ 1 Token - Rp 5.000", callback_data="package_1")],
        [InlineKeyboardButton("5️⃣ 5 Token - Rp 20.000", callback_data="package_5")],
        [InlineKeyboardButton("🔟 10 Token - Rp 35.000", callback_data="package_10")],
        [InlineKeyboardButton("💎 25 Token - Rp 75.000", callback_data="package_25")],
        [InlineKeyboardButton("📞 Hubungi Admin", callback_data="contact_admin")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(callback_data: str = "back_menu") -> InlineKeyboardMarkup:
    """Get simple back button keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data=callback_data)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get cancel button keyboard."""
    keyboard = [
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_download")],
    ]
    return InlineKeyboardMarkup(keyboard)
