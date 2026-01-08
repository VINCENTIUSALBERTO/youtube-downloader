#!/usr/bin/env python3
"""
Telegram Bot for downloading YouTube media and uploading to Google Drive.

Features:
- User authentication via whitelist
- Inline keyboard for quality selection
- yt-dlp integration for downloading
- rclone integration for Google Drive upload
- Real-time status notifications
"""

import asyncio
import logging
import os
import re
from pathlib import Path

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
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if uid.strip()
]
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE", "gdrive:YouTube_Downloads")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/tmp/youtube_downloads")
COOKIES_FILE = os.getenv("COOKIES_FILE", "")  # Optional cookies.txt path

# Format options for yt-dlp
FORMAT_OPTIONS = {
    "mp3": {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "label": "🎵 MP3 (Audio Only)",
    },
    "360p": {
        "format": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        "label": "📹 Video 360p",
    },
    "720p": {
        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "label": "📹 Video 720p",
    },
    "1080p": {
        "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "label": "📹 Video 1080p",
    },
    "best": {
        "format": "bestvideo+bestaudio/best",
        "label": "🎬 Best Quality (2K/4K)",
    },
}

# URL pattern for detecting video links
URL_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|"
    r"youtube\.com/shorts/|vimeo\.com/|dailymotion\.com/video/|"
    r"twitter\.com/.*/status/|x\.com/.*/status/|"
    r"tiktok\.com/|instagram\.com/|facebook\.com/.*video|"
    r"reddit\.com/r/.*/comments/|v\.redd\.it/|"
    r"twitch\.tv/videos/|clips\.twitch\.tv/)"
    r"[^\s]+"
)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be compatible with Linux filesystem.

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


