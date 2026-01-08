# YouTube Downloader Telegram Bot

A Telegram bot for downloading media from YouTube and other platforms, then automatically uploading to Google Drive.

## Features

- 🔐 **User Authentication**: Whitelist-based security - only authorized users can use the bot
- 🎵 **Audio Download**: Extract audio as MP3 (192kbps)
- 📹 **Video Quality Options**: 360p, 720p, 1080p, or Best Quality (2K/4K)
- ☁️ **Google Drive Integration**: Automatic upload via rclone
- 🧹 **Auto Cleanup**: Files are deleted from VPS after successful upload
- 📢 **Real-time Notifications**: Status updates for downloading, uploading, and completion
- 🍪 **Cookie Support**: Optional cookies.txt for age-restricted content

## Supported Platforms

- YouTube
- Twitter/X
- TikTok
- Instagram
- Vimeo
- Reddit
- Twitch
- And many more (any platform supported by yt-dlp)

## Prerequisites

### System Requirements

- Ubuntu/Debian VPS (or any Linux distribution)
- Python 3.9 or higher
- FFmpeg
- rclone

### Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install FFmpeg
sudo apt install ffmpeg -y

# Install rclone
curl https://rclone.org/install.sh | sudo bash
```

## Setup Guide

### 1. Get Your Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the prompts to name your bot
4. Copy the bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Telegram User ID

1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Start the bot and it will show your User ID
3. Copy your numeric User ID (e.g., `123456789`)

### 3. Configure rclone for Google Drive

```bash
# Start rclone configuration
rclone config

# Follow these steps:
# 1. Type 'n' for new remote
# 2. Name it 'gdrive' (or any name you prefer)
# 3. Choose 'Google Drive' from the list (usually number 15 or 18)
# 4. Leave client_id and client_secret blank (press Enter)
# 5. Choose full access scope (usually option 1)
# 6. Leave root_folder_id blank
# 7. Leave service_account_file blank
# 8. Choose 'n' for advanced config
# 9. Choose 'y' for auto config if on a machine with browser
#    Or use remote auth if on headless server
# 10. Choose 'n' for team drive (unless you need it)
# 11. Confirm with 'y'
```

For headless servers (VPS without GUI):
```bash
# On your local machine with a browser
rclone authorize "drive"

# Copy the resulting token and paste it on your VPS when prompted
```

Test your rclone configuration:
```bash
rclone lsd gdrive:
```

### 4. Install the Bot

```bash
# Clone the repository
git clone https://github.com/VINCENTIUSALBERTO/youtube-downloader.git
cd youtube-downloader

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file or export environment variables:

```bash
# Required
export BOT_TOKEN="your_telegram_bot_token"
export ALLOWED_USER_IDS="123456789,987654321"  # Comma-separated user IDs

# Optional
export RCLONE_REMOTE="gdrive:YouTube_Downloads"  # Default: gdrive:YouTube_Downloads
export DOWNLOAD_DIR="/tmp/youtube_downloads"      # Default: /tmp/youtube_downloads
export COOKIES_FILE="/path/to/cookies.txt"        # For age-restricted content
```

### 6. Run the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python main.py
```

## Running as a System Service

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/youtube-bot.service
```

Add the following content:

```ini
[Unit]
Description=YouTube Downloader Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/youtube-downloader
Environment="BOT_TOKEN=your_token_here"
Environment="ALLOWED_USER_IDS=123456789"
Environment="RCLONE_REMOTE=gdrive:YouTube_Downloads"
ExecStart=/path/to/youtube-downloader/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable youtube-bot
sudo systemctl start youtube-bot

# Check status
sudo systemctl status youtube-bot

# View logs
journalctl -u youtube-bot -f
```

## Usage

1. Start a chat with your bot on Telegram
2. Send a video URL (YouTube, Twitter, TikTok, etc.)
3. Select your preferred format from the inline keyboard
4. Wait for the bot to download and upload to Google Drive
5. Done! ✅

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from BotFather | Required |
| `ALLOWED_USER_IDS` | Comma-separated list of authorized user IDs | Required |
| `RCLONE_REMOTE` | rclone remote destination | `gdrive:YouTube_Downloads` |
| `DOWNLOAD_DIR` | Temporary download directory | `/tmp/youtube_downloads` |
| `COOKIES_FILE` | Path to cookies.txt for age-restricted content | None |

## Cookies Setup (Optional)

For age-restricted or login-required content:

1. Install a browser extension to export cookies (e.g., "Get cookies.txt")
2. Log in to YouTube in your browser
3. Export cookies to `cookies.txt`
4. Place the file on your VPS
5. Set `COOKIES_FILE` environment variable to the file path

## Troubleshooting

### Bot doesn't respond
- Verify `BOT_TOKEN` is correct
- Check if your User ID is in `ALLOWED_USER_IDS`
- Check logs: `journalctl -u youtube-bot -f`

### Download fails
- Make sure `yt-dlp` is up to date: `pip install -U yt-dlp`
- Check if the video is available in your region
- For age-restricted content, configure cookies.txt

### Upload fails
- Verify rclone configuration: `rclone lsd gdrive:`
- Check if you have enough Google Drive storage
- Ensure the remote name matches `RCLONE_REMOTE`

## License

MIT License
