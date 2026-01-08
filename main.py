#!/usr/bin/env python3
"""
YouTube Downloader Telegram Bot - Commercial Edition

Features:
- Token-based access system (1 token = 1 download)
- Admin management system
- YouTube Music, Video, and Playlist support
- Delivery via Telegram or Google Drive (with shareable link)
- Title confirmation before download
- User token balance tracking
"""

import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_USER_IDS", "").split(",")
    if uid.strip()
]
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE", "gdrive:YouTube_Downloads")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/tmp/youtube_downloads")
COOKIES_FILE = os.getenv("COOKIES_FILE", "")
DATA_FILE = os.getenv("DATA_FILE", "bot_data.json")

# Bot configuration
ADMIN_CONTACT = os.getenv("ADMIN_CONTACT", "@admin")
TOKEN_PRICE = os.getenv("TOKEN_PRICE", "Rp 5.000 / token")

# Download type options
DOWNLOAD_TYPES = {
    "music": {
        "format": "bestaudio/best",
        "label": "🎵 YouTube Music",
        "description": "Download audio only (MP3)",
        "is_audio": True,
    },
    "video": {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "label": "📹 YouTube Video",
        "description": "Download single video (up to 1080p)",
        "is_audio": False,
    },
    "playlist": {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "label": "📋 YouTube Playlist",
        "description": "Download entire playlist (720p)",
        "is_audio": False,
        "is_playlist": True,
    },
}

# YouTube URL patterns
YOUTUBE_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|"
    r"youtube\.com/shorts/|youtube\.com/playlist\?list=|"
    r"music\.youtube\.com/watch\?v=)[^\s]+"
)


