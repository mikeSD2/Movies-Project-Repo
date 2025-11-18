# rewrite_descriptions_with_gemini.py
import os
import sys
import json
import time
import signal
from collections import deque
from datetime import datetime

import requests
import random

try:
    import ijson
    HAS_IJSON = True
except Exception:
    HAS_IJSON = False

shutdown_requested = False

def handle_shutdown_signal(signum, frame):
    global shutdown_requested
    if not shutdown_requested:
        print("\nСигнал остановки получен. Завершаю текущую задачу…")
        shutdown_requested = True
    else:
        print("\nПовторный сигнал. Принудительный выход.")

signal.signal(signal.SIGINT, handle_shutdown_signal)
try:
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
except Exception:
    pass

SOURCE_JSON = "movies-data-sorted.json"
NDJSON_OUTPUT = "rewritten-descriptions.ndjson"

# Ротация ключей
from config_env import get_gemini_keys
GEMINI_API_KEYS = get_gemini_keys()
current_gemini_key_index = 0

MODELS = [
    #  "models/gemini-3-pro-preview", 
     "models/gemini-2.5-pro", "models/gemini-2.5-flash",
    # "models/gemini-2.5-flash-lite",
    # "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite"
]
current_model_index = 0
RATE_LIMITS = {
    # "models/gemini-3-pro-preview": 5, 
    "models/gemini-2.5-pro": 5, "models/gemini-2.5-flash": 10,
    # "models/gemini-2.5-flash-lite": 15,
    # "models/gemini-2.0-flash": 15, "models/gemini-2.0-flash-lite": 30,
}
rate_windows = {idx: deque() for idx in range(len(MODELS))}
last_429_at = {idx: 0.0 for idx in range(len(MODELS))}

def get_current_url():
    model = MODELS[current_model_index]
    current_key = GEMINI_API_KEYS[current_gemini_key_index]
    return f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={current_key}"

def wait_for_rate_slot(model_idx: int):
    name = MODELS[model_idx]
    rpm = RATE_LIMITS.get(name, 15)
    dq = rate_windows[model_idx]
    while True:
        now = time.time()
        while dq and (now - dq[0]) >= 60:
            dq.popleft()
        if len(dq) < rpm:
            dq.append(now)
            return
        sleep_for = max(1, int(60 - (now - dq[0]) + 1))
        print(f"    - Достигнут минутный лимит ({rpm} RPM) для {name}. Пауза {sleep_for}с...")
        time.sleep(sleep_for)

