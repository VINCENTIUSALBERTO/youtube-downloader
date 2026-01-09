#!/usr/bin/env python3
"""
YouTube Downloader Telegram Bot

A commercial-grade Telegram bot for downloading YouTube videos and music.

Features:
- YouTube Music download (MP3)
- YouTube Video download (multiple qualities)
- YouTube Playlist download
- Token-based access system
- Admin panel for user management
- Google Drive and Telegram delivery options

Usage:
    python run.py

Environment Variables:
    BOT_TOKEN: Telegram bot token (required)
    ADMIN_USER_IDS: Comma-separated admin user IDs (required)
    RCLONE_REMOTE: rclone remote destination (default: gdrive:YouTube_Downloads)
    DOWNLOAD_DIR: Temporary download directory (default: /tmp/youtube_downloads)
    COOKIES_FILE: Path to cookies.txt for age-restricted content (optional)
    ADMIN_CONTACT: Admin Telegram username for contact (required)
    ADMIN_WHATSAPP: Admin WhatsApp number (optional)
    TOKEN_PRICE_*: Token pricing configuration

Author: YouTube Downloader Bot Team
Version: 2.0.0
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import run_bot

if __name__ == "__main__":
    run_bot()
