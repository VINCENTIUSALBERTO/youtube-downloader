"""
Callback query handler for YouTube Downloader Bot.

Handles all inline keyboard button callbacks.
"""

import asyncio
import logging
from datetime import datetime, date
from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from bot.database import Database
from bot.services.downloader import DownloaderService, FORMAT_OPTIONS
from bot.services.uploader import UploaderService
from bot.services.token_manager import TokenManager
from bot.utils.keyboards import (
    get_main_menu_keyboard,
    get_format_keyboard,
    get_delivery_keyboard,
    get_admin_keyboard,
    get_token_packages_keyboard,
    get_back_keyboard,
    get_cancel_keyboard,
    get_topup_keyboard,
    get_topup_confirm_keyboard,
    get_admin_topup_action_keyboard,
    get_registration_keyboard,
)
from bot.utils.helpers import format_download_result, format_file_size
from bot.config import config

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries from inline keyboards."""
    query = update.callback_query
    if not query or not query.message or not update.effective_user:
        return
    
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    # Initialize database
    db = Database(config.database_path)
    
    # Check if user is banned
    if db.is_user_banned(user.id):
        await query.edit_message_text(
            "❌ Akun Anda telah diblokir. Hubungi admin untuk informasi lebih lanjut."
        )
        return
    
    # Handle different callbacks
    if data == "back_menu":
        await handle_back_to_menu(query, context, db)
    
    elif data == "back_format":
        await handle_back_to_format(query, context)
    
    elif data.startswith("menu_"):
        await handle_menu_selection(query, context, data, db)
    
    elif data.startswith("format_"):
        await handle_format_selection(query, context, data)
    
    elif data.startswith("auto_format_"):
        await handle_auto_format_selection(query, context, data)
    
    elif data.startswith("deliver_"):
        await handle_delivery_selection(query, context, data, db)
    
    elif data == "my_tokens":
        await handle_my_tokens(query, db, user.id)
    
    elif data == "my_history":
        await handle_my_history(query, db, user.id)
    
    elif data == "buy_tokens":
        await handle_buy_tokens(query, db)
    
    elif data == "contact_admin":
        await handle_contact_admin(query)
    
    elif data.startswith("package_"):
        await handle_package_selection(query, data)
    
    elif data == "cancel_download":
        await handle_cancel_download(query, context)
    
    # Registration callbacks
    elif data == "verify_registration":
        await handle_verify_registration(query, context, db)
    
    # Daily bonus
    elif data == "claim_bonus":
        await handle_claim_bonus(query, db, user.id)
    
    # Topup callbacks
    elif data == "topup_menu":
        await handle_topup_menu(query)
    
    elif data.startswith("topup_"):
        await handle_topup_selection(query, context, data, db)
    
    elif data.startswith("send_proof_"):
        await handle_send_proof(query, context, data, db)
    
    elif data.startswith("approve_topup_"):
        await handle_approve_topup(query, context, data, db, user.id)
    
    elif data.startswith("reject_topup_"):
        await handle_reject_topup(query, context, data, db, user.id)
    
    # Admin callbacks
    elif data.startswith("admin_"):
        await handle_admin_callback(query, context, data, db, user.id)


async def handle_back_to_menu(query, context: ContextTypes.DEFAULT_TYPE, db: Database) -> None:
    """Handle going back to main menu."""
    # Clear user state
    if context.user_data:
        context.user_data.clear()
    
    user = query.from_user
    token_manager = TokenManager(db)
    balance = token_manager.get_balance(user.id)
    is_admin = token_manager.is_admin(user.id)
    
    admin_badge = " 👑" if is_admin else ""
    
    await query.edit_message_text(
        f"👋 *Menu Utama*{admin_badge}\n\n"
        f"💰 Saldo Token: `{balance}`\n\n"
        f"Pilih jenis download:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def handle_back_to_format(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle going back to format selection."""
    user_data = context.user_data or {}
    mode = user_data.get("mode", "video")
    
    await query.edit_message_text(
        "🎯 Pilih kualitas download:",
        reply_markup=get_format_keyboard(mode),
        parse_mode="Markdown",
    )


