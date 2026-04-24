# UTS-Pub-Sub-Aggregator
Layanan agregasi log berbasis Publish-Subscribe dengan idempotent consumer dan deduplication menggunakan SQLite. Dibangun dengan Python 3.11 + FastAPI dan dijalankan melalui Docker.
# Link Laporan 
https://docs.google.com/document/d/1ILLrJRQ_ekJYNrJ0hG0I5Wen_hHPVlWnWS5CsGScRjc/edit?tab=t.0
# Link Video
https://youtu.be/z_RaTJrNseA
## Cara Menjalankan
 
### 1. Clone repository
 
```bash
git clone https://github.com/LuthfanThamrin/UTS-Pub-Sub-Aggregator.git
cd UTS-Pub-Sub-Aggregator
```
 
### 2. Build Docker image
 
```bash
docker build -t uts-aggregator .
```
 
### 3. Buat volume persisten
 
```bash
docker volume create aggdata
```
 
### 4. Jalankan container
 
```bash
docker run -p 8080:8080 -v aggdata:/app/data --name aggregator uts-aggregator
```
 
Tunggu hingga muncul:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
```
 
Buka browser ke **http://localhost:8080/docs** untuk melihat Swagger UI.
 
### 5. Jalankan unit tests
 
```bash
pip install -r requirements.txt
pytest tests/ -v
```
 
### 6. Jalankan simulator publisher (stress test 5.000 event)
 
```bash
python publisher.py
```
 
---
 
## Docker Compose (Bonus)
 
Menjalankan aggregator dan publisher sebagai dua service terpisah secara otomatis.
 
```bash
docker compose up --build
```
 
---
 
## Referensi
 
Tanenbaum, A. S., & Van Steen, M. (2007). *Distributed systems: Principles and paradigms* (2nd ed.). Pearson Prentice Hall.
