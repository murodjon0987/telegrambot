# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import sys
import time
from datetime import datetime

from aiohttp import web  # pyrefly: ignore [missing-import] # type: ignore
from aiogram import Bot, Dispatcher, Router, F, BaseMiddleware  # pyrefly: ignore [missing-import] # type: ignore
from aiogram.filters import Command, CommandStart  # pyrefly: ignore [missing-import] # type: ignore
from aiogram.fsm.context import FSMContext  # pyrefly: ignore [missing-import] # type: ignore
from aiogram.fsm.state import State, StatesGroup  # pyrefly: ignore [missing-import] # type: ignore
from aiogram.fsm.storage.memory import MemoryStorage  # pyrefly: ignore [missing-import] # type: ignore
from aiogram.types import (  # pyrefly: ignore [missing-import] # type: ignore
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    TelegramObject,
    FSInputFile
)
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramForbiddenError  # pyrefly: ignore [missing-import] # type: ignore

import config
import database
from characters import CHARACTERS, CATEGORIES, PROFESSIONS, generate_custom_message

# -------------------------------------------------------------
# 1. LOGGING VA SOZLAMALAR (Low-RAM Optimization)
# -------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ParodyBotApp")

START_TIME = time.time()

# -------------------------------------------------------------
# 2. FSM (FINITE STATE MACHINE) HOZIRGI HOLATLAR
# -------------------------------------------------------------
class GreetingForm(StatesGroup):
    choosing_category = State()
    choosing_character = State()
    entering_recipient = State()
    choosing_profession = State()
    entering_sender = State()

class AdminBroadcastForm(StatesGroup):
    entering_message = State()
    confirming = State()

class AdminSearchUserForm(StatesGroup):
    entering_user_id = State()

# -------------------------------------------------------------
# 3. MAJBURIY OBUNA MATNI VA KLAVIATURASI
# -------------------------------------------------------------
SUBSCRIPTION_TEXT = (
    "⚠️ <b>Botdan to'liq va bepul foydalanish uchun rasmiy kanalimizga a'zo bo'ling!</b>\n\n"
    f"👉 Kanal: <b>{config.CHANNEL_ID}</b>\n\n"
    "Kanalga a'zo bo'lganingizdan so'ng, quyidagi <b>«✅ Obunani Tekshirish»</b> tugmasini bosing:"
)

def get_subscription_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Kanalga A'zo Bo'lish", url=config.CHANNEL_URL)
            ],
            [
                InlineKeyboardButton(text="✅ Obunani Tekshirish", callback_data="check_subscription")
            ]
        ]
    )

async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    """Foydalanuvchining ko'rsatilgan kanalda bor-yo'qligini tekshiradi."""
    # Bosh admin uchun har doim ruxsat beriladi
    if config.is_admin(user_id):
        return True
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        if member.status in ("creator", "administrator", "member", "restricted"):
            return True
        return False
    except Exception as e:
        logger.warning(f"Kanal a'zoligini tekshirishda xatolik ({user_id}): {e}")
        return False

# -------------------------------------------------------------
# 4. MIDDLEWARE LAR (Tracking va Majburiy Obuna)
# -------------------------------------------------------------
class UserTrackingMiddleware(BaseMiddleware):
    """Har bir kelgan xabar va tugma bosilishida foydalanuvchini bazada yangilaydi."""
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user:
            # Asinxron ravishda foydalanuvchini bazaga qo'shish/yangilash
            asyncio.create_task(database.upsert_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name or "",
                last_name=user.last_name or ""
            ))
        return await handler(event, data)

class MandatorySubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot: Bot = data.get("bot")
        user = data.get("event_from_user")
        
        # Agar tekshirish tugmasi bosilgan bo'lsa, handlerni o'ziga ruxsat beramiz
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)
        
        if user and bot:
            is_sub = await check_user_subscription(bot, user.id)
            if not is_sub:
                if isinstance(event, Message):
                    await event.answer(
                        SUBSCRIPTION_TEXT,
                        parse_mode="HTML",
                        reply_markup=get_subscription_keyboard()
                    )
                    return
                elif isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Botdan foydalanish uchun avval kanalga a'zo bo'ling!", show_alert=True)
                    try:
                        await event.message.answer(
                            SUBSCRIPTION_TEXT,
                            parse_mode="HTML",
                            reply_markup=get_subscription_keyboard()
                        )
                    except Exception:
                        pass
                    return
        
        return await handler(event, data)

