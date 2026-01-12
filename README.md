# YouTube Downloader Telegram Bot

Bot Telegram untuk mengunduh video dan musik dari YouTube dengan sistem token berbayar. Siap untuk penggunaan komersial.

## Fitur Utama

- 🎵 **YouTube Musik** - Download audio MP3 (192kbps)
- 🎬 **YouTube Video** - Download video (360p, 720p, 1080p, Best Quality)
- 📋 **YouTube Playlist** - Download seluruh playlist sekaligus
- 💰 **Sistem Token** - 1 Token = 1 Video/Musik (siap komersial)
- 👑 **Panel Admin** - Kelola user, token, dan statistik
- 📲 **Pengiriman Fleksibel** - Via Telegram (maks 50MB) atau Google Drive (unlimited)
- 🔗 **Link Google Drive** - Dapatkan link langsung setelah upload
- 📊 **Preview Video** - Lihat detail video sebelum download
- 🧹 **Auto Cleanup** - File dihapus otomatis setelah upload
- 🍪 **Cookie Support** - Untuk konten yang memerlukan login

## Menu Bot

```
1. 🎵 YouTube Musik - Download audio MP3
2. 🎬 YouTube Video - Download video (pilih kualitas)
3. 📋 YouTube Playlist - Download playlist lengkap
```

## Sistem Token

- 1 Token = 1 Video/Musik
- Playlist dihitung per video
- Beli token via admin
- Harga token dapat dikonfigurasi

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

Copy `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
nano .env
```

Konfigurasi wajib:
```bash
# Telegram Bot Token (dari BotFather)
BOT_TOKEN=your_telegram_bot_token

# Admin User IDs (comma-separated)
ADMIN_USER_IDS=123456789

# Admin Contact
ADMIN_CONTACT=@your_telegram_username
```

Konfigurasi opsional:
```bash
# Google Drive remote
RCLONE_REMOTE=gdrive:YouTube_Downloads

# Download directory
DOWNLOAD_DIR=/tmp/youtube_downloads

# Cookies untuk konten terproteksi
COOKIES_FILE=/path/to/cookies.txt

# WhatsApp admin (opsional)
ADMIN_WHATSAPP=+6281234567890

# Harga token (dalam Rupiah)
TOKEN_PRICE_1=5000
TOKEN_PRICE_5=20000
TOKEN_PRICE_10=35000
TOKEN_PRICE_25=75000
```

### 6. Run the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python run.py
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
EnvironmentFile=/path/to/youtube-downloader/.env
ExecStart=/path/to/youtube-downloader/venv/bin/python run.py
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

## Penggunaan

1. Mulai chat dengan bot di Telegram
2. Pilih jenis download (Musik/Video/Playlist)
3. Kirim link YouTube
4. Lihat preview dan konfirmasi
5. Pilih kualitas
6. Pilih metode pengiriman (Telegram/Drive)
7. Tunggu proses selesai ✅

## Perintah Bot

### User Commands
| Perintah | Deskripsi |
|----------|-----------|
| `/start` | Mulai bot dan lihat menu |
| `/help` | Tampilkan bantuan |
| `/token` | Cek saldo token |
| `/history` | Lihat riwayat download |
| `/buy` | Beli token |

### Admin Commands
| Perintah | Deskripsi |
|----------|-----------|
| `/admin` | Panel admin |
| `/addtoken <user_id> <jumlah>` | Tambah token ke user |
| `/stats` | Statistik detail |
| `/broadcast <pesan>` | Broadcast ke semua user |
| `/ban <user_id>` | Ban user |
| `/unban <user_id>` | Unban user |
| `/users` | Daftar semua user |

## Konfigurasi

| Environment Variable | Deskripsi | Default |
|---------------------|-----------|---------|
| `BOT_TOKEN` | Token bot Telegram | Required |
| `ADMIN_USER_IDS` | User ID admin (comma-separated) | Required |
| `ADMIN_CONTACT` | Username Telegram admin | Required |
| `RCLONE_REMOTE` | rclone remote destination | `gdrive:YouTube_Downloads` |
| `DOWNLOAD_DIR` | Direktori download sementara | `/tmp/youtube_downloads` |
| `COOKIES_FILE` | Path ke cookies.txt | None |
| `TOKEN_PRICE_*` | Harga paket token | See .env.example |

## Cookies Setup (Optional)

For age-restricted or login-required content:

1. Install a browser extension to export cookies (e.g., "Get cookies.txt")
2. Log in to YouTube in your browser
3. Export cookies to `cookies.txt`
4. Place the file on your VPS
5. Set `COOKIES_FILE` environment variable to the file path

## Troubleshooting

### Bot tidak merespon
- Verifikasi `BOT_TOKEN` sudah benar
- Pastikan User ID ada di `ADMIN_USER_IDS` jika ingin akses admin
- Cek logs: `journalctl -u youtube-bot -f`

### Download gagal
- Update yt-dlp: `pip install -U yt-dlp`
- Pastikan video tersedia di region Anda
- Untuk konten age-restricted, konfigurasi cookies.txt

### Upload gagal
- Verifikasi konfigurasi rclone: `rclone lsd gdrive:`
- Pastikan storage Google Drive cukup
- Pastikan nama remote sesuai `RCLONE_REMOTE`

### Token tidak terpotong
- Pastikan user memiliki saldo token cukup
- Admin tidak dipotong tokennya

## Struktur Folder

```
youtube-downloader/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Bot initialization
│   ├── config.py        # Configuration
│   ├── database.py      # SQLite database
│   ├── handlers/        # Command & callback handlers
│   │   ├── start.py
│   │   ├── admin.py
│   │   ├── download.py
│   │   └── callback.py
│   ├── services/        # Business logic
│   │   ├── downloader.py
│   │   ├── uploader.py
│   │   └── token_manager.py
│   ├── utils/           # Helper functions
│   │   ├── validators.py
│   │   ├── helpers.py
│   │   └── keyboards.py
│   └── models/          # Data models
│       └── user.py
├── data/               # Database storage
├── .env.example        # Environment template
├── requirements.txt
└── run.py              # Entry point
```

## License

MIT License