class DataManager:
    """Manage persistent data storage for users and tokens."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> dict:
        """Load data from file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.error(f"Failed to load data from {self.filepath}")
        return {"users": {}, "downloads": []}

    def _save(self) -> None:
        """Save data to file."""
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.data, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Failed to save data: {e}")

    def get_user_tokens(self, user_id: int) -> int:
        """Get user's token balance."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["users"]:
            self.data["users"][user_id_str] = {"tokens": 0, "username": ""}
        return self.data["users"][user_id_str].get("tokens", 0)

    def add_tokens(self, user_id: int, amount: int, username: str = "") -> int:
        """Add tokens to user's balance."""
        user_id_str = str(user_id)
        if user_id_str not in self.data["users"]:
            self.data["users"][user_id_str] = {"tokens": 0, "username": username}
        self.data["users"][user_id_str]["tokens"] += amount
        if username:
            self.data["users"][user_id_str]["username"] = username
        self._save()
        return self.data["users"][user_id_str]["tokens"]

    def use_token(self, user_id: int) -> bool:
        """Use one token from user's balance. Returns True if successful."""
        user_id_str = str(user_id)
        if self.get_user_tokens(user_id) > 0:
            self.data["users"][user_id_str]["tokens"] -= 1
            self._save()
            return True
        return False

    def log_download(self, user_id: int, title: str, download_type: str) -> None:
        """Log a download for history."""
        self.data["downloads"].append({
            "user_id": user_id,
            "title": title,
            "type": download_type,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_all_users(self) -> dict:
        """Get all users data."""
        return self.data["users"]


# Initialize data manager
data_manager = DataManager(DATA_FILE)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem compatibility."""
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = re.sub(r"_+", "_", filename)
    filename = filename.strip(" .")
    if len(filename) > 200:
        filename = filename[:200]
    return filename if filename else "download"


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_USER_IDS


async def get_video_info(url: str) -> Optional[dict]:
    """Get video information using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        "--no-download",
    ]
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
    cmd.append(url)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()

        if process.returncode == 0 and stdout:
            return json.loads(stdout.decode())
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
    return None


async def get_playlist_info(url: str) -> Optional[dict]:
    """Get playlist information using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--no-download",
    ]
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])
    cmd.append(url)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()

        if process.returncode == 0 and stdout:
            lines = stdout.decode().strip().split("\n")
            videos = [json.loads(line) for line in lines if line.strip()]
            if videos:
                return {
                    "title": videos[0].get("playlist_title", "Playlist"),
                    "count": len(videos),
                    "videos": videos[:10],  # First 10 for preview
                }
    except Exception as e:
        logger.error(f"Failed to get playlist info: {e}")
    return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    tokens = data_manager.get_user_tokens(user_id)

    admin_text = "\n\n🔧 *Anda adalah Admin*" if is_admin(user_id) else ""

    await update.message.reply_text(
        f"👋 *Selamat Datang di YouTube Downloader Bot!*\n\n"
        f"🎫 *Token Anda:* {tokens}\n"
        f"💰 *Harga:* {TOKEN_PRICE}\n"
        f"📞 *Hubungi Admin:* {ADMIN_CONTACT}\n"
        f"{admin_text}\n\n"
        f"*Cara Penggunaan:*\n"
        f"1. Kirim link YouTube\n"
        f"2. Pilih tipe download\n"
        f"3. Konfirmasi judul\n"
        f"4. Pilih kirim via Telegram atau Drive\n"
        f"5. 1 download = 1 token\n\n"
        f"*Commands:*\n"
        f"/start - Mulai bot\n"
        f"/tokens - Cek sisa token\n"
        f"/help - Bantuan\n"
        f"/buy - Beli token",
        parse_mode="Markdown",
    )


async def tokens_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /tokens command - check token balance."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    tokens = data_manager.get_user_tokens(user_id)

    await update.message.reply_text(
        f"🎫 *Sisa Token Anda:* {tokens}\n\n"
        f"💰 *Harga Token:* {TOKEN_PRICE}\n"
        f"📞 *Beli Token:* Hubungi {ADMIN_CONTACT}",
        parse_mode="Markdown",
    )


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /buy command - show buy info."""
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"🛒 *Beli Token*\n\n"
        f"💰 *Harga:* {TOKEN_PRICE}\n"
        f"📞 *Hubungi Admin:* {ADMIN_CONTACT}\n\n"
        f"📋 *Informasi Anda:*\n"
        f"User ID: `{user_id}`\n\n"
        f"Kirim User ID Anda ke admin untuk pembelian token.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.effective_user or not update.message:
        return

    await update.message.reply_text(
        "📖 *Bantuan*\n\n"
        "*Tipe Download:*\n"
        "🎵 *YouTube Music* - Download audio MP3\n"
        "📹 *YouTube Video* - Download video single (1080p)\n"
        "📋 *YouTube Playlist* - Download semua video playlist (720p)\n\n"
        "*Pengiriman:*\n"
        "📱 *Telegram* - File dikirim langsung ke chat\n"
        "☁️ *Google Drive* - File diupload, link diberikan\n\n"
        "*Commands:*\n"
        "/start - Mulai bot\n"
        "/tokens - Cek sisa token\n"
        "/buy - Info beli token\n"
        "/help - Bantuan\n\n"
        "*Catatan:*\n"
        "• 1 download = 1 token\n"
        "• Playlist dihitung per video\n"
        f"• Hubungi {ADMIN_CONTACT} untuk bantuan",
        parse_mode="Markdown",
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command - admin panel."""
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda bukan admin.")
        return

    await update.message.reply_text(
        "🔧 *Admin Panel*\n\n"
        "*Commands:*\n"
        "/addtoken `<user_id>` `<amount>` - Tambah token user\n"
        "/checkuser `<user_id>` - Cek info user\n"
        "/users - Lihat semua user\n\n"
        "*Contoh:*\n"
        "`/addtoken 123456789 10`",
        parse_mode="Markdown",
    )


async def addtoken_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addtoken command - admin add tokens to user."""
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda bukan admin.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format salah.\n\n"
            "Gunakan: `/addtoken <user_id> <amount>`\n"
            "Contoh: `/addtoken 123456789 10`",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        if amount <= 0:
            await update.message.reply_text("❌ Jumlah harus lebih dari 0.")
            return

        new_balance = data_manager.add_tokens(target_user_id, amount)

        await update.message.reply_text(
            f"✅ *Token Ditambahkan!*\n\n"
            f"👤 User ID: `{target_user_id}`\n"
            f"➕ Ditambahkan: {amount} token\n"
            f"🎫 Saldo Baru: {new_balance} token",
            parse_mode="Markdown",
        )

    except ValueError:
        await update.message.reply_text("❌ User ID dan amount harus berupa angka.")


async def checkuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /checkuser command - admin check user info."""
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda bukan admin.")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Format salah.\n\nGunakan: `/checkuser <user_id>`",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(context.args[0])
        tokens = data_manager.get_user_tokens(target_user_id)
        user_data = data_manager.data["users"].get(str(target_user_id), {})
        username = user_data.get("username", "Unknown")

        await update.message.reply_text(
            f"👤 *Info User*\n\n"
            f"ID: `{target_user_id}`\n"
            f"Username: @{username}\n"
            f"🎫 Token: {tokens}",
            parse_mode="Markdown",
        )

    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /users command - admin list all users."""
    if not update.effective_user or not update.message:
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda bukan admin.")
        return

    users = data_manager.get_all_users()

    if not users:
        await update.message.reply_text("📋 Belum ada user terdaftar.")
        return

    text = "👥 *Daftar User*\n\n"
    for user_id, info in users.items():
        username = info.get("username", "?")
        tokens = info.get("tokens", 0)
        text += f"• `{user_id}` (@{username}) - {tokens} token\n"

    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with YouTube URLs."""
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    text = update.message.text

    # Check for YouTube URL
    match = YOUTUBE_URL_PATTERN.search(text)

    if not match:
        await update.message.reply_text(
            "❌ *URL tidak valid*\n\n"
            "Kirim link YouTube yang valid.\n"
            "Contoh:\n"
            "• `https://youtube.com/watch?v=...`\n"
            "• `https://youtu.be/...`\n"
            "• `https://music.youtube.com/watch?v=...`",
            parse_mode="Markdown",
        )
        return

    url = match.group(0)
    tokens = data_manager.get_user_tokens(user_id)

    # Check if user has tokens (admins get free access)
    if tokens <= 0 and not is_admin(user_id):
        await update.message.reply_text(
            f"❌ *Token Habis!*\n\n"
            f"Anda tidak memiliki token.\n"
            f"💰 Harga: {TOKEN_PRICE}\n"
            f"📞 Hubungi: {ADMIN_CONTACT}\n\n"
            f"Kirim User ID Anda: `{user_id}`",
            parse_mode="Markdown",
        )
        return

    logger.info(f"Received URL from user {user_id}: {url}")

    # Store URL and username in context
    if context.user_data is not None:
        context.user_data["pending_url"] = url
        context.user_data["username"] = username

    # Create download type selection keyboard
    keyboard = [
        [InlineKeyboardButton("🎵 YouTube Music", callback_data="type_music")],
        [InlineKeyboardButton("📹 YouTube Video", callback_data="type_video")],
        [InlineKeyboardButton("📋 YouTube Playlist", callback_data="type_playlist")],
        [InlineKeyboardButton("❌ Batal", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    token_info = f"🎫 Token: {tokens}" if not is_admin(user_id) else "🔧 Admin (Free)"

    await update.message.reply_text(
        f"🔗 *Link Terdeteksi!*\n\n"
        f"{token_info}\n\n"
        f"Pilih tipe download:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    if not query or not query.message or not update.effective_user:
        return

    await query.answer()

    user_id = update.effective_user.id
    callback_data = query.data

    # Handle cancel
    if callback_data == "cancel":
        if context.user_data:
            context.user_data.clear()
        await query.edit_message_text("❌ Dibatalkan.")
        return

    # Handle download type selection
    if callback_data.startswith("type_"):
        download_type = callback_data.replace("type_", "")
        url = context.user_data.get("pending_url") if context.user_data else None

        if not url:
            await query.edit_message_text("❌ Sesi expired. Kirim link lagi.")
            return

        if context.user_data:
            context.user_data["download_type"] = download_type

        # Show loading message
        await query.edit_message_text("⏳ *Mengambil informasi...*", parse_mode="Markdown")

        # Get video/playlist info
        if download_type == "playlist":
            info = await get_playlist_info(url)
            if info:
                video_count = info.get("count", 0)
                title = info.get("title", "Unknown Playlist")

                # Check tokens for playlist
                tokens = data_manager.get_user_tokens(user_id)
                if tokens < video_count and not is_admin(user_id):
                    await query.edit_message_text(
                        f"❌ *Token Tidak Cukup!*\n\n"
                        f"Playlist: {title}\n"
                        f"Video: {video_count}\n"
                        f"Token Anda: {tokens}\n\n"
                        f"Butuh {video_count} token untuk playlist ini.",
                        parse_mode="Markdown",
                    )
                    return

                if context.user_data:
                    context.user_data["video_info"] = info
                    context.user_data["video_count"] = video_count

                keyboard = [
                    [InlineKeyboardButton("✅ Ya, Download", callback_data="confirm_yes")],
                    [InlineKeyboardButton("❌ Batal", callback_data="cancel")],
                ]

                await query.edit_message_text(
                    f"📋 *Konfirmasi Playlist*\n\n"
                    f"📁 *Judul:* {title}\n"
                    f"🎬 *Total Video:* {video_count}\n"
                    f"🎫 *Token Dibutuhkan:* {video_count}\n\n"
                    f"Lanjutkan download?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            else:
                await query.edit_message_text(
                    "❌ Gagal mengambil info playlist. Pastikan link valid."
                )
        else:
            info = await get_video_info(url)
            if info:
                title = info.get("title", "Unknown")
                duration = info.get("duration", 0)
                duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"
                channel = info.get("channel", info.get("uploader", "Unknown"))

                if context.user_data:
                    context.user_data["video_info"] = info
                    context.user_data["video_count"] = 1

                keyboard = [
                    [InlineKeyboardButton("✅ Ya, Download", callback_data="confirm_yes")],
                    [InlineKeyboardButton("❌ Batal", callback_data="cancel")],
                ]

                type_label = DOWNLOAD_TYPES[download_type]["label"]
                await query.edit_message_text(
                    f"🎬 *Konfirmasi Download*\n\n"
                    f"📁 *Judul:* {title}\n"
                    f"📺 *Channel:* {channel}\n"
                    f"⏱ *Durasi:* {duration_str}\n"
                    f"📥 *Tipe:* {type_label}\n\n"
                    f"Apakah ini benar?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                )
            else:
                await query.edit_message_text(
                    "❌ Gagal mengambil info video. Pastikan link valid."
                )
        return

    # Handle confirmation
    if callback_data == "confirm_yes":
        # Show delivery options
        keyboard = [
            [InlineKeyboardButton("📱 Kirim via Telegram", callback_data="deliver_telegram")],
            [InlineKeyboardButton("☁️ Upload ke Drive", callback_data="deliver_drive")],
            [InlineKeyboardButton("❌ Batal", callback_data="cancel")],
        ]

        await query.edit_message_text(
            "📤 *Pilih Metode Pengiriman:*\n\n"
            "📱 *Telegram* - File dikirim langsung\n"
            "☁️ *Drive* - Upload & dapat link",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # Handle delivery method selection
    if callback_data.startswith("deliver_"):
        delivery_method = callback_data.replace("deliver_", "")
        url = context.user_data.get("pending_url") if context.user_data else None
        download_type = context.user_data.get("download_type") if context.user_data else None
        video_count = context.user_data.get("video_count", 1) if context.user_data else 1

        if not url or not download_type:
            await query.edit_message_text("❌ Sesi expired. Kirim link lagi.")
            return

        # Deduct tokens (admins are free)
        if not is_admin(user_id):
            for _ in range(video_count):
                if not data_manager.use_token(user_id):
                    await query.edit_message_text("❌ Token tidak cukup!")
                    return

        if context.user_data:
            context.user_data["delivery_method"] = delivery_method

        # Start download
        await query.edit_message_text(
            "⬇️ *Downloading...*\n\n"
            "Mohon tunggu, proses download sedang berjalan.",
            parse_mode="Markdown",
        )

        # Process download in background
        task = asyncio.create_task(
            process_download(
                url=url,
                download_type=download_type,
                delivery_method=delivery_method,
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                user_id=user_id,
                context=context,
            ),
            name=f"download_{query.message.chat_id}_{query.message.message_id}",
        )
        task.add_done_callback(
            lambda t: logger.error(f"Task failed: {t.exception()}")
            if t.exception()
            else None
        )
        return


async def process_download(
    url: str,
    download_type: str,
    delivery_method: str,
    chat_id: int,
    message_id: int,
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Process the download and delivery."""
    type_opts = DOWNLOAD_TYPES.get(download_type, DOWNLOAD_TYPES["video"])

    # Create unique download directory
    unique_id = str(uuid.uuid4())[:8]
    download_dir = os.path.join(DOWNLOAD_DIR, unique_id)
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    output_template = os.path.join(download_dir, "%(title)s.%(ext)s")

    # Build yt-dlp command
    cmd = [
        "yt-dlp",
        "--format", type_opts["format"],
        "--output", output_template,
        "--restrict-filenames",
    ]

    # Playlist handling
    if download_type != "playlist":
        cmd.append("--no-playlist")

    # Audio handling
    if type_opts.get("is_audio"):
        cmd.extend([
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
        ])
    else:
        cmd.extend(["--merge-output-format", "mp4"])

    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])

    cmd.append(url)

    downloaded_files = []

    try:
        # Download
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode()[:300] if stderr else "Unknown error"
            raise RuntimeError(f"Download failed: {error_msg}")

        # Find downloaded files
        download_path = Path(download_dir)
        downloaded_files = [f for f in download_path.iterdir() if f.is_file()]

        if not downloaded_files:
            raise RuntimeError("Tidak ada file yang didownload")

        # Handle delivery
        if delivery_method == "telegram":
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="📤 *Mengirim file...*",
                parse_mode="Markdown",
            )

            for file_path in downloaded_files:
                file_size = file_path.stat().st_size
                # Telegram limit is 50MB for bots
                if file_size > 50 * 1024 * 1024:
                    # File too large, upload to drive instead
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ File `{file_path.name}` terlalu besar untuk Telegram. Mengupload ke Drive...",
                        parse_mode="Markdown",
                    )
                    drive_link = await upload_to_drive(file_path)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"☁️ *File di Drive:*\n`{file_path.name}`\n\n🔗 {drive_link}",
                        parse_mode="Markdown",
                    )
                else:
                    if type_opts.get("is_audio"):
                        await context.bot.send_audio(
                            chat_id=chat_id,
                            audio=file_path,
                            caption=f"🎵 {file_path.stem}",
                        )
                    else:
                        await context.bot.send_video(
                            chat_id=chat_id,
                            video=file_path,
                            caption=f"📹 {file_path.stem}",
                            supports_streaming=True,
                        )

                # Log download
                data_manager.log_download(user_id, file_path.stem, download_type)

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"✅ *Selesai!*\n\n"
                f"📁 {len(downloaded_files)} file telah dikirim.\n"
                f"🎫 Token tersisa: {data_manager.get_user_tokens(user_id)}",
                parse_mode="Markdown",
            )

        else:  # Drive delivery
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="☁️ *Uploading ke Drive...*",
                parse_mode="Markdown",
            )

            drive_links = []
            for file_path in downloaded_files:
                link = await upload_to_drive(file_path)
                drive_links.append((file_path.name, link))
                data_manager.log_download(user_id, file_path.stem, download_type)

            # Send result with links
            links_text = "\n".join([f"📁 `{name}`\n🔗 {link}\n" for name, link in drive_links])

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"✅ *Upload Selesai!*\n\n"
                f"{links_text}\n"
                f"🎫 Token tersisa: {data_manager.get_user_tokens(user_id)}",
                parse_mode="Markdown",
            )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing download: {error_message}")

        # Human-readable errors
        if "unavailable" in error_message.lower():
            user_error = "Video tidak tersedia atau telah dihapus."
        elif "private" in error_message.lower():
            user_error = "Video bersifat private."
        elif "age" in error_message.lower():
            user_error = "Video membutuhkan verifikasi usia."
        else:
            user_error = f"Terjadi kesalahan: {error_message[:150]}"

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"❌ *Error*\n\n{user_error}",
            parse_mode="Markdown",
        )

    finally:
        # Cleanup
        for f in downloaded_files:
            try:
                if f.exists():
                    f.unlink()
            except Exception:
                pass
        try:
            Path(download_dir).rmdir()
        except Exception:
            pass


