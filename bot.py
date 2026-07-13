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
CHAT_MEMBERS_FILE = "chat_members.json"
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

PLAYER_TITLES = [
    "🏆 Легенда дня", "⭐ Звезда чата", "👑 Король/Королева дня",
    "🎯 Снайпер дня", "🔥 Огонь чата", "💎 Бриллиант дня",
    "🚀 Ракета дня", "🎭 Актёр дня", "🦁 Лев дня", "🧠 Мозг дня",
    "😎 Красавчик дня", "🌟 Суперзвезда", "💪 Силач дня",
    "🎪 Шоумен дня", "🏄 Сёрфер волн",
]

POLL_QUESTIONS = [
    ("Что лучше?", ["Море", "Горы", "Лес", "Город"]),
    ("Когда лучше просыпаться?", ["До 7 утра", "7-9 утра", "9-11 утра", "После 11"]),
    ("Что важнее?", ["Деньги", "Здоровье", "Любовь", "Свобода"]),
    ("Какой сезон лучший?", ["Весна", "Лето", "Осень", "Зима"]),
    ("Чем заняться в выходные?", ["Дома отдохнуть", "На природу", "С друзьями", "Хобби"]),
    ("Кофе или чай?", ["Кофе", "Чай", "Другое", "Не пью"]),
    ("Какое кино на вечер?", ["Комедия", "Боевик", "Триллер", "Документалка"]),
    ("Как отметить День рождения?", ["Дома с близкими", "В ресторане", "На природе", "Уехать"]),
    ("Что выберешь?", ["Много денег", "Здоровье", "Любовь", "Слава"]),
    ("Где комфортнее жить?", ["Большой город", "Маленький город", "Деревня", "Без разницы"]),
    ("Какой спорт смотреть?", ["Футбол", "Хоккей", "Теннис", "Не смотрю"]),
    ("Что слушаешь?", ["Русская музыка", "Зарубежная", "Классика", "Подкасты"]),
    ("Как провести отпуск?", ["Пляж и море", "Города", "Горы/походы", "Дома"]),
    ("Что важнее в работе?", ["Зарплата", "Коллектив", "Интерес", "Гибкий график"]),
    ("Домашнее животное?", ["Кошка", "Собака", "Другое", "Не хочу"]),
    ("Любимое время суток?", ["Утро", "День", "Вечер", "Ночь"]),
    ("Как отдыхаешь?", ["Активно", "Пассивно", "По настроению", "Какой отдых?"]),
    ("Что закажешь на ужин?", ["Пиццу", "Суши", "Бургер", "Домашнее"]),
    ("Ты сова или жаворонок?", ["Сова 🦉", "Жаворонок 🐦", "Ни то ни другое", "Смотря день"]),
    ("Как предпочитаешь общаться?", ["Лично", "Звонок", "Сообщения", "Как придётся"]),
]