# -------------------------------------------------------------
# 5. MENYU KLAVIATURALARI
# -------------------------------------------------------------
def get_main_menu_keyboard(user_id: int = 0):
    buttons = [
        [
            InlineKeyboardButton(text="🎭 Tabrik Yaratish (Bepul)", callback_data="start_create")
        ],
        [
            InlineKeyboardButton(text="🌟 Barcha Personajlar", callback_data="all_characters"),
            InlineKeyboardButton(text="ℹ️ Bot Haqida", callback_data="about_bot")
        ],
        [
            InlineKeyboardButton(text="🤝 Reklama & Hamkorlik", callback_data="ads_partnership"),
            InlineKeyboardButton(text="⚡ Server Holati", callback_data="server_status")
        ]
    ]
    # Faqat belgilangan Admin ID ga Admin Panel tugmasi ko'rinadi
    if config.is_admin(user_id):
        buttons.append([
            InlineKeyboardButton(text="👑 Admin Boshqaruv Paneli", callback_data="admin_panel")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="📜 Jonli Harakatlar (Logs)", callback_data="admin_logs")
            ],
            [
                InlineKeyboardButton(text="👥 So'nggi Foydalanuvchilar", callback_data="admin_users"),
                InlineKeyboardButton(text="🔍 Qidirish (ID bo'yicha)", callback_data="admin_search_user")
            ],
            [
                InlineKeyboardButton(text="📢 Xabarnoma (Rassilka)", callback_data="admin_broadcast"),
                InlineKeyboardButton(text="📥 Baza Eksport (CSV/DB)", callback_data="admin_export")
            ],
            [
                InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_panel"),
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )

def get_admin_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel")
            ]
        ]
    )

def get_categories_keyboard():
    buttons = []
    for key, title in CATEGORIES.items():
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"cat_{key}")])
    buttons.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_characters_keyboard():
    buttons = []
    for key, data in CHARACTERS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{data['name']}",
                callback_data=f"char_{key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_professions_keyboard():
    buttons = []
    for key, title in PROFESSIONS.items():
        buttons.append([
            InlineKeyboardButton(text=title, callback_data=f"prof_{key}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_result_keyboard(share_text: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📲 Do'stga Ulashish (Share)",
                    switch_inline_query=share_text[:50]
                )
            ],
            [
                InlineKeyboardButton(text="🔄 Yana Boshqa Yaratish", callback_data="start_create")
            ],
            [
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )

# -------------------------------------------------------------
# 6. HANDLERLAR
# -------------------------------------------------------------
router = Router()

# Middlewarelarni ro'yxatdan o'tkazish
router.message.middleware(UserTrackingMiddleware())
router.callback_query.middleware(UserTrackingMiddleware())
router.message.middleware(MandatorySubscriptionMiddleware())
router.callback_query.middleware(MandatorySubscriptionMiddleware())

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
    """Foydalanuvchi 'Obunani Tekshirish' tugmasini bosganda tekshirish."""
    is_sub = await check_user_subscription(bot, call.from_user.id)
    if is_sub:
        await database.log_activity(
            user_id=call.from_user.id,
            username=call.from_user.username,
            full_name=call.from_user.full_name,
            action="CHECK_SUB",
            details="Kanal a'zoligini tasdiqladi"
        )
        await call.answer("✅ Rahmat! Obuna tasdiqlandi. Xush kelibsiz!", show_alert=True)
        await state.clear()
        welcome_text = (
            f"Assalomu alaykum, <b>{call.from_user.first_name}</b>! 🎭\n\n"
            "<b>«Parodiya Tabrik & Mashhurlar Qutlovi»</b> botiga xush kelibsiz!\n\n"
            "Barcha personajlar va tabriklar siz uchun <b>100% BEPUL</b>! 🎉\n\n"
            "Quyidagi tugmani bosing va do'stingiz uchun ajoyib qutlov tayyorlang:"
        )
        await call.message.edit_text(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(call.from_user.id))
    else:
        await call.answer("❌ Siz hali kanalga a'zo bo'lmadingiz! Iltimos, kanalga obuna bo'ling.", show_alert=True)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await database.log_activity(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        action="START",
        details="Botni ishga tushirdi (/start)"
    )
    welcome_text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>! 🎭\n\n"
        "<b>«Parodiya Tabrik & Mashhurlar Qutlovi»</b> botiga xush kelibsiz!\n\n"
        "Ushbu bot orqali yaqinlaringizni O'zbekistondagi mashhur "
        "personajlar tilida mutlaqo <b>BEPUL</b> qutlashingiz mumkin! 😄\n\n"
        "Quyidagi tugmani bosing va tabrik yarating:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(message.from_user.id))

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="MENU",
        details="Bosh menyuga qaytdi"
    )
    await call.message.edit_text(
        "Asosiy menyuga qaytdingiz. Qanday amal bajaramiz?",
        reply_markup=get_main_menu_keyboard(call.from_user.id)
    )
    await call.answer()

