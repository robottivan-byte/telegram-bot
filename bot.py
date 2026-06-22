import json
import os
import re
import random
import asyncio
import xml.etree.ElementTree as ET
import urllib.request
from datetime import datetime, timedelta, time
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.environ.get("BOT_TOKEN")
YANDEX_WEATHER_KEY = os.environ.get("YANDEX_WEATHER_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY")
ALLOWED_CHAT_IDS = [-5102540817, -437147591, -5182288388]
BOT_USERNAME = "Fuckbook1Bot"
AWAY_THRESHOLD_HOURS = 3
INACTIVE_HOURS = 3
HISTORY_LIMIT = 50
LAST_SEEN_FILE = "last_seen.json"
LAST_CHAT_ACTIVITY_FILE = "last_chat_activity.json"
CHAT_HISTORY_FILE = "chat_history.json"
REMINDERS_FILE = "reminders.json"
CONTENT_INDEX_FILE = "content_index.json"
LAT = "59.9311"
LON = "30.3609"

SIGNS = {
    "овен": "♈ Овен", "телец": "♉ Телец", "близнецы": "♊ Близнецы",
    "рак": "♋ Рак", "лев": "♌ Лев", "дева": "♍ Дева",
    "весы": "♎ Весы", "скорпион": "♏ Скорпион", "стрелец": "♐ Стрелец",
    "козерог": "♑ Козерог", "водолей": "♒ Водолей", "рыбы": "♓ Рыбы"
}

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
    "💡 Факт: Акулы старше деревьев — они появились 450 млн лет назад.",
    "💡 Факт: Мозг не чувствует боли — в нём нет болевых рецепторов.",
    "💡 Факт: Смех заразен — мозг автоматически готовится засмеяться, услышав смех других.",
    "💡 Факт: Кофе был открыт благодаря козам — пастух заметил, что они не спят после ягод кофейного дерева.",
    "💡 Факт: Средний человек проводит во сне треть жизни — около 25 лет.",
    "💡 Факт: Молния ударяет в Землю около 100 раз в секунду.",
    "💡 Факт: Дельфины спят с одним открытым глазом.",
    "💡 Факт: Сердце жирафа весит около 11 кг и качает кровь на высоту 2,5 метра.",
    "💡 Факт: Человек — единственное млекопитающее, которое не может дышать и глотать одновременно.",
    "🌿 Притча: Старый рыбак каждый день выходил в море. Сосед спросил: зачем, ведь денег хватает? Рыбак ответил: я выхожу не за рыбой — я выхожу за рассветом.",
    "🌿 Притча: Ученик пожаловался: у меня нет таланта. Мастер взял камень и бросил в воду. Камень утонул. Затем бросил пробку — она всплыла. Талант — это не то, с чем рождаются. Это то, что не тонет.",
    "🌿 Притча: Король спросил мудреца: что самое ценное? Мудрец ответил: момент, когда ты это понял.",
    "🌿 Притча: Путник нёс тяжёлый мешок и жаловался на усталость. Встречный спросил: а что в мешке? Обиды, ответил путник. Встречный удивился: зачем нести то, что можно оставить прямо здесь?",
    "🌿 Притча: Два брата получили одинаковые семена. Один посадил и ждал. Другой ждал идеального момента. Через год первый собирал урожай, второй всё ещё ждал.",
    "🌿 Притча: Ребёнок спросил: почему море такое большое? Дед ответил: потому что оно не отказывается ни от одной реки.",
    "🌿 Притча: Монах нёс воду в дырявом кувшине и улыбался. Ученик спросил: почему не выбросишь? Монах показал цветы вдоль дороги — они росли там, где капала вода. Даже наши недостатки могут давать жизнь.",
    "🌿 Притча: Скрипач играл на улице. Никто не останавливался. Тогда он закрыл глаза и сыграл ту же мелодию. Люди начали останавливаться. Разница была не в музыке — он перестал играть для других и начал играть для себя.",
    "💪 Мотивация: Не важно как медленно ты идёшь — главное что ты не останавливаешься.",
    "💪 Мотивация: Каждый день — это новый шанс стать лучше чем вчера.",
    "💪 Мотивация: Сложные времена создают сильных людей. Вы справитесь.",
    "💪 Мотивация: Успех — это не финал, неудача — не смерть. Важна лишь смелость продолжать.",
    "💪 Мотивация: Единственный способ делать великую работу — любить то, что делаешь.",
    "💪 Мотивация: Не жди идеального момента. Возьми момент и сделай его идеальным.",
    "💪 Мотивация: Твои ограничения существуют только в твоей голове.",
    "💬 Эй, тишина затянулась! Давайте поговорим — что сейчас у вас на уме?",
    "💬 Час тишины — повод пообщаться! Поделитесь чем-нибудь интересным 😊",
    "💬 Ау! Кто что делает? Расскажите как дела 👋",
    "💬 А вы знаете чем занимаетесь через 5 лет? Интересно было бы узнать 🤔",
    "💬 Если бы можно было улететь прямо сейчас — куда бы вы отправились? ✈️",
    "💬 Что последнее вас по-настоящему рассмешило? 😄",
]

