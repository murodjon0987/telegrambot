# -*- coding: utf-8 -*-
import asyncio
import html
import logging
import os
import sys
import time
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any

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
    ReplyKeyboardMarkup,
    KeyboardButton,
    TelegramObject,
    FSInputFile,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    BotCommand
)
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError, TelegramForbiddenError  # pyrefly: ignore [missing-import] # type: ignore

import config
import database
import media_generator
import leaderboard_web
from characters import (
    CHARACTERS, CATEGORIES, PROFESSIONS, generate_custom_message,
    QUIZ_QUESTIONS, QUIZ_RESULTS, CERTIFICATES, generate_certificate_text,
    DAILY_FORTUNES, get_daily_fortune, generate_random_roulette,
    MAGAZINE_TITLES
)

SITE_PHOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site_photos")
os.makedirs(SITE_PHOTOS_DIR, exist_ok=True)

# UTF-8 stdout sozlamalari (Windows da emojilar bilan xatolik chiqmasligi uchun)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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

class QuizForm(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()

class CertificateForm(StatesGroup):
    choosing_type = State()
    entering_recipient = State()
    entering_sender = State()

class AudioPaymentForm(StatesGroup):
    uploading_check = State()

class MagazinePaymentForm(StatesGroup):
    uploading_check = State()

class MagazineForm(StatesGroup):
    uploading_photo = State()
    entering_name = State()
    choosing_title = State()

class LeaderboardForm(StatesGroup):
    uploading_photo = State()
    entering_name = State()
    choosing_title = State()
    uploading_check = State()

class AdminCustomAmountForm(StatesGroup):
    entering_amount = State()

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
# 4. MIDDLEWARE LAR (Throttling, Ban, Tracking, Majburiy Obuna)
# -------------------------------------------------------------
class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.5):
        self.limit = limit
        self.last_actions = {}

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if not user or config.is_admin(user.id):
            return await handler(event, data)

        now = time.time()
        last_time = self.last_actions.get(user.id, 0.0)

        if now - last_time < self.limit:
            if isinstance(event, CallbackQuery):
                await event.answer("⚠️ Iltimos, biroz kuting...", show_alert=False)
            return

        self.last_actions[user.id] = now

        if len(self.last_actions) > 1000:
            threshold = now - 60
            self.last_actions = {uid: t for uid, t in self.last_actions.items() if t > threshold}

        return await handler(event, data)

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user and not config.is_admin(user.id):
            if await database.is_user_banned(user.id):
                if isinstance(event, Message):
                    await event.answer("⛔ <b>Sizning profilingiz qoidabuzarlik sababli botdan chetlashtirilgan.</b>", parse_mode="HTML")
                    return
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ Profilingiz bloklangan!", show_alert=True)
                    return
        return await handler(event, data)

class UserTrackingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user:
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
# 5. MENYU KLAVIATURALARI (Pastki doimiy va Inline)
# -------------------------------------------------------------
def get_reply_main_keyboard(user_id: int = 0):
    """Pastdagi ko'zga ko'rinadigan doimiy ReplyKeyboard tugmalari."""
    keyboard = [
        [
            KeyboardButton(text="🎭 Tabrik Yaratish"),
            KeyboardButton(text="🌟 VIP Jurnal Muqovasi")
        ],
        [
            KeyboardButton(text="👑 Saytdagi Top Boyvachchalar")
        ],
        [
            KeyboardButton(text="🧠 Qaysi Personajsan?"),
            KeyboardButton(text="📜 Parodiya Sertifikat")
        ],
        [
            KeyboardButton(text="🎲 Omad Barabani"),
            KeyboardButton(text="🔮 Kunlik Bashorat")
        ],
        [
            KeyboardButton(text="🏆 Ballar & Profilim"),
            KeyboardButton(text="📂 Mening Tabriklarim")
        ]
    ]
    if config.is_admin(user_id):
        keyboard.append([KeyboardButton(text="👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, is_persistent=True)

def get_main_menu_keyboard(user_id: int = 0):
    """Xabar ichidagi interaktiv InlineKeyboardMarkup."""
    buttons = [
        [
            InlineKeyboardButton(text="🎭 Tabrik Yaratish (Bepul)", callback_data="start_create")
        ],
        [
            InlineKeyboardButton(text="🌟 VIP Jurnal Muqovasi (Forbes)", callback_data="start_magazine"),
            InlineKeyboardButton(text="👑 Saytdagi Top Boyvachchalar", callback_data="top_leaderboard")
        ],
        [
            InlineKeyboardButton(text="🧠 Qaysi Personajsan? (Test)", callback_data="start_quiz"),
            InlineKeyboardButton(text="📜 Parodiya Sertifikat", callback_data="start_cert")
        ],
        [
            InlineKeyboardButton(text="🎲 Tavakkal Baraban", callback_data="roulette_spin"),
            InlineKeyboardButton(text="🔮 Kunlik Bashorat", callback_data="daily_fortune")
        ],
        [
            InlineKeyboardButton(text="🏆 Ballar & Profilim", callback_data="my_profile"),
            InlineKeyboardButton(text="📂 Mening Tabriklarim", callback_data="my_greetings")
        ],
        [
            InlineKeyboardButton(text="🌟 Barcha Personajlar", callback_data="all_characters"),
            InlineKeyboardButton(text="ℹ️ Bot Haqida", callback_data="about_bot")
        ]
    ]
    if config.is_admin(user_id):
        buttons.append([InlineKeyboardButton(text="👑 Admin Boshqaruv Paneli", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard(pending_count: int = 0):
    badge = f" (⏳ {pending_count} ta kutilmoqda!)" if pending_count > 0 else ""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"💳 To'lovlar & Cheklar Markazi{badge}", callback_data="admin_payments")
            ],
            [
                InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats"),
                InlineKeyboardButton(text="🏆 Reytinglar", callback_data="admin_rankings")
            ],
            [
                InlineKeyboardButton(text="📜 Jonli Harakatlar (Logs)", callback_data="admin_logs"),
                InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton(text="🔍 Qidirish (ID bo'yicha)", callback_data="admin_search_user"),
                InlineKeyboardButton(text="📢 Rassilka Yuborish", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton(text="📥 Baza Eksport (CSV/DB)", callback_data="admin_export"),
                InlineKeyboardButton(text="🧹 Loglarni Tozalash", callback_data="admin_cleanup")
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

def get_result_keyboard(share_text: str, full_message: str = "", greeting_id: int = 0):
    text_to_share = full_message if full_message else share_text
    encoded_text = urllib.parse.quote(text_to_share)
    telegram_share_url = f"https://t.me/share/url?url=https://t.me/parodiya_tabrik_uzbot&text={encoded_text}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🖼 Rasm (Otkritka) Olish", callback_data=f"get_image_{greeting_id}"),
                InlineKeyboardButton(text="🎙 Ovozli Audio (MP3)", callback_data=f"get_audio_{greeting_id}")
            ],
            [
                InlineKeyboardButton(text="🌟 Do'stga VIP Jurnal Muqovasi Yasash", callback_data="start_magazine")
            ],
            [
                InlineKeyboardButton(text="📲 Do'stga Ulashish (Telegram)", url=telegram_share_url)
            ],
            [
                InlineKeyboardButton(text="🔄 Yana Boshqa Yaratish", callback_data="start_create"),
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )

# -------------------------------------------------------------
# 6. HANDLERLAR
# -------------------------------------------------------------
router = Router()

router.message.middleware(ThrottlingMiddleware())
router.callback_query.middleware(ThrottlingMiddleware())
router.message.middleware(BanCheckMiddleware())
router.callback_query.middleware(BanCheckMiddleware())
router.message.middleware(UserTrackingMiddleware())
router.callback_query.middleware(UserTrackingMiddleware())
router.message.middleware(MandatorySubscriptionMiddleware())
router.callback_query.middleware(MandatorySubscriptionMiddleware())

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
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
        
        # Doimiy ReplyKeyboardni o'rnatish
        await call.message.answer(
            "Pastdagi tugmalar orqali botdan tezkor foydalanishingiz mumkin:",
            reply_markup=get_reply_main_keyboard(call.from_user.id)
        )
        
        welcome_text = (
            f"Assalomu alaykum, <b>{html.escape(call.from_user.first_name)}</b>! 🎭\n\n"
            "<b>«Parodiya Tabrik & Qutlovlar»</b> botiga xush kelibsiz!\n\n"
            "Sizga boshlang'ich <b>+5 ball</b> bonus berildi! 🎁\n"
            "Quyidagi qiziqarli bo'limlardan birini tanlang va yaqinlaringizga ajoyib kayfiyat ulashing:"
        )
        await call.message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(call.from_user.id))
    else:
        await call.answer("❌ Siz hali kanalga a'zo bo'lmadingiz! Iltimos, kanalga obuna bo'ling.", show_alert=True)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    referrer_id = 0
    utm_source = ""
    
    args = message.text.split()[1:]
    if args:
        payload = args[0]
        if payload.startswith("ref_") and payload[4:].isdigit():
            potential_ref = int(payload[4:])
            if potential_ref != message.from_user.id:
                referrer_id = potential_ref
        elif payload.startswith("ad_"):
            utm_source = html.escape(payload[3:50])
        else:
            utm_source = html.escape(payload[:50])

    is_new, bonus_ref_id = await database.upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
        referrer_id=referrer_id,
        utm_source=utm_source
    )

    if is_new and bonus_ref_id > 0:
        try:
            ref_notice = (
                f"🎉 <b>Do'stingiz {html.escape(message.from_user.first_name)} botga qo'shildi!</b>\n\n"
                "Sizga <b>+10 ball</b> taqdim etildi! 🎁\n"
                "Profilingiz va yutuqlaringizni ko'rish uchun /profile buyrug'ini bosing."
            )
            await bot.send_message(chat_id=bonus_ref_id, text=ref_notice, parse_mode="HTML")
        except Exception:
            pass

    await database.log_activity(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        action="START",
        details=f"Botni ishga tushirdi (/start, ref={referrer_id}, utm={utm_source})"
    )
    
    # 1. Pastki doimiy ReplyKeyboardni o'rnatish
    await message.answer(
        "Menyu tugmalari ekraningizning pastki qismiga o'rnatildi! 👇",
        reply_markup=get_reply_main_keyboard(message.from_user.id)
    )
    
    welcome_text = (
        f"Assalomu alaykum, <b>{html.escape(message.from_user.first_name)}</b>! 🎭\n\n"
        "<b>«Parodiya Tabrik & Mashhurlar Qutlovi»</b> botiga xush kelibsiz!\n\n"
        "✨ Bu yerda siz:\n"
        "• Mashhurlar tilida eksklyuziv tabriklar yaratishingiz;\n"
        "• 🖼 <b>Otkritka rasmlari</b> va 🎙 <b>Ovozli audiolarni</b> yuklab olishingiz;\n"
        "• 🧠 <b>«Qaysi personajsan?»</b> testidan o'tishingiz;\n"
        "• 📜 Do'stlaringizga <b>Rasmiy Parodiya Diplomlar</b> sovg'a qilishingiz;\n"
        "• 🎲 <b>Omad barabani</b> va 🔮 <b>Kunlik bashorat</b> olishingiz mumkin!\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(message.from_user.id))

# -------------------------------------------------------------
# 7. REPLY KEYBOARD DOIMIY TUGMALAR HANDLERLARI
# -------------------------------------------------------------
@router.message(F.text == "🎭 Tabrik Yaratish")
async def r_start_create(message: Message, state: FSMContext):
    await state.set_state(GreetingForm.choosing_category)
    text = "🎭 <b>1-Qadam: Qanday yo'nalishda matn yaratamiz?</b>\n\nQuyidagi toifalardan birini tanlang:"
    await message.answer(text, parse_mode="HTML", reply_markup=get_categories_keyboard())

@router.message(F.text == "🧠 Qaysi Personajsan?")
async def r_start_quiz(message: Message, state: FSMContext):
    await start_quiz_handler(message, state)

@router.message(F.text == "📜 Parodiya Sertifikat")
async def r_start_cert(message: Message, state: FSMContext):
    await start_cert_handler(message, state)

@router.message(F.text == "🎲 Omad Barabani")
async def r_roulette_spin(message: Message):
    await roulette_spin_handler(message)

@router.message(F.text == "🔮 Kunlik Bashorat")
async def r_daily_fortune(message: Message):
    await daily_fortune_handler(message)

@router.message(F.text == "🏆 Ballar & Profilim")
async def r_my_profile(message: Message):
    await my_profile_handler(message)

@router.message(F.text == "📂 Mening Tabriklarim")
async def r_my_greetings(message: Message):
    await my_greetings_handler(message)

@router.message(F.text == "🌟 VIP Jurnal Muqovasi")
async def r_vip_magazine(message: Message, state: FSMContext):
    await start_magazine_intro(message, state)

@router.message(F.text == "👑 Saytdagi Top Boyvachchalar")
@router.message(Command("top"))
async def r_top_leaderboard(message: Message, state: FSMContext):
    await state.clear()
    await show_leaderboard_summary(message)

@router.callback_query(F.data == "top_leaderboard")
async def cb_top_leaderboard(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_leaderboard_summary(call)

@router.message(F.text == "🌟 Barcha Personajlar")
async def r_all_characters(message: Message):
    await cmd_characters(message)

@router.message(F.text == "👑 Admin Panel")
async def r_admin_panel(message: Message, state: FSMContext):
    await cmd_admin(message, state)

# -------------------------------------------------------------
# 8. PROFIL, BALLAR VA REFERRAL TIZIMI
# -------------------------------------------------------------
@router.message(Command("profile"))
@router.callback_query(F.data == "my_profile")
async def my_profile_handler(event: TelegramObject):
    user = event.from_user
    profile = await database.get_user_profile(user.id)
    
    points = profile.get("points", 0)
    rank_title = profile.get("rank_title", "🥉 Oddiy Mehmon")
    ref_count = profile.get("ref_count", 0)
    greetings_count = profile.get("greetings_count", 0)
    next_rank = profile.get("next_rank", "")
    needed = profile.get("points_needed", 0)
    
    ref_link = f"https://t.me/parodiya_tabrik_uzbot?start=ref_{user.id}"
    share_text = (
        "🎭 Do'stim, bu botda mashhurlar tilida kulgili tabriklar, rasmiy diplomlar "
        "va 'Qaysi personajsan?' testi bor ekan! Juda qiziq, sen ham kirib ko'r: 👇\n"
        f"{ref_link}"
    )
    encoded_share = urllib.parse.quote(share_text)
    share_url = f"https://t.me/share/url?url={encoded_share}"

    text = (
        f"👤 <b>Foydalanuvchi Profili: {html.escape(user.first_name)}</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🎖 <b>Unvoningiz:</b> {rank_title}\n"
        f"⭐️ <b>To'plagan ballaringiz:</b> <b>{points} ball</b>\n"
        f"👥 <b>Taklif qilgan do'stlaringiz:</b> {ref_count} ta\n"
        f"🎁 <b>Yaratgan tabriklaringiz:</b> {greetings_count} ta\n\n"
    )
    
    if needed > 0:
        text += f"🚀 <b>Keyingi unvon:</b> {next_rank} <i>(yana {needed} ball kerak)</i>\n\n"
    else:
        text += f"🏆 <b>Siz eng yuqori VIP unvondagiz!</b>\n\n"

    text += (
        "💡 <b>Ballarni qanday to'plash mumkin?</b>\n"
        "• Har bir do'stni taklif qilganda: <b>+10 ball</b>\n"
        "• Tabrik yoki Sertifikat yaratganda: <b>+2 ball</b>\n"
        "• Viktorina testidan o'tganda: <b>+5 ball</b>\n"
        "• Kunlik bashoratni tekshirganda: <b>+1 ball</b>\n\n"
        f"🔗 <b>Sizning shaxsiy referral havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📲 Do'stlarni Taklif Qilish (+10 ball)", url=share_url)
            ],
            [
                InlineKeyboardButton(text="🏆 Top 10 Peshqadamlar", callback_data="leaderboard")
            ],
            [
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(Command("top"))
@router.callback_query(F.data == "leaderboard")
async def leaderboard_handler(event: TelegramObject):
    top_users = await database.get_leaderboard(limit=10)
    
    text = "🏆 <b>Eng Faol Foydalanuvchilar (Top 10 Peshqadamlar):</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    if not top_users:
        text += "<i>Hali peshqadamlar ro'yxati shakllanmagan. Birinchi bo'ling!</i>"
    else:
        for idx, u in enumerate(top_users):
            medal = medals[idx] if idx < len(medals) else "⭐️"
            uname = f"(@{u['username']})" if u.get("username") else ""
            fname = html.escape(u.get("first_name", "Foydalanuvchi"))
            text += (
                f"{medal} <b>{fname}</b> {uname}\n"
                f"   ⭐️ Ballar: <b>{u['points']}</b> | 👥 Do'stlar: <b>{u['ref_count']} ta</b>\n"
            )
            
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Mening Profilim", callback_data="my_profile")
            ],
            [
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

# -------------------------------------------------------------
# 9. KULGILI TEST (QAYSI PERSONAJSAN?)
# -------------------------------------------------------------
@router.message(Command("quiz"))
@router.callback_query(F.data == "start_quiz")
async def start_quiz_handler(event: TelegramObject, state: FSMContext):
    await state.clear()
    await state.set_state(QuizForm.q1)
    
    q1 = QUIZ_QUESTIONS[0]
    text = (
        "🧠 <b>«Qaysi Personajsan?» Kulgili Psixologik Test!</b>\n\n"
        f"<b>{q1['question']}</b>"
    )
    buttons = []
    for opt_key, opt_text, char_val in q1["options"]:
        buttons.append([InlineKeyboardButton(text=opt_text, callback_data=f"quiz_ans_1_{char_val}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(QuizForm.q1, F.data.startswith("quiz_ans_1_"))
async def quiz_q1_handler(call: CallbackQuery, state: FSMContext):
    chosen_char = call.data.replace("quiz_ans_1_", "")
    await state.update_data(ans1=chosen_char)
    await state.set_state(QuizForm.q2)
    
    q2 = QUIZ_QUESTIONS[1]
    text = (
        "🧠 <b>«Qaysi Personajsan?» Testi:</b>\n\n"
        f"<b>{q2['question']}</b>"
    )
    buttons = []
    for opt_key, opt_text, char_val in q2["options"]:
        buttons.append([InlineKeyboardButton(text=opt_text, callback_data=f"quiz_ans_2_{char_val}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@router.callback_query(QuizForm.q2, F.data.startswith("quiz_ans_2_"))
async def quiz_q2_handler(call: CallbackQuery, state: FSMContext):
    chosen_char = call.data.replace("quiz_ans_2_", "")
    await state.update_data(ans2=chosen_char)
    await state.set_state(QuizForm.q3)
    
    q3 = QUIZ_QUESTIONS[2]
    text = (
        "🧠 <b>«Qaysi Personajsan?» Testi:</b>\n\n"
        f"<b>{q3['question']}</b>"
    )
    buttons = []
    for opt_key, opt_text, char_val in q3["options"]:
        buttons.append([InlineKeyboardButton(text=opt_text, callback_data=f"quiz_ans_3_{char_val}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")])
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await call.answer()

@router.callback_query(QuizForm.q3, F.data.startswith("quiz_ans_3_"))
async def quiz_q3_handler(call: CallbackQuery, state: FSMContext):
    chosen_char = call.data.replace("quiz_ans_3_", "")
    data = await state.get_data()
    await state.clear()
    
    ans_list = [data.get("ans1", "boyvachcha"), data.get("ans2", "boyvachcha"), chosen_char]
    final_char = max(set(ans_list), key=ans_list.count)
    result_info = QUIZ_RESULTS.get(final_char, QUIZ_RESULTS["boyvachcha"])
    
    await database.add_user_points(call.from_user.id, 5, "Viktorina testi yakunlandi")
    
    share_text = (
        f"🧠 Men 'Parodiya Tabrik Boti'da testdan o'tdim va natijam: {result_info['title']} {result_info['icon']} bo'lib chiqdi!\n\n"
        "Sen kimsan? O'zingni tekshirib ko'r: 👇\n"
        f"https://t.me/parodiya_tabrik_uzbot?start=ref_{call.from_user.id}"
    )
    encoded_share = urllib.parse.quote(share_text)
    share_url = f"https://t.me/share/url?url={encoded_share}"
    
    res_text = (
        "🎉 <b>TEST NATIJANGIZ TAYYOR!</b>\n\n"
        f"<b>{result_info['title']}</b> {result_info['icon']}\n\n"
        f"📝 <i>{result_info['desc']}</i>\n\n"
        "⭐️ <i>Sizga testni bajarganingiz uchun <b>+5 ball</b> berildi!</i>"
    )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📲 Do'stlarga Ulashish: Sen kimsan?", url=share_url)
            ],
            [
                InlineKeyboardButton(text="🔄 Qayta Topshirish", callback_data="start_quiz"),
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )
    await call.message.edit_text(res_text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

# -------------------------------------------------------------
# 10. RASMIY PARODIYA SERTIFIKAT VA DIPLOM GENERATORI
# -------------------------------------------------------------
@router.message(Command("certificate"))
@router.callback_query(F.data == "start_cert")
async def start_cert_handler(event: TelegramObject, state: FSMContext):
    await state.clear()
    await state.set_state(CertificateForm.choosing_type)
    
    text = (
        "📜 <b>«Rasmiy Parodiya Sertifikat & Diplom» Generatori!</b>\n\n"
        "Yaqiningiz yoki do'stingizga qaysi unvonda rasmiy sertifikat sovg'a qilmoqchisiz?"
    )
    buttons = []
    for key, c in CERTIFICATES.items():
        buttons.append([InlineKeyboardButton(text=f"{c['icon']} {c['title']}", callback_data=f"cert_type_{key}")])
    buttons.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(CertificateForm.choosing_type, F.data.startswith("cert_type_"))
async def cert_type_chosen(call: CallbackQuery, state: FSMContext):
    cert_key = call.data.replace("cert_type_", "")
    await state.update_data(cert_key=cert_key)
    await state.set_state(CertificateForm.entering_recipient)
    
    cert_info = CERTIFICATES.get(cert_key, {})
    text = (
        f"Tanlangan diplom: <b>{cert_info.get('title')}</b> {cert_info.get('icon')}\n\n"
        "✍️ <b>Ushbu rasmiy sertifikat kimning nomiga rasmiylashtiriladi?</b>\n"
        "Do'stingizning yoki yaqiningizning <b>Ismini</b> yozib yuboring:\n"
        "<i>(Masalan: Jasurbek, Nodira, Sherzod)</i>"
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb)
    await call.answer()

@router.message(CertificateForm.entering_recipient)
async def cert_recipient_entered(message: Message, state: FSMContext):
    raw_name = message.text.strip()
    if len(raw_name) > 40:
        await message.answer("Iltimos, ismni qisqaroq kiriting (maksimal 40 harf):")
        return
    
    clean_name = html.escape(raw_name)
    await state.update_data(recipient_name=clean_name)
    await state.set_state(CertificateForm.entering_sender)
    
    text = (
        f"Ajoyib! Demak sertifikat <b>{clean_name}</b> nomiga bo'ladi.\n\n"
        "✍️ <b>Endi o'z ismingizni yoki kim taqdim etayotganini yozing:</b>\n"
        "<i>(Masalan: Do'stingiz Farhod, Kursdoshlar, Jamoa)</i>"
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=cancel_kb)

@router.message(CertificateForm.entering_sender)
async def cert_sender_entered(message: Message, state: FSMContext):
    raw_sender = message.text.strip()
    if len(raw_sender) > 50:
        await message.answer("Iltimos, ismni qisqaroq kiriting (maksimal 50 harf):")
        return
        
    sender_name = html.escape(raw_sender)
    data = await state.get_data()
    await state.clear()
    
    cert_key = data.get("cert_key", "boyvachcha")
    recipient_name = data.get("recipient_name", "Do'stim")
    
    cert_text = generate_certificate_text(cert_key, recipient_name, sender_name)
    
    # Bazaga saqlash
    g_id = await database.save_greeting(
        user_id=message.from_user.id,
        category="certificate",
        character=cert_key,
        recipient_name=recipient_name,
        profession="diplom",
        sender_name=sender_name,
        text=cert_text
    )
    
    await database.add_user_points(message.from_user.id, 2, "Sertifikat yaratildi")
    
    res_display = (
        "🎉 <b>Rasmiy Parodiya Sertifikati Tayyor Bo'ldi!</b>\n\n"
        "📋 <i>Quyidagi sertifikat ustiga 1 marta bosib nusxa oling yoki pastdagi tugmalar orqali rasm/audio qilib yuklab oling:</i>\n\n"
        f"<pre><code class=\"language-text\">{cert_text}</code></pre>\n\n"
        "⭐️ <i>Sizga sertifikat yaratganingiz uchun <b>+2 ball</b> berildi!</i>"
    )
    
    await message.answer(res_display, parse_mode="HTML", reply_markup=get_result_keyboard(f"{recipient_name} uchun diplom!", cert_text, g_id))

# -------------------------------------------------------------
# 11. TAVAKKAL OMAD BARABANI (ROULETTE)
# -------------------------------------------------------------
@router.message(Command("roulette"))
@router.callback_query(F.data == "roulette_spin")
async def roulette_spin_handler(event: TelegramObject):
    spin_msg_text = "🎰 <b>Omad Barabani aylanmoqda...</b>\n🍒 🍋 💎 7️⃣ 🔔..."
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(spin_msg_text, parse_mode="HTML")
        await event.answer()
        target_message = event.message
    else:
        target_message = await event.answer(spin_msg_text, parse_mode="HTML")
        
    await asyncio.sleep(1.0)
    
    roulette_data = generate_random_roulette()
    await database.add_user_points(event.from_user.id, 1, "Omad barabani aylantirildi")
    
    g_id = await database.save_greeting(
        user_id=event.from_user.id,
        category="roulette",
        character="roulette",
        recipient_name="Do'stim",
        profession="general",
        sender_name="Omad Barabani",
        text=roulette_data["text"]
    )
    
    res_text = (
        f"🎉 <b>DJЕКPOT! BARABAN TO'XTADI!</b> {roulette_data['icon']}\n\n"
        f"🎭 <b>Tasodifiy Personaj:</b> {roulette_data['character']}\n\n"
        f"<pre><code class=\"language-text\">{roulette_data['text']}</code></pre>\n\n"
        "⭐️ <i>Sizga omad barabani uchun <b>+1 ball</b> berildi!</i>"
    )
    
    await target_message.edit_text(res_text, parse_mode="HTML", reply_markup=get_result_keyboard("Omadli parodiya!", roulette_data['text'], g_id))

# -------------------------------------------------------------
# 12. KUNLIK KULGILI BASHORAT (GOROSKOP)
# -------------------------------------------------------------
@router.message(Command("fortune"))
@router.callback_query(F.data == "daily_fortune")
async def daily_fortune_handler(event: TelegramObject):
    user = event.from_user
    can_claim = await database.can_claim_daily_fortune(user.id)
    fortune_text = get_daily_fortune(user.id)
    
    if can_claim:
        await database.claim_daily_fortune(user.id)
        bonus_notice = "⭐️ <b>Bugungi faollik uchun sizga +1 ball berildi! 🎁</b>\nErtaga yangi bashorat olish uchun yana kiring!"
    else:
        bonus_notice = "ℹ️ <i>Siz bugungi kunlik bashorat va ballingizni olgansiz. Yangi bashorat ertaga yangilanadi!</i>"
        
    full_text = (
        "🔮 <b>Bugungi Kulgili Parodiya Bashoratingiz:</b>\n\n"
        f"{fortune_text}\n\n"
        f"{bonus_notice}"
    )
    
    share_content = (
        f"{fortune_text}\n\n"
        "🔮 Sizning bugungi bashoratingiz qanday? Botga kirib bilib oling: @parodiya_tabrik_uzbot"
    )
    encoded_share = urllib.parse.quote(share_content)
    share_url = f"https://t.me/share/url?url=https://t.me/parodiya_tabrik_uzbot&text={encoded_share}"
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📲 Bashoratni Do'stlarga Ulashish", url=share_url)
            ],
            [
                InlineKeyboardButton(text="👤 Mening Profilim", callback_data="my_profile"),
                InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
            ]
        ]
    )
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(full_text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(full_text, parse_mode="HTML", reply_markup=kb)

# -------------------------------------------------------------
# 13. RASM (OTKRITKA) VA AUDIO (OVOZLI) YUKLAB OLISH (5,000 SO'M)
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("get_image_"))
async def get_image_callback(call: CallbackQuery):
    greeting_id_str = call.data.replace("get_image_", "")
    await call.answer("🖼 Otkritka rasmi tayyorlanmoqda...", show_alert=False)
    
    g_info = None
    if greeting_id_str.isdigit():
        g_info = await database.get_greeting_by_id(int(greeting_id_str))
        
    if not g_info:
        # Fallback oxirgi tabrik
        greetings = await database.get_user_greetings(call.from_user.id, limit=1)
        if greetings:
            g_info = greetings[0]
            
    if not g_info:
        await call.message.answer("❌ Otkritka uchun tabrik matni topilmadi. Avval yangi tabrik yarating.")
        return
        
    char_name = CHARACTERS.get(g_info["character"], {}).get("name", g_info["character"])
    rec_name = g_info.get("recipient_name", "Do'stim")
    s_name = g_info.get("sender_name", "Qadrdoningiz")
    msg_text = g_info.get("generated_text", "")
    
    output_png = f"postcard_{call.from_user.id}_{int(time.time())}.png"
    try:
        media_generator.generate_postcard_image(char_name, rec_name, msg_text, s_name, output_png)
        if os.path.exists(output_png):
            caption = (
                f"🖼 <b>{rec_name} uchun eksklyuziv tabrik otkritkasi!</b>\n"
                f"🎭 Obraz: <b>{char_name}</b>\n\n"
                "👉 @parodiya_tabrik_uzbot — Bepul parodiya tabriklar"
            )
            await call.message.answer_photo(
                photo=FSInputFile(output_png),
                caption=caption,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Rasm yaratishda xatolik: {e}", exc_info=True)
        await call.message.answer(f"❌ Rasm tayyorlashda xatolik yuz berdi: {e}")
    finally:
        if os.path.exists(output_png):
            try:
                os.remove(output_png)
            except Exception:
                pass

@router.callback_query(F.data.startswith("get_audio_"))
async def get_audio_callback(call: CallbackQuery):
    greeting_id_str = call.data.replace("get_audio_", "")
    user_id = call.from_user.id
    await call.answer("🎙 Ovozli tabrik tayyorlanmoqda...", show_alert=False)
    await send_generated_audio(call.bot, user_id, greeting_id_str, call.message)

# -------------------------------------------------------------
# 14. VIP "YIL ODAMI" JURNALI MUQOVASI (FORBES / 5,000 SO'M YOKI 25 BALL)
# -------------------------------------------------------------
@router.message(Command("magazine"))
@router.callback_query(F.data == "start_magazine")
async def start_magazine_intro(event: TelegramObject, state: FSMContext):
    await state.clear()
    user_id = event.from_user.id
    profile = await database.get_user_profile(user_id)
    pts = profile.get("points", 0)
    
    intro_text = (
        "🌟 <b>«FORBES VIP — YIL ODAMLARI» Jurnali Muqovasi!</b> 📸\n\n"
        "Do'stingiz yoki o'zingizning rasmingiz tushirilgan, hashamatli xalqaro jurnal muqovasi (Forbes / VIP Uzbekistan uslubida)!\n\n"
        "✨ <b>Imkoniyatlari:</b>\n"
        "• 📸 <b>Shaxsiy fotosurat</b> joylanadi;\n"
        "• 👑 <b>Maxsus unvon:</b> Saxiy boyvachcha, Qadrli do'st, Go'zal malika, Tezkor haydovchi va boshqalar;\n"
        "• 📰 <b>Shov-shuvli sarlavhalar</b>, shtrix-kod va oltin sifat muhri;\n"
        "• 📐 <b>1080x1440 HD sifat</b> (Instagram Story va Telegram profil uchun tayyor!);\n\n"
        "💰 <b>Xizmat narxi:</b> Ixtiyoriy summa (kamida 1,000 so'm) yoki <b>25 ball</b> referral ballari!\n"
        f"⭐️ Sizdagi ballar: <b>{pts} ball</b>\n\n"
        "Davom etish uchun variantni tanlang:"
    )
    
    buttons = [
        [
            InlineKeyboardButton(text="💎 25 Ball evaziga ochish", callback_data="mag_pay_pts")
        ],
        [
            InlineKeyboardButton(text="🧾 To'lov qilish (Kamida 1,000 so'm ixtiyoriy)", callback_data="mag_pay_chk")
        ]
    ]
    if config.is_admin(user_id):
        buttons.append([InlineKeyboardButton(text="👑 Bepul Test Qilish (Admin)", callback_data="mag_free_admin")])
    buttons.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if isinstance(event, CallbackQuery):
        await event.message.answer(intro_text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(intro_text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "mag_free_admin")
async def mag_free_admin_cb(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Faqat admin uchun!", show_alert=True)
        return
    await call.answer("👑 Admin rejimi faollashdi!", show_alert=False)
    await start_magazine_form(call.message, state)

@router.callback_query(F.data == "mag_pay_pts")
async def mag_pay_points_cb(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    profile = await database.get_user_profile(user_id)
    pts = profile.get("points", 0)
    
    if pts < 25:
        await call.answer(
            f"❌ Ballaringiz yetarli emas! Sizda {pts} ball bor (kamida 25 ball kerak).\nDo'stlaringizni taklif qiling (+10 ball) yoki ixtiyoriy summa (kamida 1,000 so'm) to'lang.",
            show_alert=True
        )
        return
        
    await database.add_user_points(user_id, -25, "VIP Jurnal muqovasi xarid qilindi")
    await call.answer("✅ 25 ball yechildi! Jurnal yaratish boshlandi.", show_alert=False)
    await start_magazine_form(call.message, state)

@router.callback_query(F.data == "mag_pay_chk")
async def mag_pay_check_cb(call: CallbackQuery, state: FSMContext):
    await state.set_state(MagazinePaymentForm.uploading_check)
    card_number = getattr(config, "PAYMENT_CARD", "4067070008610359")
    text = (
        "🧾 <b>VIP Jurnal Muqovasi Uchun To'lov</b>\n\n"
        "1. Quyidagi karta raqamiga <b>ixtiyoriy summa (kamida 1,000 so'm)</b> o'tkazing:\n"
        f"💳 <code>{card_number}</code>\n"
        "<i>(Karta raqami ustiga bossangiz, avtomatik nusxalanadi 📲)</i>\n"
        "To'lov ilovalari: <b>Click / Payme / Uzum / Paynet</b>\n\n"
        "2. To'lov amalga oshirilgach, chekning <b>skrinshotini</b> yoki <b>faylini</b> shu yerga yuboring.\n\n"
        "<i>Chek adminga tekshirish uchun yuboriladi va tasdiqlanishi bilan jurnal yaratish darhol ochiladi!</i>"
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb)
    await call.answer()

@router.message(MagazinePaymentForm.uploading_check, F.photo | F.document)
async def mag_check_received(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    file_type = "photo" if message.photo else "document"
    min_amount = getattr(config, "MIN_PAYMENT_AMOUNT", 1000)
    
    # 1. Chekni ma'lumotlar bazasiga xavfsiz saqlaymiz (hech narsa yo'qolmaydi!)
    receipt_id = await database.save_payment_receipt(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        file_id=file_id,
        file_type=file_type,
        amount=min_amount
    )
    
    admin_caption = (
        f"🧾 <b>Yangi VIP Jurnal To'lov Cheki #{receipt_id}!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{html.escape(message.from_user.full_name)}</b>\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"🔗 Username: @{message.from_user.username or 'mavjud_emas'}\n"
        f"💵 Summa: <b>Ixtiyoriy to'lov (kamida {min_amount:,} so'm)</b>\n"
        f"📅 Vaqti: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        "To'lovni tasdiqlaysizmi?"
    )
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash va Jurnalni Ochish", callback_data=f"adm_mag_app_{receipt_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_mag_rej_{receipt_id}")
            ]
        ]
    )
    try:
        if message.photo:
            await bot.send_photo(
                chat_id=config.ADMIN_ID,
                photo=file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        elif message.document:
            await bot.send_document(
                chat_id=config.ADMIN_ID,
                document=file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        await message.answer(
            f"✅ <b>Chekingiz qabul qilindi (Chek #{receipt_id})!</b>\n"
            "Administrator tekshirib tasdiqlashi bilan jurnal muqovasi yaratish ochiladi.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Adminga chek yuborishda xatolik: {e}", exc_info=True)
        await message.answer(f"⚠️ Chekni adminga jo'natishda xatolik yuz berdi: {e}")

@router.message(MagazinePaymentForm.uploading_check)
async def mag_check_fallback(message: Message):
    await message.answer(
        "⚠️ <b>Iltimos, to'lov chekining skrinshotini (rasm yoki fayl ko'rinishida) yuboring!</b>\n"
        "Bekor qilish uchun /cancel yoki pastdagi menyudan foydalaning.",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("adm_mag_app_"))
async def adm_mag_app_cb(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    id_param = int(call.data.replace("adm_mag_app_", ""))
    receipt = await database.update_receipt_status(id_param, "approved")
    target_user_id = receipt["user_id"] if receipt else id_param
    
    await call.answer("✅ Chek tasdiqlandi!", show_alert=True)
    
    after_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Keyingi Kutilayotgan Chek", callback_data="adm_view_pending_0"),
                InlineKeyboardButton(text="💳 To'lovlar Markazi", callback_data="admin_payments")
            ]
        ]
    )
    
    try:
        await call.message.edit_caption(
            caption=(call.message.caption or "") + f"\n\n✅ <b>ADMIN TASDIQLADI! (Chek #{id_param})</b>",
            parse_mode="HTML",
            reply_markup=after_kb
        )
    except Exception:
        pass
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🚀 Jurnal Muqovasini Yaratish", callback_data="mag_start_approved")]]
    )
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 <b>Tabriklaymiz! To'lovingiz (Chek #{id_param}) muvaffaqiyatli tasdiqlandi!</b>\n\nEndi VIP Jurnal muqovasini yaratish uchun quyidagi tugmani bosing:",
            parse_mode="HTML",
            reply_markup=kb
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_mag_rej_"))
async def adm_mag_rej_cb(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    id_param = int(call.data.replace("adm_mag_rej_", ""))
    receipt = await database.update_receipt_status(id_param, "rejected")
    target_user_id = receipt["user_id"] if receipt else id_param
    
    await call.answer("❌ Chek rad etildi.", show_alert=True)
    
    after_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Keyingi Kutilayotgan Chek", callback_data="adm_view_pending_0"),
                InlineKeyboardButton(text="💳 To'lovlar Markazi", callback_data="admin_payments")
            ]
        ]
    )
    
    try:
        await call.message.edit_caption(
            caption=(call.message.caption or "") + f"\n\n❌ <b>TO'LOV RAD ETILDI! (Chek #{id_param})</b>",
            parse_mode="HTML",
            reply_markup=after_kb
        )
    except Exception:
        pass
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"❌ <b>Kechirasiz, yuborgan to'lov chekingiz (Chek #{id_param}) tasdiqlanmadi.</b>\nIltimos, haqiqiy to'lov skrinshotini yuboring yoki adminga murojaat qiling.",
            parse_mode="HTML"
        )
    except Exception:
        pass

@router.callback_query(F.data == "mag_start_approved")
async def mag_start_approved_cb(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await start_magazine_form(call.message, state)

async def start_magazine_form(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(MagazineForm.uploading_photo)
    prompt = (
        "📸 <b>1-Qadam: Jurnal muqovasi uchun fotosurat yuboring!</b>\n\n"
        "Do'stingiz yoki o'zingizning yaxshi ko'ringan rasmingizni (rasm yoki fayl ko'rinishida) yuboring."
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await message.answer(prompt, parse_mode="HTML", reply_markup=cancel_kb)

@router.message(MagazineForm.uploading_photo, F.photo | F.document)
async def mag_photo_received(message: Message, state: FSMContext, bot: Bot):
    temp_photo = f"user_mag_photo_{message.from_user.id}_{int(time.time())}.jpg"
    try:
        if message.photo:
            photo = message.photo[-1]
            await bot.download(photo, destination=temp_photo)
        elif message.document:
            await bot.download(message.document, destination=temp_photo)
    except Exception as e:
        logger.error(f"Rasm yuklab olishda xatolik: {e}")
        await message.answer("❌ Rasmni yuklab olishda xatolik bo'ldi. Iltimos, qaytadan boshqa rasm yuborib ko'ring.")
        return
        
    await state.update_data(photo_path=temp_photo)
    await state.set_state(MagazineForm.entering_name)
    
    prompt = (
        "✍️ <b>2-Qadam: Jurnal muqovasida chiqadigan Ism va Familiyani yozing:</b>\n\n"
        "Masalan: <code>Sardorbek Rahimov</code> yoki <code>Madina Aliyeva</code>"
    )
    await message.answer(prompt, parse_mode="HTML")

@router.message(MagazineForm.uploading_photo)
async def mag_photo_fallback(message: Message):
    await message.answer("⚠️ <b>Iltimos, fotosurat (rasm yoki rasm fayli) yuboring!</b>", parse_mode="HTML")

@router.message(MagazineForm.entering_name, F.text)
async def mag_name_received(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 40:
        await message.answer("⚠️ Iltimos, ismni to'g'ri kiriting (2 tadan 40 ta harfgacha).")
        return
        
    await state.update_data(person_name=name)
    await state.set_state(MagazineForm.choosing_title)
    
    prompt = (
        f"👑 <b>3-Qadam: {html.escape(name)} uchun jurnal unvonini tanlang:</b>\n\n"
        "Quyidagi mashhur unvonlardan birini bosing:"
    )
    
    buttons = []
    for t_key, t_info in MAGAZINE_TITLES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{t_info['icon']} {t_info['title']}",
                callback_data=f"mag_title_{t_key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(prompt, parse_mode="HTML", reply_markup=kb)

@router.callback_query(MagazineForm.choosing_title, F.data.startswith("mag_title_"))
async def mag_title_chosen(call: CallbackQuery, state: FSMContext, bot: Bot):
    title_key = call.data.replace("mag_title_", "")
    title_info = MAGAZINE_TITLES.get(title_key, list(MAGAZINE_TITLES.values())[0])
    
    data = await state.get_data()
    await state.clear()
    
    photo_path = data.get("photo_path", "")
    person_name = data.get("person_name", "Yil Qahramoni")
    
    wait_msg = await call.message.answer("⏳ <i>VIP Forbes Jurnal muqovangiz yuqori sifatda tayyorlanmoqda (1080x1440)...</i>", parse_mode="HTML")
    await call.answer()
    
    output_jpg = f"magazine_{call.from_user.id}_{int(time.time())}.jpg"
    try:
        await asyncio.to_thread(
            media_generator.generate_magazine_cover,
            photo_path,
            person_name,
            title_info,
            output_jpg
        )
        
        if os.path.exists(output_jpg):
            caption = (
                f"🌟 <b>{html.escape(person_name)} uchun maxsus FORBES VIP Jurnal Muqovasi!</b> 👑\n\n"
                f"🏆 <b>Unvon:</b> {title_info['icon']} {title_info['title']}\n"
                f"💎 <b>Kategoriya:</b> {title_info['subtitle']}\n\n"
                "📲 <i>Instagram Stories va Telegram avatarka uchun tayyor!</i>\n"
                "👉 @parodiya_tabrik_uzbot"
            )
            
            # 1. Rasm ko'rinishida jo'natish
            await bot.send_photo(
                chat_id=call.from_user.id,
                photo=FSInputFile(output_jpg),
                caption=caption,
                parse_mode="HTML"
            )
            # 2. HD fayl ko'rinishida jo'natish
            await bot.send_document(
                chat_id=call.from_user.id,
                document=FSInputFile(output_jpg, filename=f"Forbes_VIP_{person_name}.jpg"),
                caption="📥 Yuqori HD sifatdagi fayl (bosmaga yoki statusga)",
                parse_mode="HTML"
            )
            
            await database.add_user_points(call.from_user.id, 5, "VIP Jurnal muqovasi yaratildi")
            
            share_text = f"Do'stim {person_name} Forbes VIP jurnali muqovasiga chiqdi! Sen ham o'zingnikini yarat: https://t.me/parodiya_tabrik_uzbot"
            share_url = f"https://t.me/share/url?url=https://t.me/parodiya_tabrik_uzbot&text={urllib.parse.quote(share_text)}"
            
            finish_kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📲 Do'stlarga Ulashish", url=share_url)],
                    [InlineKeyboardButton(text="🌟 Yana Boshqa Jurnal Yaratish", callback_data="start_magazine")],
                    [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")]
                ]
            )
            await call.message.answer("🎉 <b>Jurnalingiz tayyor bo'ldi!</b> Do'stlaringizga ulashing yoki statusga qo'ying:", parse_mode="HTML", reply_markup=finish_kb)
            
            try:
                await wait_msg.delete()
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Jurnal yaratishda xatolik: {e}", exc_info=True)
        await call.message.answer(f"❌ Jurnal yaratishda xatolik yuz berdi: {e}")
    finally:
        if photo_path and os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except Exception:
                pass
        if os.path.exists(output_jpg):
            try:
                os.remove(output_jpg)
            except Exception:
                pass

# -------------------------------------------------------------
# 13.5 SAYT REYTINGI — TOP BOYVACHCHALAR & SHON-SHARAF TAXTASI
# -------------------------------------------------------------
LEADERBOARD_TITLES = {
    "boyvachcha": {"title": "Toshkentning Eng Katta Boyvachchasi", "icon": "👑"},
    "homiy": {"title": "Choyxona Bosh Homiysi", "icon": "☕️"},
    "milliarder": {"title": "Kelajak Milliarderi & Shef", "icon": "💼"},
    "saxiy": {"title": "Poytaxtning Eng Saxiy Insoni", "icon": "💎"},
    "qahramon": {"title": "Yil Qahramoni & Do'stlar Sarvari", "icon": "🌟"},
    "tezkor": {"title": "Poytaxtning Eng Tezkor Do'sti", "icon": "🏎"}
}

async def show_leaderboard_summary(event: TelegramObject):
    entries = await database.get_top_leaderboard(limit=5)
    stats = await database.get_leaderboard_stats()
    
    total_part = stats.get("total_participants", 0)
    top_record = stats.get("highest_donation", 0)
    
    text = (
        "👑 <b>FORBES UZBEKISTAN — TOP BOYVACHCHALAR REYTINGI!</b> 🏆\n\n"
        "Do'stini eng ko'p qo'llab-quvvatlagan, qadriga yetgan va pul o'tkazgan insonlar jonli veb-saytimiz shon-sharaf taxtasida <b>1-o'rin, 2-o'rin, 3-o'rin</b> bo'lib turishadi!\n\n"
        f"👥 <b>Jami boyvachchalar:</b> {total_part} ta\n"
        f"🥇 <b>1-O'rin rekordi:</b> {top_record:,} so'm\n\n"
        "🔥 <b>Hozirgi Top Yetakchilar:</b>\n"
    )
    
    if entries:
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for idx, item in enumerate(entries[:5]):
            m_icon = medals[idx] if idx < len(medals) else "⭐️"
            name = html.escape(item.get("friend_name", "Noma'lum"))
            amt = item.get("amount", 0)
            u_title = html.escape(item.get("friend_title", "Boyvachcha"))
            text += f"{m_icon} <b>{name}</b> ({amt:,} so'm) — <i>{u_title}</i>\n"
    else:
        text += "<i>Hozircha reyting bo'sh! Birinchi bo'lib do'stingizni #1 o'ringa chiqaring!</i>\n"
        
    text += (
        "\n🌐 <b>Jonli veb-sayt:</b> <code>https://telegrambot-wtzt.onrender.com/leaderboard</code>\n\n"
        "<i>Siz ham do'stingizning rasmi va ismini saytga joylab, #1 o'ringa chiqarmoqchimisiz?</i>"
    )
    
    buttons = [
        [
            InlineKeyboardButton(text="🌐 Saytda Jonli Ko'rish (Web)", url="https://telegrambot-wtzt.onrender.com/leaderboard")
        ],
        [
            InlineKeyboardButton(text="🚀 Do'stimni Saytga Joylash (+ O'rin Olish)", callback_data="start_submit_leaderboard")
        ]
    ]
    if config.is_admin(event.from_user.id):
        buttons.append([InlineKeyboardButton(text="👑 Bepul Test Qilish (Admin)", callback_data="ldb_free_admin")])
    buttons.append([
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="top_leaderboard"),
        InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")
    ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "start_submit_leaderboard")
async def start_submit_leaderboard_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(LeaderboardForm.uploading_photo)
    
    prompt = (
        "📸 <b>1-Qadam: Do'stingizning fotosuratini yuboring!</b>\n\n"
        "Saytda hamma ko'rishi uchun do'stingizning (yoki o'zingizning) yaxshi tushgan rasmini (rasm yoki fayl ko'rinishida) yuboring."
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await call.message.answer(prompt, parse_mode="HTML", reply_markup=cancel_kb)
    await call.answer()

@router.callback_query(F.data == "ldb_free_admin")
async def ldb_free_admin_cb(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Faqat admin uchun!", show_alert=True)
        return
        
    sample_names = ["Jasur Bekmirzayev", "Sardor Rahimov", "Madina Aliyeva", "Bobur Mirzayev"]
    sample_titles = ["Toshkentning Eng Katta Boyvachchasi", "Choyxona Bosh Homiysi", "Kelajak Milliarderi & Shef", "Poytaxtning Eng Saxiy Insoni"]
    sample_amts = [150000, 80000, 45000, 20000]
    
    stats = await database.get_leaderboard_stats()
    idx = stats["total_participants"] % len(sample_names)
    
    await database.add_leaderboard_entry(
        user_id=call.from_user.id,
        friend_name=sample_names[idx],
        friend_title=sample_titles[idx],
        image_filename="",
        amount=sample_amts[idx],
        status="approved",
        receipt_id=0
    )
    
    await call.answer(f"👑 Test: {sample_names[idx]} saytga joylandi ({sample_amts[idx]:,} so'm)!", show_alert=True)
    await show_leaderboard_summary(call)

@router.message(LeaderboardForm.uploading_photo, F.photo | F.document)
async def ldb_photo_received(message: Message, state: FSMContext, bot: Bot):
    filename = f"friend_{message.from_user.id}_{int(time.time())}.jpg"
    dest_path = os.path.join(SITE_PHOTOS_DIR, filename)
    
    try:
        if message.photo:
            photo = message.photo[-1]
            await bot.download(photo, destination=dest_path)
        elif message.document:
            await bot.download(message.document, destination=dest_path)
    except Exception as e:
        logger.error(f"Reyting rasmini yuklashda xatolik: {e}")
        await message.answer("❌ Rasmni yuklab olishda xatolik bo'ldi. Iltimos, qaytadan boshqa rasm yuborib ko'ring.")
        return
        
    await state.update_data(image_filename=filename)
    await state.set_state(LeaderboardForm.entering_name)
    
    prompt = (
        "✍️ <b>2-Qadam: Do'stingizning Ism va Familiyasini yozing:</b>\n\n"
        "Sayt shon-sharaf taxtasida shu ism chiqadi. Masalan: <code>Jasur Bekmirzayev</code>"
    )
    await message.answer(prompt, parse_mode="HTML")

@router.message(LeaderboardForm.uploading_photo)
async def ldb_photo_fallback(message: Message):
    await message.answer("⚠️ <b>Iltimos, do'stingizning fotosuratini (rasm yoki rasm fayli) yuboring!</b>", parse_mode="HTML")

@router.message(LeaderboardForm.entering_name, F.text)
async def ldb_name_received(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 45:
        await message.answer("⚠️ Iltimos, ismni to'g'ri kiriting (2 tadan 45 ta harfgacha).")
        return
        
    await state.update_data(friend_name=name)
    await state.set_state(LeaderboardForm.choosing_title)
    
    prompt = (
        f"👑 <b>3-Qadam: {html.escape(name)} uchun rasmiy unvon tanlang:</b>\n\n"
        "Quyidagi unvonlardan birini bosing:"
    )
    buttons = []
    for t_key, t_info in LEADERBOARD_TITLES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{t_info['icon']} {t_info['title']}",
                callback_data=f"ldb_title_{t_key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(prompt, parse_mode="HTML", reply_markup=kb)

@router.callback_query(LeaderboardForm.choosing_title, F.data.startswith("ldb_title_"))
async def ldb_title_chosen(call: CallbackQuery, state: FSMContext):
    t_key = call.data.replace("ldb_title_", "")
    t_info = LEADERBOARD_TITLES.get(t_key, list(LEADERBOARD_TITLES.values())[0])
    friend_title = t_info["title"]
    
    await state.update_data(friend_title=friend_title)
    await state.set_state(LeaderboardForm.uploading_check)
    
    card_number = getattr(config, "PAYMENT_CARD", "4067070008610359")
    min_amount = getattr(config, "MIN_PAYMENT_AMOUNT", 1000)
    
    prompt = (
        "🧾 <b>4-Qadam: Saytdagi O'rin Uchun To'lov</b>\n\n"
        f"1. Karta raqamiga <b>ixtiyoriy summa (kamida {min_amount:,} so'm)</b> o'tkazing:\n"
        f"💳 <code>{card_number}</code>\n"
        "<i>(Karta raqami ustiga bossangiz, avtomatik nusxalanadi 📲)</i>\n"
        "To'lov ilovalari: <b>Click / Payme / Uzum / Paynet</b>\n\n"
        "🔥 <b>QOIDA:</b> Qancha ko'p summa o'tkazsangiz, do'stingiz sayt reytingida shuncha yuqori (hatto <b>🥇 1-O'RINGA!</b>) chiqadi!\n\n"
        "2. To'lov amalga oshirilgach, chekning <b>skrinshotini</b> yoki <b>faylini</b> shu yerga yuboring.\n\n"
        "<i>Chek adminga tekshirish uchun yuboriladi va tasdiqlanishi bilan do'stingiz darhol jonli saytga joylanadi!</i>"
    )
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await call.message.edit_text(prompt, parse_mode="HTML", reply_markup=cancel_kb)
    await call.answer()

@router.message(LeaderboardForm.uploading_check, F.photo | F.document)
async def ldb_check_received(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    
    friend_name = data.get("friend_name", "Yil Boyvachchasi")
    friend_title = data.get("friend_title", "Do'stlar Sarvari")
    image_filename = data.get("image_filename", "")
    
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    file_type = "photo" if message.photo else "document"
    min_amount = getattr(config, "MIN_PAYMENT_AMOUNT", 1000)
    
    receipt_id = await database.save_payment_receipt(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        file_id=file_id,
        file_type=file_type,
        amount=min_amount
    )
    
    entry_id = await database.add_leaderboard_entry(
        user_id=message.from_user.id,
        friend_name=friend_name,
        friend_title=friend_title,
        image_filename=image_filename,
        amount=min_amount,
        status="pending",
        receipt_id=receipt_id
    )
    
    admin_caption = (
        f"👑 <b>YANGI SAYT REYTINGI TALABI! (Do'stini saytga joylamoqchi)</b>\n\n"
        f"👤 <b>Yuboruvchi:</b> {html.escape(message.from_user.full_name)} (ID: <code>{message.from_user.id}</code>)\n"
        f"📸 <b>Saytga chiqadigan do'st:</b> <b>{html.escape(friend_name)}</b>\n"
        f"👑 <b>Unvoni:</b> {html.escape(friend_title)}\n"
        f"🧾 <b>Chek ID:</b> #{receipt_id}\n\n"
        "<i>To'lov summasiga qarab saytda o'rni belgilanadi. Chekdagi summani tasdiqlang:</i>"
    )
    
    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ 1,000 so'm", callback_data=f"adm_ldb_app_{entry_id}_1000"),
                InlineKeyboardButton(text="✅ 5,000 so'm", callback_data=f"adm_ldb_app_{entry_id}_5000")
            ],
            [
                InlineKeyboardButton(text="✅ 10,000 so'm", callback_data=f"adm_ldb_app_{entry_id}_10000"),
                InlineKeyboardButton(text="✅ 20,000 so'm", callback_data=f"adm_ldb_app_{entry_id}_20000")
            ],
            [
                InlineKeyboardButton(text="✅ 50,000 so'm", callback_data=f"adm_ldb_app_{entry_id}_50000"),
                InlineKeyboardButton(text="✅ 100,000 so'm (Qirol)", callback_data=f"adm_ldb_app_{entry_id}_100000")
            ],
            [
                InlineKeyboardButton(text="✍️ Boshqa Summa Kiritish", callback_data=f"adm_ldb_custom_{entry_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_ldb_rej_{entry_id}")
            ]
        ]
    )
    
    try:
        if message.photo:
            await bot.send_photo(
                chat_id=config.ADMIN_ID,
                photo=file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        else:
            await bot.send_document(
                chat_id=config.ADMIN_ID,
                document=file_id,
                caption=admin_caption,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        await message.answer(
            f"✅ <b>Chekingiz qabul qilindi (Chek #{receipt_id})!</b>\n\n"
            f"Administrator to'lovni tasdiqlashi bilan <b>{html.escape(friend_name)}</b> darhol sayt shon-sharaf taxtasiga chiqadi.\n"
            "🌐 Sayt havolasi: https://telegrambot-wtzt.onrender.com/leaderboard",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Adminga reyting chekini jo'natishda xatolik: {e}")
        await message.answer(f"⚠️ Chekni adminga jo'natishda xatolik yuz berdi: {e}")

@router.callback_query(F.data.startswith("adm_ldb_app_"))
async def adm_ldb_app_cb(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    parts = call.data.replace("adm_ldb_app_", "").split("_")
    entry_id = int(parts[0])
    amount = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1000
    
    entry = await database.update_leaderboard_status(entry_id, status="approved", amount=amount)
    if not entry:
        await call.answer("Yozuv topilmadi!", show_alert=True)
        return
        
    if entry.get("receipt_id"):
        await database.update_receipt_status(entry["receipt_id"], status="approved")
        
    await call.answer(f"✅ {amount:,} so'm bilan saytga joylandi!", show_alert=True)
    
    try:
        await call.message.edit_caption(
            caption=(call.message.caption or "") + f"\n\n✅ <b>ADMIN TASDIQLADI! SAYTGA JOYLANDI: {amount:,} SO'M</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    user_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Saytda Ko'rish (Jonli)", url="https://telegrambot-wtzt.onrender.com/leaderboard")]
        ]
    )
    try:
        await bot.send_message(
            chat_id=entry["user_id"],
            text=(
                f"🎉 <b>Tabriklaymiz! Do'stingiz «{html.escape(entry['friend_name'])}» Forbes Uzbekistan sayt reytingiga muvaffaqiyatli joylashtirildi!</b>\n\n"
                f"💰 <b>Kiritilgan summa:</b> {amount:,} so'm\n"
                f"👑 <b>Unvoni:</b> {html.escape(entry['friend_title'])}\n\n"
                "Quyidagi havola orqali o'zingiz va do'stingiz saytda qaysi o'rindaligini ko'ring:"
            ),
            parse_mode="HTML",
            reply_markup=user_kb
        )
    except Exception as e:
        logger.warning(f"Foydalanuvchiga tasdiq xabarini yuborishda xatolik: {e}")

@router.callback_query(F.data.startswith("adm_ldb_custom_"))
async def adm_ldb_custom_cb(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    entry_id = int(call.data.replace("adm_ldb_custom_", ""))
    await state.update_data(target_entry_id=entry_id)
    await state.set_state(AdminCustomAmountForm.entering_amount)
    
    await call.message.answer(
        f"✍️ <b>Yozuv #{entry_id} uchun tasdiqlanadigan summani kiriting:</b>\n"
        "Faqat son yozing, masalan: <code>15000</code> yoki <code>250000</code>",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(AdminCustomAmountForm.entering_amount, F.text)
async def adm_custom_amount_received(message: Message, state: FSMContext, bot: Bot):
    if not config.is_admin(message.from_user.id):
        return
        
    raw_text = message.text.strip().replace(" ", "").replace(",", "")
    if not raw_text.isdigit():
        await message.answer("⚠️ Iltimos, faqat musbat son kiriting (masalan: 15000).")
        return
        
    amount = int(raw_text)
    data = await state.get_data()
    await state.clear()
    
    entry_id = data.get("target_entry_id", 0)
    entry = await database.update_leaderboard_status(entry_id, status="approved", amount=amount)
    if not entry:
        await message.answer("❌ Yozuv topilmadi.")
        return
        
    if entry.get("receipt_id"):
        await database.update_receipt_status(entry["receipt_id"], status="approved")
        
    await message.answer(f"✅ <b>Muvaffaqiyatli tasdiqlandi!</b> «{entry['friend_name']}» saytga <b>{amount:,} so'm</b> bilan joylandi!", parse_mode="HTML")
    
    user_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Saytda Ko'rish (Jonli)", url="https://telegrambot-wtzt.onrender.com/leaderboard")]
        ]
    )
    try:
        await bot.send_message(
            chat_id=entry["user_id"],
            text=(
                f"🎉 <b>Tabriklaymiz! Do'stingiz «{html.escape(entry['friend_name'])}» Forbes Uzbekistan sayt reytingiga muvaffaqiyatli joylashtirildi!</b>\n\n"
                f"💰 <b>Kiritilgan summa:</b> {amount:,} so'm\n"
                f"👑 <b>Unvoni:</b> {html.escape(entry['friend_title'])}\n\n"
                "Quyidagi havola orqali o'zingiz va do'stingiz saytda qaysi o'rindaligini ko'ring:"
            ),
            parse_mode="HTML",
            reply_markup=user_kb
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_ldb_rej_"))
async def adm_ldb_rej_cb(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    entry_id = int(call.data.replace("adm_ldb_rej_", ""))
    entry = await database.update_leaderboard_status(entry_id, status="rejected")
    if entry and entry.get("receipt_id"):
        await database.update_receipt_status(entry["receipt_id"], status="rejected")
        
    await call.answer("❌ Chek rad etildi.", show_alert=True)
    try:
        await call.message.edit_caption(
            caption=(call.message.caption or "") + "\n\n❌ <b>TO'LOV RAD ETILDI (SAYTGA JOYLANMADI)</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
    if entry:
        try:
            await bot.send_message(
                chat_id=entry["user_id"],
                text="❌ <b>Kechirasiz, sayt reytingi uchun yuborgan to'lov chekingiz tasdiqlanmadi.</b>\nIltimos, haqiqiy to'lov skrinshotini yuboring.",
                parse_mode="HTML"
            )
        except Exception:
            pass

async def send_generated_audio(bot: Bot, user_id: int, greeting_id_str: str, notify_msg: Optional[Message] = None):
    """Audio fayl yasab foydalanuvchiga jo'natish yordamchisi."""
    g_info = None
    if greeting_id_str.isdigit():
        g_info = await database.get_greeting_by_id(int(greeting_id_str))
        
    if not g_info:
        greetings = await database.get_user_greetings(user_id, limit=1)
        if greetings:
            g_info = greetings[0]
            
    if not g_info:
        if notify_msg:
            await notify_msg.answer("❌ Tabrik matni topilmadi.")
        return
        
    char_key = g_info.get("character", "boyvachcha")
    char_name = CHARACTERS.get(char_key, {}).get("name", char_key)
    rec_name = g_info.get("recipient_name", "Do'stim")
    msg_text = g_info.get("generated_text", "")
    
    output_mp3 = f"audio_{user_id}_{int(time.time())}.mp3"
    try:
        await media_generator.generate_audio_voice(msg_text, char_key, output_mp3)
        if os.path.exists(output_mp3):
            # Ovozli xabar (Voice) va MP3 hujjat qilib jo'natish
            caption = (
                f"🎙 <b>{rec_name} uchun eksklyuziv ovozli tabrik!</b>\n"
                f"🎭 Obraz: <b>{char_name}</b>\n\n"
                "👉 @parodiya_tabrik_uzbot"
            )
            await bot.send_voice(
                chat_id=user_id,
                voice=FSInputFile(output_mp3),
                caption=caption,
                parse_mode="HTML"
            )
            await bot.send_audio(
                chat_id=user_id,
                audio=FSInputFile(output_mp3, filename=f"Tabrik_{rec_name}.mp3"),
                caption="📥 Yuklab olish uchun MP3 fayl",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Audio jo'natishda xatolik: {e}", exc_info=True)
        try:
            await bot.send_message(chat_id=user_id, text=f"❌ Audio tayyorlashda xatolik yuz berdi: {e}")
        except Exception:
            pass
    finally:
        if os.path.exists(output_mp3):
            try:
                os.remove(output_mp3)
            except Exception:
                pass

# -------------------------------------------------------------
# 14. TABRIK YARATISH BOSQICHLARI (FSM)
# -------------------------------------------------------------
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
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb)
    await call.answer()

@router.message(GreetingForm.entering_recipient)
async def recipient_entered_handler(message: Message, state: FSMContext):
    raw_name = message.text.strip()
    if len(raw_name) > 40:
        await message.answer("Iltimos, ismni qisqaroq qilib kiriting (maksimal 40 harf):")
        return
    
    clean_name = html.escape(raw_name)
    await state.update_data(recipient_name=clean_name)
    await state.set_state(GreetingForm.choosing_profession)
    
    await database.log_activity(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        action="ENTER_RECIPIENT",
        details=f"Qabul qiluvchi ismi kiritildi: {clean_name}"
    )
    
    text = (
        f"Ajoyib! Demak, <b>{clean_name}</b> uchun tayyorlaymiz.\n\n"
        "💼 <b>4-Qadam:</b> Matn yanada kulgili va aniq chiqishi uchun — "
        f"<b>{clean_name} qaysi sohada ishlaydi (kasbi nima)?</b>"
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
    cancel_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")]]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=cancel_kb)
    await call.answer()

@router.message(GreetingForm.entering_sender)
async def sender_entered_handler(message: Message, state: FSMContext):
    raw_sender = message.text.strip()
    if len(raw_sender) > 50:
        await message.answer("Iltimos, ismni qisqaroq qilib kiriting (maksimal 50 harf):")
        return

    sender_name = html.escape(raw_sender)
    data = await state.get_data()
    await state.clear()
    
    category = data.get("chosen_category", "greeting")
    char_key = data.get("chosen_char", "boyvachcha")
    recipient_name = data.get("recipient_name", "Do'stim")
    prof_key = data.get("chosen_profession", "general")
    
    generated_text = generate_custom_message(
        char_key=char_key,
        recipient_name=recipient_name,
        category=category,
        profession_key=prof_key,
        sender_name=sender_name
    )
    
    g_id = await database.save_greeting(
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
    
    result_text = (
        "🎉 <b>Eksklyuziv Matn Tayyor Bo'ldi!</b>\n\n"
        "📋 <i>Quyidagi matnning burchagidagi <b>«Copy»</b> tugmasini bosib (yoki matn ustiga 1 marta bosib) nusxalab oling:</i>\n\n"
        f"<pre><code class=\"language-text\">{generated_text}</code></pre>\n\n"
        "⭐️ <i>Sizga tabrik yaratganingiz uchun <b>+2 ball</b> berildi!</i>"
    )
    
    share_caption = (
        f"{generated_text}\n\n"
        "🎭 Siz ham yaqinlaringizga shunday eksklyuziv parodiya tabrik yaratmoqchimisiz?\n"
        "👉 Bepul bot: @parodiya_tabrik_uzbot"
    )

    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=get_result_keyboard(f"{recipient_name} uchun eksklyuziv xabar!", share_caption, g_id)
    )

# -------------------------------------------------------------
# 15. MENING TABRIKLARIM, BUYRUQLAR VA INLINE QUERY
# -------------------------------------------------------------
@router.message(Command("mygreetings"))
@router.callback_query(F.data == "my_greetings")
async def my_greetings_handler(event: TelegramObject):
    user = event.from_user
    greetings = await database.get_user_greetings(user.id, limit=5)
    
    if not greetings:
        text = (
            "📂 <b>Siz hali birorta ham tabrik yaratmadingiz!</b>\n\n"
            "Do'stlaringiz va yaqinlaringiz uchun birinchi ajoyib tabrikni yaratish uchun "
            "quyidagi tugmani bosing:"
        )
    else:
        text = f"📂 <b>Siz yaratgan oxirgi {len(greetings)} ta tabrik:</b>\n\n"
        for idx, g in enumerate(greetings, 1):
            char_info = CHARACTERS.get(g['character'], {})
            char_name = char_info.get('name', g['character'])
            preview_snippet = html.escape(g['generated_text'][:100])
            text += (
                f"<b>{idx}. {html.escape(g['recipient_name'])} uchun</b> ({char_name})\n"
                f"📅 <i>{g['created_at']}</i>\n"
                f"💬 <code>{preview_snippet}...</code>\n"
                "──────────────────\n"
            )
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Yangi Tabrik Yaratish", callback_data="start_create")],
            [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")]
        ]
    )
    
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    elif isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>«Parodiya Tabrik Boti» Qo'llanmasi:</b>\n\n"
        "1️⃣ <b>Tabrik yaratish:</b> <b>«🎭 Tabrik Yaratish»</b> tugmasi orqali do'stingizga kulgili qutlov tayyorlang.\n"
        "2️⃣ <b>Rasm (Otkritka):</b> Matn ostidagi <b>«🖼 Rasm Olish»</b> orqali hashamatli oltin otkritkani yuklab oling.\n"
        "3️⃣ <b>Ovozli Audio (MP3):</b> Tabrikni <b>«🎙 Audio Olish»</b> orqali tabiiy aktyor ovozida MP3 qilib oling (5,000 so'm yoki 25 ball).\n"
        "4️⃣ <b>Qaysi personajsan?</b> 3 ta savolli testdan o'tib, kimligingizni bilib oling va do'stlarga ulashing!\n"
        "5️⃣ <b>Parodiya Diplom:</b> Do'stingizga 'Yil Boyvachchasi' yoki 'Yil Taksisti' sertifikatini sovg'a qiling!\n"
        "6️⃣ <b>Omad Barabani:</b> Birgina bosishda tasodifiy kutilmagan parodiya oling!\n"
        "7️⃣ <b>Ballar & Unvonlar:</b> Do'stlaringizni taklif qilib har biridan <b>+10 ball</b> oling va VIP unvonga ko'tariling!\n\n"
        "📌 <b>Mavjud buyruqlar:</b>\n"
        "• <code>/start</code> — Asosiy menyu\n"
        "• <code>/profile</code> — Sizning profilingiz va ballaringiz\n"
        "• <code>/top</code> — Top 10 peshqadamlar\n"
        "• <code>/quiz</code> — 'Qaysi personajsan?' testi\n"
        "• <code>/certificate</code> — Rasmiy parodiya diplom generatori\n"
        "• <code>/roulette</code> — Omad barabani\n"
        "• <code>/fortune</code> — Kunlik kulgili bashorat\n"
        "• <code>/mygreetings</code> — Oxirgi yaratgan tabriklaringiz\n"
        "• <code>/cancel</code> — Joriy amalni bekor qilish\n"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Tabrik Yaratish", callback_data="start_create")],
            [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")]
        ]
    )
    await message.answer(help_text, parse_mode="HTML", reply_markup=kb)

@router.message(Command("characters"))
async def cmd_characters(message: Message):
    text = (
        "🌟 <b>Mavjud Barcha 8 ta Personaj (100% Bepul):</b>\n\n"
        "1. 💰 <b>Saxiy Boyvachcha Otaxon</b> — Dollar sochadigan saxiy millioner\n"
        "2. 👮 <b>Katta Leytenant (GAI)</b> — Qat'iy protokol va jarima hazillari\n"
        "3. 🍏 <b>Malika Savdogari</b> — O'rikzor va Malikaning chaqqon savdogari\n"
        "4. 📜 <b>Xalq Donishmandi & Shoir Bobo</b> — Kulgili va falsafiy baytlar\n"
        "5. 🕶️ <b>Xorijdagi Shef (Don Karleone)</b> — Jiddiy va katta doiradagi mafioz biznesmen\n"
        "6. 🚕 <b>Toshkent Taksisti (Aka)</b> — 'Bratan, propkada qoldim' uslubidagi taksist\n"
        "7. 🎓 <b>Charchagan Talaba (Sessiya Qurboni)</b> — Doshirak va stipendiya orzusidagi talaba\n"
        "8. 🧕 <b>Hazilkash Qaynona & Kelin</b> — Mahalla va qaynona-kelin hazillari\n\n"
        "<i>Barchasi 100% bepul va cheksiz foydalanish uchun ochiq!</i>"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎭 Tabrik Yaratish", callback_data="start_create")],
            [InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")]
        ]
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await database.log_activity(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        action="CANCEL",
        details="Amalni bekor qildi (/cancel)"
    )
    await message.answer("❌ Harakat bekor qilindi. Asosiy menyudasiz:", reply_markup=get_main_menu_keyboard(message.from_user.id))

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
        "Asosiy menyudasiz. Qaysi bo'limdan foydalanamiz?",
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
        "🌟 <b>Mavjud Barcha 8 ta Personaj (100% Bepul):</b>\n\n"
        "1. 💰 <b>Saxiy Boyvachcha Otaxon</b> — Dollar sochadigan saxiy millioner\n"
        "2. 👮 <b>Katta Leytenant (GAI)</b> — Qat'iy nazorat va protokol hazillari\n"
        "3. 🍏 <b>Malika Savdogari</b> — O'rikzor va Malikaning chaqqon savdogari\n"
        "4. 📜 <b>Xalq Donishmandi & Shoir</b> — Qofiyali, kulgili va falsafiy baytlar\n"
        "5. 🕶️ <b>Xorijdagi Shef (Don Karleone)</b> — Jiddiy va katta doiradagi nufuzli biznesmen\n"
        "6. 🚕 <b>Toshkent Taksisti</b> — Poytaxt probkasi va hayotiy hazillar ustasi\n"
        "7. 🎓 <b>Charchagan Talaba</b> — Sessiya, stipendiya va yotoqxona romantikasi\n"
        "8. 🧕 <b>Hazilkash Qaynona & Kelin</b> — Mahalla va to'y-marosimlar hazili\n\n"
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
        f"⭐️ <b>Foydalanuvchilar jami ballari:</b> {stats.get('total_points', 0)} ball\n"
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

@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    raw_text = query.query.strip()
    recipient = html.escape(raw_text) if raw_text else "Do'stim"

    results = []
    sample_chars = [
        ("boyvachcha", "Saxiy Boyvachcha Otaxon", "💰"),
        ("taksist", "Toshkent Taksisti", "🚕"),
        ("talaba", "Charchagan Talaba", "🎓"),
        ("savdogar", "Malika Savdogari", "🍏"),
        ("gai", "Katta Leytenant (GAI)", "👮"),
        ("mafioz", "Don Karleone (Shef)", "🕶️"),
        ("shoir", "Shoir Bobo", "📜")
    ]

    for idx, (c_key, c_name, c_icon) in enumerate(sample_chars, 1):
        msg = generate_custom_message(c_key, recipient, "greeting", "general", "Do'stingiz")
        share_content = (
            f"{msg}\n\n"
            "🎭 Siz ham yaqinlaringizga shunday tabrik yaratish uchun botga kiring:\n"
            "👉 @parodiya_tabrik_uzbot"
        )
        results.append(
            InlineQueryResultArticle(
                id=f"inline_{c_key}_{idx}",
                title=f"{c_icon} {c_name} nomidan tabrik",
                description=f"{recipient} uchun eksklyuziv parodiya tabrik",
                input_message_content=InputTextMessageContent(
                    message_text=share_content,
                    parse_mode="Markdown"
                )
            )
        )
    await query.answer(results, cache_time=10, is_personal=True)

# -------------------------------------------------------------
# 16. ADMIN PANEL (FAQAT ID: 6268220201 UCHUN)
# -------------------------------------------------------------
@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not config.is_admin(message.from_user.id):
        return
    
    await state.clear()
    stats = await database.get_statistics()
    pay_stats = await database.get_payment_stats()
    
    text = (
        "👑 <b>Admin Boshqaruv Paneliga Xush Kelibsiz!</b>\n\n"
        f"🆔 <b>Admin ID:</b> <code>{message.from_user.id}</code>\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎁 <b>Yaratilgan tabriklar:</b> {stats['total_greetings']} ta\n"
        f"💳 <b>Kutilayotgan cheklar:</b> <b>{pay_stats['pending']} ta</b>\n"
        f"💰 <b>Jami to'lovlar tushumi:</b> <b>{pay_stats['total_revenue']:,} so'm</b>\n"
        f"⭐️ <b>Tarqatilgan jami ballar:</b> {stats.get('total_points', 0)} ball\n"
        f"⛔ <b>Bloklanganlar:</b> {stats['banned_users']} ta\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_keyboard(pay_stats['pending']))

@router.message(Command("backup"))
async def cmd_backup(message: Message, bot: Bot):
    if not config.is_admin(message.from_user.id):
        return

    csv_filename = "users_backup.csv"
    await database.export_users_csv(csv_filename)
    try:
        if os.path.exists(csv_filename):
            await bot.send_document(
                chat_id=message.from_user.id,
                document=FSInputFile(csv_filename, filename=f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"),
                caption="📊 <b>Foydalanuvchilar zaxira nusxasi (CSV)</b>",
                parse_mode="HTML"
            )
        if os.path.exists(database.DB_FILE):
            await bot.send_document(
                chat_id=message.from_user.id,
                document=FSInputFile(database.DB_FILE, filename=f"bot_database_{datetime.now().strftime('%Y%m%d_%H%M')}.sqlite"),
                caption="🗄 <b>To'liq SQLite ma'lumotlar bazasi</b>",
                parse_mode="HTML"
            )
    finally:
        if os.path.exists(csv_filename):
            try:
                os.remove(csv_filename)
            except Exception:
                pass

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat berilmagan!", show_alert=True)
        return
    
    await state.clear()
    stats = await database.get_statistics()
    pay_stats = await database.get_payment_stats()
    
    text = (
        "👑 <b>Admin Boshqaruv Paneli</b>\n\n"
        f"🆔 <b>Admin ID:</b> <code>{call.from_user.id}</code>\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎁 <b>Yaratilgan tabriklar:</b> {stats['total_greetings']} ta\n"
        f"💳 <b>Kutilayotgan cheklar:</b> <b>{pay_stats['pending']} ta</b>\n"
        f"💰 <b>Jami to'lovlar tushumi:</b> <b>{pay_stats['total_revenue']:,} so'm</b>\n"
        f"⭐️ <b>Tarqatilgan jami ballar:</b> {stats.get('total_points', 0)} ball\n"
        f"⛔ <b>Bloklanganlar:</b> {stats['banned_users']} ta\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard(pay_stats['pending']))
    await call.answer()

# -------------------------------------------------------------
# TO'LOVLAR VA CHEKLAR BOSHQARUV MARKAZI
# -------------------------------------------------------------
@router.callback_query(F.data == "admin_payments")
async def admin_payments_dashboard(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    stats = await database.get_payment_stats()
    
    text = (
        "💳 <b>To'lovlar va Cheklar Boshqaruv Markazi</b>\n\n"
        f"⏳ <b>Kutilayotgan (tasdiqlanmagan) cheklar:</b> <b>{stats['pending']} ta</b>\n"
        f"✅ <b>Tasdiqlangan to'lovlar:</b> <b>{stats['approved']} ta</b>\n"
        f"❌ <b>Rad etilgan cheklar:</b> <b>{stats['rejected']} ta</b>\n"
        f"📊 <b>Jami kelgan cheklar:</b> <b>{stats['total']} ta</b>\n\n"
        f"💰 <b>Jami tushum (Kassada):</b> <b>{stats['total_revenue']:,} so'm</b>\n\n"
        "<i>Kerakli bo'limni tanlang:</i>"
    )
    
    buttons = []
    if stats["pending"] > 0:
        buttons.append([
            InlineKeyboardButton(text=f"⏳ Kutilayotgan Cheklarni Ko'rish ({stats['pending']} ta)", callback_data="adm_view_pending_0")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="✅ Kutilayotgan Cheklar Yo'q (Barchasi ko'rilgan)", callback_data="adm_no_pending")
        ])
        
    buttons.append([
        InlineKeyboardButton(text="📜 Barcha To'lovlar Tarixi (Oxirgi 15 ta)", callback_data="adm_all_receipts_0")
    ])
    buttons.append([
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_payments"),
        InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel")
    ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "adm_no_pending")
async def adm_no_pending_cb(call: CallbackQuery):
    await call.answer("🎉 Hozircha kutilayotgan yangi cheklar yo'q! Barchasi ko'rib chiqilgan.", show_alert=True)

@router.callback_query(F.data.startswith("adm_view_pending_"))
async def adm_view_pending_cb(call: CallbackQuery, bot: Bot):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    offset_str = call.data.replace("adm_view_pending_", "")
    offset = int(offset_str) if offset_str.isdigit() else 0
    
    pending_list = await database.get_pending_receipts(limit=1, offset=offset)
    stats = await database.get_payment_stats()
    
    if not pending_list:
        await call.answer("Boshqa kutilayotgan chek qolmadi!", show_alert=True)
        await admin_payments_dashboard(call)
        return
        
    receipt = pending_list[0]
    total_pending = stats["pending"]
    current_num = offset + 1
    
    caption = (
        f"🧾 <b>Kutilayotgan Chek #{receipt['id']}</b> ({current_num}/{total_pending})\n\n"
        f"👤 <b>Foydalanuvchi:</b> {html.escape(receipt['full_name'])}\n"
        f"🆔 <b>Telegram ID:</b> <code>{receipt['user_id']}</code>\n"
        f"🔗 <b>Username:</b> @{receipt['username'] or 'mavjud_emas'}\n"
        f"💵 <b>Summa:</b> {receipt['amount']:,} so'm\n"
        f"📅 <b>Kelgan vaqti:</b> {receipt['created_at']}\n\n"
        "To'lovni tasdiqlaysizmi?"
    )
    
    nav_buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_mag_app_{receipt['id']}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_mag_rej_{receipt['id']}")
        ]
    ]
    
    row_nav = []
    if offset > 0:
        row_nav.append(InlineKeyboardButton(text="⬅️ Oldingisi", callback_data=f"adm_view_pending_{offset - 1}"))
    if current_num < total_pending:
        row_nav.append(InlineKeyboardButton(text="Keyingisi ➡️", callback_data=f"adm_view_pending_{offset + 1}"))
    if row_nav:
        nav_buttons.append(row_nav)
        
    nav_buttons.append([InlineKeyboardButton(text="🔙 To'lovlar Menyusi", callback_data="admin_payments")])
    kb = InlineKeyboardMarkup(inline_keyboard=nav_buttons)
    
    await call.answer()
    try:
        if receipt["file_type"] == "photo":
            await bot.send_photo(
                chat_id=call.from_user.id,
                photo=receipt["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb
            )
        else:
            await bot.send_document(
                chat_id=call.from_user.id,
                document=receipt["file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=kb
            )
    except Exception as e:
        logger.error(f"Chekni ko'rsatishda xatolik: {e}")
        await call.message.answer(f"⚠️ Chekni yuklashda xatolik: {e}", reply_markup=kb)

@router.callback_query(F.data.startswith("adm_all_receipts_"))
async def adm_all_receipts_cb(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
        
    receipts = await database.get_all_receipts(limit=15)
    
    text = "📜 <b>Oxirgi 15 ta To'lov Cheki Tarixi:</b>\n\n"
    if not receipts:
        text += "<i>Hozircha hech qanday chek kelmagan.</i>"
    else:
        for r in receipts:
            status_icon = "⏳" if r["status"] == "pending" else ("✅" if r["status"] == "approved" else "❌")
            status_word = "Kutilmoqda" if r["status"] == "pending" else ("Tasdiqlangan" if r["status"] == "approved" else "Rad etilgan")
            text += (
                f"{status_icon} <b>Chek #{r['id']}</b> ({r['amount']:,} so'm)\n"
                f"👤 {html.escape(r['full_name'])} (@{r['username'] or 'yoq'})\n"
                f"📅 {r['created_at']} — <i>{status_word}</i>\n\n"
            )
            
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="adm_all_receipts_0")],
            [InlineKeyboardButton(text="🔙 To'lovlar Menyusi", callback_data="admin_payments")]
        ]
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
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
        f"⭐️ <b>Jami berilgan ballar:</b> {stats.get('total_points', 0)} ball\n"
        f"📜 <b>Jami kuzatilgan amallar:</b> {stats['total_logs']} ta\n"
        f"⛔ <b>Bloklangan foydalanuvchilar:</b> {stats['banned_users']} ta\n"
        f"⏱ <b>Server Uptime:</b> {hours} soat, {minutes} daqiqa, {seconds} soniya\n"
        f"📢 <b>Majburiy kanal:</b> {config.CHANNEL_ID}\n\n"
        "<i>Barcha ma'lumotlar real vaqt rejimida hisoblanadi.</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_rankings")
async def admin_rankings_callback(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    top_stats = await database.get_top_stats()
    
    text = "🏆 <b>Eng Ommabop Reytinglar (Top Tanlovlar):</b>\n\n"
    
    text += "🎭 <b>Eng Ko'p Tanlangan Personajlar:</b>\n"
    if top_stats["top_characters"]:
        for idx, c in enumerate(top_stats["top_characters"], 1):
            c_info = CHARACTERS.get(c["character"], {})
            name = c_info.get("name", c["character"])
            text += f"{idx}. {name}: <b>{c['count']} marta</b>\n"
    else:
        text += "<i>Hali tabriklar yaratilmagan.</i>\n"
    text += "\n"

    text += "💼 <b>Eng Ko'p Tanlangan Kasblar:</b>\n"
    if top_stats["top_professions"]:
        for idx, p in enumerate(top_stats["top_professions"], 1):
            title = PROFESSIONS.get(p["profession"], p["profession"])
            text += f"{idx}. {title}: <b>{p['count']} marta</b>\n"
    else:
        text += "<i>Hali kasblar tanlanmagan.</i>\n"
    text += "\n"

    text += "👥 <b>Eng Ko'p Do'st Taklif Qilganlar:</b>\n"
    if top_stats["top_referrers"]:
        for idx, r in enumerate(top_stats["top_referrers"], 1):
            text += f"{idx}. ID <code>{r['referrer_id']}</code>: <b>{r['ref_count']} ta do'st</b>\n"
    else:
        text += "<i>Hali takliflar mavjud emas.</i>\n"

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_cleanup")
async def admin_cleanup_callback(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    deleted_count = await database.cleanup_old_logs(days=30)
    await call.answer(f"🧹 {deleted_count} ta eskirgan log tozalandi!", show_alert=True)
    await admin_panel_callback(call, None)

@router.callback_query(F.data == "admin_logs")
async def admin_logs_callback(call: CallbackQuery):
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
            user_str = f"<b>{html.escape(log.get('full_name', 'Foydalanuvchi'))}</b> {username_part} [<code>{log['user_id']}</code>]"
            text += (
                f"⏱ <b>{log['created_at']}</b>\n"
                f"👤 {user_str}\n"
                f"⚡ <b>Amal:</b> <code>{log['action']}</code>\n"
                f"📝 <b>Tafsilot:</b> {html.escape(log['details'])}\n"
                "──────────────────\n"
            )
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_back_keyboard())
    await call.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users_callback(call: CallbackQuery):
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
            full_name = html.escape(f"{fname} {lname}".strip() or "Noma'lum")
            ban_badge = " [⛔ BLOKLANGAN]" if u.get("is_banned") else ""
            pts = u.get("points", 0)
            text += (
                f"<b>{idx}. {full_name}</b> ({uname}){ban_badge}\n"
                f"🆔 ID: <code>{u['user_id']}</code> | ⭐️ Ballar: <b>{pts}</b>\n"
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
    full_name = html.escape(f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or "Noma'lum")
    is_banned = bool(user_info.get("is_banned"))
    utm_source_label = user_info.get("utm_source", "") or "To'g'ridan-to'g'ri"
    pts = user_info.get("points", 0)
    
    report = (
        f"👤 <b>Foydalanuvchi Profili:</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_info['user_id']}</code>\n"
        f"📝 <b>Ism-familiya:</b> {full_name}\n"
        f"🌐 <b>Username:</b> {uname}\n"
        f"⭐️ <b>Ballar:</b> <b>{pts} ball</b>\n"
        f"⛔ <b>Holati:</b> {'Bloklangan' if is_banned else 'Faol'}\n"
        f"👥 <b>Taklif qilgan do'stlari:</b> <code>{user_info.get('ref_count', 0)} ta</code>\n"
        f"👥 <b>Taklif qilgan ID:</b> <code>{user_info.get('referrer_id', 0)}</code>\n"
        f"🎯 <b>UTM Manba:</b> <code>{utm_source_label}</code>\n"
        f"📅 <b>Birinchi kirgan:</b> {user_info['created_at']}\n"
        f"⚡ <b>Oxirgi faollik:</b> {user_info['last_active']}\n"
        f"🎁 <b>Jami tabriklari:</b> {user_info['greetings_count']} ta\n\n"
    )
    
    if user_info.get("recent_activities"):
        report += "<b>Oxirgi harakatlari:</b>\n"
        for a in user_info["recent_activities"]:
            report += f"• [{a['created_at']}] <code>{a['action']}</code>: {html.escape(a['details'])}\n"
        report += "\n"
        
    if user_info.get("recent_greetings"):
        report += "<b>Oxirgi yaratgan tabriklari:</b>\n"
        for g in user_info["recent_greetings"]:
            report += f"• [{g['created_at']}] {g['character']} -> {html.escape(g['recipient_name'])} ({g['profession']})\n"

    ban_btn_text = "✅ Blokdan Chiqarish" if is_banned else "⛔ Bloklash"
    ban_cb_data = f"unban_{target_id}" if is_banned else f"ban_{target_id}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=ban_btn_text, callback_data=ban_cb_data)],
            [InlineKeyboardButton(text="🔙 Admin Panel", callback_data="admin_panel")]
        ]
    )
            
    await message.answer(report, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("ban_"))
async def admin_ban_user_callback(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    target_id = int(call.data.replace("ban_", ""))
    await database.ban_user(target_id)
    await call.answer(f"⛔ {target_id} foydalanuvchi bloklandi!", show_alert=True)
    await admin_panel_callback(call, None)

@router.callback_query(F.data.startswith("unban_"))
async def admin_unban_user_callback(call: CallbackQuery):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    target_id = int(call.data.replace("unban_", ""))
    await database.unban_user(target_id)
    await call.answer(f"✅ {target_id} foydalanuvchi blokdan chiqarildi!", show_alert=True)
    await admin_panel_callback(call, None)

# --- ADMIN RASSILKA / XABARNOMA BOSQICHLARI ---

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(call: CallbackQuery, state: FSMContext):
    if not config.is_admin(call.from_user.id):
        await call.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    await state.set_state(AdminBroadcastForm.entering_message)
    text = (
        "📢 <b>Ommaviy Xabarnoma (Rassilka) Yuborish</b>\n\n"
        "Barcha faol foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.\n"
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
    
    user_ids = await database.get_all_user_ids()
    total_users = len(user_ids)
    
    text = (
        f"📢 <b>Xabar qabul qilindi!</b>\n\n"
        f"👥 Qabul qiluvchilar soni: <b>{total_users} ta</b> faol foydalanuvchi.\n\n"
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
            fail_count += 1
        except Exception as e:
            logger.warning(f"Rassilka yuborishda xatolik ({uid}): {e}")
            fail_count += 1
        
        await asyncio.sleep(0.04)
        
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
    
    csv_filename = "users_list_export.csv"
    await database.export_users_csv(csv_filename)
    
    try:
        csv_file = FSInputFile(csv_filename, filename=f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")
        await bot.send_document(
            chat_id=call.from_user.id,
            document=csv_file,
            caption="📊 <b>Foydalanuvchilar ro'yxati (CSV formatida)</b>",
            parse_mode="HTML"
        )
        
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
        if os.path.exists(csv_filename):
            try:
                os.remove(csv_filename)
            except Exception:
                pass

# -------------------------------------------------------------
# 17. KEEP-ALIVE AIOHTTP VEB-SERVER (Render talabi)
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

async def handle_leaderboard(request: web.Request) -> web.Response:
    entries = await database.get_top_leaderboard(limit=100)
    stats = await database.get_leaderboard_stats()
    html_text = leaderboard_web.render_leaderboard_html(entries, stats, bot_username="parodiya_tabrik_uzbot")
    return web.Response(text=html_text, content_type="text/html", charset="utf-8")

async def handle_leaderboard_photo(request: web.Request) -> web.StreamResponse:
    raw_filename = request.match_info.get("filename", "")
    filename = os.path.basename(raw_filename)
    file_path = os.path.join(SITE_PHOTOS_DIR, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return web.FileResponse(file_path)
    return web.Response(status=404, text="Rasm topilmadi")

def create_web_server() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/leaderboard", handle_leaderboard)
    app.router.add_get("/top", handle_leaderboard)
    app.router.add_get("/photo/{filename}", handle_leaderboard_photo)
    return app

# -------------------------------------------------------------
# 18. CRASH-PROOF BOT WATCHDOG SIKLI
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

async def auto_backup_loop(bot: Bot):
    """Har 24 soatda avtomatik ravishda bazani admin chatiga (6268220201) zaxira qilib yuboradi."""
    while True:
        try:
            await asyncio.sleep(86400)
            if os.path.exists(database.DB_FILE):
                csv_path = "auto_backup_users.csv"
                await database.export_users_csv(csv_path)
                try:
                    await bot.send_document(
                        chat_id=config.ADMIN_ID,
                        document=FSInputFile(csv_path, filename=f"users_backup_{datetime.now().strftime('%Y%m%d')}.csv"),
                        caption="🛡️ <b>Avtomatik 24 soatlik zaxira nusxa (CSV)</b>",
                        parse_mode="HTML"
                    )
                finally:
                    if os.path.exists(csv_path):
                        try:
                            os.remove(csv_path)
                        except Exception:
                            pass
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Avtomatik backupda xatolik: {e}")

# -------------------------------------------------------------
# 19. ASOSIY ENTRYPOINT (MAIN SIKL)
# -------------------------------------------------------------
async def main():
    logger.info("🚀 Ilova ishga tushirilmoqda...")

    await database.init_db()
    logger.info("📦 SQLite Ma'lumotlar bazasi muvaffaqiyatli ishga tushirildi.")

    if not config.BOT_TOKEN:
        logger.error("❌ XATO: BOT_TOKEN aniqlanmadi! Iltimos, .env faylini to'ldiring.")
        return

    bot = Bot(token=config.BOT_TOKEN)

    # Telegram ko'k 'Menu' tugmasiga barcha asosiy buyruqlarni o'rnatish
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="🚀 Bosh menyu"),
            BotCommand(command="profile", description="🏆 Ballaringiz va referral havolangiz"),
            BotCommand(command="quiz", description="🧠 'Qaysi personajsan?' kulgili test"),
            BotCommand(command="certificate", description="📜 Rasmiy parodiya diplom"),
            BotCommand(command="magazine", description="🌟 VIP Forbes Jurnali Muqovasi (Rasmli)"),
            BotCommand(command="top", description="👑 Saytdagi Top Boyvachchalar Reytingi"),
            BotCommand(command="roulette", description="🎲 Omad barabani"),
            BotCommand(command="fortune", description="🔮 Kunlik bashorat"),
            BotCommand(command="characters", description="🌟 Barcha 8 ta personaj"),
            BotCommand(command="mygreetings", description="📂 Mening tabriklarim"),
            BotCommand(command="help", description="📖 Qo'llanma"),
            BotCommand(command="cancel", description="❌ Bekor qilish")
        ])
        logger.info("✅ Telegram menyu buyruqlari muvaffaqiyatli o'rnatildi.")
    except Exception as e:
        logger.warning(f"Menyu buyruqlarini o'rnatishda xatolik: {e}")

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    app = create_web_server()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host=config.HOST, port=config.PORT)
    await site.start()
    logger.info(f"🌐 Keep-Alive Veb-Server {config.HOST}:{config.PORT} manzilida tinglamoqda.")
    logger.info(f"📢 Majburiy kanal a'zoligi faol: {config.CHANNEL_ID}")
    logger.info(f"👑 Boshqaruvchi Admin ID: {config.ADMIN_ID}")

    backup_task = asyncio.create_task(auto_backup_loop(bot))

    try:
        await run_bot_polling_watchdog(bot, dp)
    finally:
        backup_task.cancel()
        logger.info("🧹 Resurslarni tozalash va yopish...")
        await runner.cleanup()
        await bot.session.close()
        logger.info("👋 Ilova toza yopildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Dastur foydalanuvchi tomonidan to'xtatildi.")
