"""
Main bot module for YouTube Downloader Bot.

Initializes and runs the Telegram bot with all handlers.
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import config
from bot.handlers.start import (
    start_command,
    help_command,
    token_command,
    history_command,
    buy_command,
    topup_command,
    bonus_command,
)
from bot.handlers.admin import (
    admin_command,
    add_token_command,
    stats_command,
    broadcast_command,
    ban_command,
    unban_command,
    users_command,
)
from bot.handlers.download import handle_url_message, handle_photo_message
from bot.handlers.callback import handle_callback_query

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Create and configure the bot application."""
    
    if not config.bot_token:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    if not config.admin_user_ids:
        logger.warning(
            "ADMIN_USER_IDS is not configured. Admin features will be unavailable."
        )
    
    # Create application
    application = Application.builder().token(config.bot_token).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("topup", topup_command))
    application.add_handler(CommandHandler("bonus", bonus_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("addtoken", add_token_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("users", users_command))
    
    # Message handler for URLs
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message)
    )
    
    # Message handler for photos (topup proof)
    application.add_handler(
        MessageHandler(filters.PHOTO, handle_photo_message)
    )
    
    # Callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    logger.info("Bot application created successfully")
    
    return application


def run_bot() -> None:
    """Start the bot."""
    logger.info("Starting YouTube Downloader Bot...")
    logger.info(f"Admin IDs: {config.admin_user_ids}")
    logger.info(f"Download directory: {config.download_dir}")
    logger.info(f"rclone remote: {config.rclone_remote}")
    
    application = create_application()
    
    # Start polling
    logger.info("Bot is now running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
