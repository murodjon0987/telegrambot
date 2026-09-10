import os
from dotenv import load_dotenv

# .env faylidan yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
# Bulutli serverlar (Render, Koyeb) portni $PORT o'zgaruvchisida beradi. Standart: 8080
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# Demo to'lov narxi (so'mda)
VIP_PRICE = int(os.getenv("VIP_PRICE", 7000))

if not BOT_TOKEN:
    # Lokal testda xabar berish
    print("[OGOHLANTIRISH] BOT_TOKEN topilmadi! .env fayliga BOT_TOKEN ni kiriting.")
