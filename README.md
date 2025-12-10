# 🌐 IoT Project - ESP32 MQTT (UTS Pemrograman IoT)

Halo semuaa 👋  
Perkenalkan, saya **Achmad Bimo Rahadian (NRP: 152023029)**.  
Project ini saya kerjakan dalam rangka **UTS Mata Kuliah Pemrograman IoT**.

Project ini menghubungkan **ESP32** dengan **backend Python (Flask)** menggunakan protokol **MQTT**, serta menampilkan data sensor ke halaman web sederhana.


---

## 🧠 Deskripsi Singkat

### 🛰️ ESP32
- Mengambil data dari sensor **DHT11/DHT22** (suhu & kelembapan) dan sensor cahaya (**LDR**).
- Mengirimkan data secara periodik ke **broker MQTT (`broker.hivemq.com`)**.

### ⚙️ Backend (Python)
- Menggunakan **Flask** untuk membuat REST API.  
- File `mqtt.py` berfungsi untuk **subscribe** dari broker MQTT dan menyimpan data ke database MySQL.

### 💻 Frontend (Web)
- File `index.html` menampilkan data sensor terbaru menggunakan **AJAX/fetch API** dari Flask backend.

---

## 🗄️ Struktur Database

Database: `iot_db`  
Tabel: `data_sensor`

```sql
CREATE DATABASE IF NOT EXISTS `iot_db`;
USE `iot_db`;

CREATE TABLE IF NOT EXISTS `data_sensor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `suhu` float DEFAULT NULL,
  `humidity` float DEFAULT NULL,
  `lux` int DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
);