@router.callback_query(F.data == "all_characters")
async def all_characters_handler(call: CallbackQuery):
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="VIEW_CHARACTERS",
        details="Personajlar ro'yxatini ko'rdi"
    )
    text = (
        "🌟 <b>Mavjud Barcha Personajlar (100% Bepul):</b>\n\n"
        "1. 💰 <b>Saxiy Boyvachcha Otaxon</b> — Dollar sochadigan saxiy millioner uslubida\n"
        "2. 👮 <b>Katta Leytenant (GAI)</b> — Qat'iy nazorat va protokol hazillari bilan\n"
        "3. 🍏 <b>Malika / O'rikzor Savdogari</b> — 'O'zimni yaqinimga beradigan narxda' uslubi\n"
        "4. 📜 <b>Xalq Donishmandi & Shoir</b> — Qofiyali, kulgili va falsafiy baytlar\n"
        "5. 🕶️ <b>Xorijdagi Shef (Don Karleone)</b> — Jiddiy va katta doiradagi nufuzli biznesmen\n\n"
        "<i>Barcha personajlardan cheksiz va bepul foydalanishingiz mumkin!</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Tabrik Yaratish", callback_data="start_create")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
        ]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "about_bot")
async def about_bot_handler(call: CallbackQuery):
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="VIEW_ABOUT",
        details="Bot haqida bo'limini ko'rdi"
    )
    text = (
        "<b>🎭 «Parodiya Tabrik & Qutlovlar» Boti</b>\n\n"
        "Yaqinlaringiz va do'stlaringizga O'zbekistonning eng mashhur personajlari "
        "tilida eksklyuziv, kulgili va unutilmas tabriklar ulashuvchi 100% bepul bot! ✨\n\n"
        f"👑 <b>Loyiha Muallifi:</b> {config.CREATOR_USERNAME}\n"
        f"📢 <b>Rasmiy Kanal:</b> {config.CHANNEL_ID}\n"
        "⚡ <b>Xizmat:</b> 100% Bepul va Cheksiz\n"
        "🛡️ <b>Ishlash Rejimi:</b> 24/7 To'xtovsiz (Bulutli Cloud)\n\n"
        "<i>Har bir kuningiz bayramona quvonch va tabassumga to'lsin! 🎁</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Muallif Bilan Bog'lanish", url="https://t.me/wenzone72")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
        ]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "server_status")
async def server_status_handler(call: CallbackQuery):
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    stats = await database.get_statistics()
    
    status_text = (
        "<b>⚡ Bulutli Server Holati:</b>\n\n"
        "🟢 <b>Status:</b> 24/7 Onlayn (Active)\n"
        f"⏱ <b>Uptime:</b> {hours} soat, {minutes} daqiqa, {seconds} soniya\n"
        f"👥 <b>Bazada jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎁 <b>Yaratilgan jami tabriklar:</b> {stats['total_greetings']} ta\n"
        f"📢 <b>Kanal Monitoringi:</b> {config.CHANNEL_ID} (Faol)\n"
        "🛡️ <b>Crash-Proof Watchdog:</b> Faol\n"
        "💤 <b>Anti-Sleep Pinger:</b> Faol\n\n"
        "<i>Server noutbukingiz o'chiq bo'lsa ham 24/7 to'xtovsiz ishlaydi!</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]]
    )
    await call.message.edit_text(status_text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "ads_partnership")
