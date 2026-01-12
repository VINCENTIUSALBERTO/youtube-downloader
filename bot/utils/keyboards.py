"""
Keyboard utilities for YouTube Downloader Bot.

Provides inline keyboard builders for bot interactions.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.config import config


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
        [
            InlineKeyboardButton("🎁 Bonus Harian", callback_data="claim_bonus"),
            InlineKeyboardButton("💳 Topup", callback_data="topup_menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_registration_keyboard() -> InlineKeyboardMarkup:
    """Get registration keyboard."""
    keyboard = [
        [InlineKeyboardButton(
            f"📢 Join {config.required_channel}",
            url=f"https://t.me/{config.required_channel.replace('@', '')}",
        )],
        [InlineKeyboardButton("✅ Verifikasi", callback_data="verify_registration")],
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
            [InlineKeyboardButton("📹 Semua Video 360p", callback_data="format_playlist_360p")],
            [InlineKeyboardButton("📺 Semua Video 720p", callback_data="format_playlist_720p")],
            [InlineKeyboardButton("🎬 Semua Video 1080p", callback_data="format_playlist_1080p")],
            [InlineKeyboardButton("⭐ Semua Best Quality", callback_data="format_playlist_best")],
            [InlineKeyboardButton("📋 Pilih Video Tertentu", callback_data="playlist_select_videos")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
        ]
    return InlineKeyboardMarkup(keyboard)


def get_auto_detect_format_keyboard() -> InlineKeyboardMarkup:
    """Get format selection keyboard for auto-detected YouTube links."""
    keyboard = [
        [InlineKeyboardButton("🎵 Download MP3", callback_data="auto_format_mp3")],
        [InlineKeyboardButton("📹 Video 360p", callback_data="auto_format_360p")],
        [InlineKeyboardButton("📺 Video 720p (HD)", callback_data="auto_format_720p")],
        [InlineKeyboardButton("🎬 Video 1080p", callback_data="auto_format_1080p")],
        [InlineKeyboardButton("⭐ Best Quality", callback_data="auto_format_best")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel_download")],
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
        [InlineKeyboardButton("📋 Topup Pending", callback_data="admin_pending_topup")],
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


def get_topup_keyboard() -> InlineKeyboardMarkup:
    """Get topup menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(f"1️⃣ 1 Token - Rp {config.token_price_1:,}".replace(",", "."), callback_data="topup_1")],
        [InlineKeyboardButton(f"5️⃣ 5 Token - Rp {config.token_price_5:,}".replace(",", "."), callback_data="topup_5")],
        [InlineKeyboardButton(f"🔟 10 Token - Rp {config.token_price_10:,}".replace(",", "."), callback_data="topup_10")],
        [InlineKeyboardButton(f"💎 25 Token - Rp {config.token_price_25:,}".replace(",", "."), callback_data="topup_25")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_topup_confirm_keyboard(package: str) -> InlineKeyboardMarkup:
    """Get topup confirmation keyboard."""
    keyboard = [
        [InlineKeyboardButton("📤 Kirim Bukti Transfer", callback_data=f"send_proof_{package}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="topup_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_topup_action_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Get admin topup action keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Terima", callback_data=f"approve_topup_{request_id}"),
            InlineKeyboardButton("❌ Tolak", callback_data=f"reject_topup_{request_id}"),
        ],
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


def get_playlist_video_selection_keyboard(
    videos: list,
    selected_ids: list,
    page: int = 0,
    per_page: int = 8,
) -> InlineKeyboardMarkup:
    """
    Get keyboard for selecting videos from playlist.
    
    Args:
        videos: List of video dicts with 'id' and 'title'
        selected_ids: List of already selected video IDs
        page: Current page number (0-indexed)
        per_page: Number of videos per page
    """
    keyboard = []
    
    total_videos = len(videos)
    total_pages = (total_videos + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_videos)
    
    # Add video selection buttons
    for i, video in enumerate(videos[start_idx:end_idx], start=start_idx + 1):
        video_id = video.get("id", "")
        title = video.get("title", f"Video {i}")[:35]
        is_selected = video_id in selected_ids
        
        prefix = "✅ " if is_selected else "⬜ "
        callback_data = f"playlist_toggle_{video_id}"
        
        keyboard.append([InlineKeyboardButton(f"{prefix}{i}. {title}", callback_data=callback_data)])
    
    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"playlist_page_{page - 1}"))
    
    if selected_ids:
        nav_buttons.append(InlineKeyboardButton(f"({len(selected_ids)} dipilih)", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"playlist_page_{page + 1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Selection actions
    action_buttons = []
    action_buttons.append(InlineKeyboardButton("☑️ Pilih Semua", callback_data="playlist_select_all"))
    action_buttons.append(InlineKeyboardButton("❎ Batal Pilih", callback_data="playlist_deselect_all"))
    keyboard.append(action_buttons)
    
    # Confirm and back buttons
    if selected_ids:
        keyboard.append([InlineKeyboardButton(f"✅ Lanjut Download ({len(selected_ids)} video)", callback_data="playlist_confirm_selection")])
    
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_format")])
    
    return InlineKeyboardMarkup(keyboard)


def get_playlist_format_after_selection_keyboard() -> InlineKeyboardMarkup:
    """Get format selection keyboard after videos are selected."""
    keyboard = [
        [InlineKeyboardButton("🎵 Download MP3", callback_data="selected_format_mp3")],
        [InlineKeyboardButton("📹 Video 360p", callback_data="selected_format_360p")],
        [InlineKeyboardButton("📺 Video 720p (HD)", callback_data="selected_format_720p")],
        [InlineKeyboardButton("🎬 Video 1080p", callback_data="selected_format_1080p")],
        [InlineKeyboardButton("⭐ Best Quality", callback_data="selected_format_best")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_selection")],
    ]
    return InlineKeyboardMarkup(keyboard)