async def handle_menu_selection(query, context: ContextTypes.DEFAULT_TYPE, data: str, db: Database) -> None:
    """Handle main menu selection."""
    mode = data.replace("menu_", "")
    user = query.from_user
    
    # Check registration
    token_manager = TokenManager(db)
    if not token_manager.is_admin(user.id) and not db.is_user_registered(user.id):
        await query.edit_message_text(
            "❌ Anda belum terdaftar. Gunakan /start untuk mendaftar.",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
        return
    
    if context.user_data is None:
        context.user_data = {}
    
    context.user_data["mode"] = mode
    
    mode_labels = {
        "music": "🎵 YouTube Musik",
        "video": "🎬 YouTube Video",
        "playlist": "📋 YouTube Playlist",
    }
    
    await query.edit_message_text(
        f"*{mode_labels.get(mode, 'Download')}*\n\n"
        f"📝 Kirim link YouTube untuk melanjutkan.\n\n"
        f"*Contoh link:*\n"
        f"• `https://youtube.com/watch?v=xxxxx`\n"
        f"• `https://youtu.be/xxxxx`\n"
        + ("• `https://youtube.com/playlist?list=xxxxx`\n" if mode == "playlist" else "") +
        f"\nKetuk tombol di bawah untuk kembali.",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


async def handle_format_selection(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle format selection."""
    format_key = data.replace("format_", "").replace("playlist_", "")
    
    if context.user_data is None:
        context.user_data = {}
    
    context.user_data["format"] = format_key
    
    # Get format label
    format_info = FORMAT_OPTIONS.get(format_key, {})
    format_label = format_info.get("label", format_key.upper())
    
    await query.edit_message_text(
        f"✅ *Kualitas Dipilih:* {format_label}\n\n"
        f"📤 *Pilih metode pengiriman:*\n\n"
        f"• *Telegram* - File dikirim langsung ke chat\n"
        f"  ⚠️ Maksimal 50MB\n\n"
        f"• *Google Drive* - Unlimited ukuran\n"
        f"  📎 Anda akan mendapat link download",
        reply_markup=get_delivery_keyboard(),
        parse_mode="Markdown",
    )


async def handle_auto_format_selection(query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
    """Handle auto-detected format selection."""
    format_key = data.replace("auto_format_", "")
    
    if context.user_data is None:
        context.user_data = {}
    
    context.user_data["format"] = format_key
    
    # Set mode based on format
    if format_key == "mp3":
        context.user_data["mode"] = "music"
    else:
        context.user_data["mode"] = "video"
    
    # Get format label
    format_info = FORMAT_OPTIONS.get(format_key, {})
    format_label = format_info.get("label", format_key.upper())
    
    await query.edit_message_text(
        f"✅ *Format Dipilih:* {format_label}\n\n"
        f"📤 *Pilih metode pengiriman:*\n\n"
        f"• *Telegram* - File dikirim langsung ke chat\n"
        f"  ⚠️ Maksimal 50MB\n\n"
        f"• *Google Drive* - Unlimited ukuran\n"
        f"  📎 Anda akan mendapat link download",
        reply_markup=get_delivery_keyboard(),
        parse_mode="Markdown",
    )


async def handle_delivery_selection(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    data: str,
    db: Database,
) -> None:
    """Handle delivery method selection and start download."""
    delivery_method = data.replace("deliver_", "")
    user = query.from_user
    
    user_data = context.user_data or {}
    url = user_data.get("pending_url")
    format_key = user_data.get("format", "720p")
    mode = user_data.get("mode", "video")
    url_type = user_data.get("url_type", "video")
    required_tokens = user_data.get("required_tokens", 1)
    pending_info = user_data.get("pending_info")
    
    if not url:
        await query.edit_message_text(
            "❌ *Sesi Kadaluarsa*\n\n"
            "Silakan kirim ulang link YouTube.",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard(),
        )
        return
    
    # Check and deduct tokens
    token_manager = TokenManager(db)
    is_admin = token_manager.is_admin(user.id)
    
    if not is_admin:
        balance = token_manager.get_balance(user.id)
        if balance < required_tokens:
            await query.edit_message_text(
                f"❌ *Token Tidak Cukup!*\n\n"
                f"💰 Saldo: `{balance}` token\n"
                f"📦 Dibutuhkan: `{required_tokens}` token\n\n"
                f"Hubungi {config.admin_contact} untuk beli token.",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard(),
            )
            return
        
        # Deduct token
        for _ in range(required_tokens):
            token_manager.use_token(user.id, f"Download: {url[:50]}")
        
        new_balance = token_manager.get_balance(user.id)
    else:
        new_balance = token_manager.get_balance(user.id)
    
    # Create download record
    title = ""
    if pending_info:
        if hasattr(pending_info, "title"):
            title = pending_info.title
        elif isinstance(pending_info, dict):
            title = pending_info.get("title", "")
    
    download_id = db.create_download(
        user_id=user.id,
        url=url,
        download_type=mode,
        delivery_method=delivery_method,
        title=title,
    )
    
    # Clear pending data
    context.user_data.pop("pending_url", None)
    context.user_data.pop("pending_info", None)
    
    # Show processing message
    await query.edit_message_text(
        f"⏳ *Memproses Download...*\n\n"
        f"📦 Kualitas: `{format_key.upper()}`\n"
        f"📤 Pengiriman: `{delivery_method.title()}`\n"
        f"💰 Token Sisa: `{new_balance}`\n\n"
        f"Mohon tunggu, proses ini mungkin memakan waktu beberapa menit.",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard(),
    )
    
    # Start download process
    asyncio.create_task(
        process_download(
            query=query,
            context=context,
            db=db,
            download_id=download_id,
            url=url,
            format_key=format_key,
            delivery_method=delivery_method,
            user_id=user.id,
        )
    )


async def process_download(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    db: Database,
    download_id: int,
    url: str,
    format_key: str,
    delivery_method: str,
    user_id: int,
) -> None:
    """Process the actual download and upload."""
    try:
        # Initialize services
        downloader = DownloaderService(
            download_dir=config.download_dir,
            cookies_file=config.cookies_file if config.cookies_file else None,
        )
        uploader = UploaderService(rclone_remote=config.rclone_remote)
        
        # Update status
        async def update_status(message: str):
            try:
                await query.edit_message_text(
                    f"⏳ *{message}*\n\n"
                    f"Mohon tunggu...",
                    parse_mode="Markdown",
                )
            except Exception:
                pass
        
        # Download
        await update_status("Mengunduh video...")
        result = await downloader.download(url, format_key, update_status)
        
        if not result.success:
            db.update_download(download_id, status="failed")
            await query.edit_message_text(
                f"❌ *Download Gagal*\n\n"
                f"{result.error or 'Terjadi kesalahan'}",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard(),
            )
            return
        
        # Update download record with title
        db.update_download(
            download_id,
            title=result.title,
            duration=result.duration,
            file_size=result.file_size,
        )
        
        # Upload
        await update_status("Mengunggah file...")
        
        drive_link = None
        is_audio = format_key == "mp3"
        
        if delivery_method == "telegram":
            upload_result = await uploader.upload_to_telegram(
                bot=context.bot,
                chat_id=query.message.chat_id,
                file_path=result.file_path,
                caption=f"🎵 *{result.title}*" if is_audio else f"🎬 *{result.title}*",
                is_audio=is_audio,
            )
            
            if not upload_result.success:
                # Fallback to Drive if Telegram fails
                await update_status("Telegram gagal, menggunakan Drive...")
                upload_result = await uploader.upload_to_drive(result.file_path)
                delivery_method = "drive"
                drive_link = upload_result.drive_link
                
        else:  # drive
            upload_result = await uploader.upload_to_drive(result.file_path)
            drive_link = upload_result.drive_link
        
        # Cleanup downloaded file
        downloader.cleanup_file(result.file_path)
        
        if not upload_result.success:
            db.update_download(download_id, status="failed")
            await query.edit_message_text(
                f"❌ *Upload Gagal*\n\n"
                f"{upload_result.error or 'Terjadi kesalahan'}",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard(),
            )
            return
        
        # Update download record
        db.update_download(
            download_id,
            status="completed",
            drive_link=drive_link,
        )
        
        # Send success message
        success_message = format_download_result(
            title=result.title,
            quality=format_key,
            file_size=result.file_size,
            duration=result.duration,
            delivery_method=delivery_method,
            drive_link=drive_link,
        )
        
        await query.edit_message_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard(),
        )
        
        logger.info(f"Download completed for user {user_id}: {result.title}")
        
    except Exception as e:
        logger.error(f"Download process error: {e}")
        db.update_download(download_id, status="failed")
        await query.edit_message_text(
            f"❌ *Terjadi Kesalahan*\n\n"
            f"{str(e)[:200]}",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard(),
        )


async def handle_my_tokens(query, db: Database, user_id: int) -> None:
    """Handle token balance check."""
    token_manager = TokenManager(db)
    balance = token_manager.get_balance(user_id)
    history = token_manager.get_transaction_history(user_id, 5)
    
    text = (
        f"💰 *Saldo Token Anda*\n\n"
        f"🪙 Token: `{balance}`\n\n"
    )
    
    if history:
        text += "📜 *Transaksi Terakhir:*\n"
        for tx in history:
            amount_str = f"+{tx['amount']}" if tx['amount'] > 0 else str(tx['amount'])
            text += f"• {amount_str} - {tx['description'][:25]}\n"
    
    text += f"\n💎 Beli token? Ketuk tombol di bawah."
    
    await query.edit_message_text(
        text,
        reply_markup=get_token_packages_keyboard(),
        parse_mode="Markdown",
    )


async def handle_my_history(query, db: Database, user_id: int) -> None:
    """Handle download history."""
    downloads = db.get_user_downloads(user_id, 10)
    
    if not downloads:
        text = "📊 *Riwayat Download*\n\nBelum ada riwayat download."
    else:
        text = "📊 *Riwayat Download Anda*\n\n"
        for i, dl in enumerate(downloads, 1):
            status_emoji = "✅" if dl["status"] == "completed" else "❌"
            title = (dl["title"] or "Unknown")[:25]
            text += f"{i}. {status_emoji} {title}\n"
    
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


async def handle_buy_tokens(query, db: Database) -> None:
    """Handle buy tokens menu."""
    token_manager = TokenManager(db)
    text = token_manager.get_price_list_text()
    
    await query.edit_message_text(
        text,
        reply_markup=get_token_packages_keyboard(),
        parse_mode="Markdown",
    )


async def handle_contact_admin(query) -> None:
    """Handle contact admin request."""
    text = (
        f"📞 *Hubungi Admin*\n\n"
        f"Untuk pembelian token atau bantuan:\n\n"
        f"• Telegram: {config.admin_contact}\n"
    )
    
    if config.admin_whatsapp:
        text += f"• WhatsApp: {config.admin_whatsapp}\n"
    
    text += (
        f"\n📝 *Informasi yang diperlukan:*\n"
        f"• User ID Anda: `{query.from_user.id}`\n"
        f"• Jumlah token yang ingin dibeli\n"
        f"• Bukti transfer"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


async def handle_package_selection(query, data: str) -> None:
    """Handle token package selection."""
    package = data.replace("package_", "")
    
    prices = {
        "1": config.token_price_1,
        "5": config.token_price_5,
        "10": config.token_price_10,
        "25": config.token_price_25,
    }
    
    price = prices.get(package, 0)
    
    text = (
        f"💎 *Pembelian Token*\n\n"
        f"📦 Paket: `{package}` Token\n"
        f"💰 Harga: `Rp {price:,}`\n\n".replace(",", ".") +
        f"📞 *Untuk melanjutkan pembelian:*\n"
        f"Hubungi {config.admin_contact}\n\n"
        f"📝 Kirim:\n"
        f"• User ID: `{query.from_user.id}`\n"
        f"• Paket: {package} Token\n"
        f"• Bukti transfer"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


async def handle_cancel_download(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle download cancellation."""
    if context.user_data:
        context.user_data.clear()
    
    await query.edit_message_text(
        "❌ *Download Dibatalkan*\n\n"
        "Gunakan /start untuk memulai lagi.",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(),
    )


async def handle_verify_registration(query, context: ContextTypes.DEFAULT_TYPE, db: Database) -> None:
    """Handle registration verification."""
    user = query.from_user
    
    try:
        member = await context.bot.get_chat_member(
            chat_id=config.required_channel,
            user_id=user.id,
        )
        is_member = member.status in [
            ChatMember.MEMBER,
            ChatMember.ADMINISTRATOR,
            ChatMember.OWNER,
        ]
    except TelegramError as e:
        logger.error(f"Error checking channel membership: {e}")
        is_member = True  # Allow if we can't check
    
    if not is_member:
        await query.edit_message_text(
            f"❌ *Verifikasi Gagal*\n\n"
            f"Anda belum bergabung ke channel {config.required_channel}.\n\n"
            f"Silakan bergabung terlebih dahulu, lalu tekan tombol Verifikasi.",
            reply_markup=get_registration_keyboard(),
            parse_mode="Markdown",
        )
        return
    
    # Register user
    db.register_user(user.id)
    
    # Give welcome bonus
    today_str = date.today().isoformat()
    new_balance = db.claim_daily_bonus(user.id, config.daily_bonus_amount, today_str)
    
    await query.edit_message_text(
        f"🎉 *Registrasi Berhasil!*\n\n"
        f"Terima kasih telah bergabung ke {config.required_channel}!\n\n"
        f"🎁 Anda mendapatkan *{config.daily_bonus_amount} Token GRATIS* sebagai bonus selamat datang!\n"
        f"💰 Saldo Anda: `{new_balance}` token\n\n"
        f"Gunakan /start untuk memulai download.",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(),
    )


async def handle_claim_bonus(query, db: Database, user_id: int) -> None:
    """Handle daily bonus claim."""
    # Check registration
    if not db.is_user_registered(user_id):
        await query.edit_message_text(
            "❌ Anda belum terdaftar. Gunakan /start untuk mendaftar.",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
        return
    
    # Check if already claimed today
    today_str = date.today().isoformat()
    last_bonus = db.get_last_daily_bonus(user_id)
    
    if last_bonus == today_str:
        await query.edit_message_text(
            "⏰ *Bonus Harian*\n\n"
            "Anda sudah mengklaim bonus hari ini.\n"
            "Silakan kembali besok! 🌅",
            reply_markup=get_back_keyboard(),
            parse_mode="Markdown",
        )
        return
    
    # Claim bonus
    new_balance = db.claim_daily_bonus(user_id, config.daily_bonus_amount, today_str)
    
    await query.edit_message_text(
        f"🎁 *Bonus Harian Diklaim!*\n\n"
        f"➕ Anda mendapat *+{config.daily_bonus_amount} Token*\n"
        f"💰 Saldo Anda sekarang: `{new_balance}` token\n\n"
        f"Kembali lagi besok untuk bonus berikutnya! 🌅",
        reply_markup=get_back_keyboard(),
        parse_mode="Markdown",
    )


async def handle_topup_menu(query) -> None:
    """Handle topup menu display."""
    text = (
        "💳 *Menu Topup Token*\n\n"
        "Pilih paket token yang ingin Anda beli:\n\n"
        f"📦 *Paket Tersedia:*\n"
        f"• 1 Token - Rp {config.token_price_1:,}\n".replace(",", ".") +
        f"• 5 Token - Rp {config.token_price_5:,}\n".replace(",", ".") +
        f"• 10 Token - Rp {config.token_price_10:,}\n".replace(",", ".") +
        f"• 25 Token - Rp {config.token_price_25:,}\n\n".replace(",", ".") +
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Cara Topup:*\n"
        f"1. Pilih paket di bawah\n"
        f"2. Transfer ke rekening yang tertera\n"
        f"3. Kirim bukti transfer\n"
        f"4. Admin akan memverifikasi\n"
        f"5. Token otomatis ditambahkan ✅"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_topup_keyboard(),
        parse_mode="Markdown",
    )


async def handle_topup_selection(query, context: ContextTypes.DEFAULT_TYPE, data: str, db: Database) -> None:
    """Handle topup package selection."""
    package = data.replace("topup_", "")
    
    prices = {
        "1": config.token_price_1,
        "5": config.token_price_5,
        "10": config.token_price_10,
        "25": config.token_price_25,
    }
    
    amounts = {
        "1": 1,
        "5": 5,
        "10": 10,
        "25": 25,
    }
    
    price = prices.get(package, 0)
    amount = amounts.get(package, 0)
    
    # Store topup info in context
    if context.user_data is None:
        context.user_data = {}
    
    context.user_data["topup_package"] = package
    context.user_data["topup_amount"] = amount
    context.user_data["topup_price"] = price
    
    text = (
        f"💳 *Topup Token*\n\n"
        f"📦 *Paket:* {amount} Token\n"
        f"💰 *Harga:* Rp {price:,}\n\n".replace(",", ".") +
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏦 *Transfer ke:*\n"
        f"Bank: `{config.payment_bank}`\n"
        f"No. Rekening: `{config.payment_account}`\n"
        f"Atas Nama: `{config.payment_name}`\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📋 *Langkah-langkah:*\n"
        f"1. Transfer *Rp {price:,}* ke rekening di atas\n".replace(",", ".") +
        f"2. Screenshot bukti transfer\n"
        f"3. Tekan tombol *Kirim Bukti Transfer*\n"
        f"4. Kirim screenshot bukti transfer Anda\n"
        f"5. Tunggu verifikasi admin (maks 1x24 jam)\n\n"
        f"⚠️ *Penting:* Pastikan nominal transfer sesuai!"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=get_topup_confirm_keyboard(package),
        parse_mode="Markdown",
    )


async def handle_send_proof(query, context: ContextTypes.DEFAULT_TYPE, data: str, db: Database) -> None:
    """Handle send proof button - user needs to send a photo."""
    package = data.replace("send_proof_", "")
    user = query.from_user
    
    user_data = context.user_data or {}
    amount = user_data.get("topup_amount", 0)
    price = user_data.get("topup_price", 0)
    
    if not amount or not price:
        await query.edit_message_text(
            "❌ *Sesi Kadaluarsa*\n\n"
            "Silakan pilih paket topup lagi.",
            reply_markup=get_topup_keyboard(),
            parse_mode="Markdown",
        )
        return
    
    # Create topup request
    request_id = db.create_topup_request(
        user_id=user.id,
        amount=amount,
        package=package,
        price=price,
    )
    
    # Store request ID in context for later
    context.user_data["topup_request_id"] = request_id
    context.user_data["awaiting_proof"] = True
    
    await query.edit_message_text(
        f"📤 *Kirim Bukti Transfer*\n\n"
        f"Silakan kirim *screenshot/foto* bukti transfer Anda sebagai pesan berikutnya.\n\n"
        f"📋 *Detail Topup:*\n"
        f"• Paket: {amount} Token\n"
        f"• Harga: Rp {price:,}\n".replace(",", ".") +
        f"• ID Request: `#{request_id}`\n\n"
        f"⏳ Menunggu bukti transfer...",
        parse_mode="Markdown",
    )


async def handle_approve_topup(query, context: ContextTypes.DEFAULT_TYPE, data: str, db: Database, admin_id: int) -> None:
    """Handle admin approving a topup request."""
    token_manager = TokenManager(db)
    
    if not token_manager.is_admin(admin_id):
        return
    
    request_id = int(data.replace("approve_topup_", ""))
    request = db.get_topup_request(request_id)
    
    if not request:
        await query.edit_message_text("❌ Request tidak ditemukan.")
        return
    
    if request["status"] != "pending":
        await query.edit_message_text("❌ Request sudah diproses.")
        return
    
    # Add tokens to user
    token_manager.add_tokens(
        user_id=request["user_id"],
        amount=request["amount"],
        admin_id=admin_id,
        description=f"Topup {request['amount']} token (#{request_id})",
    )
    
    # Update request status
    db.update_topup_request(
        request_id=request_id,
        status="approved",
        processed_by=admin_id,
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=request["user_id"],
            text=f"✅ *Topup Berhasil!*\n\n"
                 f"Topup Anda telah diverifikasi.\n\n"
                 f"📦 Paket: {request['amount']} Token\n"
                 f"💰 ID Request: `#{request_id}`\n\n"
                 f"Token sudah ditambahkan ke saldo Anda!",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to notify user: {e}")
    
    await query.edit_message_text(
        f"✅ *Topup Disetujui*\n\n"
        f"User ID: `{request['user_id']}`\n"
        f"Amount: {request['amount']} Token\n"
        f"Request ID: #{request_id}",
        parse_mode="Markdown",
    )


async def handle_reject_topup(query, context: ContextTypes.DEFAULT_TYPE, data: str, db: Database, admin_id: int) -> None:
    """Handle admin rejecting a topup request."""
    token_manager = TokenManager(db)
    
    if not token_manager.is_admin(admin_id):
        return
    
    request_id = int(data.replace("reject_topup_", ""))
    request = db.get_topup_request(request_id)
    
    if not request:
        await query.edit_message_text("❌ Request tidak ditemukan.")
        return
    
    if request["status"] != "pending":
        await query.edit_message_text("❌ Request sudah diproses.")
        return
    
    # Update request status
    db.update_topup_request(
        request_id=request_id,
        status="rejected",
        processed_by=admin_id,
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=request["user_id"],
            text=f"❌ *Topup Ditolak*\n\n"
                 f"Maaf, topup Anda tidak dapat diverifikasi.\n\n"
                 f"📦 Paket: {request['amount']} Token\n"
                 f"💰 ID Request: `#{request_id}`\n\n"
                 f"Alasan: Bukti transfer tidak valid.\n"
                 f"Hubungi {config.admin_contact} jika ada kesalahan.",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Failed to notify user: {e}")
    
    await query.edit_message_text(
        f"❌ *Topup Ditolak*\n\n"
        f"User ID: `{request['user_id']}`\n"
        f"Amount: {request['amount']} Token\n"
        f"Request ID: #{request_id}",
        parse_mode="Markdown",
    )


async def handle_admin_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    data: str,
    db: Database,
    user_id: int,
) -> None:
    """Handle admin-specific callbacks."""
    token_manager = TokenManager(db)
    
    if not token_manager.is_admin(user_id):
        await query.edit_message_text("❌ Anda tidak memiliki akses admin.")
        return
    
    action = data.replace("admin_", "")
    
    if action == "users":
        users = db.get_all_users()[:10]
        text = "👥 *Daftar User*\n\n"
        for u in users:
            name = u.get("username") or u.get("first_name") or "Unknown"
            banned = "🚫" if u["is_banned"] else ""
            text += f"• `{u['user_id']}` - {name} {banned}\n  💰 {u['tokens']} token\n"
        
        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown",
        )
    
    elif action == "stats":
        stats = db.get_user_stats()
        text = (
            "📊 *Statistik*\n\n"
            f"👥 Total User: `{stats['total_users']}`\n"
            f"🪙 Total Token: `{stats['total_tokens']}`\n"
            f"📥 Total Download: `{stats['total_downloads']}`"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown",
        )
    
    elif action == "add_token":
        text = (
            "➕ *Tambah Token*\n\n"
            "Gunakan perintah:\n"
            "`/addtoken <user_id> <jumlah>`\n\n"
            "Contoh:\n"
            "`/addtoken 123456789 10`"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown",
        )
    
    elif action == "ban":
        text = (
            "🚫 *Ban/Unban User*\n\n"
            "Gunakan perintah:\n"
            "`/ban <user_id>` - Ban user\n"
            "`/unban <user_id>` - Unban user\n\n"
            "Contoh:\n"
            "`/ban 123456789`"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown",
        )
    
    elif action == "broadcast":
        text = (
            "📢 *Broadcast*\n\n"
            "Gunakan perintah:\n"
            "`/broadcast <pesan>`\n\n"
            "Contoh:\n"
            "`/broadcast Halo semua! Ada promo hari ini.`"
        )
        
        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown",
        )
    
    elif action == "pending_topup":
        pending = db.get_pending_topup_requests()
        
        if not pending:
            text = "💳 *Topup Pending*\n\nTidak ada request topup yang pending."
        else:
            text = f"💳 *Topup Pending* ({len(pending)})\n\n"
            for req in pending[:10]:
                user = db.get_user(req["user_id"])
                username = user.get("username") if user else "Unknown"
                text += (
                    f"• ID: `#{req['id']}`\n"
                    f"  User: `{req['user_id']}` (@{username})\n"
                    f"  Paket: {req['amount']} Token\n"
                    f"  Harga: Rp {req['price']:,}\n\n".replace(",", ".")
                )
        
        await query.edit_message_text(
            text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown",
        )
