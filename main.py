# -*- coding: utf-8 -*-
import asyncio
import logging
import sys
import time
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    TelegramObject
)
from aiogram.exceptions import TelegramAPIError, TelegramNetworkError

import config
from characters import CHARACTERS, REASONS, generate_greeting

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
    choosing_character = State()
    entering_recipient = State()
    choosing_reason = State()
    entering_sender = State()

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
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        if member.status in ("creator", "administrator", "member", "restricted"):
            return True
        return False
    except Exception as e:
        logger.warning(f"Kanal a'zoligini tekshirishda xatolik ({user_id}): {e}")
        # Agar kanalga bot admin qilib qo'shilmagan bo'lsa, xatolik chiqishi mumkin
        return False

# -------------------------------------------------------------
# 4. MAJBURIY OBUNA MIDDLEWARE (Doimiy va qat'iy tekshiruv)
# Agar foydalanuvchi kanaldan chiqib ketsa, bot darhol yana to'xtatadi!
# -------------------------------------------------------------
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
# 5. ASOSIY MENYU KLAVIATURALARI (100% BEPUL)
# -------------------------------------------------------------
def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
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
    )

def get_characters_keyboard():
    buttons = []
    for key, data in CHARACTERS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{data['name']} (Bepul)",
                callback_data=f"char_{key}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Bosh menyu", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_reasons_keyboard():
    buttons = []
    for key, title in REASONS.items():
        buttons.append([
            InlineKeyboardButton(text=title, callback_data=f"reason_{key}")
        ])
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="back_to_menu")])
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
                InlineKeyboardButton(text="🔄 Yana Boshqa Tabrik Yaratish", callback_data="start_create")
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

# Middlewareni barcha xabar va tugmalarga biriktirish
router.message.middleware(MandatorySubscriptionMiddleware())
router.callback_query.middleware(MandatorySubscriptionMiddleware())

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
    """Foydalanuvchi 'Obunani Tekshirish' tugmasini bosganda tekshirish."""
    is_sub = await check_user_subscription(bot, call.from_user.id)
    if is_sub:
        await call.answer("✅ Rahmat! Obuna tasdiqlandi. Xush kelibsiz!", show_alert=True)
        await state.clear()
        welcome_text = (
            f"Assalomu alaykum, <b>{call.from_user.first_name}</b>! 🎭\n\n"
            "<b>«Parodiya Tabrik & Mashhurlar Qutlovi»</b> botiga xush kelibsiz!\n\n"
            "Barcha personajlar va tabriklar siz uchun <b>100% BEPUL</b>! 🎉\n\n"
            "Quyidagi tugmani bosing va do'stingiz uchun ajoyib qutlov tayyorlang:"
        )
        await call.message.edit_text(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
    else:
        await call.answer("❌ Siz hali kanalga a'zo bo'lmadingiz! Iltimos, kanalga obuna bo'ling.", show_alert=True)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>! 🎭\n\n"
        "<b>«Parodiya Tabrik & Mashhurlar Qutlovi»</b> botiga xush kelibsiz!\n\n"
        "Ushbu bot orqali yaqinlaringizni O'zbekistondagi mashhur "
        "personajlar tilida mutlaqo <b>BEPUL</b> qutlashingiz mumkin! 😄\n\n"
        "Quyidagi tugmani bosing va tabrik yarating:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Asosiy menyuga qaytdingiz. Qanday amal bajaramiz?",
        reply_markup=get_main_menu_keyboard()
    )
    await call.answer()

