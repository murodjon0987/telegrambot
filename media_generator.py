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

def generate_magazine_cover(
    photo_path: str,
    person_name: str,
    title_data: dict,
    output_path: str
) -> str:
    """
    1080x1440 o'lchamli hashamatli VIP Forbes uslubidagi jurnal muqovasi generatsiyasi.
    """
    W, H = 1080, 1440
    cover = Image.new("RGB", (W, H), (15, 20, 35))
    
    # 1. Foto yuklash va joylashtirish
    if photo_path and os.path.exists(photo_path):
        try:
            user_img = Image.open(photo_path).convert("RGBA")
            img_w, img_h = user_img.size
            scale = max(W / img_w, (H * 0.72) / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            user_img = user_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            pos_x = (W - new_w) // 2
            pos_y = int(H * 0.15)
            cover.paste(user_img.convert("RGB"), (pos_x, pos_y))
        except Exception as e:
            logger.warning(f"Rasm yuklashda xato: {e}")
            
    # 2. Gradient overlay (Yuqori va pastki qismlarni qoraytirish)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    
    # Top gradient
    for y in range(250):
        alpha = int(225 * (1 - y / 250))
        draw_ov.line([(0, y), (W, y)], fill=(10, 15, 28, alpha))
        
    # Bottom gradient
    for y in range(H - 580, H):
        factor = (y - (H - 580)) / 580
        alpha = int(245 * (factor ** 1.3))
        draw_ov.line([(0, y), (W, y)], fill=(8, 12, 22, alpha))
        
    cover.paste(Image.alpha_composite(cover.convert("RGBA"), overlay).convert("RGB"))
    draw = ImageDraw.Draw(cover)
    
    # 3. Hashamatli Oltin hoshiya
    border_col = (218, 165, 32)
    border_inner = (255, 215, 0)
    draw.rectangle([(25, 25), (W - 25, H - 25)], outline=border_col, width=3)
    draw.rectangle([(32, 32), (W - 32, H - 32)], outline=border_inner, width=1)
    
    for cx, cy in [(25, 25), (W - 25, 25), (25, H - 25), (W - 25, H - 25)]:
        draw.rectangle([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=border_inner)
        
    # 4. Masthead (FORBES VIP / YIL ODAMLARI)
    font_top_tag = _get_font(20, bold=True)
    draw.text((W // 2, 55), "* * *  O'ZBEKISTONNING ENG NUFUSLI JURNALI  * * *", font=font_top_tag, fill=(255, 215, 0), anchor="mm")
    
    font_masthead = _get_font(105, bold=True)
    draw.text((W // 2 + 3, 132 + 3), "FORBES VIP", font=font_masthead, fill=(0, 0, 0), anchor="mm")
    draw.text((W // 2, 132), "FORBES VIP", font=font_masthead, fill=(255, 255, 255), anchor="mm")
    
    draw.line([(50, 190), (W - 50, 190)], fill=border_col, width=2)
    font_sub = _get_font(19, bold=True)
    draw.text((60, 208), "MAXSUS SON - No007", font=font_sub, fill=(220, 220, 220), anchor="lm")
    draw.text((W // 2, 208), "YIL ODAMLARI REYTINQI", font=font_sub, fill=(255, 215, 0), anchor="mm")
    draw.text((W - 60, 208), "2026-YIL MAQSUS NASHR", font=font_sub, fill=(220, 220, 220), anchor="rm")
    draw.line([(50, 226), (W - 50, 226)], fill=border_col, width=2)
    
    # 5. Shov-shuvli maqola sarlavhalari
    t1_cat = title_data.get("t1_cat", "SENSIYA")
    t1_sub = title_data.get("t1_sub", "1 oyda boyvachchaga\naylanish siri!")
    t2_cat = title_data.get("t2_cat", "EXCLUSIVE")
    t2_sub = title_data.get("t2_sub", "Do'stlarining doimiy\nfaxri va suyanchi!")
    badge = title_data.get("badge", "100% ISHONCHLI")
    
    font_t1 = _get_font(24, bold=True)
    font_t2 = _get_font(19, bold=False)
    
    # Chap tomondagi sarlavha 1
    draw.text((55, 470), f"{t1_cat}:", font=font_t1, fill=(255, 69, 0), anchor="lm")
    cur_y = 500
    for line in t1_sub.split("\n"):
        draw.text((55, cur_y), line, font=font_t2, fill=(255, 255, 255), anchor="lm")
        cur_y += 28
        
    # Chap tomondagi sarlavha 2
    draw.text((55, 650), f"{t2_cat}:", font=font_t1, fill=(50, 205, 50), anchor="lm")
    cur_y = 680
    for line in t2_sub.split("\n"):
        draw.text((55, cur_y), line, font=font_t2, fill=(255, 215, 0), anchor="lm")
        cur_y += 28
        
    # O'ng tomondagi sarlavha
    draw.text((W - 55, 500), badge, font=font_t1, fill=(255, 215, 0), anchor="rm")
    draw.text((W - 55, 532), "Mahallaning faxri,", font=font_t2, fill=(255, 255, 255), anchor="rm")
    draw.text((W - 55, 560), "El-yurt suyanchi!", font=font_t2, fill=(255, 255, 255), anchor="rm")
    
    draw.text((W - 55, 660), "REKORD NATIJA:", font=font_t1, fill=(0, 191, 255), anchor="rm")
    draw.text((W - 55, 692), "Yilning eng havas", font=font_t2, fill=(255, 255, 255), anchor="rm")
    draw.text((W - 55, 720), "qilsa arziydigan shaxsi", font=font_t2, fill=(255, 215, 0), anchor="rm")
    
    # 6. Markazdagi Shaxs Ismi va Katta Unvoni
    name_display = person_name.strip().upper()
    font_name = _get_font(48, bold=True)
    
    tag_h = 75
    tag_y = H - 390
    draw.rectangle([(55, tag_y), (W - 55, tag_y + tag_h)], fill=(218, 165, 32))
    draw.rectangle([(59, tag_y + 4), (W - 59, tag_y + tag_h - 4)], fill=(18, 22, 38))
    
    draw.text((W // 2, tag_y + tag_h // 2), f"[ {name_display} ]", font=font_name, fill=(255, 215, 0), anchor="mm")
    
    main_title = title_data.get("title", "YILNING ENG SAXIY INSONI").upper()
    font_main_title = _get_font(30, bold=True)
    draw.text((W // 2 + 2, H - 280 + 2), main_title, font=font_main_title, fill=(0, 0, 0), anchor="mm")
    draw.text((W // 2, H - 280), main_title, font=font_main_title, fill=(255, 255, 255), anchor="mm")
    
    sub_title = title_data.get("subtitle", "«O'zbekistonning 2026-yildagi eng hurmatli va saxiy insoni»")
    font_sub_title = _get_font(21, bold=False)
    draw.text((W // 2, H - 235), sub_title, font=font_sub_title, fill=(255, 215, 0), anchor="mm")
    
    # 7. Pastki shtrix-kod va maxsus muhri (Barcode & Quality Seal)
    bc_x = 55
    bc_y = H - 140
    draw.rectangle([(bc_x - 8, bc_y - 8), (bc_x + 185, bc_y + 75)], fill=(255, 255, 255))
    import random
    rng = random.Random(sum(ord(c) for c in person_name))
    cur_x = bc_x
    while cur_x < bc_x + 170:
        w_line = rng.choice([2, 3, 4, 5])
        draw.line([(cur_x, bc_y), (cur_x, bc_y + 55)], fill=(0, 0, 0), width=w_line)
        cur_x += w_line + rng.choice([2, 3, 4])
    font_bc = _get_font(13, bold=True)
    draw.text((bc_x + 85, bc_y + 65), "9 780201 379624", font=font_bc, fill=(0, 0, 0), anchor="mm")
    
    seal_x = W - 130
    seal_y = H - 95
    draw.ellipse([(seal_x - 50, seal_y - 50), (seal_x + 50, seal_y + 50)], fill=(218, 165, 32), outline=(255, 215, 0), width=3)
    draw.ellipse([(seal_x - 44, seal_y - 44), (seal_x + 44, seal_y + 44)], fill=(15, 20, 35))
    font_seal = _get_font(15, bold=True)
    draw.text((seal_x, seal_y - 10), "100%", font=font_seal, fill=(255, 215, 0), anchor="mm")
    draw.text((seal_x, seal_y + 10), "ORIGINAL", font=_get_font(12, bold=True), fill=(255, 255, 255), anchor="mm")
    
    draw.text((W // 2, H - 95), "VIP EDITION • @parodiya_tabrik_uzbot", font=_get_font(19, bold=True), fill=(180, 180, 190), anchor="mm")
    
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    cover.save(output_path, format="JPEG", quality=95)
    return output_path
