# TincHost - Statik saytlarni bir zumda joylashtirish platformasi


<img src="tinchost.jpg">



TincHost - bu HTML, CSS va JavaScript loyihalaringizni bir necha soniyada internetga chiqarish uchun yaratilgan oddiy va tezkor platforma. Faylni yuklang, havola oling va saytingiz tayyor!

## 🎯 Nima uchun TincHost?

- **Tezkor**: Faylni yuklang, 5 ta harf bilan subdomen oling
- **Oddiy**: Hech qanday murakkab sozlamalar yo'q
- **Bepul**: To'liq ochiq kodli va bepul
- **Xavfsiz**: Fayllar tekshiriladi va xavfsiz joylanadi
- **Homeserver**: O'z serveringizda ishlaydigan mustaqil tizim

## 🏗️ Tizim Arxitekturasi

```
Internet
    ↓
Cloudflare Tunnel (tinchost.uz)
    ↓
Nginx (Port 80)
    ├── tinchost.uz → FastAPI (Port 8000)
    └── *.tinchost.uz → Static Files (/var/www/sites/)
    ↓
FastAPI Backend
    ├── File Upload & Validation
    ├── User Management
    ├── Subdomain Generation
    └── Admin Panel
    ↓
SQLite Database
```

## 🔄 Fayl Yuklash Jarayoni

```
1. User ZIP fayl yuklaydi
   ↓
2. Fayl turi tekshiriladi (.zip)
   ↓
3. Fayl hajmi tekshiriladi (max 100MB)
   ↓
4. ZIP ichidagi fayllar tekshiriladi
   ↓
5. 5 harfli tasodifiy subdomen yaratiladi (masalan: "abcde")
   ↓
6. Fayllar /var/www/sites/abcde/ ga chiqariladi
   ↓
7. Nginx orqali abcde.tinchost.uz da xizmat qiladi
   ↓
8. User havolani oladi: https://abcde.tinchost.uz
```

## 🌐 Tunnel va Networking

### Nima uchun Tunnel kerak?

**Statik IP muammosi:**
- Uy internetida IP manzil doimo o'zgaradi
- Router orqali port forwarding murakkab
- ISP ba'zan 80/443 portlarni bloklaydi

**Cloudflare Tunnel yechimi:**
- Serverdan Cloudflare'ga ulanish (outbound)
- Hech qanday port ochish shart emas
- Avtomatik SSL sertifikat
- DDoS himoyasi

### Qanday ishlaydi?

```
[Homeserver] --tunnel--> [Cloudflare] <--internet-- [Foydalanuvchilar]
     ↑                        ↓
  cloudflared              tinchost.uz
```

1. **Cloudflared** serveri Cloudflare'ga ulanadi
2. **Cloudflare** tinchost.uz domenini tunnel'ga yo'naltiradi  
3. **Foydalanuvchilar** tinchost.uz ga kirganda Cloudflare so'rovni tunnel orqali serverga yuboradi

## 🔧 O'rnatish va Sozlash

### 1. Tizim Talablari

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip nginx sqlite3 curl
```

### 2. Loyihani Klonlash

```bash
git clone https://github.com/username/tinchost.git
cd tinchost
```

### 3. Python Muhitini Sozlash

```bash
# Virtual environment yaratish
python3 -m venv venv
source venv/bin/activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 4. Konfiguratsiya

`.env` fayl yarating:

```env
SECRET_KEY=your-very-secret-key-here
DEBUG=False
BASE_DOMAIN=tinchost.uz
SITES_FOLDER=/var/www/sites
MAX_FILE_SIZE=104857600
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
```

### 5. Ma'lumotlar Bazasini Sozlash

```bash
python3 -c "from database import db; db.init_database()"
```

### 6. Nginx Sozlash

