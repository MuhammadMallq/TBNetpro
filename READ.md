# 🚀 PyRTC: Aplikasi Chat Multi-Client Premium

PyRTC adalah aplikasi chat real-time yang dibangun menggunakan bahasa pemrograman Python dengan protokol TCP (Transmission Control Protocol)**. Aplikasi ini mengadopsi arsitektur Client-Server yang tangguh, di mana server mampu menangani banyak koneksi client secara bersamaan melalui teknologi Multithreading.

Dengan antarmuka pengguna (GUI) yang modern dan responsif menggunakan pustaka `tkinter`, PyRTC menawarkan pengalaman chatting yang kaya fitur, setara dengan aplikasi pesan instan modern saat ini.

---

## ✨ Fitur Unggulan

### 1. ⌨️ Real-time Typing Indicator
Mengetahui saat teman bicara Anda sedang mengetik. Status "Username is typing..." akan muncul secara instan saat ada input di kolom chat.

### 3. 🌓 Dynamic Theme Switcher (Dark/Light Mode)
Ubah tampilan aplikasi dalam satu klik. Pilih antara **Premium Dark Mode** untuk kenyamanan mata di malam hari atau **Clean Light Mode** yang cerah dan minimalis.

### 4. ✓✓ Smart Read Receipts (Message Status)
Lacak status pesan Anda:
- **✓ Sent**: Pesan telah dikirim ke server.
- **✓✓ Delivered**: Pesan telah diterima oleh sistem.
- **✓✓ Read (Blue)**: Pesan telah dilihat/dibaca oleh pengguna lain.

### 5. � File & Image Sharing
Kirim file dan gambar secara langsung melalui chat. Aplikasi mendukung preview gambar inline dan sistem download untuk file dokumen atau lainnya.

### 6. 🏘️ Multi-Room Support
Buat room chat baru atau masuk ke room yang sudah ada (misal: General, Gaming, Study). Setiap room memiliki history pesan dan daftar pengguna yang terpisah.

### 7. � Real-time User List & Avatars
Daftar pengguna online yang selalu terupdate sesuai room mereka, lengkap dengan inisial avatar berwarna unik untuk setiap pengguna.

### 8. 🔊 Sound Notifications
Notifikasi suara yang halus saat ada pesan masuk, memastikan Anda tidak melewatkan percakapan penting.

---

## 🛠️ Detail Teknis

- **Pustaka Core**: `socket` (Jaringan), `threading` (Multitasking), `base64` (File Encoding).
- **Antarmuka**: `tkinter` dengan custom styling untuk estetika premium.
- **Data Handling**: Menggunakan format metadata kustom untuk menangani protocol (typing, reactions, file transfers, room management).
- **Log Sistem**: Mencatat seluruh aktivitas chat ke dalam file log secara otomatis di folder `logs/`.

---

## 🚀 Cara Menjalankan

1. **Jalankan Server**:
   ```bash
   python server/server.py
   ```

2. **Jalankan Client**:
   ```bash
   python client/client.py
   ```

## 📋 Persyaratan Sistem
- Python 3.7 ke atas.
- Jaringan LAN / WiFi (jika dijalankan di beberapa perangkat terpisah).
- Resolusi layar minimal 800x600.
