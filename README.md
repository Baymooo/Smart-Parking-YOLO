# 🚗 Smart Parking System (YOLO + AI Detection)

Project ini adalah aplikasi Smart Parking berbasis Computer Vision menggunakan YOLOv8 untuk mendeteksi plat nomor, kendaraan, dan status slot parkir secara otomatis.
Aplikasi ini bisa membantu sistem parkir modern dalam proses vehicle monitoring dan occupancy tracking secara real-time.

👥 Anggota Kelompok E7
152023029 - Achmad Bimo Rahadian
152023071 - Chandra Kirana Irawan
152023178 - Mesa Melinda
152023181 - Syifa Luthfiyah
152023216 - Tio Natanael Zagoto

---

## 🧠 Deskripsi Singkat
Fitur Utama

🔍 Deteksi plat nomor menggunakan YOLOv8
🚗 Deteksi kendaraan (motor & mobil)
🅿️ Perhitungan slot parkir otomatis (occupied / empty)
📊 Output ditampilkan dalam UI Streamlit
🎥 Bisa dijalankan dari video atau kamera
---
📥 1. Clone/Download Project
Kalian bisa download project ini melalui tombol Code → Download ZIP atau clone pakai Git:
git clone https://github.com/Baymooo/Smart-Parking-YOLO.git

Masuk ke folder project:
cd Smart-Parking-YOLO

---

## 🧩 Buat Virtual Environment (Wajib)

Buka terminal di folder project, lalu jalankan:

Untuk Windows
python -m venv venv
.\venv\Scripts\activate

---

## 📦 Install Dependencies

Semua library sudah dirangkum di requirements.txt.
Jalankan:
pip install -r requirements.txt

---

## 📊 Download Model YOLO (Wajib)

Karena file YOLO besar, model tidak disimpan di GitHub.
Silakan download model di sini:

🔗 YOLO Plate Model:
https://universe.roboflow.com/christine-ndtou/license-plate-detection-yolov8/dataset/1

🔗 YOLO Vehicle Model:
https://universe.roboflow.com/…
 (isi sesuai dataset mobil kalian)

Setelah download, simpan file .pt ke folder:

models/

---

## ▶️ Cara Menjalankan Aplikasi

Setelah semua siap, jalankan UI aplikasi:
streamlit run ui/app.py

Aplikasi otomatis terbuka di browser.