```bash
# Konfiguratsiyani nusxalash
sudo cp nginx_tinchost.conf /etc/nginx/sites-available/tinchost
sudo ln -s /etc/nginx/sites-available/tinchost /etc/nginx/sites-enabled/

# Saytlar papkasini yaratish
sudo mkdir -p /var/www/sites
sudo chown -R $USER:www-data /var/www/sites
sudo chmod -R 775 /var/www/sites

# Nginx'ni qayta ishga tushirish
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Cloudflare Tunnel Sozlash



```bash
# Cloudflared o'rnatish(Ubuntu)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Cloudflare'ga login
cloudflared tunnel login

# Tunnel yaratish
cloudflared tunnel create tinchost

# DNS sozlash
cloudflared tunnel route dns tinchost tinchost.uz
cloudflared tunnel route dns tinchost "*.tinchost.uz"

# Konfiguratsiyani nusxalash
sudo cp cloudflared.yml /etc/cloudflared/config.yml

# Service sifatida ishga tushirish
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### 8. TincHost Service Sozlash

```bash
# Systemd service yaratish
sudo cp systemd/tinchost.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tinchost
sudo systemctl start tinchost
```

## 🚀 Ishlatish

### Fayl Yuklash

1. **Saytga kiring**: https://tinchost.uz
2. **ZIP fayl tayyorlang**: HTML, CSS, JS fayllaringizni ZIP ga siqing
3. **Yuklang**: "Choose File" tugmasini bosing va ZIP faylni tanlang
4. **Natija**: 5 harfli subdomen bilan havola oling (masalan: https://abcde.tinchost.uz)

### Qabul qilinadigan fayllar

- **HTML**: .html, .htm
- **CSS**: .css
- **JavaScript**: .js
- **Rasmlar**: .png, .jpg, .jpeg, .gif, .svg, .webp
- **Shriftlar**: .woff, .woff2, .ttf, .eot
- **Boshqalar**: .json, .xml, .txt, .md

### Cheklovlar

- **Maksimal hajm**: 100MB
- **Fayl turi**: Faqat ZIP
- **Subdomen**: 5 harfli tasodifiy nom
- **Vaqt**: Cheksiz (admin tomonidan o'chirilmaguncha)

## 👨‍💼 Admin Panel

Admin panel orqali tizimni boshqarish mumkin:

- **URL**: https://tinchost.uz/admin
- **Login**: `.env` faylidagi `ADMIN_USERNAME` va `ADMIN_PASSWORD`

### Admin imkoniyatlari:

- Tizim statistikalarini ko'rish
- Barcha foydalanuvchilarni boshqarish
- Subdomenlarni o'chirish
- Server resurslarini monitoring qilish
- Loglarni ko'rish

## 🔒 Xavfsizlik

### Fayl Tekshiruvi

```python
# Ruxsat etilgan fayl turlari
ALLOWED_EXTENSIONS = {
    '.html', '.htm', '.css', '.js', '.json', '.xml', '.txt', '.md',
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
    '.woff', '.woff2', '.ttf', '.eot', '.otf'
}

# Taqiqlangan fayllar
DANGEROUS_EXTENSIONS = {
    '.php', '.py', '.sh', '.exe', '.bat', '.cmd', '.scr'
}
```

### Nginx Xavfsizlik

- Maxfiy fayllarni bloklash (.htaccess, .env, .git)
- Executable fayllarni rad etish
- CORS sozlamalari
- XSS himoyasi

## 📊 Monitoring va Backup

### Loglar

```bash
# TincHost loglari
sudo journalctl -u tinchost -f

# Nginx loglari
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Cloudflared loglari
sudo journalctl -u cloudflared -f
```


## 🛠️ Development

### Lokal ishga tushirish

```bash
# Development server
python3 app.py

# Yoki uvicorn bilan
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Testlash

```bash
# Fayl yuklash testi
curl -X POST -F "file=@test.zip" http://localhost:8000/upload/

# Health check
curl http://localhost:8000/health
```

## 🤝 Hissa Qo'shish

1. Fork qiling
2. Feature branch yarating (`git checkout -b feature/yangi-funksiya`)
3. O'zgarishlarni commit qiling (`git commit -am 'Yangi funksiya qo'shildi'`)
4. Branch'ni push qiling (`git push origin feature/yangi-funksiya`)
5. Pull Request yarating
