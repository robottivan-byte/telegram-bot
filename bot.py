import json
import os
import random
from datetime import datetime, timedelta
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPORT_BOT_TOKEN = os.environ.get("REPORT_BOT_TOKEN", BOT_TOKEN)
RELAY_SECRET = os.environ.get("RELAY_SECRET", "changeme")
ALLOWED_CHAT_ID = -5102540817
AWAY_THRESHOLD_HOURS = 6
LAST_SEEN_FILE = "last_seen.json"

GREETINGS = [
    "Привет, {name}! Давно не виделись 👋",
    "О, {name} вернулся! Рады тебя видеть 😊",
    "Привет, {name}! Соскучились по тебе 🙌",
    "Вот и {name}! Добро пожаловать обратно 👏",
    "Привет-привет, {name}! Как дела? 😄",
]
EMOJIS = ["🔥","❤️","👍","😂","😮","🎉","💯","👏","🤩","😎","🥳","💪"]

def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_last_seen(data):
    with open(LAST_SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    user = update.effective_user
    if not user:
        return
    user_id = str(user.id)
    user_name = user.first_name or user.username or "друг"
    now = datetime.utcnow()
    last_seen = load_last_seen()
    if user_id in last_seen:
        last_time = datetime.fromisoformat(last_seen[user_id])
        if now - last_time >= timedelta(hours=AWAY_THRESHOLD_HOURS):
            greeting = GREETINGS[user.id % len(GREETINGS)].format(name=user_name)
            await update.message.reply_text(greeting)
    last_seen[user_id] = now.isoformat()
    save_last_seen(last_seen)
    await update.message.reply_text(random.choice(EMOJIS))

async def relay_handler(request):
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="bad json")
    if data.get("secret") != RELAY_SECRET:
        return web.Response(status=403, text="forbidden")
    chat_id = data.get("chat_id")
    text = data.get("text", "")
    if not chat_id or not text:
        return web.Response(status=400, text="missing fields")
    bot = Bot(token=REPORT_BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    return web.Response(text="ok")

async def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web = web.Application()
    app_web.router.add_post("/report", relay_handler)
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server on port {port}")

if __name__ == "__main__":
    import asyncio

    async def main():
        await run_web()
        tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
        tg_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        print("Бот запущен!")
        async with tg_app:
            await tg_app.start()
            await tg_app.updater.start_polling()
            await asyncio.Event().wait()

    asyncio.run(main())