JOKES = [
    "— Доктор, у меня проблемы с памятью.\n— И давно?\n— Что давно?",
    "— Ты чего грустный?\n— Жена ушла к соседу.\n— Найдёшь другую.\n— Другую найду, но в шашки кто играть будет?",
    "Программист открывает холодильник — видит молоко, яйца, масло. Закрывает. Думает: «Надо купить хлеб».",
    "— Как дела?\n— Как у Цезаря перед смертью.\n— Это как?\n— Всё шло хорошо, пока не началось.",
    "— Дорогой, ты меня слышишь?\n— ...\n— Дорогой!\n— Да. Я тебя слышу. Я не отвечаю.",
    "Объявление в зоопарке: «Не кормите крокодила. Последний, кто его кормил, тоже больше не кормит».",
    "— Почему ты ешь суп вилкой?\n— Диета. Так меньше влезает.",
    "— Дорогой, что хочешь на день рождения?\n— Ничего.\n— Хорошо, ничего и подарю.\n— Опять?!",
    "Сантехник: — Починю трубу за 5000 рублей.\n— Я меньше зарабатываю как хирург!\n— Я тоже, когда был хирургом.",
    "— Вовочка, сколько будет 7×8?\n— 56!\n— Как так быстро?\n— Заранее выучил ответ на самый страшный вопрос.",
    "Оптимист: стакан наполовину полон.\nПессимист: наполовину пуст.\nИнженер: стакан в два раза больше, чем нужно.",
    "— Ты что, снова за компьютером в 3 ночи?\n— Нет, сплю.\n— Но ты же отвечаешь!\n— Я отвечаю во сне. Это нормально.",
    "— Почему слон такой большой?\n— Потому что маленький слон много ел.\n— А почему много ел?\n— Потому что он большой.",
    "IT-шник умирает и попадает в ад. Везде WiFi, кофе, кондиционеры. Через неделю Дьявол: «Ошибка, тебе в рай». IT-шник: «Нет уж, у вас тут DevOps настроен».",
    "— Дорогая, я разбила твою любимую кружку.\n— Как?!\n— Я ударила ею твою вторую любимую кружку.",
    "Врач: — У вас две новости: хорошая и плохая.\n— Начните с хорошей.\n— Вам осталось жить 24 часа.\n— А плохая?\n— Я должен был сказать вчера.",
    "— Ты читал «Как стать богатым»?\n— Да.\n— Ну и как?\n— Теперь знаю: надо писать книги «Как стать богатым».",
    "— Доктор, мне кажется, что я невидимка.\n— Следующий!",
    "Начальник: — Вы опоздали третий раз на этой неделе. Знаете, что это значит?\nСотрудник: — Что сегодня среда?",
    "— Сколько психологов нужно, чтобы вкрутить лампочку?\n— Один, но лампочка должна сама этого захотеть.",
    "Ребёнок отцу: — Правда, что в некоторых странах муж и жена не знакомы до свадьбы?\n— Сынок, так везде. Это потом начинают узнавать друг друга.",
    "— Почему программисты путают Хэллоуин и Рождество?\n— Потому что Oct 31 = Dec 25.",
    "Муж возвращается — дома беспорядок.\nЖена: — Ты спрашивал, что я делаю целый день? Вот — сегодня ничего не делала.\nМуж: — А разница?\n— Не заметна, правда?",
    "— Дорогой, купи хлеб. И если будут яйца — возьми десяток.\nМуж вернулся с десятью батонами: — Яйца были.",
    "— Что общего между мужем и WiFi?\n— Когда рядом — не замечаешь. Когда исчезает — сразу чувствуешь.",
    "Человек приходит к психиатру:\n— Доктор, мой брат думает, что он курица.\n— Почему не лечите?\n— Нам нужны яйца.",
    "— Папа, а правда, что деньги не пахнут?\n— Правда, сынок. Именно поэтому их так сложно найти.",
    "Объявление: «Продаю парашют. Б/У. Один раз не раскрылся. Торг уместен».",
    "— Дорогой, я записалась на курсы вождения.\n— Это хорошо.\n— Кстати, где наш кот?\n— Это плохо.",
    "Учитель: — Вася, назови трёх великих русских писателей!\nВася: — Пушкин, Лермонтов... и... телефон разрядился.",
]