def is_user_authorized(user_id: int) -> bool:
    """Check if user is in the whitelist."""
    if not ALLOWED_USER_IDS:
        logger.warning("No ALLOWED_USER_IDS configured. Denying all users.")
        return False
    return user_id in ALLOWED_USER_IDS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.effective_user or not update.message:
        return

    if not is_user_authorized(update.effective_user.id):
        logger.info(f"Unauthorized user: {update.effective_user.id}")
        return

    await update.message.reply_text(
        "👋 *Welcome to YouTube Downloader Bot!*\n\n"
        "Send me a video link and I'll help you download it.\n\n"
        "*Supported platforms:*\n"
        "• YouTube\n"
        "• Twitter/X\n"
        "• TikTok\n"
        "• Instagram\n"
        "• And many more!\n\n"
        "*How to use:*\n"
        "1. Send a video link\n"
        "2. Choose your preferred format\n"
        "3. Wait for download and upload to Drive\n"
        "4. Done! ✅",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.effective_user or not update.message:
        return

    if not is_user_authorized(update.effective_user.id):
        return

    await update.message.reply_text(
        "📖 *Help*\n\n"
        "*Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "*Format Options:*\n"
        "🎵 MP3 - Audio only (192kbps)\n"
        "📹 360p - Low quality video\n"
        "📹 720p - HD video\n"
        "📹 1080p - Full HD video\n"
        "🎬 Best - Maximum quality available",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with URLs."""
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        logger.info(f"Unauthorized message from user: {user_id}")
        return

    text = update.message.text
    match = URL_PATTERN.search(text)

    if not match:
        await update.message.reply_text(
            "❌ No valid video URL found.\n\n"
            "Please send a link from YouTube, Twitter, TikTok, or other supported platforms."
        )
        return

    url = match.group(0)
    logger.info(f"Received URL from user {user_id}: {url}")

    # Store URL in user context for callback
    if context.user_data is not None:
        context.user_data["pending_url"] = url

    # Create inline keyboard with format options
    keyboard = [
        [InlineKeyboardButton(FORMAT_OPTIONS["mp3"]["label"], callback_data="mp3")],
        [
            InlineKeyboardButton(FORMAT_OPTIONS["360p"]["label"], callback_data="360p"),
            InlineKeyboardButton(FORMAT_OPTIONS["720p"]["label"], callback_data="720p"),
        ],
        [
            InlineKeyboardButton(
                FORMAT_OPTIONS["1080p"]["label"], callback_data="1080p"
            ),
            InlineKeyboardButton(FORMAT_OPTIONS["best"]["label"], callback_data="best"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔗 *Link detected!*\n\n"
        f"`{url[:80]}{'...' if len(url) > 80 else ''}`\n\n"
        "Choose your preferred format:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def download_and_upload(
    url: str,
    format_key: str,
    chat_id: int,
    message_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Download video using yt-dlp and upload to Google Drive using rclone.

    Args:
        url: Video URL to download
        format_key: Format option key (mp3, 360p, etc.)
        chat_id: Telegram chat ID for status updates
        message_id: Message ID to edit for status updates
        context: Telegram bot context
    """
    format_opts = FORMAT_OPTIONS.get(format_key, FORMAT_OPTIONS["720p"])

    # Create download directory
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Build yt-dlp command
    output_template = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "--format",
        format_opts["format"],
        "--output",
        output_template,
        "--restrict-filenames",
        "--no-playlist",
        "--merge-output-format",
        "mp4" if format_key != "mp3" else "mp3",
    ]

    # Add cookies file if configured
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        cmd.extend(["--cookies", COOKIES_FILE])

    # Add audio extraction for MP3
    if format_key == "mp3":
        cmd.extend(
            [
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "192K",
            ]
        )

    cmd.append(url)

    downloaded_file = None

    try:
        # Update status: Downloading
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="⬇️ *Downloading...*\n\nPlease wait while I download your video.",
            parse_mode="Markdown",
        )

        # Get video info first to determine filename
        info_cmd = ["yt-dlp", "--print", "filename", "--output", output_template]
        if COOKIES_FILE and os.path.exists(COOKIES_FILE):
            info_cmd.extend(["--cookies", COOKIES_FILE])
        if format_key == "mp3":
            info_cmd.extend(["--extract-audio", "--audio-format", "mp3"])
        info_cmd.append(url)

        # Run info command
        info_result = await asyncio.create_subprocess_exec(
            *info_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await info_result.communicate()
        expected_filename = stdout.decode().strip().split("\n")[-1]
        if format_key == "mp3" and not expected_filename.endswith(".mp3"):
            expected_filename = (
                os.path.splitext(expected_filename)[0] + ".mp3"
            )

        # Run download command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode()[:500] if stderr else "Unknown error"
            raise RuntimeError(f"Download failed: {error_msg}")

        # Find downloaded file
        download_path = Path(DOWNLOAD_DIR)
        files = list(download_path.glob("*"))

        if not files:
            raise RuntimeError("No file was downloaded")

        # Get the most recently modified file
        downloaded_file = max(files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Downloaded file: {downloaded_file}")

        # Update status: Uploading
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="☁️ *Uploading to Drive...*\n\nAlmost done!",
            parse_mode="Markdown",
        )

        # Upload to Google Drive using rclone
        rclone_cmd = [
            "rclone",
            "copy",
            str(downloaded_file),
            RCLONE_REMOTE,
            "--progress",
        ]

        rclone_process = await asyncio.create_subprocess_exec(
            *rclone_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, rclone_stderr = await rclone_process.communicate()

        if rclone_process.returncode != 0:
            error_msg = rclone_stderr.decode()[:500] if rclone_stderr else "Unknown error"
            raise RuntimeError(f"Upload failed: {error_msg}")

        # Cleanup: Delete local file after successful upload
        if downloaded_file and downloaded_file.exists():
            downloaded_file.unlink()
            logger.info(f"Deleted local file: {downloaded_file}")

        # Update status: Done
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ *Done!*\n\n"
            f"📁 *File:* `{sanitize_filename(downloaded_file.name)}`\n"
            f"📂 *Location:* `{RCLONE_REMOTE}`\n\n"
            f"Your file has been uploaded to Google Drive!",
            parse_mode="Markdown",
        )

    except Exception as e:
        error_message = str(e)
        # Provide human-readable error messages
        if "Video unavailable" in error_message or "not available" in error_message:
            user_error = "This video is not available or has been removed."
        elif "age" in error_message.lower():
            user_error = "This video requires age verification. Please configure cookies.txt."
        elif "private" in error_message.lower():
            user_error = "This video is private and cannot be accessed."
        elif "copyright" in error_message.lower():
            user_error = "This video is blocked due to copyright restrictions."
        elif "rclone" in error_message.lower() or "Upload failed" in error_message:
            user_error = "Failed to upload to Google Drive. Please check rclone configuration."
        else:
            user_error = f"An error occurred: {error_message[:200]}"

        logger.error(f"Error processing URL {url}: {error_message}")

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"❌ *Error*\n\n{user_error}",
            parse_mode="Markdown",
        )

        # Cleanup on error
        if downloaded_file and downloaded_file.exists():
            downloaded_file.unlink()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    if not query or not query.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    if not is_user_authorized(user_id):
        await query.answer("You are not authorized to use this bot.")
        return

    await query.answer()

    format_key = query.data
    if format_key not in FORMAT_OPTIONS:
        await query.edit_message_text("❌ Invalid format selection.")
        return

    # Get stored URL
    url = context.user_data.get("pending_url") if context.user_data else None
    if not url:
        await query.edit_message_text(
            "❌ Session expired. Please send the link again."
        )
        return

    # Clear pending URL
    if context.user_data:
        context.user_data.pop("pending_url", None)

    # Update message to show processing
    await query.edit_message_text(
        f"⏳ *Processing...*\n\n"
        f"Format: {FORMAT_OPTIONS[format_key]['label']}\n"
        f"This may take a few minutes.",
        parse_mode="Markdown",
    )

    # Process download in background
    asyncio.create_task(
        download_and_upload(
            url=url,
            format_key=format_key,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            context=context,
        )
    )


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        raise ValueError("BOT_TOKEN environment variable is required")

    if not ALLOWED_USER_IDS:
        logger.warning(
            "ALLOWED_USER_IDS is not configured. Bot will deny all users."
        )

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(CallbackQueryHandler(button_callback))

    # Start polling
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
