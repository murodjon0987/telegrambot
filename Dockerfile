# Minimal xotira sarflaydigan yengil Python 3.11-slim tasviri
FROM python:3.11-slim

# Muhit o'zgaruvchilari:
# 1. PYTHONUNBUFFERED=1: Loglar konsolga kechikmasdan darhol chiqishi uchun
# 2. PYTHONDONTWRITEBYTECODE=1: Ortiqcha .pyc fayllar yozib xotirani band qilmaslik
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Avval faqat requirements.txt ni ko'chiramiz (Docker keshidan unumli foydalanish)
COPY requirements.txt .

# Kutubxonalarni keshsiz (no-cache-dir) o'rnatish - konteyner hajmini minimal darajada ushlaydi
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha kodlarni ko'chiramiz
COPY . .

# Standart portni ochamiz
EXPOSE 8080

# Bot va Keep-Alive veb-serverni ishga tushirish buyrug'i
CMD ["python", "main.py"]