CONTENT = [
    '💬 «Жизнь — это то, что происходит с тобой, пока ты строишь другие планы.» — Джон Леннон',
    '🧠 Загадка: Что всегда идёт, но никуда не приходит? (Время)',
    '💬 «Единственный способ делать великую работу — любить то, что делаешь.» — Стив Джобс',
    '🧠 Загадка: Чем больше берёшь, тем больше становится. Что это? (Яма)',
    '💬 «В конце концов, не годы жизни считаются. Считается жизнь в годах.» — Авраам Линкольн',
    '🧠 Загадка: Без рук, без ног, а ворота открывает. Что это? (Ветер)',
    '💬 «Будь собой. Все остальные роли уже заняты.» — Оскар Уайльд',
    '🧠 Загадка: Сам не ест, а всех кормит. Что это? (Ложка)',
    '💬 «Успех — это умение идти от неудачи к неудаче, не теряя энтузиазма.» — Черчилль',
    '🧠 Загадка: Что можно сломать словами, но не руками? (Молчание)',
    '💬 «Счастье — это не станция назначения, а способ путешествовать.» — М. Л. Ранбек',
    '🧠 Загадка: Что видит каждый, но потрогать не может? (Тень)',
    '💬 «Лучшее время посадить дерево — 20 лет назад. Второе лучшее — сейчас.» — Китайская пословица',
    '🧠 Загадка: Чем больше сохнет, тем мокрее становится. Что это? (Полотенце)',
    '💬 «Воображение важнее знания.» — Альберт Эйнштейн',
    '🧠 Загадка: Два кольца, два конца, а посередине гвоздик. Что это? (Ножницы)',
    '💬 «Смелость — это не отсутствие страха, а преодоление его.» — Нельсон Мандела',
    '🧠 Загадка: Четыре брата под одной шляпой стоят. Что это? (Стол)',
    '💬 «Нет ничего постоянного, кроме перемен.» — Гераклит',
    '🧠 Загадка: Что есть у каждого, но никто не может дать другому? (Имя)',
    '💬 «Лучше зажечь одну свечу, чем проклинать темноту.» — Конфуций',
    '🧠 Загадка: Что можно поймать, но не кинуть? (Насморк)',
    '💬 «Жить — значит действовать.» — Оноре де Бальзак',
    '🧠 Загадка: Всегда во рту, но не проглотить. Что это? (Язык)',
    '💬 «Каждый день — это новая жизнь для мудрого человека.» — Уильям Блейк',
    '🧠 Загадка: Что бежит без ног? (Вода)',
    '💬 «Ошибка — это не неудача. Это урок.» — Генри Форд',
    '🧠 Загадка: Маленький, кругленький, а за хвост не поймаешь. Что это? (Клубок)',
    '💬 «Стремись не к успеху, а к тому, чтобы твоя жизнь имела смысл.» — Эйнштейн',
    '🧠 Загадка: Умирает — воняет, рождается — пахнет. Что это? (Свеча)',
    '💬 «В каждом человеке есть солнце. Только дайте ему светить.» — Сократ',
    '🧠 Загадка: Без чего хлеб не испечёшь? (Без корки)',
    '💬 «Тот, кто знает себя — просветлён.» — Лао-цзы',
    '🧠 Загадка: Что нужно поднять, чтобы опустить? (Якорь)',
    '💬 «Будущее принадлежит тем, кто верит в красоту своих мечтаний.» — Э. Рузвельт',
    '🧠 Загадка: Не море, не земля — корабли не плавают, ходить нельзя. Что это? (Болото)',
    '💬 «Ты не можешь изменить начало, но можешь изменить конец.» — К. С. Льюис',
    '🧠 Загадка: У двух матерей по пять сыновей, одно имя всем. Что это? (Пальцы)',
    '💬 «Делай что можешь, с тем что имеешь, там где ты есть.» — Теодор Рузвельт',
    '🧠 Загадка: Стоит без ног, висит без рук, всем путь кажет. Что это? (Указатель)',
    '💬 «Сначала они тебя не замечают, потом смеются, затем борются. А потом ты побеждаешь.» — Ганди',
    '💬 «Чем больше я узнаю людей, тем больше люблю собак.» — Марк Твен',
    '💬 «Мечтайте так, как будто будете жить вечно. Живите так, как будто умрёте сегодня.» — Джеймс Дин',
    '💬 «Великие умы обсуждают идеи. Средние — события. Мелкие — людей.» — Э. Рузвельт',
    '💬 «Жизнь — это 10% того, что с тобой происходит, и 90% того, как ты на это реагируешь.» — Свиндолл',
    '💬 «Единственное реальное путешествие — это взгляд другими глазами.» — Марсель Пруст',
    '💬 «Хочешь быть счастливым — будь им.» — Козьма Прутков',
    '💬 «Если хочешь изменить мир — начни с себя.» — Махатма Ганди',
    '💬 «Главное — никогда не переставать задавать вопросы.» — Альберт Эйнштейн',
    '💬 «Тысячемильное путешествие начинается с одного шага.» — Лао-цзы',
    '💬 «Самое тёмное время — перед рассветом.» — Томас Фуллер',
    '💬 «Где есть желание, найдётся и путь.» — Уильям Хэзлитт',
    '💬 «Творчество — это интеллект, получающий удовольствие.» — Альберт Эйнштейн',
    '💬 «Риск — это плата за возможность.» — Хью Джекман',
    '💬 «Не бойся медленно идти — бойся стоять на месте.» — Японская пословица',
    '💬 «Дорогу осилит идущий.» — Народная мудрость',
    '💬 «Тот, кто хочет — ищет возможности. Тот, кто не хочет — ищет причины.» — Сократ',
    '💬 «Молчание — лучший ответ дураку.» — Восточная мудрость',
    '💬 «Человеку нужно три вещи для счастья: кого любить, что делать и на что надеяться.» — Кант',
    '💬 «Не важно, как медленно ты идёшь — главное не останавливаться.» — Конфуций',
]

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

