import json
import os
import re
import random
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime, timedelta
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.environ.get("BOT_TOKEN")
YANDEX_WEATHER_KEY = os.environ.get("YANDEX_WEATHER_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ALLOWED_CHAT_IDS = [-5102540817, -437147591]
BOT_USERNAME = "Fuckbook1Bot"
AWAY_THRESHOLD_HOURS = 3
INACTIVE_HOURS = 3
HISTORY_LIMIT = 50
LAST_SEEN_FILE = "last_seen.json"
LAST_CHAT_ACTIVITY_FILE = "last_chat_activity.json"
CHAT_HISTORY_FILE = "chat_history.json"
REMINDERS_FILE = "reminders.json"
LAT = "59.9311"
LON = "30.3609"

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
    "🌿 Притча: Ученик спросил мудреца как стать счастливым. Мудрец ответил: перестань искать счастье, начни его создавать.",
    "🌿 Притча: Камень, который мешает одному, становится ступенькой для другого. Всё зависит от взгляда.",
    "🌿 Притча: Лучшее время посадить дерево было 20 лет назад. Второе лучшее время — сейчас.",
    "💪 Мотивация: Не важно как медленно ты идёшь — главное что ты не останавливаешься.",
    "💪 Мотивация: Каждый день — это новый шанс стать лучше чем вчера.",
    "💪 Мотивация: Сложные времена создают сильных людей. Вы справитесь.",
    "💬 Эй, тишина затянулась! Давайте поговорим — что сейчас у вас на уме?",
    "💬 Час тишины — повод пообщаться! Поделитесь чем-нибудь интересным 😊",
    "💬 Ау! Кто что делает? Расскажите как дела 👋",
]

CONDITIONS = {
    "clear": "Ясно", "partly-cloudy": "Малооблачно", "cloudy": "Облачно",
    "overcast": "Пасмурно", "light-rain": "Небольшой дождь", "rain": "Дождь",
    "heavy-rain": "Сильный дождь", "snow": "Снег", "light-snow": "Небольшой снег",
    "snowfall": "Снегопад", "hail": "Град", "thunderstorm": "Гроза",
    "fog": "Туман", "drizzle": "Морось"
}

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

def add_to_history(chat_id: str, name: str, text: str):
    history = load_json(CHAT_HISTORY_FILE)
    if chat_id not in history:
        history[chat_id] = []
    history[chat_id].append({"name": name, "text": text})
    history[chat_id] = history[chat_id][-HISTORY_LIMIT:]
    save_json(CHAT_HISTORY_FILE, history)

def get_history(chat_id: str) -> list:
    history = load_json(CHAT_HISTORY_FILE)
    return history.get(chat_id, [])

def get_weather():
    try:
        url = f"https://api.weather.yandex.ru/v2/forecast?lat={LAT}&lon={LON}&lang=ru_RU&limit=1"
        req = urllib.request.Request(url, headers={"X-Yandex-API-Key": YANDEX_WEATHER_KEY})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        fact = data["fact"]
        temp = fact["temp"]
        feels = fact["feels_like"]
        desc = CONDITIONS.get(fact["condition"], fact["condition"])
        return f"🌤 Погода в Санкт-Петербурге: {desc}, {temp}°C (ощущается как {feels}°C)"
    except Exception as e:
        return f"🌤 Погода: не удалось получить данные ({e})"

def get_weather_forecast():
    try:
        url = f"https://api.weather.yandex.ru/v2/forecast?lat={LAT}&lon={LON}&lang=ru_RU&limit=2"
        req = urllib.request.Request(url, headers={"X-Yandex-API-Key": YANDEX_WEATHER_KEY})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        tomorrow = data["forecasts"][1]
        day = tomorrow["parts"]["day"]
        night = tomorrow["parts"]["night"]
        date_str = tomorrow["date"]
        day_desc = CONDITIONS.get(day["condition"], day["condition"])
        night_desc = CONDITIONS.get(night["condition"], night["condition"])
        return (
            f"📅 Прогноз на завтра ({date_str}), Санкт-Петербург:\n\n"
            f"☀️ День: {day_desc}, {day['temp_avg']}°C (ощущается как {day['feels_like']}°C)\n"
            f"🌙 Ночь: {night_desc}, {night['temp_avg']}°C (ощущается как {night['feels_like']}°C)"
        )
    except Exception as e:
        return f"📅 Прогноз: не удалось получить данные ({e})"