async def ads_partnership_handler(call: CallbackQuery):
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="VIEW_ADS",
        details="Reklama va hamkorlik bo'limini ko'rdi"
    )
    text = (
        "<b>🤝 Reklama va Hamkorlik Bo'limi</b> 📢\n\n"
        "Botingiz va kanallaringiz auditoriyasini biz bilan birga kengaytiring! "
        "Biz quyidagi yo'nalishlarda hamkorlik qilishga tayyormiz:\n\n"
        "📌 <b>Taklif Qilinadigan Xizmatlar:</b>\n"
        "• <b>Majburiy Obuna (OP):</b> Kanalingizga jonli, faol va real o'zbek auditoriyasini jalb qilish.\n"
        "• <b>Xabarnoma (Rassilka):</b> Botning barcha foydalanuvchilariga reklama xabaringizni yuborish.\n"
        "• <b>Tugmali Integratsiya:</b> Bot ichidagi tabriklar va menyularda maxsus reklama havolalari joylashtirish.\n"
        "• <b>O'zaro Hamkorlik (VP):</b> Boshqa bot va kanallar bilan do'stona almashinuv.\n\n"
        f"👑 <b>Reklama Bo'yicha Mas'ul:</b> {config.CREATOR_USERNAME}\n\n"
        "<i>Batafsil ma'lumot va narxlar bo'yicha pastdagi tugma orqali murojaat qiling:</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Adminga Yozish (@wenzone72)", url="https://t.me/wenzone72")],
            [InlineKeyboardButton(text="📢 Rasmiy Kanalimiz", url=config.CHANNEL_URL)],
            [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")]
        ]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

# --- TABRIK VA MATN YARATISH BOSQICHLARI (FSM) ---

@router.callback_query(F.data == "start_create")
async def start_create_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(GreetingForm.choosing_category)
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="START_CREATE",
        details="Tabrik yaratish jarayonini boshladi"
    )
    text = (
        "🎭 <b>1-Qadam: Qanday yo'nalishda matn yaratamiz?</b>\n\n"
        "Quyidagi qiziqarli toifalardan birini tanlang:"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_categories_keyboard())
    await call.answer()

@router.callback_query(GreetingForm.choosing_category, F.data.startswith("cat_"))
async def category_chosen_handler(call: CallbackQuery, state: FSMContext):
    category_key = call.data.replace("cat_", "")
    await state.update_data(chosen_category=category_key)
    await state.set_state(GreetingForm.choosing_character)
    
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="CHOOSE_CATEGORY",
        details=f"Kategoriya tanladi: {CATEGORIES.get(category_key, category_key)}"
    )
    
    text = (
        "👤 <b>2-Qadam: Ushbu matn kimning nomidan (qaysi personaj tilida) bo'lsin?</b>\n\n"
        "O'zingizga ma'qul xarakterni tanlang:"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_characters_keyboard())
    await call.answer()

