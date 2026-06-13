import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_CHAT_IDS = [-5102540817, -437147591]
AWAY_THRESHOLD_HOURS = 3
LAST_SEEN_FILE = "last_seen.json"

GREETINGS = [
    "Привет, {name}! Тебя не было {time} 👋",
    "О, {name} вернулся! Отсутствовал {time} 😊",
    "Привет, {name}! Не было тебя {time} 🙌",
    "Вот и {name}! Пропадал на {time} 👏",
    "Привет-привет, {name}! Где был {time}? 😄",
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

def format_duration(delta: timedelta) -> str:
    total_minutes = int(delta.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours == 0:
        return f"{minutes} мин"
    elif minutes == 0:
        return f"{hours} ч"
    else:
        return f"{hours} ч {minutes} мин"

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
        delta = now - last_time
        if delta >= timedelta(hours=AWAY_THRESHOLD_HOURS):
            time_str = format_duration(delta)
            greeting = GREETINGS[user.id % len(GREETINGS)].format(name=user_name, time=time_str)
            await update.message.reply_text(greeting)
    last_seen[user_id] = now.isoformat()
    save_last_seen(last_seen)
    await update.message.reply_text(random.choice(EMOJIS))

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()