def get_chat_stats(chat_id: str) -> str:
    history = load_json(CHAT_HISTORY_FILE)
    messages = history.get(chat_id, [])
    if not messages:
        return "📊 Статистика: история пуста"
    counts = {}
    for m in messages:
        name = m.get("name", "?")
        counts[name] = counts.get(name, 0) + 1
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    total = sum(counts.values())
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"📊 Статистика чата (последние {len(messages)} сообщ.):\n"]
    for i, (name, count) in enumerate(sorted_counts):
        medal = medals[i] if i < 3 else f"{i+1}."
        pct = round(count / total * 100)
        lines.append(f"{medal} {name} — {count} сообщ. ({pct}%)")
    return "\n".join(lines)

def get_events() -> str:
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    today = now_moscow.date()
    year = today.year
    # (month, day, name, is_nonworking)
    holidays = [
        (1,  1,  "Новый год 🎆", True),
        (1,  7,  "Рождество Христово ⛪", True),
        (2,  14, "День святого Валентина 💝", False),
        (2,  23, "День защитника Отечества 🎖", True),
        (3,  8,  "Международный женский день 💐", True),
        (4,  1,  "День смеха 😂", False),
        (4,  12, "День космонавтики 🚀", False),
        (5,  1,  "Праздник весны и труда 🌸", True),
        (5,  9,  "День Победы 🎗", True),
        (6,  1,  "День защиты детей 👶", False),
        (6,  12, "День России 🇷🇺", True),
        (8,  22, "День Государственного флага РФ 🚩", False),
        (9,  1,  "День знаний 📚", False),
        (11, 4,  "День народного единства 🤝", True),
        (12, 31, "Новый год (канун) 🎄", False),
    ]
    upcoming = []
    for month, day, name, is_nonworking in holidays:
        try:
            event_date = datetime(year, month, day).date()
            if event_date < today:
                event_date = datetime(year + 1, month, day).date()
            delta = (event_date - today).days
            upcoming.append((delta, event_date, name, is_nonworking))
        except Exception:
            pass
    upcoming.sort()
    lines = ["🗓 Ближайшие праздники:\n"]
    for delta, evt_date, name, is_nonworking in upcoming[:5]:
        if delta == 0:
            when = "Сегодня!"
        elif delta == 1:
            when = "Завтра"
        elif delta <= 14:
            when = f"Через {delta} дн. ({evt_date.strftime('%d.%m')})"
        else:
            when = f"{evt_date.strftime('%d.%m')} (через {delta} дн.)"
        marker = " 🔴 выходной" if is_nonworking else ""
        lines.append(f"{when} — {name}{marker}")
    return "\n".join(lines)

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
        return f"{sign_name} — гороскоп на {date_str}:\n{response.choices[0].message.content}"
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
        return f"🔮 Гороскоп на {date_str}:\n\n{response.choices[0].message.content}"
    except Exception as e:
        return f"🔮 Гороскоп: ошибка ({e})"

