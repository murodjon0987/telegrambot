# -*- coding: utf-8 -*-
import asyncio
import os
import re
import logging
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import edge_tts

logger = logging.getLogger("MediaGenerator")

def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidate_fonts = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf",
    ]
    for font_name in candidate_fonts:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def generate_postcard_image(
    character_name: str,
    recipient_name: str,
    message_text: str,
    sender_name: str,
    output_path: str
) -> str:
    """
    1080x1080 o'lchamli hashamatli oltin hoshiyali otkritka rasm generatsiyasi.
    """
    width, height = 1080, 1080
    
    # To'q hashamatli gradient
    base = Image.new("RGB", (width, height), (15, 23, 42))
    draw = ImageDraw.Draw(base)
    
    for y in range(height):
        ratio = y / height
        r = int(15 * (1 - ratio) + 35 * ratio)
        g = int(23 * (1 - ratio) + 20 * ratio)
        b = int(42 * (1 - ratio) + 65 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Oltin hoshiya
    draw.rectangle([35, 35, width - 35, height - 35], outline=(212, 175, 55), width=5)
    draw.rectangle([50, 50, width - 50, height - 50], outline=(255, 215, 0), width=2)
    
    # Burchak bezaklari
    corners = [(35, 35), (width - 35, 35), (35, height - 35), (width - 35, height - 35)]
    for cx, cy in corners:
        draw.rectangle([cx - 16, cy - 16, cx + 16, cy + 16], fill=(212, 175, 55))
        
    font_title = _get_font(34, bold=True)
    font_label = _get_font(24, bold=False)
    font_name = _get_font(42, bold=True)
    font_char = _get_font(28, bold=True)
    font_body = _get_font(26, bold=False)
    font_footer = _get_font(22, bold=False)
    
    # Sarlavha
    draw.text((width // 2, 95), "🎭 PARODIYA TABRIK & QUTLOV 🎭", fill=(255, 215, 0), font=font_title, anchor="mm")
    
    # Qabul qiluvchi
    draw.text((width // 2, 180), "Aziz va Hurmatli:", fill=(148, 163, 184), font=font_label, anchor="mm")
    draw.text((width // 2, 240), recipient_name, fill=(255, 255, 255), font=font_name, anchor="mm")
    
    # Obraz nishoni
    draw.rectangle([120, 295, width - 120, 365], fill=(30, 41, 59), outline=(212, 175, 55), width=2)
    draw.text((width // 2, 330), f"Obraz: {character_name}", fill=(255, 215, 0), font=font_char, anchor="mm")
    
    # Tozalangan matnni qatorlarga ajratish
    clean_msg = re.sub(r'[*_`#\[\]]', '', message_text)
    clean_msg = " ".join(clean_msg.split())
    
    words = clean_msg.split()
    lines = []
    current_line = []
    
    for w in words:
        current_line.append(w)
        if len(" ".join(current_line)) > 42:
            lines.append(" ".join(current_line[:-1]))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))
        
    start_y = 430
    line_spacing = 42
    for line in lines[:9]:
        draw.text((width // 2, start_y), line, fill=(241, 245, 249), font=font_body, anchor="mm")
        start_y += line_spacing
        
    # Jo'natuvchi va pastki ma'lumot
    draw.line([(160, 880), (width - 160, 880)], fill=(212, 175, 55), width=2)
    draw.text((width // 2, 920), f"Taqdim etdi: {sender_name}", fill=(255, 215, 0), font=font_char, anchor="mm")
    draw.text((width // 2, 980), "Telegram: @parodiya_tabrik_uzbot", fill=(148, 163, 184), font=font_footer, anchor="mm")
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    base.save(output_path, format="PNG", quality=95)
    return output_path

async def generate_audio_voice(text: str, character_key: str, output_path: str) -> str:
    """
    Microsoft Edge Neural TTS orqali tabiiy o'zbekcha MP3 audio generatsiyasi.
    Xatolikka qarshi 2 martalik avtomatik qayta urinish (retry).
    """
    voice = "uz-UZ-MadinaNeural" if character_key == "qaynona" else "uz-UZ-SardorNeural"
    
    clean_text = re.sub(r'[*_`#\[\]\n\r]', ' ', text)
    clean_text = " ".join(clean_text.split())
    
    if len(clean_text) > 600:
        clean_text = clean_text[:600] + "..."
        
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    last_err = None
    for attempt in range(2):
        try:
            communicate = edge_tts.Communicate(clean_text, voice)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            last_err = e
            logger.warning(f"Audio generatsiyasida urinish {attempt+1} xato berdi: {e}")
            await asyncio.sleep(1.0)
            
    if last_err is not None:
        raise last_err
    raise RuntimeError("Audio generatsiya qilib bo'lmadi")
