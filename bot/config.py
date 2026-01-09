"""
Configuration module for YouTube Downloader Bot.

Loads and validates environment variables.
"""

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration loaded from environment variables."""
    
    # Telegram Bot Token
    bot_token: str
    
    # Admin user IDs (can manage tokens and users)
    admin_user_ids: List[int]
    
    # rclone remote destination
    rclone_remote: str
    
    # Temporary download directory
    download_dir: str
    
    # Optional cookies file path
    cookies_file: str
    
    # Admin contact information
    admin_contact: str
    admin_whatsapp: str
    
    # Token pricing (in IDR)
    token_price_1: int
    token_price_5: int
    token_price_10: int
    token_price_25: int
    
    # Database path
    database_path: str


def load_config() -> Config:
    """Load configuration from environment variables."""
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is required")
    
    admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
    admin_user_ids = [
        int(uid.strip())
        for uid in admin_ids_str.split(",")
        if uid.strip().isdigit()
    ]
    
    return Config(
        bot_token=bot_token,
        admin_user_ids=admin_user_ids,
        rclone_remote=os.getenv("RCLONE_REMOTE", "gdrive:YouTube_Downloads"),
        download_dir=os.getenv("DOWNLOAD_DIR", "/tmp/youtube_downloads"),
        cookies_file=os.getenv("COOKIES_FILE", ""),
        admin_contact=os.getenv("ADMIN_CONTACT", "@admin"),
        admin_whatsapp=os.getenv("ADMIN_WHATSAPP", ""),
        token_price_1=int(os.getenv("TOKEN_PRICE_1", "5000")),
        token_price_5=int(os.getenv("TOKEN_PRICE_5", "20000")),
        token_price_10=int(os.getenv("TOKEN_PRICE_10", "35000")),
        token_price_25=int(os.getenv("TOKEN_PRICE_25", "75000")),
        database_path=os.getenv("DATABASE_PATH", "data/bot.db"),
    )


# Global config instance
config = load_config()