def rewrite_description_sync(
    description: str,
    title: str | None,
    year: int | None,
    original_title: str | None,
    country: str | None,
    category: str | None,
) -> str | None:
    global current_model_index, last_429_at, current_gemini_key_index
    description = description or ""
    title_for_prompt = (title or "").strip() or "это произведение"
    original_parenthetical = f" ({str(original_title).strip()})" if original_title and str(original_title).strip() else ""
    year_suffix = f" {year} года" if year else ""
    country_suffix = f", страна: {str(country).strip()}" if country and str(country).strip() else ""
    category_suffix = f", категория: {str(category).strip()}" if category and str(category).strip() else ""

    prompt = (
        "Я хочу, чтобы ты переписал предоставленный ниже текст-описание фильма в максимально очеловеченном, но при этом профессиональном и увлекательном стиле.\n"
        "Главная задача: Достигнуть эффекта 100% human-written текста без использования сленга, ругательств, неуместных вопросов к читателю или неуместно свободных выражений типа 'ну ты понимаешь' или 'короче'.\n"
        "Примени следующие стилистические изменения:\n"
        "Упрости синтаксис: Разбей длинные и сложные предложения на более короткие, используя при этом тире, двоеточия и точку с запятой для динамики где это уместно, а не только формальные союзы.\n"
        "Увеличь вовлеченность: Используй более активные глаголы. Старайся заменять 'мертвые' описания на более живые, но не сленговые, метафоры или идиомы, ТОЛЬКО ЕСЛИ ОНИ ЗВУЧАТ ЕСТЕСТВЕННО И УМЕСТНО (например, вместо 'его жизнь рушится' — 'его жизнь катится в пропасть'; вместо 'втянут в конфликт' — 'оказывается меж двух огней')."
        "КРИТИЧЕСКИ ВАЖНО: Эти примеры — лишь для иллюстрации стиля. Не используй их в итоговом тексте, чтобы избежать шаблонности. Ищи синонимы и аналогичные по духу, но уникальные выражения."
        "Опасайся 'псевдо-идиом': Избегай неуклюжих, грамматически неверных или вымученных попыток создать метафору (вроде 'верного плеча, всегда готового подставить его'). Если идиома не приходит на ум естественно и не вписывается в текст гладко, ИСПОЛЬЗУЙ ПРОСТОЕ, НО ЯСНОЕ И СИЛЬНОЕ ПРЕДЛОЖЕНИЕ без нее. Ясность и естественность важнее формального наличия метафоры."
        "Акцент на последствиях, а не на фактах: Если в сюжете происходит резкий поворотный момент (смерть, катастрофа, внезапный удар), который в исходнике описан сухо ('произошла трагедия'), не пытайся 'драматизировать' само событие ('в их мир врывается...'). Вместо этого, сделай резкий переход и сразу сфокусируйся на том, как это **мгновенно изменило жизнь** персонажей. Покажи 'что было' и 'что стало' после щелчка пальцев."
        "Введи интонацию: Сделай тон более разговорным и непосредственным, фокусируясь на внутренних переживаниях и желаниях персонажей ('он мечтал о покое' или 'она решила, что с неё хватит').\n"
        "Убери книжные клише: Избегай слишком формальных фраз типа 'внешне обычный семьянин', 'по мере развития событий' и 'таинственный покровитель'. Заменяй их на более живые, но уместные эквиваленты.\n"
        "Сохрани структуру: Текст должен быть связным, логичным и не рубленным (не должен выглядеть как набор телеграфных фраз). Он должен читаться как динамичный, но грамотный анонс фильма.\n"
        f"Вот текст произведения \"{title_for_prompt}\"{original_parenthetical}{year_suffix}{country_suffix}{category_suffix}, который ты должен переписать:\n"
        f"\"{description}\"\n"
        "Целевой объем и как его достичь (800-1200 символов).\n"
        "Если исходный текст слишком короткий, но ты знаешь дополнительную информацию о этом произведении, то смело добавляй ее в описание чтобы дотянуть описание хотя-бы до 800 символов, при этом придерживаясь правил \"человечности\" о которых сказано выше, НО КАТЕГОРИЧЕСКИ ВАЖНО что ты не должен придумывать ничего, используй дополнительную информацию ТОЛЬКО если ты точно знаешь что она точно относиться к ИМЕННО ЭТОМУ произведению. КРИТИЧЕСКИ ВАЖНО чтобы ты не перепутал части франшизы, то есть, например, не используй детали сюжета \"Никто 1\" для описания \"Никто 2\". Тщательно проверяй соответствие года и названия.\n"
        f"Если исходный текст оказался пустым (\"\") то напиши сам что знаешь о произведении \"{title_for_prompt}\"{original_parenthetical}{year_suffix}{country_suffix}{category_suffix}, опять-таки, придерживаясь всех правил \"человечности\", оформления и т.д., что даны тебе в этом промпте. НЕ ВЫДУМЫВАЙ факты и не путай части франшизы; сверься с годом, оригинальным названием, страной и категорией.\n"
        "Проверка на 'роботизированность' (Ритм): Это критически важно для 'человечности'. После того, как текст готов, мысленно перечитай его. Если он звучит слишком гладко, 'причёсанно' или монотонно — это плохо. Он будет обнаружен как ИИ. Чтобы избежать этого, ЦЕЛЕНАПРАВЛЕННО ВАРЬИРУЙ РИТМ. Убедись, что в тексте есть 'качели': рядом с длинными, плавными описаниями должны стоять короткие, 'ударные' фразы из 2-5 слов. Используй этот контраст длин и структур, чтобы текст 'дышал'. Живой текст не боится резких точек.\n"
        "Уникальность: Итоговый текст ОБЯЗАТЕЛЬНО должен быть уникальным (более 90% по сравнению с исходным \"Текстом\"). Для этого используй перефразирование и синонимы, но только там, где они не нарушают правила простоты и естественности.\n"
        "Оформление: Очень важно: Твой ответ должен содержать ТОЛЬКО итоговый переписанный текст. Категорически запрещено писать любой текст до или после него. Не должно быть предисловий ('Вот переписанный текст:'), разделителей, заголовков ('Переписанный текст:'), послесловий, уточнений, комментариев или любых итоговых вопросов и предложений ('Хотите, я найду...?', 'Могу ли я помочь...?' и т.д.). Только сам текст и ничего кроме него."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {"Content-Type": "application/json"}

    consec_5xx = 0
    backoff = 5

    attempts = 0
    max_attempts = 30
    consecutive_403 = 0

    while True:
        if attempts >= max_attempts:
            print(f"    - Достигнут лимит попыток ({max_attempts}). Пропуск.")
            return None
        if shutdown_requested:
            print("    - Операция рерайта прервана.")
            return None

        if current_model_index >= len(MODELS):
            print("\nЛимиты всех моделей для текущего ключа исчерпаны.")
            current_model_index = 0
            current_gemini_key_index += 1
            if current_gemini_key_index >= len(GEMINI_API_KEYS):
                print("Все API ключи исчерпали лимиты. Пауза 5 минут...")
                current_gemini_key_index = 0
                time.sleep(300)
            last_429_at = {idx: 0.0 for idx in range(len(MODELS))}
            print(f"Переключились на API ключ #{current_gemini_key_index + 1}.")
            continue

        model_name = MODELS[current_model_index]
        url = get_current_url()
        print(f"    - Рерайт через {model_name}...")
        wait_for_rate_slot(current_model_index)

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            if "candidates" in data and data.get("candidates"):
                content = data["candidates"][0].get("content", {})
                if "parts" in content and content.get("parts"):
                    return content["parts"][0].get("text")

            if "promptFeedback" in data and "blockReason" in data["promptFeedback"]:
                reason = data["promptFeedback"]["blockReason"]
                print(f"    - Контент заблокирован ({reason}). Пропуск.")
                return None

            print("    - Не удалось извлечь текст. Переключение модели и пауза 15с...")
            current_model_index += 1
            attempts += 1
            time.sleep(15)
            continue

        except requests.exceptions.RequestException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            detail = ""
            try:
                if getattr(e, "response", None) is not None:
                    detail = (e.response.text or "")[:300]
            except Exception:
                pass

            if status is not None:
                if status == 429:
                    now = time.time()
                    if (now - last_429_at[current_model_index]) > 120:
                        last_429_at[current_model_index] = now
                        print("    - 429 минутный. Пауза 61с…")
                        time.sleep(61)
                    else:
                        print("    - 429 дневной. Переключение модели…")
                        current_model_index += 1
                        attempts += 1
                    continue
                elif status == 403:
                    # Быстрая ротация ключа при 403, чтобы не застревать на одном ключе
                    consecutive_403 += 1
                    old_key_idx = current_gemini_key_index
                    current_gemini_key_index = (current_gemini_key_index + 1) % len(GEMINI_API_KEYS)
                    print(f"    - 403 Forbidden. Переключение API ключа #{old_key_idx + 1} -> #{current_gemini_key_index + 1}…")
                    # Если прошлись по всем ключам для этой модели — сменим модель
                    if consecutive_403 % len(GEMINI_API_KEYS) == 0:
                        current_model_index += 1
                        print("    - 403 на всех ключах для текущей модели. Переключение модели…")
                    attempts += 1
                    time.sleep(3)
                    continue
                elif status in [404, 400]:
                    print(f"    - Ошибка {status}. Переключение модели…")
                    current_model_index += 1
                    attempts += 1
                    continue
                elif status >= 500:
                    consec_5xx += 1
                    print(f"    - Сервер {status}. {('Подробности: ' + detail) if detail else ''}".strip())
                    if consec_5xx >= 3:
                        print("    - 5xx три раза подряд. Переключение модели…")
                        current_model_index += 1
                        attempts += 1
                        consec_5xx = 0
                        backoff = 5
                    else:
                        sleep_for = min(120, backoff + random.randint(0, 5))
                        print(f"    - Пауза {sleep_for}с…")
                        time.sleep(sleep_for)
                        backoff = min(120, backoff * 2)
                    continue

            print(f"    - Сеть/транспорт: {e}. Пауза 15с…")
            attempts += 1
            time.sleep(15)
            continue

def iter_movies_items(path: str):
    if HAS_IJSON:
        with open(path, "rb") as f:
            for item in ijson.items(f, "movies.item"):
                yield item
    else:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("movies", []):
                yield item

def load_existing_ids_from_ndjson(path: str) -> set[str]:
    ids = set()
    if not os.path.exists(path):
        return ids
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                mid = obj.get("id")
                if mid:
                    ids.add(mid)
            except Exception:
                continue
    return ids

def append_to_ndjson(mid: str, rewritten: str):
    rec = {"id": mid, "description": rewritten}
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(NDJSON_OUTPUT, "a", encoding="utf-8") as f:
        f.write(line)

def main():
    print(f"Источник: {SOURCE_JSON}")
    print(f"Вывод NDJSON: {NDJSON_OUTPUT}")

    existing_ids = load_existing_ids_from_ndjson(NDJSON_OUTPUT)
    print(f"Уже есть в NDJSON: {len(existing_ids)} записей")

    idx = -1
    written = 0
    skipped = 0

    for item in iter_movies_items(SOURCE_JSON):
        idx += 1
        if shutdown_requested:
            break

        mid = item.get("id")
        if not mid:
            continue

        if mid in existing_ids:
            skipped += 1
            if skipped % 1000 == 0:
                print(f"Пропущено по дубликатам: {skipped}")
            continue

        desc = item.get("description") or ""
        title = item.get("title")
        year = item.get("year")
        orig_title = item.get("originalTitle")
        country = item.get("country")
        category = item.get("category")

        print(f"[{idx}] {mid}: отправка на рерайт…")
        rewritten = rewrite_description_sync(desc, title, year, orig_title, country, category)

        # Если нажали Ctrl+C во время рерайта — ничего не пишем для текущего элемента
        if shutdown_requested:
            print(f"[{idx}] {mid}: остановлено пользователем — запись не произведена.")
            break

        if rewritten is None:
            print(f"[{idx}] {mid}: контент заблокирован, пропуск.")
            rewritten = ""
        else:
            rewritten = (rewritten or "").strip()
            print(f"[{idx}] {mid}: готово.")

        append_to_ndjson(mid, rewritten)
        existing_ids.add(mid)
        written += 1

        if shutdown_requested:
            break

    print(f"Готово. Новых строк: {written}, пропущено по дубликатам: {skipped}.")

if __name__ == "__main__":
    main()