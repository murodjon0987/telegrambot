# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv  # pyrefly: ignore [missing-import] # type: ignore

# .env faylidan yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
# Bulutli serverlar (Render, Koyeb) portni $PORT o'zgaruvchisida beradi. Standart: 8080
PORT = int(os.getenv("PORT", 8080))
HOST = os.getenv("HOST", "0.0.0.0")

# Majburiy a'zo bo'linishi kerak bo'lgan kanal sozlamalari
CHANNEL_ID = os.getenv("CHANNEL_ID", "@my_shaxsiyolam").strip()
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/my_shaxsiyolam").strip()

# Loyiha asoschisi (Muallif)
CREATOR_USERNAME = os.getenv("CREATOR_USERNAME", "@wenzone72").strip()

# Boshqaruvchi Admin ID (Faqat shu ID ga Admin Panel ko'rinadi)
ADMIN_ID = int(os.getenv("ADMIN_ID", "6268220201"))

# To'lov karta raqami (VIP Jurnal va pullik xizmatlar uchun)
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "4067070008610359").strip()
MIN_PAYMENT_AMOUNT = int(os.getenv("MIN_PAYMENT_AMOUNT", "1000"))

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi asosiy admin ekanligini tekshiradi."""
    return user_id == ADMIN_ID

if not BOT_TOKEN:
    # Lokal testda xabar berish
    print("[OGOHLANTIRISH] BOT_TOKEN topilmadi! .env fayliga BOT_TOKEN ni kiriting.")

