# -*- coding: utf-8 -*-
"""Обработка входящих сообщений и кнопок модерации.

- Кнопки: публикация/отклонение черновиков, созданных bot.py.
- Текст от админа: рерайт через Claude (смысл сохраняется) и публикация в канал.
"""
import json
import os
import time

import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]  # @имя_канала или -100...
ADMIN_CHAT_ID = str(os.environ.get("ADMIN_CHAT_ID", ""))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REWRITE_PROMPT = """Полностью перепиши текст новости СВОИМИ словами для Telegram-канала \
логистической компании. Требования к рерайту:
- ни одно предложение не должно совпадать с оригиналом дословно;
- измени структуру подачи: другой порядок мыслей, другие формулировки, свой заголовок;
- сохрани все факты, цифры, названия и даты точно — их менять нельзя;
- ничего не выдумывай и не добавляй от себя;
- стиль: деловой, но живой; коротко; 1-2 уместных эмодзи;
- в конце 2-4 хэштега (#логистика #таможня #ВЭД и т.п.).
В ответе — ТОЛЬКО готовый текст поста, без пояснений.

Текст новости:
"""

STATE_FILE = "state.json"
TG_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
WEEK = 7 * 24 * 3600


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"offset": 0, "pending": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def rewrite(text):
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-5",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": REWRITE_PROMPT + text}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return "".join(
        b.get("text", "") for b in resp.json()["content"] if b.get("type") == "text"
    ).strip()


def tg_send(chat_id, text):
    return requests.post(f"{TG_API}/sendMessage", json={
        "chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True,
    }, timeout=30)


def handle_admin_message(msg):
    """Новость от админа: рерайт и публикация в канал."""
    text = msg.get("text") or ""
    if not text or text.startswith("/"):
        return
    try:
        post = rewrite(text)
        pub = tg_send(CHANNEL_ID, post)
        if pub.ok and pub.json().get("ok"):
            tg_send(msg["chat"]["id"], "✅ Опубликовано в канал:\n\n" + post)
        else:
            tg_send(msg["chat"]["id"], "⚠️ Рерайт готов, но публикация не удалась:\n\n"
                    + post + "\n\nОшибка: " + pub.text[:200])
    except Exception as e:  # noqa: BLE001
        tg_send(msg["chat"]["id"], f"⚠️ Ошибка рерайта: {e}")


def edit_draft(chat_id, message_id, text, status):
    requests.post(f"{TG_API}/editMessageText", json={
        "chat_id": chat_id,
        "message_id": message_id,
        "text": f"{status}\n\n{text[:3800]}",
        "disable_web_page_preview": True,
    }, timeout=30)


def main():
    state = load_state()
    r = requests.get(f"{TG_API}/getUpdates", params={
        "offset": state["offset"] + 1,
        "timeout": 0,
        "allowed_updates": '["callback_query","message"]',
    }, timeout=60)
    r.raise_for_status()
    changed = False

    for upd in r.json().get("result", []):
        state["offset"] = max(state["offset"], upd["update_id"])
        changed = True

        msg = upd.get("message")
        if msg and str(msg["chat"]["id"]) == ADMIN_CHAT_ID:
            handle_admin_message(msg)
            continue

        cq = upd.get("callback_query")
        if not cq:
            continue
        data = cq.get("data", "")
        action, _, post_id = data.partition(":")
        post = state["pending"].get(post_id)
        chat_id = cq["message"]["chat"]["id"]
        msg_id = cq["message"]["message_id"]

        if not post:
            answer = "Пост не найден (устарел)"
        elif action == "pub":
            pub = tg_send(CHANNEL_ID, post["text"])
            if pub.ok and pub.json().get("ok"):
                edit_draft(chat_id, msg_id, post["text"], "✅ ОПУБЛИКОВАНО")
                del state["pending"][post_id]
                answer = "Опубликовано в канал"
            else:
                answer = "Ошибка публикации: " + pub.text[:150]
        elif action == "rej":
            edit_draft(chat_id, msg_id, post["text"], "❌ ОТКЛОНЕНО")
            del state["pending"][post_id]
            answer = "Отклонено"
        else:
            answer = "Неизвестное действие"

        requests.post(f"{TG_API}/answerCallbackQuery", json={
            "callback_query_id": cq["id"], "text": answer,
        }, timeout=30)
        # Дублируем результат сообщением в личку — уведомление на кнопке
        # часто не успевает показаться из-за задержки обработки
        tg_send(chat_id, f"ℹ️ Результат нажатия кнопки: {answer}")

    # Чистка черновиков старше недели
    now = int(time.time())
    stale = [k for k, v in state["pending"].items() if now - v.get("created", now) > WEEK]
    for k in stale:
        del state["pending"][k]
        changed = True

    if changed:
        save_state(state)
    print(f"Обработано обновлений: {len(r.json().get('result', []))}")


if __name__ == "__main__":
    main()
