# YouTube Downloader Telegram Bot - Commercial Edition

Bot Telegram untuk mendownload media dari YouTube dengan sistem token berbayar. Mendukung pengiriman via Telegram atau Google Drive.

## ✨ Fitur

- 🎫 **Sistem Token**: 1 token = 1 download (dapat dijual)
- 🔧 **Admin Panel**: Kelola user dan token
- 🎵 **YouTube Music**: Download audio MP3
- 📹 **YouTube Video**: Download video single (1080p)
- 📋 **YouTube Playlist**: Download semua video playlist (720p)
- ✅ **Konfirmasi Judul**: Cek judul sebelum download
- 📱 **Kirim via Telegram**: File langsung dikirim ke chat
- ☁️ **Upload ke Drive**: File diupload, link diberikan
- 🍪 **Cookie Support**: Untuk konten age-restricted

## 🛠 Persyaratan

### Sistem
- Ubuntu/Debian VPS
- Python 3.9+
- FFmpeg
- rclone

### Instalasi Dependencies

```bash
# Update sistem
sudo apt update

# Install Python
sudo apt install python3 python3-pip python3-venv -y

# Install FFmpeg
sudo apt install ffmpeg -y

# Install rclone
curl https://rclone.org/install.sh | sudo bash
```

## 📋 Panduan Setup

### 1. Dapatkan Bot Token

1. Buka Telegram, cari [@BotFather](https://t.me/BotFather)
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Copy token (contoh: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Dapatkan User ID Anda (untuk Admin)

1. Buka Telegram, cari [@userinfobot](https://t.me/userinfobot)
2. Start bot, akan ditampilkan User ID Anda
3. Copy User ID (contoh: `123456789`)

### 3. Konfigurasi rclone untuk Google Drive

```bash
rclone config

# Ikuti langkah berikut:
# 1. Ketik 'n' untuk remote baru
# 2. Beri nama 'gdrive'
# 3. Pilih 'Google Drive'
# 4. Kosongkan client_id dan client_secret (tekan Enter)
# 5. Pilih full access scope
# 6. Ikuti proses autentikasi
# 7. Konfirmasi dengan 'y'
```

Test konfigurasi:
```bash
rclone lsd gdrive:
```

### 4. Install Bot

```bash
# Clone repository
git clone https://github.com/VINCENTIUSALBERTO/youtube-downloader.git
cd youtube-downloader

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Konfigurasi Environment Variables

```bash
# Wajib
export BOT_TOKEN="your_telegram_bot_token"
export ADMIN_USER_IDS="123456789"  # User ID admin (comma-separated)

# Opsional
export RCLONE_REMOTE="gdrive:YouTube_Downloads"
export DOWNLOAD_DIR="/tmp/youtube_downloads"
export COOKIES_FILE="/path/to/cookies.txt"
export DATA_FILE="bot_data.json"
export ADMIN_CONTACT="@your_username"
export TOKEN_PRICE="Rp 5.000 / token"
```

### 6. Jalankan Bot

```bash
source venv/bin/activate
python main.py
```

## 🖥 Menjalankan sebagai Service

```bash
sudo nano /etc/systemd/system/youtube-bot.service
```

```ini
[Unit]
Description=YouTube Downloader Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/youtube-downloader
Environment="BOT_TOKEN=your_token"
Environment="ADMIN_USER_IDS=123456789"
Environment="ADMIN_CONTACT=@your_username"
Environment="TOKEN_PRICE=Rp 5.000 / token"
ExecStart=/path/to/youtube-downloader/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable youtube-bot
sudo systemctl start youtube-bot
```

## 📱 Cara Penggunaan

### Untuk User

1. Start chat dengan bot
2. Kirim link YouTube
3. Pilih tipe download (Music/Video/Playlist)
4. Konfirmasi judul
5. Pilih pengiriman (Telegram/Drive)
6. Selesai! (1 download = 1 token)

### Commands User
- `/start` - Mulai bot
- `/tokens` - Cek sisa token
- `/buy` - Info beli token
- `/help` - Bantuan

### Commands Admin
- `/admin` - Panel admin
- `/addtoken <user_id> <amount>` - Tambah token user
- `/checkuser <user_id>` - Cek info user
- `/users` - Lihat semua user

## ⚙️ Konfigurasi

| Variable | Deskripsi | Default |
|----------|-----------|---------|
| `BOT_TOKEN` | Token bot Telegram | Wajib |
| `ADMIN_USER_IDS` | ID admin (comma-separated) | Wajib |
| `RCLONE_REMOTE` | Remote rclone | `gdrive:YouTube_Downloads` |
| `DOWNLOAD_DIR` | Folder download temp | `/tmp/youtube_downloads` |
| `COOKIES_FILE` | File cookies.txt | None |
| `DATA_FILE` | File database JSON | `bot_data.json` |
| `ADMIN_CONTACT` | Kontak admin | `@admin` |
| `TOKEN_PRICE` | Harga token | `Rp 5.000 / token` |

## 💰 Model Bisnis

- Setiap download membutuhkan 1 token
- Playlist dihitung per video
- Admin menentukan harga token
- Token ditambahkan manual oleh admin setelah pembayaran
- Admin mendapat akses gratis (unlimited)

## 🔧 Troubleshooting

### Bot tidak merespon
- Cek `BOT_TOKEN` sudah benar
- Cek logs: `journalctl -u youtube-bot -f`

### Download gagal
- Update yt-dlp: `pip install -U yt-dlp`
- Cek video tersedia di region Anda
- Untuk age-restricted: konfigurasi cookies.txt

### Upload gagal
- Cek konfigurasi rclone: `rclone lsd gdrive:`
- Cek storage Google Drive

## 📝 Data Storage

Bot menyimpan data di file JSON (`bot_data.json`):
- Saldo token user
- Username user
- History download

## 📄 License

MIT License
