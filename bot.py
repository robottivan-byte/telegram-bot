import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_CHAT_IDS = [-5102540817, -437147591]
AWAY_THRESHOLD_HOURS = 3
INACTIVE_HOURS = 3
LAST_SEEN_FILE = "last_seen.json"
LAST_CHAT_ACTIVITY_FILE = "last_chat_activity.json"

GREETINGS = [
    "Привет, {name}! Тебя не было {time} 👋",
    "О, {name} вернулся! Отсутствовал {time} 😊",
    "Привет, {name}! Не было тебя {time} 🙌",
    "Вот и {name}! Пропадал на {time} 👏",
    "Привет-привет, {name}! Где был {time}? 😄",
]

REACTIONS = ["👍","❤","🔥","🎉","🤩","💯","👏","😁","🏆","⚡","🥰","😱","🤣","💔","😎"]

CONTENT = [
    "💡 Факт: Мёд не портится. В египетских гробницах нашли мёду 3000 лет — он был съедобен.",
    "💡 Факт: Осьминоги имеют три сердца и голубую кровь.",
    "💡 Факт: Человек — единственное животное, которое краснеет.",
    "💡 Факт: Банан — ягода, а клубника — нет.",
    "💡 Факт: Муравьи никогда не спят и не имеют лёгких.",
    "🌿 Притча: Однажды ученик спросил мудреца: «Как стать счастливым?» Мудрец ответил: «Перестань искать счастье — начни его создавать».",
    "🌿 Притча: Камень, который мешает одному — становится ступенькой для другого. Всё зависит от взгляда.",
    "🌿 Притча: Лучшее время посадить дерево было 20 лет назад. Второе лучшее время — сейчас.",
    "💪 Мотивация: Не важно, как медленно ты идёшь — главное, что ты не останавливаешься.",
    "💪 Мотивация: Каждый день — это новый шанс стать лучше, чем вчера.",
    "💪 Мотивация: Сложные времена создают сильных людей. Вы справитесь.",
    "💬 Эй, тишина затянулась! Давайте поговорим — что сейчас у вас на уме? 🤔",
    "💬 Час тишины — повод пообщаться! Поделитесь чем-нибудь интересным 😊",
    "💬 Ау! Кто что делает? Расскажите как дела 👋",
]

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
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

async def check_inactive_chats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()
    moscow_hour = (now.hour + 3) % 24
    if moscow_hour < 9 or moscow_hour >= 23:
        return
    chat_activity = load_json(LAST_CHAT_ACTIVITY_FILE)
    for chat_id in ALLOWED_CHAT_IDS:
        chat_key = str(chat_id)
        if chat_key in chat_activity:
            last_time = datetime.fromisoformat(chat_activity[chat_key])
            if now - last_time >= timedelta(hours=INACTIVE_HOURS):
                await context.bot.send_message(chat_id=chat_id, text=random.choice(CONTENT))
                chat_activity[chat_key] = now.isoformat()
    save_json(LAST_CHAT_ACTIVITY_FILE, chat_activity)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_CHAT_IDS:
        return
    user = update.effective_user
    if not user:
        return
    user_id = str(user.id)
    chat_id = str(update.effective_chat.id)
    user_name = user.first_name or user.username or "друг"
    now = datetime.utcnow()

    last_seen = load_json(LAST_SEEN_FILE)
    if user_id in last_seen:
        last_time = datetime.fromisoformat(last_seen[user_id])
        delta = now - last_time
        if delta >= timedelta(hours=AWAY_THRESHOLD_HOURS):
            time_str = format_duration(delta)
            greeting = GREETINGS[user.id % len(GREETINGS)].format(name=user_name, time=time_str)
            await update.message.reply_text(greeting)
    last_seen[user_id] = now.isoformat()
    save_json(LAST_SEEN_FILE, last_seen)

    chat_activity = load_json(LAST_CHAT_ACTIVITY_FILE)
    chat_activity[chat_id] = now.isoformat()
    save_json(LAST_CHAT_ACTIVITY_FILE, chat_activity)

    msg = update.message
    if msg.photo or msg.video or msg.video_note:
        await msg.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(check_inactive_chats, interval=600, first=60)
    print("Бот запущен!")
    app.run_polling()