def football_request(url):
    if not FOOTBALL_API_KEY:
        return None
    req = urllib.request.Request(url, headers={"X-Auth-Token": FOOTBALL_API_KEY, "User-Agent": "Mozilla/5.0"})
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
        all_dates = sorted(by_date.keys(), key=lambda d: datetime.strptime(d + ".2026", "%d.%m.%Y"))
        lines = ["⚽ ЧМ 2026 — последние результаты:\n"]
        for date_key in all_dates[-3:]:
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
        lines.append(f"⚽ ЧМ 2026 — результаты за {now_moscow.strftime('%d.%m')}:" if today_finished else "⚽ ЧМ 2026: сегодня матчей не было")
        lines.extend(today_finished)
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
        return f"⚽ ЧМ 2026: ошибка {e.code}"
    except Exception as e:
        return f"⚽ ЧМ 2026: не удалось получить данные ({e})"

def get_weather():
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               f"&current=temperature_2m,apparent_temperature,weathercode&timezone=Europe%2FMoscow")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        cur = data["current"]
        emoji = WMO_EMOJI.get(cur["weathercode"], "🌡")
        return (f"{emoji} Погода в Санкт-Петербурге: {round(cur['temperature_2m'])}°C "
                f"(ощущается как {round(cur['apparent_temperature'])}°C)")
    except Exception as e:
        return f"🌤 Погода: не удалось получить данные ({e})"

def get_weather_forecast():
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               f"&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,weathercode"
               f"&timezone=Europe%2FMoscow&forecast_days=2")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        d = data["daily"]
        emoji = WMO_EMOJI.get(d["weathercode"][1], "🌡")
        return (f"📅 Прогноз на завтра ({d['time'][1]}), Санкт-Петербург:\n"
                f"{emoji} День: {round(d['temperature_2m_max'][1])}°C (ощущается как {round(d['apparent_temperature_max'][1])}°C)\n"
                f"🌙 Ночь: {round(d['temperature_2m_min'][1])}°C (ощущается как {round(d['apparent_temperature_min'][1])}°C)")
    except Exception as e:
        return f"📅 Прогноз: не удалось получить данные ({e})"

def get_weather_hourly(day_index=0, hours_from=None, hours_count=12):
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
               f"&hourly=temperature_2m,weathercode&timezone=Europe%2FMoscow&forecast_days=2")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        if hours_from is None:
            hours_from = now_moscow.hour
        target_date = now_moscow.strftime("%Y-%m-%d") if day_index == 0 else (now_moscow + timedelta(days=1)).strftime("%Y-%m-%d")
        label = "Прогноз на сегодня" if day_index == 0 else "Прогноз на завтра"
        lines = []
        for t, temp, code in zip(data["hourly"]["time"], data["hourly"]["temperature_2m"], data["hourly"]["weathercode"]):
            if not t.startswith(target_date):
                continue
            hour = int(t[11:13])
            if day_index == 0 and hour < hours_from:
                continue
            lines.append(f"{hour:02d}:00 {WMO_EMOJI.get(code, '🌡')} {round(temp)}°C")
            if len(lines) >= hours_count:
                break
        return f"🕐 {label}, Санкт-Петербург:\n\n" + "\n".join(lines)
    except Exception as e:
        return f"🕐 Почасовой прогноз: не удалось получить данные ({e})"

def get_currency():
    try:
        with urllib.request.urlopen("https://www.cbr.ru/scripts/XML_daily.asp", timeout=10) as r:
            root = ET.parse(r).getroot()
        rates = {}
        for v in root.findall("Valute"):
            code = v.find("CharCode").text
            if code in ("USD", "EUR", "CNY"):
                rates[code] = round(float(v.find("Value").text.replace(",", ".")) / int(v.find("Nominal").text), 2)
        return f"💵 Курс ЦБ:\n  USD — {rates.get('USD','?')}₽\n  EUR — {rates.get('EUR','?')}₽\n  CNY — {rates.get('CNY','?')}₽"
    except:
        return "💵 Курс валют: не удалось получить данные"

