"""
Start and help command handlers for YouTube Downloader Bot.

Handles /start and /help commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.database import Database
from bot.services.token_manager import TokenManager
from bot.utils.keyboards import get_main_menu_keyboard
from bot.config import config

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.effective_user or not update.message:
        return
    
    user = update.effective_user
    
    # Initialize database and register user
    db = Database(config.database_path)
    db.create_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )
    
    # Check if user is banned
    if db.is_user_banned(user.id):
        await update.message.reply_text(
            "❌ Akun Anda telah diblokir. Hubungi admin untuk informasi lebih lanjut."
        )
        return
    
    # Get token balance
    token_manager = TokenManager(db)
    balance = token_manager.get_balance(user.id)
    is_admin = token_manager.is_admin(user.id)
    
    # Build welcome message
    admin_badge = " 👑" if is_admin else ""
    
    welcome_text = (
        f"👋 *Selamat datang, {user.first_name}!*{admin_badge}\n\n"
        f"🤖 *YouTube Downloader Bot*\n"
        f"Bot ini membantu Anda mengunduh video dan musik dari YouTube.\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Saldo Token Anda:* `{balance}` token\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 *Menu Utama:*\n"
        f"• 🎵 *YouTube Musik* - Download audio MP3\n"
        f"• 🎬 *YouTube Video* - Download video\n"
        f"• 📋 *YouTube Playlist* - Download playlist\n\n"
        f"📝 *Cara Penggunaan:*\n"
        f"1. Pilih jenis download di bawah\n"
        f"2. Kirim link YouTube\n"
        f"3. Konfirmasi dan pilih kualitas\n"
        f"4. Pilih metode pengiriman\n"
        f"5. Tunggu proses selesai ✅\n\n"
        f"💡 *1 Token = 1 Video/Musik*\n"
        f"Beli token dengan menghubungi admin."
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )
    
    logger.info(f"User {user.id} ({user.username}) started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.effective_user or not update.message:
        return
    
    db = Database(config.database_path)
    if db.is_user_banned(update.effective_user.id):
        return
    
    help_text = (
        "📖 *Panduan Penggunaan Bot*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📌 *Perintah Tersedia:*\n"
        "• /start - Mulai bot dan lihat menu\n"
        "• /help - Tampilkan bantuan ini\n"
        "• /token - Cek saldo token\n"
        "• /history - Lihat riwayat download\n"
        "• /buy - Beli token\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎵 *Format Audio:*\n"
        "• MP3 (192kbps) - Kualitas standar\n\n"
        "📹 *Format Video:*\n"
        "• 360p - Kualitas rendah, hemat data\n"
        "• 720p - HD, rekomendasi\n"
        "• 1080p - Full HD\n"
        "• Best - Kualitas terbaik tersedia\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📤 *Metode Pengiriman:*\n"
        "• Telegram - File dikirim langsung (max 50MB)\n"
        "• Google Drive - Unlimited, dapat link\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💰 *Sistem Token:*\n"
        "• 1 Token = 1 Video/Musik\n"
        "• Playlist dihitung per video\n"
        "• Beli token via admin\n\n"
        f"📞 *Kontak Admin:* {config.admin_contact}"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
    )


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /token command - check token balance."""
    if not update.effective_user or not update.message:
        return
    
    user = update.effective_user
    db = Database(config.database_path)
    
    if db.is_user_banned(user.id):
        return
    
    token_manager = TokenManager(db)
    balance = token_manager.get_balance(user.id)
    history = token_manager.get_transaction_history(user.id, 5)
    
    text = (
        f"💰 *Saldo Token Anda*\n\n"
        f"🪙 Token: `{balance}`\n\n"
    )
    
    if history:
        text += "📜 *Transaksi Terakhir:*\n"
        for tx in history:
            amount_str = f"+{tx['amount']}" if tx['amount'] > 0 else str(tx['amount'])
            text += f"• {amount_str} - {tx['description'][:30]}\n"
    
    text += f"\n💎 Beli token? Hubungi {config.admin_contact}"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command - show download history."""
    if not update.effective_user or not update.message:
        return
    
    user = update.effective_user
    db = Database(config.database_path)
    
    if db.is_user_banned(user.id):
        return
    
    downloads = db.get_user_downloads(user.id, 10)
    
    if not downloads:
        await update.message.reply_text(
            "📊 *Riwayat Download*\n\nBelum ada riwayat download.",
            parse_mode="Markdown",
        )
        return
    
    text = "📊 *Riwayat Download Anda*\n\n"
    
    for i, dl in enumerate(downloads, 1):
        status_emoji = "✅" if dl["status"] == "completed" else "❌"
        title = dl["title"][:30] if dl["title"] else "Unknown"
        text += f"{i}. {status_emoji} {title}\n"
        text += f"   📁 {dl['download_type']} | 📤 {dl['delivery_method']}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /buy command - show token packages."""
    if not update.effective_user or not update.message:
        return
    
    db = Database(config.database_path)
    if db.is_user_banned(update.effective_user.id):
        return
    
    token_manager = TokenManager(db)
    price_text = token_manager.get_price_list_text()
    
    await update.message.reply_text(price_text, parse_mode="Markdown")