def get_weather_hourly():
    try:
        url = f"https://api.weather.yandex.ru/v2/forecast?lat={LAT}&lon={LON}&lang=ru_RU&limit=2&hours=true"
        req = urllib.request.Request(url, headers={"X-Yandex-API-Key": YANDEX_WEATHER_KEY})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        current_hour = now_moscow.hour
        today_hours = data["forecasts"][0].get("hours", [])
        tomorrow_hours = data["forecasts"][1].get("hours", [])
        # берём только часы начиная с текущего
        remaining_today = [h for h in today_hours if int(h["hour"]) >= current_hour]
        all_hours = remaining_today + tomorrow_hours
        lines = []
        for h in all_hours[:12]:
            h_hour = int(h["hour"])
            temp = h["temp"]
            feels = h["feels_like"]
            desc = CONDITIONS.get(h["condition"], h["condition"])
            lines.append(f"  {h_hour:02d}:00 — {desc}, {temp}°C (ощущается {feels}°C)")
        result = "\n".join(lines)
        return f"🕐 Почасовой прогноз, Санкт-Петербург:\n\n{result}"
    except Exception as e:
        return f"🕐 Почасовой прогноз: не удалось получить данные ({e})"

def get_currency():
    try:
        url = "https://www.cbr.ru/scripts/XML_daily.asp"
        with urllib.request.urlopen(url, timeout=10) as r:
            tree = ET.parse(r)
        root = tree.getroot()
        rates = {}
        for valute in root.findall("Valute"):
            char_code = valute.find("CharCode").text
            value = valute.find("Value").text.replace(",", ".")
            nominal = valute.find("Nominal").text
            if char_code in ("USD", "EUR"):
                rates[char_code] = round(float(value) / int(nominal), 2)
        return f"💵 Курс ЦБ: USD — {rates.get('USD', '?')}₽ | EUR — {rates.get('EUR', '?')}₽"
    except:
        return "💵 Курс валют: не удалось получить данные"

def get_news():
    try:
        url = "https://lenta.ru/rss/news"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            tree = ET.parse(r)
        root = tree.getroot()
        items = root.findall(".//item")[:3]
        news = "\n".join(f"• {item.find('title').text}" for item in items)
        return f"📰 Новости:\n{news}"
    except:
        return "📰 Новости: не удалось получить данные"

def ask_gpt(question: str, chat_id: str) -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        history = get_history(chat_id)
        history_text = "\n".join(f"{m['name']}: {m['text']}" for m in history)
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        current_time = now_moscow.strftime("%H:%M")
        messages = [
            {"role": "system", "content": f"Ты — Пятница, дружелюбный бот для группового чата друзей. Версия 6. Отвечай коротко, по-русски, неформально. Сейчас московское время: {current_time}.\n\nПоследние сообщения в чате:\n{history_text}"},
            {"role": "user", "content": question}
        ]
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"

def parse_reminder(text: str, chat_id: str):
    match = re.search(r'напомнить\s+"(\d{1,2}:\d{2})"\s+текст\s+"([^"]+)"', text, re.IGNORECASE)
    if not match:
        return None
    time_str = match.group(1)
    reminder_text = match.group(2).strip()
    hour, minute = map(int, time_str.split(":"))
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    event_time = now_moscow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if event_time <= now_moscow:
        event_time += timedelta(days=1)
    notifications = []
    for minutes_before in [120, 60, 30, 0]:
        notify_at = event_time - timedelta(minutes=minutes_before)
        if notify_at > now_moscow:
            label = f"за {minutes_before} мин" if minutes_before > 0 else "в момент события"
            notifications.append({
                "minutes_before": minutes_before,
                "label": label,
                "notify_at": notify_at.isoformat(),
                "notified": False
            })
    if not notifications:
        return None
    return {
        "chat_id": chat_id,
        "text": reminder_text,
        "event_time": event_time.strftime("%H:%M"),
        "event_dt": event_time.isoformat(),
        "notifications": notifications
    }

def save_reminder(reminder: dict):
    reminders = load_json(REMINDERS_FILE)
    chat_id = reminder["chat_id"]
    if chat_id not in reminders:
        reminders[chat_id] = []
    reminders[chat_id].append(reminder)
    save_json(REMINDERS_FILE, reminders)

def parse_poll(text: str):
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'голосование\s*', '', text, flags=re.IGNORECASE).strip()
    options = re.split(r'\s+или\s+', text, flags=re.IGNORECASE)
    options = [o.strip() for o in options if o.strip()]
    return options if len(options) >= 2 else None

