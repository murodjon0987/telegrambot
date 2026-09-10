# Minimal xotira sarflaydigan yengil Python 3.11-slim tasviri
FROM python:3.11-slim

# Muhit o'zgaruvchilari:
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Shriftlarni o'rnatish (Otkritka rasmlari chiroyli chiqishi uchun)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Avval faqat requirements.txt ni ko'chiramiz (Docker keshidan unumli foydalanish)
COPY requirements.txt .

# Kutubxonalarni keshsiz (no-cache-dir) o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Qolgan barcha kodlarni ko'chiramiz
COPY . .

# Standart portni ochamiz
EXPOSE 8080

# Bot va Keep-Alive veb-serverni ishga tushirish buyrug'i
CMD ["python", "main.py"]