@router.callback_query(GreetingForm.choosing_character, F.data.startswith("char_"))
async def character_chosen_handler(call: CallbackQuery, state: FSMContext):
    char_key = call.data.replace("char_", "")
    await state.update_data(chosen_char=char_key)
    await state.set_state(GreetingForm.entering_recipient)
    
    char_info = CHARACTERS.get(char_key, {})
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="CHOOSE_CHARACTER",
        details=f"Personaj tanladi: {char_info.get('name', char_key)}"
    )
    
    text = (
        f"Tanlangan personaj: <b>{char_info.get('name')}</b> {char_info.get('icon')}\n\n"
        "✍️ <b>3-Qadam:</b> Ushbu xabar kim uchun yoziladi? "
        "Do'stingizning yoki yaqiningizning <b>Ismini</b> yozib yuboring:\n"
        "<i>(Masalan: Sardor, Madina, Jasur)</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()

@router.message(GreetingForm.entering_recipient)
async def recipient_entered_handler(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) > 40:
        await message.answer("Iltimos, ismni qisqaroq qilib kiriting (maksimal 40 harf):")
        return
    
    await state.update_data(recipient_name=name)
    await state.set_state(GreetingForm.choosing_profession)
    
    await database.log_activity(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        action="ENTER_RECIPIENT",
        details=f"Qabul qiluvchi ismi kiritildi: {name}"
    )
    
    text = (
        f"Ajoyib! Demak, <b>{name}</b> uchun tayyorlaymiz.\n\n"
        "💼 <b>4-Qadam:</b> Matn yanada kulgili va aniq chiqishi uchun — "
        f"<b>{name} qaysi sohada ishlaydi (kasbi nima)?</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_professions_keyboard())

@router.callback_query(GreetingForm.choosing_profession, F.data.startswith("prof_"))
async def profession_chosen_handler(call: CallbackQuery, state: FSMContext):
    prof_key = call.data.replace("prof_", "")
    await state.update_data(chosen_profession=prof_key)
    await state.set_state(GreetingForm.entering_sender)
    
    await database.log_activity(
        user_id=call.from_user.id,
        username=call.from_user.username,
        full_name=call.from_user.full_name,
        action="CHOOSE_PROFESSION",
        details=f"Kasbi tanlandi: {PROFESSIONS.get(prof_key, prof_key)}"
    )
    
    text = (
        "👤 <b>5-Qadam:</b> Ushbu tabrik kimning nomidan yuboriladi?\n"
        "O'z ismingizni yoki laqabingizni yozib yuboring:\n"
        "<i>(Masalan: Do'stingiz Alisher, Sinfdoshlar, Bojxona jamoasi)</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()

@router.message(GreetingForm.entering_sender)
async def sender_entered_handler(message: Message, state: FSMContext):
    sender_name = message.text.strip()
    data = await state.get_data()
    await state.clear()
    
    category = data.get("chosen_category", "greeting")
    char_key = data.get("chosen_char", "boyvachcha")
    recipient_name = data.get("recipient_name", "Do'stim")
    prof_key = data.get("chosen_profession", "general")
    
    # Eksklyuziv dinamik matnni generatsiya qilish
    generated_text = generate_custom_message(
        char_key=char_key,
        recipient_name=recipient_name,
        category=category,
        profession_key=prof_key,
        sender_name=sender_name
    )
    
    # Bazaga tabrikni saqlash va hisoblagichni oshirish
    await database.save_greeting(
        user_id=message.from_user.id,
        category=category,
        character=char_key,
        recipient_name=recipient_name,
        profession=prof_key,
        sender_name=sender_name,
        text=generated_text
    )
    
    await database.log_activity(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        action="TABRIK_CREATED",
        details=f"Tabrik yaratdi: {char_key} -> {recipient_name} ({prof_key}), Jo'natuvchi: {sender_name}"
    )
    
    await message.answer("✨ <b>Matn tayyorlanmoqda... 3, 2, 1...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    
    # Burchakda copy bo'lishi uchun maxsus pre code formati
    result_text = (
        "🎉 <b>Eksklyuziv Matn Tayyor Bo'ldi!</b>\n\n"
        "📋 <i>Quyidagi matnning burchagidagi <b>«Copy»</b> tugmasini bosib (yoki matn ustiga 1 marta bosib) nusxalab oling:</i>\n\n"
        f"<pre><code class=\"language-text\">{generated_text}</code></pre>"
    )
    
    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=get_result_keyboard(f"{recipient_name} uchun eksklyuziv xabar!")
    )

# -------------------------------------------------------------
# 7. ADMIN PANEL (FAQAT ID: 6268220201 UCHUN)
# -------------------------------------------------------------

def admin_required(func):
    """Admin tekshiruvchi dekorator / yordamchi."""
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if not config.is_admin(user_id):
            if isinstance(event, CallbackQuery):
                await event.answer("❌ Bu bo'lim faqat bosh administrator uchun!", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("❌ Bu buyruq faqat bosh administrator uchun!")
            return
        return await func(event, *args, **kwargs)
    return wrapper

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not config.is_admin(message.from_user.id):
        return  # Boshqalar uchun jim qoladi
    
    await state.clear()
    stats = await database.get_statistics()
    text = (
        "👑 <b>Admin Boshqaruv Paneliga Xush Kelibsiz!</b>\n\n"
        f"🆔 <b>Admin ID:</b> <code>{message.from_user.id}</code>\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎁 <b>Yaratilgan tabriklar:</b> {stats['total_greetings']} ta\n"
        f"📜 <b>Qayd etilgan harakatlar:</b> {stats['total_logs']} ta\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat berilmagan!", show_alert=True)
        return
    
    await state.clear()
    stats = await database.get_statistics()
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"🆔 <b>Admin ID:</b> <code>{call.from_user.id}</code>\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎁 <b>Yaratilgan tabriklar:</b> {stats['total_greetings']} ta\n"
        f"📜 <b>Qayd etilgan harakatlar:</b> {stats['total_logs']} ta\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    uptime_sec = int(time.time() - START_TIME)
    hours, remainder = divmod(uptime_sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    stats = await database.get_statistics()
    
    text = (
        "📊 <b>Batafsil Bot Statistikasi:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🆕 <b>Bugun yangi qo'shilganlar:</b> {stats['today_users']} ta\n"
        f"🔥 <b>Bugun faol bo'lganlar:</b> {stats['active_today']} ta\n\n"
        f"🎁 <b>Jami yaratilgan tabriklar:</b> {stats['total_greetings']} ta\n"
        f"📅 <b>Bugungi yaratilgan tabriklar:</b> {stats['today_greetings']} ta\n\n"
        f"📜 <b>Jami kuzatilgan amallar:</b> {stats['total_logs']} ta\n"
        f"⏱ <b>Server Uptime:</b> {hours} soat, {minutes} daqiqa, {seconds} soniya\n"
        f"📢 <b>Majburiy kanal:</b> {config.CHANNEL_ID}\n\n"
        "<i>Barcha ma'lumotlar real vaqt rejimida hisoblanadi.</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_logs")
async def admin_logs_callback(call: CallbackQuery):
    """Oxirgi 15 ta jonli harakatlar jurnali (Kim kirib nima qilyapti)."""
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    logs = await database.get_recent_logs(limit=15)
    
    if not logs:
        text = "📜 <b>Jonli Harakatlar Jurnali:</b>\n\nHozircha harakatlar qayd etilmagan."
    else:
        text = "📜 <b>Oxirgi 15 ta Jonli Harakat Jurnali:</b>\n\n"
        for log in logs:
            username_part = f"(@{log['username']})" if log.get("username") else ""
            user_str = f"<b>{log.get('full_name', 'Foydalanuvchi')}</b> {username_part} [<code>{log['user_id']}</code>]"
            text += (
                f"⏱ <b>{log['created_at']}</b>\n"
                f"👤 {user_str}\n"
                f"⚡ <b>Amal:</b> <code>{log['action']}</code>\n"
                f"📝 <b>Tafsilot:</b> {log['details']}\n"
                "──────────────────\n"
            )
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users_callback(call: CallbackQuery):
    """Oxirgi faol 10 ta foydalanuvchi ma'lumotlari."""
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    users = await database.get_recent_users(limit=10)
    
    if not users:
        text = "👥 <b>Foydalanuvchilar Ro'yxati:</b>\n\nBazada hali foydalanuvchilar mavjud emas."
    else:
        text = "👥 <b>Oxirgi Faol 10 ta Foydalanuvchi:</b>\n\n"
        for idx, u in enumerate(users, 1):
            uname = f"@{u['username']}" if u.get("username") else "Mavjud emas"
            fname = u.get("first_name") or ""
            lname = u.get("last_name") or ""
            full_name = f"{fname} {lname}".strip() or "Noma'lum"
            text += (
                f"<b>{idx}. {full_name}</b> ({uname})\n"
                f"🆔 ID: <code>{u['user_id']}</code>\n"
                f"📅 Qo'shilgan: {u['created_at']}\n"
                f"⚡ Oxirgi faollik: {u['last_active']}\n"
                f"🎁 Yaratgan tabriklari: <b>{u['greetings_count']} ta</b>\n"
                "──────────────────\n"
            )
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_search_user")
async def admin_search_user_callback(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await state.set_state(AdminSearchUserForm.entering_user_id)
    text = (
        "🔍 <b>Foydalanuvchini Qidirish</b>\n\n"
        "Qidirmoqchi bo'lgan foydalanuvchining <b>Telegram ID</b> raqamini yuboring:\n"
        "<i>(Masalan: 123456789)</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_panel")]]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.message(AdminSearchUserForm.entering_user_id)
async def admin_search_user_result(message: Message, state: FSMContext):
    if not config.is_admin(message.from_user.id):
        return
    
    target_id_str = message.text.strip()
    if not target_id_str.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan iborat Telegram ID kiriting:")
        return
    
    target_id = int(target_id_str)
    user_info = await database.get_user_info(target_id)
    await state.clear()
    
    if not user_info:
        await message.answer(
            f"❌ <code>{target_id}</code> ID ga ega foydalanuvchi ma'lumotlar bazasida topilmadi.",
            parse_mode="HTML",
            reply_markup=get_admin_back_keyboard()
        )
        return
    
    uname = f"@{user_info['username']}" if user_info.get("username") else "Mavjud emas"
    full_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
    
    report = (
        f"👤 <b>Foydalanuvchi Profili:</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_info['user_id']}</code>\n"
        f"📝 <b>Ism-familiya:</b> {full_name}\n"
        f"🌐 <b>Username:</b> {uname}\n"
        f"📅 <b>Birinchi kirgan:</b> {user_info['created_at']}\n"
        f"⚡ <b>Oxirgi faollik:</b> {user_info['last_active']}\n"
        f"🎁 <b>Jami tabriklari:</b> {user_info['greetings_count']} ta\n\n"
    )
    
    if user_info.get("recent_activities"):
        report += "<b>Oxirgi harakatlari:</b>\n"
        for a in user_info["recent_activities"]:
            report += f"• [{a['created_at']}] <code>{a['action']}</code>: {a['details']}\n"
        report += "\n"
        
    if user_info.get("recent_greetings"):
        report += "<b>Oxirgi yaratgan tabriklari:</b>\n"
        for g in user_info["recent_greetings"]:
            report += f"• [{g['created_at']}] {g['character']} -> {g['recipient_name']} ({g['profession']})\n"
            
    await message.answer(report, parse_mode="HTML", reply_markup=get_admin_back_keyboard())

# --- ADMIN RASSILKA / XABARNOMA BOSQICHLARI ---

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await state.set_state(AdminBroadcastForm.entering_message)
    text = (
        "📢 <b>Ommaviy Xabarnoma (Rassilka) Yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
        "<i>(Matn, rasm, video, formatlangan xabar yoki forward qabul qilinadi)</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="admin_panel")]]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.message(AdminBroadcastForm.entering_message)
async def admin_broadcast_preview(message: Message, state: FSMContext):
    if not config.is_admin(message.from_user.id):
        return
    
    await state.update_data(broadcast_message_id=message.message_id, broadcast_chat_id=message.chat.id)
    await state.set_state(AdminBroadcastForm.confirming)
    
    total_users = (await database.get_statistics())["total_users"]
    
    text = (
        f"📢 <b>Xabar qabul qilindi!</b>\n\n"
        f"👥 Qabul qiluvchilar soni: <b>{total_users} ta</b> foydalanuvchi.\n\n"
        "Haqiqatan ham ushbu xabarni barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Ha, Yuborilsin!", callback_data="confirm_broadcast"),
                InlineKeyboardButton(text="❌ Bekor Qilish", callback_data="admin_panel")
            ]
        ]
    )
    await message.reply(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(AdminBroadcastForm.confirming, F.data == "confirm_broadcast")
async def admin_broadcast_execute(call: CallbackQuery, bot: Bot, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    data = await state.get_data()
    await state.clear()
    
    msg_id = data.get("broadcast_message_id")
    chat_id = data.get("broadcast_chat_id")
    
    user_ids = await database.get_all_user_ids()
    total = len(user_ids)
    
    status_msg = await call.message.answer(
        f"⏳ <b>Xabarnoma yuborilmoqda...</b>\n0/{total} yakunlandi.",
        parse_mode="HTML"
    )
    
    success_count = 0
    fail_count = 0
    
    for idx, uid in enumerate(user_ids, 1):
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=chat_id, message_id=msg_id)
            success_count += 1
        except TelegramForbiddenError:
            # Foydalanuvchi botni bloklagan
            fail_count += 1
        except Exception as e:
            logger.warning(f"Rassilka yuborishda xatolik ({uid}): {e}")
            fail_count += 1
        
        # Telegram limitlariga tushmaslik uchun kichik tanaffus
        await asyncio.sleep(0.04)
        
        # Har 20 ta foydalanuvchida statusni yangilab borish
        if idx % 20 == 0 or idx == total:
            try:
                await status_msg.edit_text(
                    f"⏳ <b>Xabarnoma yuborilmoqda...</b>\n"
                    f"Progress: <b>{idx}/{total}</b>\n"
                    f"✅ Yetkazildi: {success_count}\n"
                    f"❌ Yetkazilmadi: {fail_count}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
                
    final_text = (
        "🎉 <b>Xabarnoma Muvaffaqiyatli Yakunlandi!</b>\n\n"
        f"📊 <b>Jami foydalanuvchilar:</b> {total}\n"
        f"✅ <b>Muvaffaqiyatli yetkazildi:</b> {success_count} ta\n"
        f"❌ <b>Yetkazilmadi (bloklagan/xato):</b> {fail_count} ta"
    )
    await status_msg.edit_text(final_text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

# --- ADMIN BAZA EKSPORT ---

@router.callback_query(F.data == "admin_export")
async def admin_export_callback(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await call.answer("⏳ Fayllar tayyorlanmoqda...", show_alert=False)
    
    # 1. CSV fayl generatsiya qilish
    csv_filename = "users_list_export.csv"
    await database.export_users_csv(csv_filename)
    
    try:
        # CSV faylni jo'natish
        csv_file = FSInputFile(csv_filename, filename=f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        await bot.send_document(
            chat_id=call.from_user.id,
            document=csv_file,
            caption="📊 <b>Foydalanuvchilar ro'yxati (CSV formatida)</b>",
            parse_mode="HTML"
        )
        
        # SQLite bazaning o'zini jo'natish
        if os.path.exists(database.DB_FILE):
            db_file = FSInputFile(database.DB_FILE, filename=f"bot_database_{datetime.now().strftime('%Y%m%d_%H%M')}.sqlite")
            await bot.send_document(
                chat_id=call.from_user.id,
                document=db_file,
                caption="🗄 <b>To'liq SQLite ma'lumotlar bazasi (Barcha jadvallar va loglar)</b>",
                parse_mode="HTML"
            )
            
        await call.message.answer(
            "✅ <b>Baza fayllari muvaffaqiyatli yuborildi!</b>",
            parse_mode="HTML",
            reply_markup=get_admin_back_keyboard()
        )
    except Exception as e:
        logger.error(f"Baza eksport qilishda xatolik: {e}", exc_info=True)
        await call.message.answer(f"❌ Fayllarni yuborishda xatolik: {e}", reply_markup=get_admin_back_keyboard())
    finally:
        # Vaqtinchalik CSV faylni o'chirish
        if os.path.exists(csv_filename):
            try:
                os.remove(csv_filename)
            except Exception:
                pass

# -------------------------------------------------------------
# 8. KEEP-ALIVE AIOHTTP VEB-SERVER (Render / Koyeb talabi)
# -------------------------------------------------------------
async def handle_root(request: web.Request) -> web.Response:
    stats = await database.get_statistics()
    return web.json_response({
        "status": "alive",
        "service": "Telegram Parody Greeting Bot",
        "channel": config.CHANNEL_ID,
        "total_users": stats["total_users"],
        "total_greetings": stats["total_greetings"],
        "bot": "running"
    })

async def handle_health(request: web.Request) -> web.Response:
    uptime_sec = int(time.time() - START_TIME)
    stats = await database.get_statistics()
    return web.json_response({
        "status": "healthy",
        "uptime_seconds": uptime_sec,
        "channel": config.CHANNEL_ID,
        "total_users": stats["total_users"],
        "anti_sleep": "enabled"
    })

def create_web_server() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    return app

# -------------------------------------------------------------
# 9. CRASH-PROOF BOT WATCHDOG SIKLI
# -------------------------------------------------------------
async def run_bot_polling_watchdog(bot: Bot, dp: Dispatcher):
    retry_delay = 5
    while True:
        try:
            logger.info("🤖 Telegram Bot Polling ishga tushirilmoqda...")
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        except (TelegramNetworkError, TelegramAPIError) as api_err:
            logger.warning(f"⚠️ Telegram tarmog'ida vaqtinchalik uzilish: {api_err}")
            logger.info(f"⏳ {retry_delay} soniyadan so'ng avtomatik qayta ulanish...")
            await asyncio.sleep(retry_delay)
        except asyncio.CancelledError:
            logger.info("🛑 Polling vazifasi to'xtatildi (Graceful shutdown).")
            break
        except Exception as e:
            logger.error(f"❌ Kutilmagan xatolik yuz berdi: {e}", exc_info=True)
            logger.info(f"⏳ {retry_delay} soniyada qayta ishga tushirishga urinish...")
            await asyncio.sleep(retry_delay)

# -------------------------------------------------------------
# 10. ASOSIY ENTRYPOINT (MAIN SIKL)
# -------------------------------------------------------------
async def main():
    logger.info("🚀 Ilova ishga tushirilmoqda...")

    # 0. Ma'lumotlar bazasini ishga tushirish
    await database.init_db()
    logger.info("📦 SQLite Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi.")

    if not config.BOT_TOKEN:
        logger.error("❌ XATO: BOT_TOKEN aniqlanmadi! Iltimos, .env faylini to'ldiring.")
        return

    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    # 1. aiohttp Veb-Serverini ishga tushirish
    app = create_web_server()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host=config.HOST, port=config.PORT)
    await site.start()
    logger.info(f"🌐 Keep-Alive Veb-Server {config.HOST}:{config.PORT} manzilida tinglamoqda.")
    logger.info(f"📢 Majburiy kanal a'zoligi faol: {config.CHANNEL_ID}")
    logger.info(f"👑 Boshqaruvchi Admin ID: {config.ADMIN_ID}")

    # 2. Crash-proof Bot Watchdog Pollingni ishga tushirish
    try:
        await run_bot_polling_watchdog(bot, dp)
    finally:
        logger.info("🧹 Resurslarni tozalash va yopish...")
        await runner.cleanup()
        await bot.session.close()
        logger.info("👋 Ilova toza yopildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Dastur foydalanuvchi tomonidan to'xtatildi.")