CONDITIONS = {
    "clear": "Ясно", "partly-cloudy": "Малооблачно", "cloudy": "Облачно",
    "overcast": "Пасмурно", "light-rain": "Небольшой дождь", "rain": "Дождь",
    "heavy-rain": "Сильный дождь", "snow": "Снег", "light-snow": "Небольшой снег",
    "snowfall": "Снегопад", "hail": "Град", "thunderstorm": "Гроза",
    "fog": "Туман", "drizzle": "Морось"
}

WMO_EMOJI = {
    0: "☀️", 1: "🌤", 2: "⛅", 3: "☁️",
    45: "🌫", 48: "🌫",
    51: "🌧", 53: "🌧", 55: "🌧",
    61: "🌦", 63: "🌧", 65: "⛈",
    71: "🌨", 73: "❄️", 75: "❄️", 77: "❄️",
    80: "🌦", 81: "🌧", 82: "⛈",
    85: "🌨", 86: "❄️",
    95: "⛈", 96: "⛈", 99: "⛈",
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

def get_last_seen_time(entry) -> datetime:
    if isinstance(entry, dict):
        return datetime.fromisoformat(entry["last_seen"])
    return datetime.fromisoformat(entry)

def get_last_seen_name(entry, user_id="") -> str:
    if isinstance(entry, dict):
        return entry.get("name", user_id)
    return user_id

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

def get_user_absence(name: str) -> str:
    last_seen = load_json(LAST_SEEN_FILE)
    now = datetime.utcnow()
    name_lower = name.lower().strip()
    for uid, entry in last_seen.items():
        stored_name = get_last_seen_name(entry, uid)
        if name_lower in stored_name.lower():
            last_time = get_last_seen_time(entry)
            delta = now - last_time
            if delta.total_seconds() < 300:
                return f"👤 {stored_name} был в чате только что"
            return f"👤 {stored_name} отсутствует уже {format_duration(delta)}"
    return f"👤 Не нашёл {name} в истории чата"

def get_horoscope_one(sign: str) -> str:
    try:
        sign_lower = sign.lower().strip()
        sign_name = SIGNS.get(sign_lower)
        if not sign_name:
            return "Не знаю такой знак. Напиши: Овен, Телец, Близнецы, Рак, Лев, Дева, Весы, Скорпион, Стрелец, Козерог, Водолей, Рыбы"
        client = OpenAI(api_key=OPENAI_API_KEY)
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        date_str = now_moscow.strftime("%d.%m.%Y")
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": f"Напиши гороскоп на {date_str} для знака {sign_name}. 3-4 предложения, позитивно, конкретно, по-русски. Без заголовка."}],
            max_tokens=200
        )
        text = response.choices[0].message.content
        return f"{sign_name} — гороскоп на {date_str}:\n{text}"
    except Exception as e:
        return f"🔮 Гороскоп: ошибка ({e})"