async def upload_to_drive(file_path: Path) -> str:
    """Upload file to Google Drive and return shareable link."""
    # Upload using rclone
    rclone_cmd = [
        "rclone", "copy",
        str(file_path),
        RCLONE_REMOTE,
    ]

    process = await asyncio.create_subprocess_exec(
        *rclone_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()

    if process.returncode != 0:
        raise RuntimeError("Upload ke Drive gagal")

    # Get shareable link
    remote_path = f"{RCLONE_REMOTE}/{file_path.name}"
    link_cmd = ["rclone", "link", remote_path]

    link_process = await asyncio.create_subprocess_exec(
        *link_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await link_process.communicate()

    if link_process.returncode == 0 and stdout:
        return stdout.decode().strip()

    return f"File uploaded to: {RCLONE_REMOTE}"


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        raise ValueError("BOT_TOKEN is required")

    if not ADMIN_USER_IDS:
        logger.warning("No ADMIN_USER_IDS configured.")

    application = Application.builder().token(BOT_TOKEN).build()

    # User commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tokens", tokens_command))
    application.add_handler(CommandHandler("buy", buy_command))

    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("addtoken", addtoken_command))
    application.add_handler(CommandHandler("checkuser", checkuser_command))
    application.add_handler(CommandHandler("users", users_command))

    # Message and callback handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Starting YouTube Downloader Bot (Commercial Edition)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
