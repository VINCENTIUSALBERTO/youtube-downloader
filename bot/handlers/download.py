"""
Download handler for YouTube Downloader Bot.

Handles URL messages and initiates download process.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.database import Database
from bot.services.token_manager import TokenManager
from bot.utils.validators import validate_youtube_url, get_video_info, get_playlist_info
from bot.utils.keyboards import get_back_keyboard
from bot.utils.helpers import format_number, format_duration
from bot.config import config

logger = logging.getLogger(__name__)


async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming URL messages."""
    if not update.effective_user or not update.message or not update.message.text:
        return
    
    user = update.effective_user
    text = update.message.text.strip()
    
    # Initialize database
    db = Database(config.database_path)
    
    # Check if user is banned
    if db.is_user_banned(user.id):
        await update.message.reply_text(
            "❌ Akun Anda telah diblokir. Hubungi admin untuk informasi lebih lanjut."
        )
        return
    
    # Register/update user
    db.create_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    
    # Check if we're expecting a URL based on current state
    user_data = context.user_data or {}
    current_mode = user_data.get("mode")
    
    if not current_mode:
        # Not in download mode, show instructions
        await update.message.reply_text(
            "❓ Silakan pilih jenis download terlebih dahulu.\n\n"
            "Gunakan /start untuk melihat menu.",
        )
        return
    
    # Validate YouTube URL
    is_valid, url_type, video_id = validate_youtube_url(text)
    
    if not is_valid:
        await update.message.reply_text(
            "❌ *URL Tidak Valid*\n\n"
            "Kirim link YouTube yang valid.\n"
            "*Contoh:*\n"
            "• `https://youtube.com/watch?v=xxxxx`\n"
            "• `https://youtu.be/xxxxx`\n"
            "• `https://youtube.com/playlist?list=xxxxx`",
            parse_mode="Markdown",
        )
        return
    
    # Check token balance
    token_manager = TokenManager(db)
    balance = token_manager.get_balance(user.id)
    
    if balance < 1 and not token_manager.is_admin(user.id):
        await update.message.reply_text(
            "❌ *Token Tidak Cukup!*\n\n"
            f"💰 Saldo Anda: `{balance}` token\n"
            f"📦 Dibutuhkan: `1` token\n\n"
            f"Beli token dengan menghubungi:\n"
            f"📞 {config.admin_contact}",
            parse_mode="Markdown",
        )
        return
    
    # Show loading message
    loading_msg = await update.message.reply_text(
        "⏳ *Mengambil informasi video...*\n\n"
        "Mohon tunggu sebentar.",
        parse_mode="Markdown",
    )
    
    # Get video/playlist info for preview
    try:
        if url_type == "playlist":
            # Playlist mode
            if current_mode != "playlist":
                await loading_msg.edit_text(
                    "❌ *Mode Tidak Sesuai*\n\n"
                    "Anda mengirim link playlist, tapi memilih mode video/musik.\n"
                    "Silakan pilih *YouTube Playlist* dari menu.",
                    parse_mode="Markdown",
                )
                return
            
            playlist_info = await get_playlist_info(text, config.cookies_file)
            
            if not playlist_info:
                await loading_msg.edit_text(
                    "❌ *Gagal Mengambil Info Playlist*\n\n"
                    "Pastikan playlist tersedia dan tidak private.",
                )
                return
            
            # Check if user has enough tokens for playlist
            video_count = playlist_info["count"]
            if balance < video_count and not token_manager.is_admin(user.id):
                await loading_msg.edit_text(
                    f"❌ *Token Tidak Cukup untuk Playlist!*\n\n"
                    f"💰 Saldo Anda: `{balance}` token\n"
                    f"📦 Dibutuhkan: `{video_count}` token ({video_count} video)\n\n"
                    f"Beli token dengan menghubungi:\n"
                    f"📞 {config.admin_contact}",
                    parse_mode="Markdown",
                )
                return
            
            # Store playlist info and show preview
            context.user_data["pending_url"] = text
            context.user_data["pending_info"] = playlist_info
            context.user_data["url_type"] = "playlist"
            context.user_data["required_tokens"] = video_count
            
            preview_text = (
                f"📋 *Preview Playlist*\n\n"
                f"📌 *Judul:*\n`{playlist_info['title'][:60]}`\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Detail:*\n"
                f"├ 🎬 Total Video: `{video_count}`\n"
                f"├ 💰 Token Diperlukan: `{video_count}`\n"
                f"└ 💳 Saldo Anda: `{balance}`\n\n"
                f"Pilih kualitas untuk melanjutkan:"
            )
            
            from bot.utils.keyboards import get_format_keyboard
            await loading_msg.edit_text(
                preview_text,
                reply_markup=get_format_keyboard("playlist"),
                parse_mode="Markdown",
            )
            
        else:
            # Single video mode
            video_info = await get_video_info(text, config.cookies_file)
            
            if not video_info:
                await loading_msg.edit_text(
                    "❌ *Gagal Mengambil Info Video*\n\n"
                    "Pastikan video tersedia dan tidak private.\n"
                    "Jika video memerlukan login, pastikan cookies sudah dikonfigurasi.",
                )
                return
            
            # Check mode compatibility
            if current_mode == "playlist":
                await loading_msg.edit_text(
                    "❌ *Mode Tidak Sesuai*\n\n"
                    "Anda mengirim link video, tapi memilih mode playlist.\n"
                    "Silakan pilih *YouTube Video* atau *YouTube Musik* dari menu.",
                    parse_mode="Markdown",
                )
                return
            
            # Store video info and show preview
            context.user_data["pending_url"] = text
            context.user_data["pending_info"] = video_info
            context.user_data["url_type"] = "video"
            context.user_data["required_tokens"] = 1
            
            preview_text = (
                f"🎬 *Preview Video*\n\n"
                f"📌 *Judul:*\n`{video_info.title[:60]}`\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 *Detail:*\n"
                f"├ 👤 Channel: `{video_info.channel[:30]}`\n"
                f"├ ⏱️ Durasi: `{video_info.duration}`\n"
                f"├ 👁️ Views: `{format_number(video_info.view_count)}`\n"
                f"├ 📅 Upload: `{video_info.upload_date}`\n"
                f"└ 💰 Token: `1`\n\n"
                f"💳 Saldo Anda: `{balance}` token\n\n"
                f"Pilih kualitas untuk melanjutkan:"
            )
            
            from bot.utils.keyboards import get_format_keyboard
            format_type = "music" if current_mode == "music" else "video"
            await loading_msg.edit_text(
                preview_text,
                reply_markup=get_format_keyboard(format_type),
                parse_mode="Markdown",
            )
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        await loading_msg.edit_text(
            "❌ *Terjadi Kesalahan*\n\n"
            f"Gagal mengambil informasi: {str(e)[:100]}",
            parse_mode="Markdown",
        )