def get_horoscope_all() -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        date_str = now_moscow.strftime("%d.%m.%Y")
        signs_list = ", ".join(SIGNS.values())
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "user", "content": f"Напиши краткий гороскоп на {date_str} для каждого из 12 знаков зодиака: {signs_list}. Для каждого знака 1-2 предложения. Формат: эмодзи знак — текст. По-русски, позитивно."}],
            max_tokens=800
        )
        text = response.choices[0].message.content
        return f"🔮 Гороскоп на {date_str}:\n\n{text}"
    except Exception as e:
        return f"🔮 Гороскоп: ошибка ({e})"

def football_request(url):
    if not FOOTBALL_API_KEY:
        return None
    req = urllib.request.Request(
        url,
        headers={"X-Auth-Token": FOOTBALL_API_KEY, "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def get_world_cup_results():
    if not FOOTBALL_API_KEY:
        return "⚽ ЧМ 2026: добавь FOOTBALL_API_KEY в Railway Variables"
    try:
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        today_str = now_moscow.strftime("%Y-%m-%d")
        data = football_request("https://api.football-data.org/v4/competitions/WC/matches?status=FINISHED")
        if not data:
            return "⚽ ЧМ 2026: нет данных"
        matches = data.get("matches", [])
        if not matches:
            return "⚽ ЧМ 2026: матчи ещё не сыграны"
        by_date = {}
        for m in matches:
            utc_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
            moscow_dt = utc_dt + timedelta(hours=3)
            moscow_date = moscow_dt.strftime("%d.%m")
            home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name", "?")
            away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name", "?")
            score = m["score"]["fullTime"]
            hg = score["home"] if score["home"] is not None else "-"
            ag = score["away"] if score["away"] is not None else "-"
            if moscow_date not in by_date:
                by_date[moscow_date] = []
            by_date[moscow_date].append(f"  {home} {hg}:{ag} {away}")
        lines = ["⚽ ЧМ 2026 — все результаты:\n"]
        for date_key in sorted(by_date.keys(), key=lambda d: datetime.strptime(d + ".2026", "%d.%m.%Y")):
            lines.append(f"📅 {date_key}")
            lines.extend(by_date[date_key])
            lines.append("")
        data2 = football_request("https://api.football-data.org/v4/competitions/WC/matches?status=SCHEDULED")
        today_matches = []
        if data2:
            for m in data2.get("matches", []):
                utc_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                moscow_dt = utc_dt + timedelta(hours=3)
                if moscow_dt.strftime("%Y-%m-%d") == today_str:
                    home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name", "?")
                    away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name", "?")
                    today_matches.append(f"  {moscow_dt.strftime('%H:%M')} | {home} — {away}")
        if today_matches:
            lines.append("🔜 Сегодня играют:")
            lines.extend(today_matches)
        return "\n".join(lines)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "⚽ ЧМ 2026: нет доступа — проверь API ключ"
        if e.code == 404:
            return "⚽ ЧМ 2026: турнир ещё не добавлен в API"
        return f"⚽ ЧМ 2026: ошибка {e.code}"
    except Exception as e:
        return f"⚽ ЧМ 2026: не удалось получить данные ({e})"

def get_world_cup_today():
    if not FOOTBALL_API_KEY:
        return "⚽ ЧМ 2026: добавь FOOTBALL_API_KEY в Railway Variables"
    try:
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        today_str = now_moscow.strftime("%Y-%m-%d")
        tomorrow_str = (now_moscow + timedelta(days=1)).strftime("%Y-%m-%d")
        lines = []
        data = football_request("https://api.football-data.org/v4/competitions/WC/matches?status=FINISHED")
        today_finished = []
        if data:
            for m in data.get("matches", []):
                utc_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                moscow_dt = utc_dt + timedelta(hours=3)
                if moscow_dt.strftime("%Y-%m-%d") == today_str:
                    home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name", "?")
                    away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name", "?")
                    score = m["score"]["fullTime"]
                    today_finished.append(f"  {home} {score['home']}:{score['away']} {away}")
        if today_finished:
            lines.append(f"⚽ ЧМ 2026 — результаты за {now_moscow.strftime('%d.%m')}:")
            lines.extend(today_finished)
        else:
            lines.append("⚽ ЧМ 2026: сегодня матчей не было")
        data2 = football_request("https://api.football-data.org/v4/competitions/WC/matches?status=SCHEDULED")
        tomorrow_matches = []
        if data2:
            for m in data2.get("matches", []):
                utc_dt = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
                moscow_dt = utc_dt + timedelta(hours=3)
                if moscow_dt.strftime("%Y-%m-%d") == tomorrow_str:
                    home = m["homeTeam"].get("shortName") or m["homeTeam"].get("name", "?")
                    away = m["awayTeam"].get("shortName") or m["awayTeam"].get("name", "?")
                    tomorrow_matches.append(f"  {moscow_dt.strftime('%H:%M')} | {home} — {away}")
        if tomorrow_matches:
            lines.append(f"\n🔜 Завтра ({(now_moscow + timedelta(days=1)).strftime('%d.%m')}):")
            lines.extend(tomorrow_matches)
        return "\n".join(lines)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return "⚽ ЧМ 2026: нет доступа — проверь API ключ"
        if e.code == 404:
            return "⚽ ЧМ 2026: турнир ещё не добавлен в API"
        return f"⚽ ЧМ 2026: ошибка {e.code}"
    except Exception as e:
        return f"⚽ ЧМ 2026: не удалось получить данные ({e})"

def get_weather():
    try:
        url = f"https://api.weather.yandex.ru/v2/forecast?lat={LAT}&lon={LON}&lang=ru_RU&limit=1"
        req = urllib.request.Request(url, headers={"X-Yandex-API-Key": YANDEX_WEATHER_KEY})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        fact = data["fact"]
        desc = CONDITIONS.get(fact["condition"], fact["condition"])
        return f"🌤 Погода в Санкт-Петербурге: {desc}, {fact['temp']}°C (ощущается как {fact['feels_like']}°C)"
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
        day_desc = CONDITIONS.get(day["condition"], day["condition"])
        night_desc = CONDITIONS.get(night["condition"], night["condition"])
        return (
            f"📅 Прогноз на завтра ({tomorrow['date']}), Санкт-Петербург:\n"
            f"☀️ День: {day_desc}, {day['temp_avg']}°C (ощущается как {day['feels_like']}°C)\n"
            f"🌙 Ночь: {night_desc}, {night['temp_avg']}°C (ощущается как {night['feels_like']}°C)"
        )
    except Exception as e:
        return f"📅 Прогноз: не удалось получить данные ({e})"

def get_weather_hourly(day_index=0, hours_from=None, hours_count=12):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}"
            f"&hourly=temperature_2m,weathercode"
            f"&timezone=Europe%2FMoscow&forecast_days=2"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())

        now_moscow = datetime.utcnow() + timedelta(hours=3)
        if hours_from is None:
            hours_from = now_moscow.hour

        today = now_moscow.strftime("%Y-%m-%d")
        tomorrow = (now_moscow + timedelta(days=1)).strftime("%Y-%m-%d")
        target_date = today if day_index == 0 else tomorrow
        label = "Прогноз на сегодня" if day_index == 0 else "Прогноз на завтра"

        times = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]
        codes = data["hourly"]["weathercode"]

        lines = []
        for t, temp, code in zip(times, temps, codes):
            if not t.startswith(target_date):
                continue
            hour = int(t[11:13])
            if day_index == 0 and hour < hours_from:
                continue
            emoji = WMO_EMOJI.get(code, "🌡")
            lines.append(f"{hour:02d}:00 {emoji} {round(temp)}°C")
            if len(lines) >= hours_count:
                break

        return f"🕐 {label}, Санкт-Петербург:\n\n" + "\n".join(lines)
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
            value = float(valute.find("Value").text.replace(",", "."))
            nominal = int(valute.find("Nominal").text)
            if char_code in ("USD", "EUR", "CNY"):
                rates[char_code] = round(value / nominal, 2)
        return (
            f"💵 Курс ЦБ:\n"
            f"  USD — {rates.get('USD', '?')}₽\n"
            f"  EUR — {rates.get('EUR', '?')}₽\n"
            f"  CNY — {rates.get('CNY', '?')}₽"
        )
    except:
        return "💵 Курс валют: не удалось получить данные"

