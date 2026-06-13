import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_CHAT_IDS = [-5102540817, -437147591]
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
    if update.effective_chat.id not in ALLOWED_CHAT_IDS:
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

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()