def get_bitcoin():
    try:
        req = urllib.request.Request("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=rub,usd", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            btc = json.loads(r.read())["bitcoin"]
        return f"₿ Bitcoin: {btc['usd']:,.0f}$ / {btc['rub']:,.0f}₽".replace(",", " ")
    except Exception as e:
        return f"₿ Bitcoin: не удалось получить данные ({e})"

def get_moex():
    try:
        req = urllib.request.Request("https://iss.moex.com/iss/engines/stock/markets/index/boards/SNDX/securities/IMOEX.json?iss.meta=off", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        cols = data["marketdata"]["columns"]
        rows = data["marketdata"]["data"]
        if not rows:
            return "📊 ММВБ: нет данных"
        last = rows[0][cols.index("CURRENTVALUE")]
        return f"📊 ММВБ (IMOEX): {last:,.2f}" if last else "📊 ММВБ: нет данных (рынок закрыт)"
    except Exception as e:
        return f"📊 ММВБ: не удалось получить данные ({e})"

def get_nasdaq():
    try:
        req = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/%5EIXIC?interval=1d&range=1d", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            meta = json.loads(r.read())["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        change_pct = ((price - meta["previousClose"]) / meta["previousClose"] * 100) if meta.get("previousClose") else 0
        return f"{'📈' if change_pct >= 0 else '📉'} NASDAQ: {price:,.2f} ({change_pct:+.2f}%)"
    except Exception as e:
        return f"📈 NASDAQ: не удалось получить данные ({e})"

def get_news():
    try:
        req = urllib.request.Request("https://lenta.ru/rss/news", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            items = ET.parse(r).getroot().findall(".//item")[:3]
        return "📰 Новости:\n" + "\n".join(f"• {i.find('title').text}" for i in items)
    except:
        return "📰 Новости: не удалось получить данные"

def get_science_news():
    try:
        req = urllib.request.Request("https://ria.ru/export/rss2/science/index.xml", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            items = ET.parse(r).getroot().findall(".//item")[:3]
        return "🔬 Наука:\n" + "\n".join(f"• {i.find('title').text}" for i in items)
    except Exception as e:
        return f"🔬 Наука: не удалось получить данные ({e})"

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
        "🔬 наука — новости науки\n"
        "🗓 события — ближайшие праздники\n"
        "😂 анекдот — случайный анекдот\n"
        "🎲 рандом 1 100 — случайное число\n"
        "📊 статистика — кто больше всех пишет\n"
        "⚽ чм — результаты ЧМ 2026\n"
        "🔮 гороскоп — все знаки на сегодня\n"
        "🔮 гороскоп Овен — гороскоп для знака\n"
        "👤 сколько отсутствовал Имя\n"
        "🗳 голосование X или Y или Z\n"
        "🔔 напомнить \"19:30\" текст \"баня\"\n"
        "📋 команды — список команд\n"
        "💬 любой вопрос — отвечу через AI\n\n"
        "Все команды через @Fuckbook1Bot"
    )

def ask_gpt(question: str, chat_id: str) -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        history = get_history(chat_id)
        history_text = "\n".join(f"{m['name']}: {m['text']}" for m in history)
        now_moscow = datetime.utcnow() + timedelta(hours=3)
        messages = [
            {"role": "system", "content": f"Ты — Пятница, дружелюбный бот для группового чата друзей. Отвечай коротко, по-русски, неформально. Сегодня: {now_moscow.strftime('%d.%m.%Y')}, московское время: {now_moscow.strftime('%H:%M')}.\n\nПоследние сообщения в чате:\n{history_text}"},
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
    hour, minute = map(int, match.group(1).split(":"))
    reminder_text = match.group(2).strip()
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    event_time = now_moscow.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if event_time <= now_moscow:
        event_time += timedelta(days=1)
    notifications = []
    for minutes_before in [120, 60, 30, 0]:
        notify_at = event_time - timedelta(minutes=minutes_before)
        if notify_at > now_moscow:
            label = f"за {minutes_before} мин" if minutes_before > 0 else "в момент события"
            notifications.append({"minutes_before": minutes_before, "label": label, "notify_at": notify_at.isoformat(), "notified": False})
    if not notifications:
        return None
    return {"chat_id": chat_id, "text": reminder_text, "event_time": event_time.strftime("%H:%M"), "event_dt": event_time.isoformat(), "notifications": notifications}

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
    options = [o.strip() for o in re.split(r'\s+или\s+', text, flags=re.IGNORECASE) if o.strip()]
    return options if len(options) >= 2 else None

async def morning_digest(context: ContextTypes.DEFAULT_TYPE):
    now_moscow = datetime.utcnow() + timedelta(hours=3)
    text1 = (
        f"☀️ Доброе утро! Сводка на {now_moscow.strftime('%d.%m.%Y')}:\n\n"
        f"{get_weather()}\n\n{get_weather_hourly(day_index=0, hours_from=9, hours_count=14)}\n\n"
        f"{get_currency()}\n\n"
        f"{get_bitcoin()}\n{get_moex()}\n{get_nasdaq()}\n\n"
        f"{get_news()}\n\n{get_science_news()}\n\n{get_events()}"
    )
    await asyncio.sleep(2)
    text2 = get_world_cup_results()
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text1)
        except Exception as e:
            print(f"[morning_digest] text1 → {chat_id}: {e}")
        await asyncio.sleep(1)
        try:
            await context.bot.send_message(chat_id=chat_id, text=text2)
        except Exception as e:
            print(f"[morning_digest] text2 → {chat_id}: {e}")

async def daily_horoscope(context: ContextTypes.DEFAULT_TYPE):
    horoscope = get_horoscope_all()
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=horoscope)
        except Exception as e:
            print(f"[daily_horoscope] → {chat_id}: {e}")

async def player_of_day(context: ContextTypes.DEFAULT_TYPE):
    chat_members = load_json(CHAT_MEMBERS_FILE)
    for chat_id in ALLOWED_CHAT_IDS:
        members = chat_members.get(str(chat_id), {})
        if not members:
            continue
        name = members[random.choice(list(members.keys()))]
        title = random.choice(PLAYER_TITLES)
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"{title}\n\nСегодня им становится — {name}! 🎉\n\nПоздравляем, удачного дня!")
        except Exception as e:
            print(f"[player_of_day] → {chat_id}: {e}")

async def daily_poll_job(context: ContextTypes.DEFAULT_TYPE):
    content_index = load_json(CONTENT_INDEX_FILE)
    poll_idx = content_index.get("poll_index", 0)
    question, options = POLL_QUESTIONS[poll_idx % len(POLL_QUESTIONS)]
    content_index["poll_index"] = (poll_idx + 1) % len(POLL_QUESTIONS)
    save_json(CONTENT_INDEX_FILE, content_index)
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await context.bot.send_poll(chat_id=chat_id, question=f"🎯 Вопрос дня: {question}", options=options, is_anonymous=False)
        except Exception as e:
            print(f"[daily_poll] → {chat_id}: {e}")

async def evening_forecast(context: ContextTypes.DEFAULT_TYPE):
    forecast = get_weather_hourly(day_index=1, hours_from=0, hours_count=24)
    await asyncio.sleep(2)
    text = f"🌙 Вечерняя сводка:\n\n{forecast}\n\n{get_world_cup_today()}"
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"[evening_forecast] → {chat_id}: {e}")