def get_bitcoin():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=rub,usd"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        btc = data["bitcoin"]
        rub = f"{btc['rub']:,.0f}".replace(",", " ")
        usd = f"{btc['usd']:,.0f}".replace(",", " ")
        return f"₿ Bitcoin: {usd}$ / {rub}₽"
    except Exception as e:
        return f"₿ Bitcoin: не удалось получить данные ({e})"

def get_moex():
    try:
        url = "https://iss.moex.com/iss/engines/stock/markets/index/boards/SNDX/securities/IMOEX.json?iss.meta=off"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        cols = data["marketdata"]["columns"]
        rows = data["marketdata"]["data"]
        if not rows:
            return "📊 ММВБ: нет данных"
        last = rows[0][cols.index("CURRENTVALUE")]
        if last is None:
            return "📊 ММВБ: нет данных (рынок закрыт)"
        return f"📊 ММВБ (IMOEX): {last:,.2f}"
    except Exception as e:
        return f"📊 ММВБ: не удалось получить данные ({e})"

def get_nasdaq():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        change_pct = ((price - meta["previousClose"]) / meta["previousClose"] * 100) if meta.get("previousClose") else 0
        arrow = "📈" if change_pct >= 0 else "📉"
        return f"{arrow} NASDAQ: {price:,.2f} ({change_pct:+.2f}%)"
    except Exception as e:
        return f"📈 NASDAQ: не удалось получить данные ({e})"

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

