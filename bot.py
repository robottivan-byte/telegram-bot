# -*- coding: utf-8 -*-
"""Сбор новостей через Claude API (web search) и отправка постов на модерацию в Telegram."""
import json
import os
import time
import uuid

import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = os.environ["ADMIN_CHAT_ID"]

STATE_FILE = "state.json"
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

PROMPT = """Ты — редактор Telegram-канала логистической компании (международная логистика, \
грузоперевозки, таможня/ФТС, фитосанитарный контроль/Россельхознадзор, Роспотребнадзор, \
экспедирование грузов).

Найди через веб-поиск самые свежие новости (за последние 1-2 дня) по темам: изменения \
таможенного законодательства РФ и ЕАЭС, новости ФТС, фитосанитарные ограничения \
Россельхознадзора, санитарный контроль Роспотребнадзора, ставки фрахта и перевозки \
Китай-Россия, международные грузоперевозки, валютный контроль и платежи за рубеж \
(Китай, ОАЭ, Турция, расчёты в юанях), санкции и экспортный контроль, маркировка \
«Честный знак», сертификация и декларации соответствия ЕАС, очереди на погранпереходах \
и загрузка портов, тарифы и ограничения РЖД, e-commerce и лимиты беспошлинного ввоза \
посылок, утильсбор и импорт автомобилей, МТК «Север-Юг» и Севморпуть, агроэкспорт \
(квоты, пошлины, «Меркурий»), ГИС ЭПД и электронные перевозочные документы, \
курс юаня и доллара и его влияние на стоимость поставок.

Выбери 4-5 самых важных для импортёров/экспортёров новостей (разные темы, не повторяйся) \
и напиши по каждой готовый пост для Telegram-канала:
- деловой, но живой стиль; коротко (до 800 знаков);
- эмодзи в меру, факты с цифрами, в конце хэштеги (#логистика #таможня #ВЭД и т.п.);
- в конце поста — короткий призыв обратиться в компанию (экспедирование, таможенное \
оформление, доставка);
- только подтверждённые источниками факты, в конце поста строка "Источник: <URL>".

Раздели посты строкой ===POST=== (без другого текста до, между и после постов, кроме \
самих постов и разделителей)."""


def generate_posts():
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-5",
            "max_tokens": 8000,
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 12}],
            "messages": [{"role": "user", "content": PROMPT}],
        },
        timeout=600,
    )
    resp.raise_for_status()
    text = "".join(
        b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text"
    )
    posts = [
        p.strip() for p in text.split("===POST===")
        if len(p.strip()) > 100 and "#" in p  # отсекаем служебные фразы без хэштегов
    ]
    return posts[:6]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"offset": 0, "pending": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_for_moderation(post_id, text):
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Опубликовать", "callback_data": f"pub:{post_id}"},
            {"text": "❌ Отклонить", "callback_data": f"rej:{post_id}"},
        ]]
    }
    r = requests.post(
        f"{TG_API}/sendMessage",
        json={
            "chat_id": ADMIN_CHAT_ID,
            "text": "📝 Черновик поста:\n\n" + text[:3900],
            "reply_markup": keyboard,
            "disable_web_page_preview": True,
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["result"]["message_id"]


def main():
    posts = generate_posts()
    if not posts:
        requests.post(f"{TG_API}/sendMessage", json={
            "chat_id": ADMIN_CHAT_ID,
            "text": "⚠️ Сегодня не удалось собрать посты (нет свежих новостей или ошибка генерации).",
        }, timeout=30)
        return
    state = load_state()
    for text in posts:
        post_id = uuid.uuid4().hex[:8]
        msg_id = send_for_moderation(post_id, text)
        state["pending"][post_id] = {
            "text": text,
            "message_id": msg_id,
            "created": int(time.time()),
        }
    save_state(state)
    print(f"Отправлено на модерацию: {len(posts)}")


if __name__ == "__main__":
    main()