@router.callback_query(F.data == "all_characters")
async def all_characters_handler(call: CallbackQuery):
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
    
    status_text = (
        "<b>⚡ Bulutli Server Holati:</b>\n\n"
        "🟢 <b>Status:</b> 24/7 Onlayn (Active)\n"
        f"⏱ <b>Uptime:</b> {hours} soat, {minutes} daqiqa, {seconds} soniya\n"
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

# --- TABRIK YARATISH BOSQICHLARI (FSM) ---

@router.callback_query(F.data == "start_create")
async def start_create_handler(call: CallbackQuery, state: FSMContext):
    await state.set_state(GreetingForm.choosing_character)
    text = (
        "🎭 <b>1-Qadam: Kimning nomidan tabrik tayyorlaymiz?</b>\n\n"
        "Quyidagi personajlardan birini tanlang (barchasi bepul):"
    )
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=get_characters_keyboard())
    await call.answer()

@router.callback_query(GreetingForm.choosing_character, F.data.startswith("char_"))
async def character_chosen_handler(call: CallbackQuery, state: FSMContext):
    char_key = call.data.replace("char_", "")
    await state.update_data(chosen_char=char_key)
    await state.set_state(GreetingForm.entering_recipient)
    
    char_info = CHARACTERS.get(char_key, {})
    text = (
        f"Siz <b>{char_info.get('name')}</b> personajini tanladingiz! {char_info.get('icon')}\n\n"
        "✍️ <b>2-Qadam:</b> Tabrik kim uchun yoziladi? "
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
    await state.set_state(GreetingForm.choosing_reason)
    
    text = (
        f"Ajoyib! Demak, <b>{name}</b> uchun tabrik tayyorlaymiz.\n\n"
        "🎉 <b>3-Qadam:</b> Tabriklash sababini tanlang:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_reasons_keyboard())

@router.callback_query(GreetingForm.choosing_reason, F.data.startswith("reason_"))
async def reason_chosen_handler(call: CallbackQuery, state: FSMContext):
    reason_key = call.data.replace("reason_", "")
    await state.update_data(chosen_reason=reason_key)
    await state.set_state(GreetingForm.entering_sender)
    
    text = (
        "👤 <b>4-Qadam:</b> Ushbu tabrik kimning nomidan yuboriladi?\n"
        "O'z ismingizni yoki laqabingizni yozib yuboring:\n"
        "<i>(Masalan: Do'stingiz Alisher, Bojxona bo'limi, Sinfdoshlar)</i>"
    )
    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()

@router.message(GreetingForm.entering_sender)
async def sender_entered_handler(message: Message, state: FSMContext):
    sender_name = message.text.strip()
    data = await state.get_data()
    await state.clear()
    
    char_key = data.get("chosen_char", "boyvachcha")
    recipient_name = data.get("recipient_name", "Do'stim")
    reason_key = data.get("chosen_reason", "birthday")
    
    # Eksklyuziv tabrik matnini generatsiya qilish
    greeting_text = generate_greeting(
        char_key=char_key,
        recipient_name=recipient_name,
        reason_key=reason_key,
        sender_name=sender_name
    )
    
    await message.answer("✨ <b>Tabrik tayyorlanmoqda... 3, 2, 1...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    
    await message.answer(
        greeting_text,
        reply_markup=get_result_keyboard(f"{recipient_name} uchun eksklyuziv qutlov!")
    )

# -------------------------------------------------------------
# 7. KEEP-ALIVE AIOHTTP VEB-SERVER (Render / Koyeb talabi)
# -------------------------------------------------------------
async def handle_root(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "alive",
        "service": "Telegram Parody Greeting Bot",
        "channel": config.CHANNEL_ID,
        "bot": "running"
    })

async def handle_health(request: web.Request) -> web.Response:
    uptime_sec = int(time.time() - START_TIME)
    return web.json_response({
        "status": "healthy",
        "uptime_seconds": uptime_sec,
        "channel": config.CHANNEL_ID,
        "anti_sleep": "enabled"
    })

def create_web_server() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)
    return app

# -------------------------------------------------------------
# 8. CRASH-PROOF BOT WATCHDOG SIKLI
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
# 9. ASOSIY ENTRYPOINT (MAIN SIKL)
# -------------------------------------------------------------
async def main():
    logger.info("🚀 Ilova ishga tushirilmoqda...")

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