def get_commands_text():
    return (
        "📋 Доступные команды:\n\n"
        "🌤 погода — погода сейчас\n"
        "📅 прогноз — прогноз на завтра\n"
        "🕐 часы — почасовой прогноз\n"
        "💵 курс — USD / EUR / CNY к рублю\n"
        "₿ биткоин — цена Bitcoin\n"
        "📊 ммвб — индекс Мосбиржи\n"
        "📊 nasdaq — индекс NASDAQ\n"
        "📰 новости — топ новости\n"
        "⚽ чм — все результаты ЧМ 2026\n"
        "🔮 гороскоп — все знаки на сегодня\n"
        "🔮 гороскоп Овен — гороскоп для знака\n"
        "👤 сколько отсутствовал Имя — время отсутствия\n"
        "🗳 голосование X или Y или Z — создать опрос\n"
        "🔔 напомнить \"19:30\" текст \"баня\" — напоминание\n"
        "📋 команды — список команд\n"
        "💬 любой вопрос — отвечу через AI\n\n"
        "Все команды пишутся через @Fuckbook1Bot"
    )

def ask_gpt(question: str, chat_id: str) -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        history = get_history(chat_id)
        history_text = "\n".join(f"{m['name']}: {m['text']}" for m in history)
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        messages = [
            {"role": "system", "content": f"Ты — Пятница, дружелюбный бот для группового чата друзей. Вариант 9. Отвечай коротко, по-русски, неформально. Сейчас московское время: {now_moscow.strftime('%H:%M')}.\n\nПоследние сообщения в чате:\n{history_text}"},
            {"role": "user", "content": question}
        ]
        response = client.chat.completions.create(model="gpt-4.1", messages=messages, max_tokens=500)
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
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    weather = get_weather()
    hourly = get_weather_hourly(day_index=0, hours_from=9, hours_count=14)
    currency = get_currency()
    bitcoin = get_bitcoin()
    moex = get_moex()
    nasdaq = get_nasdaq()
    news = get_news()
    await asyncio.sleep(2)
    wc = get_world_cup_results()
    text = (
        f"☀️ Доброе утро! Сводка на {now_moscow.strftime('%d.%m.%Y')}:\n\n"
        f"{weather}\n\n{hourly}\n\n"
        f"{currency}\n\n"
        f"{bitcoin}\n{moex}\n{nasdaq}\n\n"
        f"{news}\n\n"
        f"{wc}"
    )
    for chat_id in ALLOWED_CHAT_IDS:
        await context.bot.send_message(chat_id=chat_id, text=text)

async def daily_horoscope(context: ContextTypes.DEFAULT_TYPE):
    horoscope = get_horoscope_all()
    for chat_id in ALLOWED_CHAT_IDS:
        await context.bot.send_message(chat_id=chat_id, text=horoscope)

