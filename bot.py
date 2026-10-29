from __future__ import annotations
import asyncio,logging,os,re
from html import escape
from aiogram import Bot,Dispatcher,F,types
from aiogram.enums import ParseMode
from aiogram.filters import Command,CommandStart
from aiogram.types import BotCommand,InlineKeyboardButton,InlineKeyboardMarkup
from dotenv import load_dotenv
from aiohttp import web
from database import Database
from lookup_service import lookup_phone_number

load_dotenv()
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
BOT_TOKEN=os.getenv("bot_token") or os.getenv("BOT_TOKEN") or ""
BOT_TOKEN=BOT_TOKEN.strip()
DEFAULT_REGION=os.getenv("DEFAULT_REGION","IN").strip().upper()
DB_PATH=os.getenv("DATABASE_PATH","bot_data.db")
FREE_LOOKUPS=int(os.getenv("FREE_LOOKUPS_PER_DAY","5"))
UPDATES_URL=os.getenv("UPDATES_CHANNEL_URL","https://t.me/telegram")
TERMS_URL=os.getenv("TERMS_URL","https://telegram.org/tos")
ADMIN_IDS={int(x) for x in os.getenv("ADMIN_USER_IDS","").split(",") if x.strip().isdigit()}
if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is not configured.")
bot=Bot(BOT_TOKEN); dp=Dispatcher(); db=Database(DB_PATH)

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
      [InlineKeyboardButton(text="👑 Get Premium",callback_data="premium"),
       InlineKeyboardButton(text="👤 My Profile",callback_data="profile")],
      [InlineKeyboardButton(text="📢 Official Updates",url=UPDATES_URL)],
      [InlineKeyboardButton(text="📜 T&C",url=TERMS_URL)]
    ])

def premium_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👑 Get Premium",callback_data="premium")]])

def format_result(r:dict)->str:
    s1,s2=r["server_1"],r["server_2"]
    def v(x): return escape(str(x or "Not found"))
    status=s1.get("source","unknown")
    status_label={"directory":"Lookup completed","not-configured":"Provider not configured","provider-error":"Provider error"}.get(status, status.replace("http-","HTTP ") if status.startswith("http-") else "Unavailable")
    lines=[
        f"📱 <b>Phone Number</b>\n<code>{escape(r['e164'])}</code>","",
        "🌍 <b>Number Information</b>",
        f"Country: <code>{v(r['country'])}</code> {r['flag']}",
        f"Type: <code>{v(r['number_type'])}</code>",
        f"Carrier: <code>{v(s2.get('carrier'))}</code>",
        f"Region: <code>{v(s2.get('location'))}</code>",
        f"Time Zone: <code>{v(s2.get('timezone'))}</code>","",
        "👤 <b>Caller Identity</b>",
        f"Name: <code>{v(s1.get('name'))}</code>",
        f"Business: <code>{v(s1.get('business'))}</code>","",
        "🔎 <b>Sources</b>",
        f"Directory: <code>{escape(status_label)}</code>",
        "Phone metadata: <code>Available</code>","",
        f'💬 <a href="https://wa.me/{r["digits_only"]}">Open WhatsApp</a>'
    ]
    return "\n".join(lines)

@dp.message(CommandStart())
async def start(message:types.Message):
    await db.get_or_create_user(message.from_user.id,message.from_user.username,message.from_user.first_name)
    await message.answer(f"<b>Hello {escape(message.from_user.first_name or 'User')} 👋</b>\n\n"
        "<b>Send me a phone number to get available caller/phone metadata.</b>\n\n"
        "<b>Example:</b> <code>+919876543210</code>",parse_mode=ParseMode.HTML,reply_markup=main_keyboard())

