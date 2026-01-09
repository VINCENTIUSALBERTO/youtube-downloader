"""
Admin command handlers for YouTube Downloader Bot.

Handles admin-only commands for user and token management.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.database import Database
from bot.services.token_manager import TokenManager
from bot.utils.keyboards import get_admin_keyboard
from bot.config import config

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in config.admin_user_ids


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin command - show admin panel."""
    if not update.effective_user or not update.message:
        return
    
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    db = Database(config.database_path)
    stats = db.get_user_stats()
    
    text = (
        "👑 *Panel Admin*\n\n"
        f"📊 *Statistik:*\n"
        f"• Total User: `{stats['total_users']}`\n"
        f"• Total Token: `{stats['total_tokens']}`\n"
        f"• Total Download: `{stats['total_downloads']}`\n\n"
        "Pilih aksi di bawah:"
    )
    
    await update.message.reply_text(
        text,
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown",
    )


async def add_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /addtoken command - add tokens to user.
    
    Usage: /addtoken <user_id> <amount>
    """
    if not update.effective_user or not update.message:
        return
    
    admin_id = update.effective_user.id
    
    if not is_admin(admin_id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    # Parse arguments
    args = context.args if context.args else []
    
    if len(args) < 2:
        await update.message.reply_text(
            "📝 *Cara Penggunaan:*\n"
            "`/addtoken <user_id> <jumlah>`\n\n"
            "*Contoh:*\n"
            "`/addtoken 123456789 10`\n\n"
            "Ini akan menambahkan 10 token ke user 123456789.",
            parse_mode="Markdown",
        )
        return
    
    try:
        target_user_id = int(args[0])
        amount = int(args[1])
        
        if amount <= 0:
            await update.message.reply_text("❌ Jumlah token harus lebih dari 0.")
            return
        
        if amount > 1000:
            await update.message.reply_text("❌ Maksimal 1000 token per transaksi.")
            return
        
    except ValueError:
        await update.message.reply_text("❌ User ID dan jumlah harus berupa angka.")
        return
    
    db = Database(config.database_path)
    token_manager = TokenManager(db)
    
    # Check if user exists
    user = db.get_user(target_user_id)
    if not user:
        # Create user if not exists
        db.create_or_update_user(target_user_id)
    
    # Add tokens
    description = f"Added by admin {admin_id}"
    new_balance = token_manager.add_tokens(target_user_id, amount, admin_id, description)
    
    await update.message.reply_text(
        f"✅ *Token Berhasil Ditambahkan!*\n\n"
        f"👤 User ID: `{target_user_id}`\n"
        f"➕ Jumlah: `{amount}` token\n"
        f"💰 Saldo Baru: `{new_balance}` token",
        parse_mode="Markdown",
    )
    
    logger.info(f"Admin {admin_id} added {amount} tokens to user {target_user_id}")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - show detailed statistics."""
    if not update.effective_user or not update.message:
        return
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    db = Database(config.database_path)
    stats = db.get_user_stats()
    users = db.get_all_users()
    
    # Get top users by tokens
    top_users = sorted(users, key=lambda x: x["tokens"], reverse=True)[:5]
    
    text = (
        "📊 *Statistik Detail*\n\n"
        f"👥 *Total User:* `{stats['total_users']}`\n"
        f"🪙 *Total Token Beredar:* `{stats['total_tokens']}`\n"
        f"📥 *Total Download Selesai:* `{stats['total_downloads']}`\n\n"
        "🏆 *Top 5 User (Token):*\n"
    )
    
    for i, user in enumerate(top_users, 1):
        name = user.get("username") or user.get("first_name") or f"User {user['user_id']}"
        text += f"{i}. {name}: `{user['tokens']}` token\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /broadcast command - send message to all users.
    
    Usage: /broadcast <message>
    """
    if not update.effective_user or not update.message:
        return
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    # Get message to broadcast
    if not context.args:
        await update.message.reply_text(
            "📝 *Cara Penggunaan:*\n"
            "`/broadcast <pesan>`\n\n"
            "*Contoh:*\n"
            "`/broadcast Halo semua! Ada promo token hari ini.`",
            parse_mode="Markdown",
        )
        return
    
    message = " ".join(context.args)
    
    db = Database(config.database_path)
    users = db.get_all_users()
    
    success_count = 0
    fail_count = 0
    
    for user in users:
        if user["is_banned"]:
            continue
        
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 *Pengumuman Admin*\n\n{message}",
                parse_mode="Markdown",
            )
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to {user['user_id']}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"✅ *Broadcast Selesai!*\n\n"
        f"• Berhasil: `{success_count}` user\n"
        f"• Gagal: `{fail_count}` user",
        parse_mode="Markdown",
    )


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /ban command - ban a user.
    
    Usage: /ban <user_id>
    """
    if not update.effective_user or not update.message:
        return
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    args = context.args if context.args else []
    
    if not args:
        await update.message.reply_text(
            "📝 *Cara Penggunaan:*\n"
            "`/ban <user_id>`\n\n"
            "*Contoh:*\n"
            "`/ban 123456789`",
            parse_mode="Markdown",
        )
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return
    
    if target_user_id in config.admin_user_ids:
        await update.message.reply_text("❌ Tidak dapat mem-ban admin.")
        return
    
    db = Database(config.database_path)
    db.ban_user(target_user_id, True)
    
    await update.message.reply_text(
        f"🚫 User `{target_user_id}` telah di-ban.",
        parse_mode="Markdown",
    )


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /unban command - unban a user.
    
    Usage: /unban <user_id>
    """
    if not update.effective_user or not update.message:
        return
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    args = context.args if context.args else []
    
    if not args:
        await update.message.reply_text(
            "📝 *Cara Penggunaan:*\n"
            "`/unban <user_id>`\n\n"
            "*Contoh:*\n"
            "`/unban 123456789`",
            parse_mode="Markdown",
        )
        return
    
    try:
        target_user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID harus berupa angka.")
        return
    
    db = Database(config.database_path)
    db.ban_user(target_user_id, False)
    
    await update.message.reply_text(
        f"✅ User `{target_user_id}` telah di-unban.",
        parse_mode="Markdown",
    )


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /users command - list all users."""
    if not update.effective_user or not update.message:
        return
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Anda tidak memiliki akses admin.")
        return
    
    db = Database(config.database_path)
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("📊 Belum ada user terdaftar.")
        return
    
    # Paginate if too many users
    page = 1
    per_page = 10
    
    if context.args:
        try:
            page = int(context.args[0])
        except ValueError:
            pass
    
    start = (page - 1) * per_page
    end = start + per_page
    page_users = users[start:end]
    total_pages = (len(users) + per_page - 1) // per_page
    
    text = f"👥 *Daftar User* (Halaman {page}/{total_pages})\n\n"
    
    for user in page_users:
        name = user.get("username") or user.get("first_name") or "Unknown"
        banned = "🚫" if user["is_banned"] else ""
        text += (
            f"• `{user['user_id']}` - {name} {banned}\n"
            f"  💰 Token: {user['tokens']}\n"
        )
    
    if total_pages > 1:
        text += f"\n📄 Gunakan `/users <halaman>` untuk navigasi."
    
    await update.message.reply_text(text, parse_mode="Markdown")