async def morning_digest(context: ContextTypes.DEFAULT_TYPE):
    weather = get_weather()
    forecast = get_weather_forecast()
    currency = get_currency()
    news = get_news()
    text = f"☀️ Доброе утро!\n\n{weather}\n\n{forecast}\n\n{currency}\n\n{news}"
    for chat_id in ALLOWED_CHAT_IDS:
        await context.bot.send_message(chat_id=chat_id, text=text)

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

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    reminders = load_json(REMINDERS_FILE)
    changed = False
    for chat_id, chat_reminders in reminders.items():
        for reminder in chat_reminders:
            for notif in reminder.get("notifications", []):
                if not notif["notified"]:
                    notify_at = datetime.fromisoformat(notif["notify_at"])
                    if now_moscow >= notify_at:
                        await context.bot.send_message(
                            chat_id=int(chat_id),
                            text=f"🔔 Напоминание ({notif['label']}):\n{reminder['text']} в {reminder['event_time']}"
                        )
                        notif["notified"] = True
                        changed = True
    if changed:
        save_json(REMINDERS_FILE, reminders)

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
    msg = update.message
    if not msg:
        return

    last_seen = load_json(LAST_SEEN_FILE)
    if user_id in last_seen:
        last_time = datetime.fromisoformat(last_seen[user_id])
        delta = now - last_time
        if delta >= timedelta(hours=AWAY_THRESHOLD_HOURS):
            time_str = format_duration(delta)
            greeting = GREETINGS[user.id % len(GREETINGS)].format(name=user_name, time=time_str)
            await msg.reply_text(greeting)
    last_seen[user_id] = now.isoformat()
    save_json(LAST_SEEN_FILE, last_seen)

    chat_activity = load_json(LAST_CHAT_ACTIVITY_FILE)
    chat_activity[chat_id] = now.isoformat()
    save_json(LAST_CHAT_ACTIVITY_FILE, chat_activity)

    if msg.text:
        add_to_history(chat_id, user_name, msg.text)

    if msg.photo or msg.video or msg.video_note:
        await msg.set_reaction([ReactionTypeEmoji(emoji=random.choice(REACTIONS))])

    if msg.text and f"@{BOT_USERNAME}" in msg.text:
        question = msg.text.replace(f"@{BOT_USERNAME}", "").strip()
        if not question:
            return

        if re.search(r'^погода$', question, re.IGNORECASE):
            await msg.reply_text(get_weather())

        elif re.search(r'^прогноз$', question, re.IGNORECASE):
            await msg.reply_text(get_weather_forecast())

        elif re.search(r'^часы$', question, re.IGNORECASE):
            await msg.reply_text(get_weather_hourly())

        elif re.search(r'^курс$', question, re.IGNORECASE):
            await msg.reply_text(get_currency())

        elif re.search(r'^новости$', question, re.IGNORECASE):
            await msg.reply_text(get_news())

        elif re.search(r'напомнить\s+"', question, re.IGNORECASE):
            reminder = parse_reminder(question, chat_id)
            if reminder:
                save_reminder(reminder)
                notif_times = "\n".join([
                    f"  • {datetime.fromisoformat(n['notify_at']).strftime('%H:%M')} — {n['label']}"
                    for n in reminder["notifications"]
                ])
                await msg.reply_text(
                    f"✅ Напоминание создано!\n"
                    f"📝 {reminder['text']}\n"
                    f"🕐 Событие в {reminder['event_time']}\n"
                    f"🔔 Уведомлю:\n{notif_times}"
                )
            else:
                await msg.reply_text(
                    '❌ Не понял формат или время уже прошло.\n\n'
                    'Используй:\n@Fuckbook1Bot напомнить "19:30" текст "баня"'
                )

        elif re.search(r'голосование', question, re.IGNORECASE):
            options = parse_poll(question)
            if options and len(options) >= 2:
                await context.bot.send_poll(
                    chat_id=update.effective_chat.id,
                    question="Голосуем! 🗳",
                    options=options[:10],
                    is_anonymous=False
                )
            else:
                await msg.reply_text("Напиши так: @Fuckbook1Bot голосование баня или кино или ресторан")

        else:
            answer = ask_gpt(question, chat_id)
            await msg.reply_text(answer)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(check_inactive_chats, interval=600, first=60)
    app.job_queue.run_repeating(check_reminders, interval=60, first=10)
    app.job_queue.run_daily(morning_digest, time=datetime.strptime("06:00", "%H:%M").time())
    print("Бот запущен!")
    app.run_polling()
