# 🎭 Parodiya Tabrik & Mashhurlar Qutlovi Telegram Boti

Ushbu loyiha Python (aiogram 3.x) asosida yaratilgan, O'zbekiston sharoitiga moslangan interaktiv parodiya tabrik boti.
Loyihaning asosiy maqsadi: **0 so'm pul sarflab**, noutbuk o'chiq bo'lsa ham bepul bulutli serverlarda **24/7 to'xtovsiz, crash-proof va kam RAM (25-35 MB)** bilan ishlash.

---

## ✨ Asosiy Xususiyatlar:
- **🎭 5 xil noyob xarakter:** Saxiy Boyvachcha Otaxon, GAI/Tergovchi, Malika/O'rikzor Savdogari, Shoir & Donishmand, Xorijdagi Shef.
- **👑 Maxfiy Admin Panel (ID: 6268220201):** Faqat belgilangan admin ko'ra oladigan to'liq boshqaruv paneli.
- **📜 Jonli Harakatlar Monitoringi (Activity Logs):** Kim qachon kirdi, nima qildi va qanday tabrik yaratdi — barchasi real vaqtda qayd etiladi.
- **📢 Ommaviy Xabarnoma (Rassilka):** Barcha foydalanuvchilarga matn/rasm/post yuborish va hisobotini olish.
- **📥 Baza Eksport:** Foydalanuvchilar ro'yxati (CSV) va SQLite ma'lumotlar bazasini to'g'ridan-to'g'ri Telegram orqali yuklab olish.
- **⚡ Keep-Alive aiohttp server:** Render.com va Koyeb uchun yagona asyncio siklida ishlaydigan veb-server (Zero extra RAM).
- **🛡️ Crash-Proof Watchdog:** Telegram API yoki tarmoq uzilsa ham avtomatik qayta ulanadi, dastur yiqilmaydi.
- **💤 Anti-Sleep mexanikasi:** UptimeRobot har 5 daqiqada `/health` manziliga so'rov yuborib, serverni doim uyg'oq tutadi.

---

## 📁 Loyiha Strukturasi:
```
telegrambot2/
├── main.py              # Asosiy bot, admin panel, keep-alive server va watchdog sikli
├── database.py          # SQLite ma'lumotlar bazasi, jonli monitoring va statistika
├── config.py            # Sozlamalar, admin ID va muhit o'zgaruvchilari
├── characters.py        # Personajlar lug'ati va tabrik generatori
├── requirements.txt     # Eng yengil kutubxonalar (aiogram, aiohttp, python-dotenv)
├── Dockerfile           # python:3.11-slim asosidagi yengil konteyner
├── .dockerignore        # Ortiqcha fayllarni chetlab o'tish
├── .env.example         # Muhit o'zgaruvchilari namunasi
├── .env                 # Lokal sozlamalar
├── .gitignore           # Git himoyasi
├── DEPLOY_GUIDE.md      # Render.com + UptimeRobot da 5 daqiqada 24/7 bepul ishga tushirish
└── README.md            # Loyiha tavsifi
```

---

## 💻 Lokal Sinovdan O'tkazish:

1. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
2. `.env` fayliga o'zingizning `@BotFather` dan olgan `BOT_TOKEN`ingizni qo'ying.
3. Botni ishga tushiring:
   ```bash
   python main.py
   ```
4. Brauzerda tekshirib ko'ring:
   - Asosiy sahifa: `http://localhost:8080/`
   - Health check: `http://localhost:8080/health`

---

## 🚀 24/7 Bepul Bulutga Deploy Qilish:
To'liq bosqichma-bosqich yo'riqnoma uchun [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) faylini o'qing!
