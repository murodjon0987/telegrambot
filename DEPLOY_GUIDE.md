# 🚀 24/7 Bepul Bulutli Xostingga Deploy Qilish Qo'llanmasi (0 So'm)

Ushbu qo'llanma orqali siz botingizni **Render.com** bepul bulutli serveriga 5 daqiqada yuklab, **UptimeRobot** yordamida **24/7/365 to'xtovsiz, noutbukingiz o'chiq bo'lsa ham** ishlaydigan qilib sozlashingiz mumkin.

---

## 📋 1-QADAM: Bot Tokenini Olish (1 daqiqa)
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug'ini yuboring.
3. Botingizga nom va unikal username tanlang (masalan: `ParodiyaTabrik_bot`).
4. BotFather sizga **HTTP API Token** beradi (masalan: `7123456789:AAH...`). Shu tokenni nusxalab oling.

---

## 🐙 2-QADAM: Kodni GitHub ga Yuklash (1.5 daqiqa)
Agar GitHub da hisobingiz bo'lmasa, [github.com](https://github.com) da 30 soniyada bepul ro'yxatdan o'ting.

Kompuyteringizdagi ushbu loyiha papkasida terminalni ochib, quyidagi buyruqlarni ketma-ket tering:
```bash
git init
git add .
git commit -m "Initial commit: 24/7 Parody Telegram Bot"
git branch -M main
```
GitHub saytida yangi bo'sh repository (masalan: `parody-telegram-bot`) oching va unga ulang:
```bash
git remote add origin https://github.com/SIZNING_USERNAME/parody-telegram-bot.git
git push -u origin main
```
*(Eslatma: `.gitignore` tufayli sizning maxfiy `.env` faylingiz GitHub ga chiqmaydi, bu to'g'ri va xavfsiz!)*

---

## ☁️ 3-QADAM: Render.com da Bepul Serverni Ishga Tushirish (2 daqiqa)
1. [Render.com](https://render.com) saytiga kiring va **GitHub orqali kiring (Sign in with GitHub)**. *(Plastik karta talab qilinmaydi!)*
2. Asosiy ekranda ko'k **«New +»** tugmasini bosib, **«Web Service»** ni tanlang.
3. Yangi ochilgan ro'yxatdan o'zingizning `parody-telegram-bot` repositoryingizni tanlang va **«Connect»** tugmasini bosing.
4. Quyidagi parametrlarni to'ldiring:
   - **Name:** `parodiya-tabrik-bot` (yoki ixtiyoriy nom)
   - **Region:** `Frankfurt (EU Central)` *(O'zbekistonga eng yaqin va tezkor)*
   - **Branch:** `main`
   - **Runtime:** `Python 3` *(yoki Docker tanlashingiz ham mumkin)*
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** **Free ($0/month)** ni tanlang!
5. Pastroqqa tushib, **«Environment Variables»** (Muhit o'zgaruvchilari) bo'limida **«Add Environment Variable»** tugmasini bosing:
   - **Key:** `BOT_TOKEN`
   - **Value:** `@BotFather bergan tokenni shu yerga qo'ying`
   - **Key:** `PORT`
   - **Value:** `8080`
6. Eng pastdagi ko'k **«Deploy Web Service»** tugmasini bosing!
7. 1-2 daqiqada server loyihani o'rnatib, ishga tushiradi. Loglarda quyidagilar chiqadi:
   ```
   🌐 Keep-Alive Veb-Server 0.0.0.0:8080 manzilida tinglamoqda.
   🤖 Telegram Bot Polling ishga tushirilmoqda...
   ```
8. Yuqori chap burchakda sizning bepul veb-manzilingiz paydo bo'ladi:
   `https://parodiya-tabrik-bot.onrender.com`

---

## ⏰ 4-QADAM: Botni 24/7 Uyg'oq Tutish (UptimeRobot - Anti-Sleep) (1 daqiqa)
Render.com bepul serverlariga 15 daqiqa davomida hech kim kirmasa, ular serverni uxlatib qo'yadi. Buni butunlay bartaraf etamiz:

1. [UptimeRobot.com](https://uptimerobot.com) saytiga kiring va bepul ro'yxatdan o'ting (Free plan, karta shart emas).
2. Dashboardda ko'k **«+ Add New Monitor»** tugmasini bosing.
3. Sozlamalarni shunday kiriting:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `Parody Bot Health Check`
   - **URL (or IP):** `https://parodiya-tabrik-bot.onrender.com/health` *(Render bergan manzilingiz oxiriga /health qo'shing)*
   - **Monitoring Interval:** `Every 5 minutes` (Har 5 daqiqada)
4. Pastdagi **«Create Monitor»** tugmasini bosing!

🎉 **BO'LDI! BARCHASI TAYYOR!**
Endi UptimeRobot har 5 daqiqada botingizning `/health` manziliga so'rov yuborib turadi. Render serveringizni **hech qachon uxlatmaydi**. Siz noutbukingizni o'chirib, bemalol uxlasangiz ham bot 24/7/365 kechayu-kunduz ishlab turadi!

---

## ⚡ QO'SHIMCHA: Alternativ Bepul Xostinglar

Agar Render.com yoqmasa, aynan shu repositoryni boshqa platformalarga ham 100% bepul deploy qilish mumkin:

### 1. Koyeb.com (0 So'm - Eco Nano)
- [Koyeb.com](https://koyeb.com) ga kiring, GitHub reponi ulang.
- Builder sifatida **Docker** yoki **Buildpack** ni tanlang.
- Environment variable: `BOT_TOKEN` ni kiriting.
- Koyeb oylik 1 ta bepul xizmat beradi va u umuman uxlamaydi.

### 2. Hugging Face Spaces (Docker SDK)
- [HuggingFace.co](https://huggingface.co) ga kiring, «New Space» oching.
- Space SDK: **Docker** ni tanlang (Blank).
- Fayllarni yuklang va Settings -> Variables bo'limiga `BOT_TOKEN` ni kiriting.
- 16 GB bepul RAM beradi!

---

## 🛡️ Nosozliklarni Bartaraf Qilish (Troubleshooting):
- **Bot javob bermayapti:** Render loglariga qarang. Agar `Unauthorized` xatosi bo'lsa, `BOT_TOKEN` xato kiritilgan.
- **Port xatosi:** Render avtomatik ravishda `$PORT` o'zgaruvchisini uzatadi, bizning `config.py` buni avtomatik o'qiydi.
- **Qayta ulanish:** Agar Telegram API da nosozlik bo'lsa, bizning `Watchdog` 5 soniyada botni qayta ulaydi, xavotir olmang!
