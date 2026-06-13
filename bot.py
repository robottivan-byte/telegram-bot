import json
import os
import random
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime, timedelta
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALLOWED_CHAT_IDS = [-5102540817, -437147591]
BOT_USERNAME = "Fuckbook1Bot"
AWAY_THRESHOLD_HOURS = 3
INACTIVE_HOURS = 3
LAST_SEEN_FILE = "last_seen.json"
LAST_CHAT_ACTIVITY_FILE = "last_chat_activity.json"
CITY = "Saint Petersburg"

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
    "💡 Факт: Муравьи никогда не спят и не
