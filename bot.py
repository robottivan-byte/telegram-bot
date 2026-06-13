import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_CHAT_IDS = [-5102540817, -437147591]
AWAY_THRESHOLD_HOURS = 3
INACTIVE_MINUTES = 60
LAST_SEEN_FILE = "last_seen.json"
LAST_CHAT_ACTIVITY_FILE = "last_chat_activity.json"

GREETINGS = [
    "Привет, {name}! Тебя не было {time} 👋",
    "О, {name} вернулся! Отсутствовал {time} 😊",
    "Привет, {name}! Не было тебя {time} 🙌",
    "Вот и {name}! Пропадал на {time} 👏",
    "Привет-привет, {name}! Где был {time}? 😄",
]

TOPICS = [
    "Что-то тихо стало 🤔 Давайте обсудим — какой фильм последний смотрели?",
    "Тишина... 😴 Кто что делает? Расскажите!",
    "Эй, живые есть? 👀 Давайте поговорим о чём-нибудь интересном!",
    "Скучновато что-то 🥱 Какие планы на выходные?",
    "Час тишины — это много 😅 Поделитесь чем-нибудь интересным!",
    "Ау! 📢 Кто что слушает сейчас?",
    "Тихо как в библиотеке 📚 Давайте оживим чат!",
]

REACTIONS = ["👍","❤","🔥","🎉","🤩","💯","👏","😁","🏆","⚡","🥰","😱","🤣","💔","😎"]

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
    chat_activity =