@dp.message(Command("profile"))
async def profile(message:types.Message):
    u=await db.get_or_create_user(message.from_user.id,message.from_user.username,message.from_user.first_name)
    status="Premium" if u["is_premium"] else "Free"
    await message.answer(f"👤 <b>Profile</b>\n\nID: <code>{u['user_id']}</code>\n"
        f"Plan: <code>{status}</code>\nCredits: <code>{u['credits']}</code>\n"
        f"Daily lookups: <code>{u['daily_used']}/{FREE_LOOKUPS}</code>\n"
        f"Sponsored links opened: <code>{u['ads_viewed']}</code>",
        parse_mode=ParseMode.HTML,reply_markup=premium_keyboard())

@dp.message(Command("premium"))
async def premium(message:types.Message):
    await message.answer("👑 <b>Premium</b>\n\n"
        "Connect this screen to Telegram Payments or another legitimate payment provider. "
        "This build does not pretend a payment happened and does not expose private data.",
        parse_mode=ParseMode.HTML)

@dp.message(Command("viewed_ads"))
async def viewed_ads(message:types.Message):
    u=await db.get_or_create_user(message.from_user.id,message.from_user.username,message.from_user.first_name)
    await message.answer(f"📢 Sponsored links opened: <code>{u['ads_viewed']}</code>",parse_mode=ParseMode.HTML)

@dp.callback_query(F.data=="profile")
async def cb_profile(c:types.CallbackQuery):
    await c.answer(); await profile(c.message)

@dp.callback_query(F.data=="premium")
async def cb_premium(c:types.CallbackQuery):
    await c.answer(); await premium(c.message)

@dp.message(Command("premium_on"))
async def premium_on(message:types.Message):
    if message.from_user.id not in ADMIN_IDS:return
    p=message.text.split()
    if len(p)!=2 or not p[1].isdigit():
        await message.answer("Usage: /premium_on <telegram_user_id>"); return
    await db.set_premium(int(p[1]),True); await message.answer("Premium enabled.")

@dp.message(Command("premium_off"))
async def premium_off(message:types.Message):
    if message.from_user.id not in ADMIN_IDS:return
    p=message.text.split()
    if len(p)!=2 or not p[1].isdigit():
        await message.answer("Usage: /premium_off <telegram_user_id>"); return
    await db.set_premium(int(p[1]),False); await message.answer("Premium disabled.")

@dp.message(F.text.regexp(re.compile(r"^\+?[0-9()\s\-]{8,20}$")))
async def lookup(message:types.Message):
    u=await db.get_or_create_user(message.from_user.id,message.from_user.username,message.from_user.first_name)
    if not await db.consume_lookup(message.from_user.id,bool(u["is_premium"]),FREE_LOOKUPS):
        await message.answer("⚠️ <b>No free lookups left.</b> Use /premium or try again tomorrow.",
                             parse_mode=ParseMode.HTML,reply_markup=premium_keyboard()); return
    result=await lookup_phone_number(message.text,DEFAULT_REGION)
    await db.record_lookup(message.from_user.id,result.get("e164",message.text),bool(result.get("valid")))
    if not result["valid"]:
        if not u["is_premium"]: await db.add_credits(message.from_user.id,1)
        await message.answer(f"❌ {escape(result['error'])}",parse_mode=ParseMode.HTML); return
    await message.answer(format_result(result),parse_mode=ParseMode.HTML,disable_web_page_preview=True)
    if not u["is_premium"]:
        await message.answer("✨ <b>More data may be available from configured directory providers.</b>\n"
                             "Use /premium for your plan options.",parse_mode=ParseMode.HTML,reply_markup=premium_keyboard())

async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "telegram-bot"})

async def start_health_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info("Health server listening on port %s", port)
    return runner

async def main():
    await db.init()
    await start_health_server()
    await bot.set_my_commands([
      BotCommand(command="start",description="Start bot"),
      BotCommand(command="premium",description="Premium plans"),
      BotCommand(command="profile",description="View profile"),
      BotCommand(command="viewed_ads",description="View sponsored-link history")])
    logging.info("Bot started"); await dp.start_polling(bot)

if __name__=="__main__": asyncio.run(main())