async def evening_forecast(context: ContextTypes.DEFAULT_TYPE):
    forecast = get_weather_hourly(day_index=1, hours_from=0, hours_count=24)
    await asyncio.sleep(2)
    wc = get_world_cup_today()
    text = f"🌙 Вечерняя сводка:\n\n{forecast}\n\n{wc}"
    for chat_id in ALLOWED_CHAT_IDS:
        await context.bot.send_message(chat_id=chat_id, text=text)

async def check_inactive_chats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()
    moscow_hour = (now.hour + 3) % 24
    if moscow_hour < 9 or moscow_hour >= 23:
        return
    chat_activity = load_json(LAST_CHAT_ACTIVITY_FILE)
    content_index = load_json(CONTENT_INDEX_FILE)
    for chat_id in ALLOWED_CHAT_IDS:
        chat_key = str(chat_id)
        if chat_key in chat_activity:
            last_time = datetime.fromisoformat(chat_activity[chat_key])
            if now - last_time >= timedelta(hours=INACTIVE_HOURS):
                idx = content_index.get(chat_key, 0)
                await context.bot.send_message(chat_id=chat_id, text=CONTENT[idx % len(CONTENT)])
                content_index[chat_key] = (idx + 1) % len(CONTENT)
                chat_activity[chat_key] = now.isoformat()
    save_json(LAST_CHAT_ACTIVITY_FILE, chat_activity)
    save_json(CONTENT_INDEX_FILE, content_index)

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
        last_time = get_last_seen_time(last_seen[user_id])
        delta = now - last_time
        if delta >= timedelta(hours=AWAY_THRESHOLD_HOURS):
            time_str = format_duration(delta)
            greeting = GREETINGS[user.id % len(GREETINGS)].format(name=user_name, time=time_str)
            await msg.reply_text(greeting)

    last_seen[user_id] = {"last_seen": now.isoformat(), "name": user_name}
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

        if re.search(r'^команды$', question, re.IGNORECASE):
            await msg.reply_text(get_commands_text())
        elif re.search(r'^погода$', question, re.IGNORECASE):
            await msg.reply_text(get_weather())
        elif re.search(r'^прогноз$', question, re.IGNORECASE):
            await msg.reply_text(get_weather_forecast())
        elif re.search(r'^часы$', question, re.IGNORECASE):
            await msg.reply_text(get_weather_hourly())
        elif re.search(r'^курс$', question, re.IGNORECASE):
            await msg.reply_text(get_currency())
        elif re.search(r'^биткоин$|^btc$', question, re.IGNORECASE):
            await msg.reply_text(get_bitcoin())
        elif re.search(r'^ммвб$|^moex$', question, re.IGNORECASE):
            await msg.reply_text(get_moex())
        elif re.search(r'^nasdaq$|^насдак$', question, re.IGNORECASE):
            await msg.reply_text(get_nasdaq())
        elif re.search(r'^новости$', question, re.IGNORECASE):
            await msg.reply_text(get_news())
        elif re.search(r'^чм$|^чм2026$|^футбол$', question, re.IGNORECASE):
            await msg.reply_text(get_world_cup_results())
        elif re.search(r'^гороскоп$', question, re.IGNORECASE):
            await msg.reply_text(get_horoscope_all())
        elif re.search(r'^гороскоп\s+\S+', question, re.IGNORECASE):
            sign = re.sub(r'^гороскоп\s+', '', question, flags=re.IGNORECASE).strip()
            await msg.reply_text(get_horoscope_one(sign))
        elif re.search(r'сколько отсутствовал|когда был[а]?', question, re.IGNORECASE):
            name = re.sub(r'сколько отсутствовал|когда был[а]?', '', question, flags=re.IGNORECASE).strip()
            await msg.reply_text(get_user_absence(name))
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
    app.job_queue.run_daily(morning_digest, time=time(6, 1))    # 09:01 МСК
    app.job_queue.run_daily(daily_horoscope, time=time(6, 2))   # 09:02 МСК
    app.job_queue.run_daily(evening_forecast, time=time(20, 0)) # 23:00 МСК
    print("Бот Пятница Про Вариант 9 запущен!")
    app.run_polling()