async def check_inactive_chats(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()
    if (now.hour + 3) % 24 < 9 or (now.hour + 3) % 24 >= 23:
        return
    chat_activity = load_json(LAST_CHAT_ACTIVITY_FILE)
    content_index = load_json(CONTENT_INDEX_FILE)
    for chat_id in ALLOWED_CHAT_IDS:
        chat_key = str(chat_id)
        if chat_key in chat_activity:
            last_time = datetime.fromisoformat(chat_activity[chat_key])
            if now - last_time >= timedelta(hours=INACTIVE_HOURS):
                idx = content_index.get(chat_key, 0)
                try:
                    await context.bot.send_message(chat_id=chat_id, text=CONTENT[idx % len(CONTENT)])
                except Exception as e:
                    print(f"[check_inactive_chats] → {chat_id}: {e}")
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
                if not notif["notified"] and now_moscow >= datetime.fromisoformat(notif["notify_at"]):
                    try:
                        await context.bot.send_message(chat_id=int(chat_id), text=f"🔔 Напоминание ({notif['label']}):\n{reminder['text']} в {reminder['event_time']}")
                    except Exception as e:
                        print(f"[check_reminders] → {chat_id}: {e}")
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
            greeting = GREETINGS[user.id % len(GREETINGS)].format(name=user_name, time=format_duration(delta))
            await msg.reply_text(greeting)
    last_seen[user_id] = {"last_seen": now.isoformat(), "name": user_name}
    save_json(LAST_SEEN_FILE, last_seen)

    chat_members = load_json(CHAT_MEMBERS_FILE)
    if chat_id not in chat_members:
        chat_members[chat_id] = {}
    chat_members[chat_id][user_id] = user_name
    save_json(CHAT_MEMBERS_FILE, chat_members)

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
        elif re.search(r'^наука$', question, re.IGNORECASE):
            await msg.reply_text(get_science_news())
        elif re.search(r'^события$|^праздники$', question, re.IGNORECASE):
            await msg.reply_text(get_events())
        elif re.search(r'^анекдот$', question, re.IGNORECASE):
            await msg.reply_text(random.choice(JOKES))
        elif re.search(r'^рандом\s+\d+\s+\d+', question, re.IGNORECASE):
            parts = re.findall(r'\d+', question)
            if len(parts) >= 2:
                a, b = int(parts[0]), int(parts[1])
                mn, mx = min(a, b), max(a, b)
                await msg.reply_text(f"🎲 Случайное число от {mn} до {mx}: {random.randint(mn, mx)}")
            else:
                await msg.reply_text("Напиши так: @Fuckbook1Bot рандом 1 100")
        elif re.search(r'^статистика$', question, re.IGNORECASE):
            await msg.reply_text(get_chat_stats(chat_id))
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
                notif_times = "\n".join([f"  • {datetime.fromisoformat(n['notify_at']).strftime('%H:%M')} — {n['label']}" for n in reminder["notifications"]])
                await msg.reply_text(f"✅ Напоминание создано!\n📝 {reminder['text']}\n🕐 Событие в {reminder['event_time']}\n🔔 Уведомлю:\n{notif_times}")
            else:
                await msg.reply_text('❌ Не понял формат.\n\nИспользуй:\n@Fuckbook1Bot напомнить "19:30" текст "баня"')
        elif re.search(r'голосование', question, re.IGNORECASE):
            options = parse_poll(question)
            if options and len(options) >= 2:
                await context.bot.send_poll(chat_id=update.effective_chat.id, question="Голосуем! 🗳", options=options[:10], is_anonymous=False)
            else:
                await msg.reply_text("Напиши так: @Fuckbook1Bot голосование баня или кино или ресторан")
        else:
            await msg.reply_text(ask_gpt(question, chat_id))

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.job_queue.run_repeating(check_inactive_chats, interval=600, first=60)
    app.job_queue.run_repeating(check_reminders, interval=60, first=10)
    app.job_queue.run_daily(morning_digest, time=time(6, 1))     # 09:01 МСК
    app.job_queue.run_daily(daily_horoscope, time=time(6, 2))    # 09:02 МСК
    app.job_queue.run_daily(player_of_day, time=time(6, 3))      # 09:03 МСК
    app.job_queue.run_daily(daily_poll_job, time=time(8, 0))     # 11:00 МСК
    app.job_queue.run_daily(evening_forecast, time=time(20, 0))  # 23:00 МСК
    print("Бот Пятница Про Золотая сборка v9.6 запущен!")
    app.run_polling(drop_pending_updates=True)
