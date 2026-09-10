import os
from dotenv import load_dotenv

# .env faylidan yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
# Bulutli serverlar (Render, Koyeb) portni $PORT o'zgaruvchisida beradi. Standart: 8080
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# Majburiy a'zo bo'linishi kerak bo'lgan kanal sozlamalari
CHANNEL_ID = os.getenv("CHANNEL_ID", "@my_shaxsiyolam").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/my_shaxsiyolam").strip()

if not BOT_TOKEN:
    # Lokal testda xabar berish
    print("[OGOHLANTIRISH] BOT_TOKEN topilmadi! .env fayliga BOT_TOKEN ni kiriting.")
