Role: Bertindaklah sebagai Senior Python Developer & DevOps Engineer.

Objective: Saya ingin membuat Telegram Bot yang berjalan di VPS Ubuntu untuk mendownload media dari YouTube (dan situs lain) menggunakan yt-dlp, lalu mengunggahnya secara otomatis ke Google Drive menggunakan rclone.

Tech Stack:

Language: Python 3.9+

Libraries: python-telegram-bot (versi terbaru/async), yt-dlp (via wrapper/subprocess).

External Tools: FFmpeg (installed on OS), rclone (installed on OS).

Detailed Feature Requirements:

1. User Interface (Telegram Bot):

Authentication: Bot HANYA boleh merespons pesan dari USER_ID tertentu (Whitelist). Abaikan user lain demi keamanan VPS.

Workflow:

User mengirim Link.

Bot mengecek link.

Bot menampilkan Inline Keyboard Buttons (Menu Pilihan):

MP3 (Audio Only)

Video 360p

Video 720p

Video 1080p

Best Quality (2K/4K)

User menekan tombol, bot mengedit pesan menjadi "Processing...".

2. Core Engine (yt-dlp):

Script harus bisa menerjemahkan pilihan tombol di atas menjadi argumen yt-dlp yang tepat.

Contoh logic resolusi: Jika user memilih 720p, gunakan format sorting bestvideo[height<=720]+bestaudio/best[height<=720].

Wajib menggunakan Cookies (opsional file cookies.txt) untuk mengantisipasi age-restricted content.

Filename harus disanitasi (dibersihkan) agar kompatibel dengan sistem file Linux.

3. Cloud Integration (Rclone):

Setelah download selesai di VPS, script harus memanggil perintah rclone copy atau rclone move.

Target remote: gdrive:YouTube_Downloads (Biarkan nama remote ini bisa dikonfigurasi di variabel).

Cleanup: Setelah sukses di-upload ke drive, file asli di VPS wajib dihapus otomatis untuk menghemat storage.

4. Feedback & Logging:

Bot harus memberikan notifikasi real-time: "Downloading...", "Uploading to Drive...", dan "Done! ✅".

Jika terjadi error, kirim pesan error yang terbaca manusia (bukan raw stack trace) ke chat Telegram.

Deliverables:

Satu file main.py yang bersih dan modular.

File requirements.txt.

Panduan singkat cara setup rclone dan cara mendapatkan BOT_TOKEN.
