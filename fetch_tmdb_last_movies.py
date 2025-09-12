import requests
import json
import os
import re
import time
from datetime import datetime
import calendar
import asyncio
from ddgs import DDGS
import sys
from collections import deque
import signal
import tempfile

# --- ГРЕЙСФУЛ ШАТДАУН ---
shutdown_requested = False

def handle_shutdown_signal(signum, frame):
    """Обработчик сигналов для чистого выхода."""
    global shutdown_requested
    if not shutdown_requested:
        print("\nСигнал остановки получен. Завершаю текущую задачу и сохраняюсь...")
        shutdown_requested = True
    else:
        print("\nПовторный сигнал. Принудительный выход.")
        sys.exit(1)

signal.signal(signal.SIGINT, handle_shutdown_signal)
signal.signal(signal.SIGTERM, handle_shutdown_signal)

# --- НОВЫЕ ФУНКЦИИ ДЛЯ NDJSON ---
def append_to_ndjson(filename, item_data):
    """Дописывает один объект в NDJSON файл атомарно."""
    try:
        # Сначала формируем полную строку, затем пишем за один вызов
        line_to_write = json.dumps(item_data, ensure_ascii=False, separators=(',', ':')) + '\n'
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(line_to_write)
    except IOError as e:
        print(f"  - !!! Ошибка записи в {filename}: {e}")

# --- КОНСТАНТЫ И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---

# Ключи API
TMDB_API_KEY = '636c87f3e6bbd33eae8ee8265c83082e'
GEMINI_API_KEY = "AIzaSyCI0qt3OOliBaM_QOztawFqmBMo5AGw_kY"

# URL и пути
LIST_BASE_URL = 'https://api.themoviedb.org/3/discover/movie'
DETAILS_BASE_URL = 'https://api.themoviedb.org/3/movie/'
JSON_DATA_FILE = 'movies-data.json'
NDJSON_OUTPUT_FILE = 'movies-data.ndjson'
UPLOADS_DIR = 'uploads/posts'

# рядом с остальными URL/путями
TV_LIST_BASE_URL = 'https://api.themoviedb.org/3/discover/tv'
TV_DETAILS_BASE_URL = 'https://api.themoviedb.org/3/tv/'
PERSON_DETAILS_BASE_URL = 'https://api.themoviedb.org/3/person/'

# кэш для имён персон
_PERSON_CACHE: dict[int, str] = {}

os.makedirs(UPLOADS_DIR, exist_ok=True)

# Словарь для транслитерации
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

# Словари для перевода
MONTH_TRANSLATION = {
    'January': 'января', 'February': 'февраля', 'March': 'марта',
    'April': 'апреля', 'May': 'мая', 'June': 'июня',
    'July': 'июля', 'August': 'августа', 'September': 'сентября',
    'October': 'октября', 'November': 'ноября', 'December': 'декабря'
}
COUNTRY_TRANSLATION = {
    "USA": "США", "United States of America": "США",
    "United Kingdom": "Великобритания", "UK": "Великобритания",
    "France": "Франция", "Germany": "Германия", "Spain": "Испания",
    "Italy": "Италия", "Canada": "Канада", "Australia": "Австралия",
    "Japan": "Япония", "South Korea": "Южная Корея", "Korea, South": "Южная Корея",
    "China": "Китай", "India": "Индия", "Russia": "Россия",
    "Sweden": "Швеция", "Norway": "Норвегия", "Denmark": "Дания",
    "Finland": "Финляндия", "Brazil": "Бразилия", "Mexico": "Мексика",
    "Argentina": "Аргентина", "Netherlands": "Нидерланды", "Belgium": "Бельгия",
    "Switzerland": "Швейцария", "Ireland": "Ирландия", "New Zealand": "Новая Зеландия",
    "Hong Kong": "Гонконг", "Taiwan": "Тайвань", "Turkey": "Турция"
}

# Настройки для Gemini API
MODELS = [
    "models/gemini-2.0-flash", "models/gemini-2.5-pro", "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash", "models/gemini-2.0-flash-lite"
]
current_model_index = 0
RATE_LIMITS = {
    "models/gemini-2.5-pro": 5, "models/gemini-2.5-flash": 10, "models/gemini-2.5-flash-lite": 15,
    "models/gemini-2.0-flash": 15, "models/gemini-2.0-flash-lite": 30,
}
rate_windows = {idx: deque() for idx in range(len(MODELS))}
last_429_at = {idx: 0.0 for idx in range(len(MODELS))}

# Прочие константы
GENRE_MAP = {
    28: "Боевик", 12: "Приключения", 16: "Мультфильм", 35: "Комедия", 80: "Криминал", 
    99: "Документальный", 18: "Драма", 10751: "Семейный", 14: "Фэнтези", 36: "История", 
    27: "Ужасы", 10402: "Музыка", 9648: "Детектив", 10749: "Мелодрама", 878: "Фантастика",
    10770: "Телевизионный фильм", 53: "Триллер", 10752: "Военный", 37: "Вестерн"
}
CATEGORY_GENRE_NAMES = {
    "filmy": "Фильмы", "multfilmy": "Мультфильмы", "anime": "Аниме", "serialy": "Сериалы"
}

# приоритет должностей для сериалов/аниме
JOB_WEIGHTS = {
    'Chief Director': 6,
    'Series Director': 5,
    'Director': 4,
    'Supervising Director': 3,
    'Co-Director': 2,
    'Episode Director': 1,
    'Assistant Director': 0,
}

# --- ФУНКЦИИ РЕРАЙТА ОПИСАНИЯ ---
def get_current_url():
    model = MODELS[current_model_index]
    return f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"

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

def rewrite_description_sync(description: str) -> str | None:
    """
    Отправляет описание в Gemini API.
    В случае неудачи повторяет попытки, меняя модели, до успешного выполнения.
    Возвращает None, если контент заблокирован API.
    """
    global current_model_index, last_429_at
    if not description: return ""

    prompt = (
        "Перепиши пожалуйста это описание фильма так чтобы оно звучало просто, без эпитетов, метафор и поэтичности. Описание сюжета должно быть в формате или 'Сюжет разворачивается вокруг...' или 'В центре повествования находится...' или 'Это история о...' или 'История вращается вокруг...' или 'Главный герой этой истории ...' и тому подобное. Чтобы было просто, но интригующе чтобы заитересовать человека к просмотру. "
        "Текст:\n" f'"{description}\n"'
        "Изо всех сил старайся довести колличество символов до 1000 не выдумывая и не повторяя уже сказанное, но пытаясь писать развернуто чтобы получилось одно целостное описание фильма. Уникальность итогового текста ОБЯЗАТЕЛЬНО должна быть БОЛЕЕ 90% поэтому ВАЖНО чтобы ты старался использовать перефразирование и синонимы (особенно в первом абзаце) где они уместны и не делают текст странным."
        "Очень важно чтобы ты не давал никаких предисловий по типу 'Вот переписанный текст:' и послесловий к тексту который был тобой переписан, должен быть только переписаный текст согласно тому как я сказал."
    )
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    while True:
        if shutdown_requested:
            print("    - Операция рерайта прервана из-за сигнала остановки.")
            return ""

        if current_model_index >= len(MODELS):
            print("\nЛимиты всех доступных моделей исчерпаны. Сбрасываем и ждем 5 минут...")
            current_model_index = 0
            time.sleep(300)
            continue

        model_name = MODELS[current_model_index]
        url = get_current_url()
        print(f"    - Рерайт через {model_name}...")
        wait_for_rate_slot(current_model_index)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'candidates' in data and data.get('candidates'):
                content = data['candidates'][0].get('content', {})
                if 'parts' in content and content.get('parts'):
                    return content['parts'][0].get('text')
            
            if 'promptFeedback' in data and 'blockReason' in data['promptFeedback']:
                reason = data['promptFeedback']['blockReason']
                print(f"    - Контент заблокирован (причина: {reason}). Рерайт невозможен, фильм будет пропущен.")
                return None

            print("    - Не удалось извлечь текст (неизвестная структура ответа). Переключение модели и пауза 15с...")
            current_model_index += 1
            time.sleep(15)
            continue

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                status_code = e.response.status_code
                if status_code == 429:
                    now = time.time()
                    if (now - last_429_at[current_model_index]) > 120:
                        last_429_at[current_model_index] = now
                        print(f"    - Ошибка 429 (минутный лимит). Пауза 61с и повтор...")
                        time.sleep(61)
                    else:
                        print(f"    - Повторная 429 (дневной лимит). Переключение модели...")
                        current_model_index += 1
                    continue
                elif status_code in [404, 400]:
                    print(f"    - Ошибка {status_code}. Переключение модели...")
                    current_model_index += 1
                    continue
                elif status_code >= 500:
                    print(f"    - Временная ошибка сервера ({status_code}). Пауза 15с...")
                    time.sleep(15)
                    continue
            print(f"    - Ошибка сети: {e}. Пауза 15с...")
            time.sleep(15)
            continue
        except Exception as e:
            print(f"    - Неизвестная ошибка при рерайте: {e}. Пауза 15с...")
            time.sleep(15)
            continue

# --- ФУНКЦИИ ПОИСКА KINOPOISK ID ---
ddgs_client = DDGS(timeout=10)
TOKENS_OK = 0.7

def _norm(s: str) -> str:
    s = (s or '').lower().replace('ё', 'е')
    s = re.sub(r'["“”«»\'`’‘-]', '', s) 
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _tokenize(s: str) -> list[str]:
    # допускаем короткие названия типа F1
    return [t for t in re.findall(r'[a-zа-яё0-9]+', _norm(s), flags=re.I) if len(t) >= 1]

def is_informative_name(name: str | None) -> bool:
    if not name: return False
    n = name.strip()
    if not n or n.lower() == 'неизвестно': return False
    return bool(re.search(r'[A-Za-zА-Яа-яЁё]', n))

def pick_informative_from_csv(csv: str | None) -> str | None:
    if not csv: return None
    for item in csv.split(','):
        item = item.strip()
        if is_informative_name(item):
            return item
    return None

def pick_informative_actor(actors_csv: str | None) -> str | None:
    return pick_informative_from_csv(actors_csv)

def _tokens_score(expected: str, candidate: str) -> float:
    exp = set(_tokenize(expected))
    if not exp: return 0.0
    cand = set(_tokenize(candidate))
    return len(exp & cand) / len(exp) if len(exp) > 0 else 0.0

async def _get_kinopoisk_id_from_search(query: str, expected_title: str, expected_original_title: str | None, expected_year: int, is_series: bool):
    site_filter = 'site:www.kinopoisk.ru/series/' if is_series else 'site:www.kinopoisk.ru/film/'
    full_query = f'{query} {site_filter} -site:hd.kinopoisk.ru -"смотреть онлайн в хорошем"'
    
    print(f"    - DDG Query: {full_query}")

    try:
        results = await asyncio.to_thread(
            ddgs_client.text, full_query, max_results=5, region='ru-ru', safesearch='off'
        )
        exp_title_norm = _norm(expected_title)
        exp_orig_title_norm = _norm(expected_original_title) if expected_original_title else None
        year_str = str(expected_year or '').strip()
        
        print("    - DDG Results:")
        for i, result in enumerate(results or []):
            url = result.get('href', '')
            title_field = result.get('title') or ''
            snippet = result.get('body') or ''
            
            ellipsis_pos = snippet.find('...')
            if ellipsis_pos != -1:
                snippet = snippet[:ellipsis_pos]

            print(f"      [{i+1}] Title: {title_field}")
            print(f"          Body (processed): {snippet[:150]}...")
            print(f"          URL: {url}")

            title_norm = _norm(title_field)
            body_norm = _norm(snippet)
            
            m = re.search(r'kinopoisk\.ru/(film|series)/(\d+)', url)
            if not m:
                print("          -> Skip: Not a film/series page.")
                continue

            url_type, kp_id = m.group(1), m.group(2)
            if (is_series and url_type != 'series') or (not is_series and url_type != 'film'):
                print(f"          -> Skip: Expected {'series' if is_series else 'film'}, got {url_type}.")
                continue

            # --- НОВАЯ СВЕРХ-СТРОГАЯ ЛОГИКА ---
            # ШАГ 1: ОБЯЗАТЕЛЬНАЯ ПРОВЕРКА РЕЛЕВАНТНОСТИ ЗАГОЛОВКА (`title_field`)
            title_score_ru = _tokens_score(expected_title, title_field)
            title_score_orig = _tokens_score(expected_original_title, title_field) if exp_orig_title_norm else 0.0
            is_title_relevant = (title_score_ru >= 0.4) or (title_score_orig >= 0.4)

            if not is_title_relevant:
                print(f"          -> Skip: Title field '{title_field}' is not relevant enough (scores ru:{title_score_ru:.2f}, orig:{title_score_orig:.2f}).")
                continue

            # ШАГ 2: ПОИСК ПОДТВЕРЖДЕННОГО СОВПАДЕНИЯ (название + год)
            if year_str and (year_str in title_norm):
                print(f"          -> Checks: title_ok=True (relevant), year_ok=True (in title field)")
                print(f"          -> ACCEPT. ID: {kp_id}")
                return kp_id

            body_has_title_ru = (exp_title_norm in body_norm) or (_tokens_score(expected_title, snippet) >= TOKENS_OK)
            body_has_title_orig = exp_orig_title_norm and ((exp_orig_title_norm in body_norm) or (_tokens_score(expected_original_title, snippet) >= TOKENS_OK))
            body_has_title = body_has_title_ru or body_has_title_orig
            body_has_year = year_str in body_norm

            year_ok_in_body = False
            if body_has_title and body_has_year:
                title_pos = -1
                search_title = exp_title_norm if body_has_title_ru else exp_orig_title_norm
                try:
                    if search_title: title_pos = body_norm.index(search_title)
                except (ValueError, TypeError): pass

                if title_pos != -1:
                    search_context = body_norm[title_pos:]
                    if year_str in search_context:
                        year_ok_in_body = True
            
            print(f"          -> Checks: title_ok={body_has_title} (in body), year_ok={year_ok_in_body} (in body after title)")

            if year_ok_in_body:
                print(f"          -> ACCEPT. ID: {kp_id}")
                return kp_id
        
        print("    - No suitable results found.")
        return None
    except Exception as e:
        print(f"  Ошибка при поиске '{query}': {e}")
        return None

def _make_kp_query(info: dict, mode: str, is_series: bool) -> str:
    title = info.get('title') or ''
    year = str(info.get('year') or '')
    parts = [f'"{title}"', f'"{year}"']

    if mode == 'director' and is_informative_name(info.get('director')):
        parts.append(f'"{info["director"]}"')
    elif mode == 'creator' and is_informative_name(info.get('creator')):
        parts.append(f'"{info["creator"]}"')
    elif mode == 'producer':
        prod = pick_informative_from_csv(info.get('producers'))
        if prod: parts.append(f'"{prod}"')
    elif mode == 'writer':
        wr = pick_informative_from_csv(info.get('writers'))
        if wr: parts.append(f'"{wr}"')
    elif mode == 'actor':
        actor_hint = pick_informative_actor(info.get('actors'))
        if actor_hint: parts.append(f'"{actor_hint}"')
    elif mode == 'premiere' and info.get('premiere'):
        parts.append(f'"{info["premiere"]}"')

    if is_series:
        parts.append('"сезон"')
    return ' '.join(parts)

async def find_kinopoisk_id(movie_info: dict) -> str | None:
    is_series = movie_info['category'] in ['serialy', 'anime']
    stages = []
    if is_informative_name(movie_info.get('director')): stages.append('director')
    if is_informative_name(movie_info.get('creator')): stages.append('creator')
    if pick_informative_from_csv(movie_info.get('producers')): stages.append('producer')
    if pick_informative_from_csv(movie_info.get('writers')): stages.append('writer')
    if pick_informative_actor(movie_info.get('actors')): stages.append('actor')
    if movie_info.get('premiere'): stages.append('premiere')
    if not stages: stages.append('basic')

    for round_num in range(1, 2+1):
        for stage in stages:
            query = _make_kp_query(movie_info, stage, is_series)
            print(f"  Попытка {round_num}, hint: {stage}...")
            kp_id = await _get_kinopoisk_id_from_search(
                query,
                movie_info['title'],
                movie_info.get('originalTitle'),
                movie_info['year'],
                is_series
            )
            if kp_id:
                return kp_id
            await asyncio.sleep(0.5)
        if round_num == 1:
            print("  ID не найден в первом раунде, начинаю второй...")
    return None

# --- ФУНКЦИИ TMDB И ОБРАБОТКИ ДАННЫХ ---

def fetch_page_current_month(api_key, page, media_type='movie'):
    now = datetime.now()
    start_of_month = now.replace(day=1).strftime('%Y-%m-%d')
    _, last_day_num = calendar.monthrange(now.year, now.month)
    end_of_month = now.replace(day=last_day_num).strftime('%Y-%m-%d')

    if media_type == 'movie':
        url = LIST_BASE_URL
        params = {
            'api_key': api_key,
            'sort_by': 'popularity.desc',
            'primary_release_date.gte': start_of_month,
            'primary_release_date.lte': end_of_month,
            'page': page,
            'language': 'ru-RU'
        }
    else:
        url = TV_LIST_BASE_URL
        params = {
            'api_key': api_key,
            'sort_by': 'popularity.desc',
            'first_air_date.gte': start_of_month,
            'first_air_date.lte': end_of_month,
            'page': page,
            'language': 'ru-RU'
        }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"\nЗапрашиваем страницу {page} ({media_type}) за {now.strftime('%Y-%m')} с TMDb... (попытка {attempt + 1}/{max_retries})")
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Ошибка при запросе страницы {page} ({media_type}) с TMDb: {e}")
            if attempt < max_retries - 1:
                print("Пауза 15 секунд перед повторной попыткой...")
                time.sleep(15)
            else:
                print("!!! КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить данные от TMDb после нескольких попыток.")
    return None

def get_details(api_key, media_id, media_type='movie'):
    """
    Получает детальную информацию о фильме или сериале с надежным механизмом повторных попыток.
    """
    max_short_retries = 5
    short_retry_delay = 10  # seconds
    long_retry_delay = 60   # seconds

    params = {
        'api_key': api_key,
        'language': 'ru-RU',
        'append_to_response': 'credits,videos'
    }
    base_url = DETAILS_BASE_URL if media_type == 'movie' else TV_DETAILS_BASE_URL
    url = f"{base_url}{media_id}"

    attempt = 0
    while not shutdown_requested:
        attempt += 1
        
        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            if attempt > 1:
                print(f"  - Детали для {media_type} ID {media_id} успешно получены с попытки #{attempt}.")
            return response.json()

        except requests.RequestException as e:
            status_code = e.response.status_code if e.response is not None else None
            
            if status_code in [401, 404]:
                print(f"  - !!! Критическая ошибка {status_code} при получении деталей для ID {media_id}. Пропуск.")
                return None

            print(f"  - Ошибка при получении деталей для ID {media_id} (попытка {attempt}): {e}")
            
            current_try_in_batch = (attempt - 1) % max_short_retries
            
            if current_try_in_batch < (max_short_retries - 1):
                sleep_duration = short_retry_delay
                print(f"    - Пауза {sleep_duration}с перед следующей быстрой попыткой...")
            else:
                sleep_duration = long_retry_delay
                print(f"    - Все {max_short_retries} быстрых попыток не удались. Пауза {sleep_duration}с...")

            # Прерываемый sleep
            for _ in range(sleep_duration):
                if shutdown_requested: break
                time.sleep(1)
            
            if shutdown_requested: break
    
    print(f"  - Получение деталей для ID {media_id} прервано.")
    return None

def slugify(text):
    if not text:
        return ""
    text = text.lower().strip()
    translit_text = ""
    for char in text:
        translit_text += TRANSLIT_MAP.get(char, char)
    slug = re.sub(r'[^a-z0-9\s-]', '', translit_text)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug

def director_job_weight(member) -> int:
    job = (member.get('job') or '').strip()
    if job in JOB_WEIGHTS:
        return JOB_WEIGHTS[job]
    best = -1
    for j in (member.get('jobs') or []):
        jw = JOB_WEIGHTS.get((j.get('job') or '').strip(), -1)
        if jw > best:
            best = jw
    return best

def format_season(n: int | None) -> str | None:
    if not n or n <= 0:
        return None
    n_mod10 = n % 10
    n_mod100 = n % 100
    if n_mod10 == 1 and n_mod100 != 11:
        suf = "сезон"
    elif n_mod10 in (2,3,4) and n_mod100 not in (12,13,14):
        suf = "сезона"
    else:
        suf = "сезонов"
    return f"{n} {suf}"

def transform_data_pre_checks(details, category, media_type):
    credits = details.get('credits') or {}
    crew = credits.get('crew', []) or []

    # режиссёр
    director = "Неизвестно"
    director_candidates = [m for m in crew if director_job_weight(m) > 0]
    if director_candidates:
        best = max(director_candidates, key=lambda m: (director_job_weight(m), (m.get('episode_count') or 0)))
        director = get_person_name_ru(best.get('id'), best.get('name') or "")
    elif media_type == 'tv' and details.get('created_by'):
        c = (details.get('created_by') or [])[0]
        director = get_person_name_ru(c.get('id'), c.get('name') or "")

    # актёры
    actors = [a.get('name') for a in (credits.get('cast') or [])[:10] if a.get('name')]
    actors_csv = ", ".join(actors) if actors else None

    # создатель/продюсеры/сценаристы — для подсказок
    creator_name = None
    if details.get('created_by'):
        c = (details.get('created_by') or [])[0]
        creator_name = get_person_name_ru(c.get('id'), c.get('name') or "")

    PRODUCER_JOBS = {'Executive Producer', 'Producer'}
    WRITER_JOBS = {'Writer', 'Screenplay', 'Series Composition'}

    def collect_people_by_jobs(jobs: set[str]) -> list[str]:
        seen, out = set(), []
        for m in crew:
            j = (m.get('job') or '').strip()
            if j in jobs:
                name = get_person_name_ru(m.get('id'), m.get('name') or "")
                if name and name not in seen:
                    seen.add(name); out.append(name)
        return out

    producers_csv = ", ".join(collect_people_by_jobs(PRODUCER_JOBS)) or None
    writers_csv = ", ".join(collect_people_by_jobs(WRITER_JOBS)) or None

    # трейлер
    trailer_url, youtube_id = None, None
    for v in (details.get('videos') or {}).get('results', []):
        if v.get('site') == 'YouTube' and v.get('type') == 'Trailer':
            youtube_id = v.get('key')
            if youtube_id:
                trailer_url = f"https://www.youtube.com/watch?v={youtube_id}"
            break

    # названия/даты/сезоны
    if media_type == 'movie':
        release_date = details.get('release_date')
        original_title = details.get('original_title', '')
        title = details.get('title', '')
        season_str = None
        is_adult = details.get('adult', False)
    else:
        release_date = details.get('first_air_date')
        original_title = details.get('original_name', '')
        title = details.get('name', '')
        season_str = format_season(details.get('number_of_seasons'))
        is_adult = False

    # премьера/год
    year = None
    premiere_rus = None
    if release_date:
        try:
            dt_obj = datetime.strptime(release_date, '%Y-%m-%d')
            year = dt_obj.year
            day = dt_obj.day
            month_eng = dt_obj.strftime('%B')
            rus_month = MONTH_TRANSLATION.get(month_eng, month_eng)
            premiere_rus = f"{day} {rus_month} {year}"
        except ValueError:
            pass

    # жанры (без «Сериалы»)
    genres = [GENRE_MAP.get(g['id']) for g in details.get('genres', []) if GENRE_MAP.get(g['id'])]

    # страна
    country_eng = "Неизвестно"
    if details.get('production_countries'):
        country_eng = details.get('production_countries')[0].get('name') or "Неизвестно"
    country_rus = COUNTRY_TRANSLATION.get(country_eng, country_eng)

    # слаг (приоритет у русского названия для SEO)
    slug_id = slugify(title) or slugify(original_title)

    return {
        "id": slug_id,
        "category": category,
        "title": title,
        "year": year,
        "season": season_str,
        "image": "",
        "description": details.get('overview'),
        "originalTitle": original_title,
        "country": country_rus,
        "premiere": premiere_rus,
        "director": director,
        "genres": list(dict.fromkeys(genres)),
        "translation": None,
        "actors": actors_csv or "",
        "kpRating": None,
        "imdbRating": details.get('vote_average'),
        "popularity": details.get('popularity'),
        "youtubeId": youtube_id,
        "trailer": trailer_url,
        "kinopoiskId": None,
        "ageRating": "18+" if is_adult else None,
        "comments": [],
        "_tmdb_poster_path": details.get('poster_path'),
        "creator": creator_name,
        "producers": producers_csv,
        "writers": writers_csv
    }

def download_and_finalize_movie(movie_data):
    poster_path = movie_data.pop("_tmdb_poster_path", None)
    movie_slug = movie_data['id']
    
    if not poster_path:
        print("  - Постер не найден на TMDb. Фильм будет пропущен.")
        return None

    image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
    _, ext = os.path.splitext(poster_path)
    if not ext: ext = '.jpg'
    
    local_filename = f"{movie_slug}{ext}"
    save_path = os.path.join(UPLOADS_DIR, local_filename).replace("\\", "/")

    if os.path.exists(save_path):
        print(f"  - Изображение уже существует: {save_path}")
        movie_data['image'] = save_path
        return movie_data

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  - Скачиваю: {image_url} -> {save_path} (попытка {attempt}/{max_retries})")
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            
            movie_data['image'] = save_path
            print("  - Изображение успешно скачано.")
            return movie_data
        except requests.RequestException as e:
            print(f"  - Ошибка скачивания на попытке {attempt}: {e}")
            if attempt < max_retries:
                print("    - Повторная попытка через 5 секунд...")
                time.sleep(5)
            else:
                print(f"    - !!! Не удалось скачать изображение {image_url} после {max_retries} попыток. Фильм будет пропущен.")
                return None
    
    return None # На случай если цикл завершится без return

def determine_movie_category(movie):
    genre_ids = movie.get('genre_ids', [])
    original_language = movie.get('original_language', '')
    if 10770 in genre_ids: return 'serialy'
    if 16 in genre_ids and original_language == 'ja': return 'anime'
    if 16 in genre_ids: return 'multfilmy'
    return 'filmy'

def determine_tv_category(tv_show):
    genre_ids = tv_show.get('genre_ids', [])
    original_language = tv_show.get('original_language', '')
    if 16 in genre_ids and original_language == 'ja': return 'anime'
    return 'serialy'

def get_person_name_ru(person_id: int, fallback_name: str) -> str:
    if not person_id:
        return fallback_name or ""
    if person_id in _PERSON_CACHE:
        return _PERSON_CACHE[person_id]
    try:
        tr = requests.get(
            f"{PERSON_DETAILS_BASE_URL}{person_id}/translations",
            params={'api_key': TMDB_API_KEY},
            timeout=15
        )
        if tr.ok:
            tr_data = tr.json() or {}
            for t in (tr_data.get('translations') or []):
                if (t.get('iso_639_1') == 'ru') or (t.get('iso_3166_1') == 'RU'):
                    ru_name = (t.get('data') or {}).get('name') or ""
                    if ru_name and re.search(r'[А-Яа-яЁё]', ru_name):
                        _PERSON_CACHE[person_id] = ru_name
                        return ru_name

        resp = requests.get(
            f"{PERSON_DETAILS_BASE_URL}{person_id}",
            params={'api_key': TMDB_API_KEY, 'language': 'ru-RU'},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json() or {}
        for alias in (data.get('also_known_as') or []):
            if re.search(r'[А-Яа-яЁё]', alias or ''):
                _PERSON_CACHE[person_id] = alias
                return alias
        for alias in (data.get('also_known_as') or []):
            if re.search(r'[A-Za-z]', alias or ''):
                _PERSON_CACHE[person_id] = alias
                return alias
        name = (data.get('name') or '').strip()
        if re.search(r'[A-Za-zА-Яа-яЁё]', name):
            _PERSON_CACHE[person_id] = name
            return name
        _PERSON_CACHE[person_id] = fallback_name or ""
        return _PERSON_CACHE[person_id]
    except requests.RequestException:
        return fallback_name or ""

def load_existing_data(json_file, ndjson_file):
    """Загружает ID из основного JSON и временного NDJSON для проверки дублей."""
    all_movies = []
    
    # 1. Читаем основной JSON
    if os.path.exists(json_file) and os.path.getsize(json_file) > 0:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'movies' in data:
                    all_movies.extend(data['movies'])
                # Поддержка старого формата с категориями
                elif isinstance(data, dict):
                    for movies_list in data.values():
                        if isinstance(movies_list, list):
                            all_movies.extend(movies_list)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка чтения {json_file}: {e}. Проверка дублей по нему может быть неполной.")

    # 2. Читаем временный NDJSON, чтобы учесть уже добавленные в этой сессии
    if os.path.exists(ndjson_file):
        try:
            with open(ndjson_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        all_movies.append(json.loads(line))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка чтения {ndjson_file}: {e}. Проверка дублей по нему может быть неполной.")
            
    return all_movies

# --- ОСНОВНОЙ БЛОК ВЫПОЛНЕНИЯ ---
#pfmукацуацуtretttttttttttttttttttацу
async def process_item(item_summary, media_type, existing_slug_ids, existing_kp_ids):
    # Шаг 1: Правильно извлекаем название и категорию в зависимости от типа
    if media_type == 'movie':
        original_title = item_summary.get('original_title', '')
        title = item_summary.get('title', '')
        category = determine_movie_category(item_summary)
    else:  # tv
        original_title = item_summary.get('original_name', '')
        title = item_summary.get('name', '')
        category = determine_tv_category(item_summary)

    # Шаг 2: Предварительный фильтр по дате релиза (с правильным названием в логе)
    rel_str = (item_summary.get('release_date') if media_type == 'movie' else item_summary.get('first_air_date')) or ''
    if rel_str:
        try:
            rel_dt = datetime.strptime(rel_str, '%Y-%m-%d').date()
            if rel_dt > datetime.now().date():
                print(f"Пропуск '{title}' ({item_summary.get('id')}): будущая дата релиза {rel_str}.")
                return None
        except ValueError:
            pass

    # Шаг 3: Логируем начало обработки
    print(f"\n--- Обработка нового контента ({media_type}): {title}")
    if rel_str:
        print(f"    - Дата релиза по TMDb: {rel_str}")
    else:
        print("    - Дата релиза по TMDb: не указана")

    # Шаг 4: Генерируем ID и проверяем на дубликаты
    slug = slugify(title) or slugify(original_title)
    if not slug:
        print(f"Не удалось сгенерировать ID для '{title}'. Пропуск.")
        return None

    if slug in existing_slug_ids:
        print(f"Контент '{title}' ({slug}) уже есть в базе (id). Пропуск.")
        return None

    details = get_details(TMDB_API_KEY, item_summary['id'], media_type)
    if not details:
        print(f"Не удалось получить детали для '{title}'. Пропуск.")
        return None

    # Фолбэк: если не было даты в списке — проверим дату из деталей
    if not rel_str:
        det_rel_str = (details.get('release_date') if media_type == 'movie' else details.get('first_air_date')) or ''
        if det_rel_str:
            try:
                det_rel_dt = datetime.strptime(det_rel_str, '%Y-%m-%d').date()
                if det_rel_dt > datetime.now().date():
                    print(f"Пропуск '{title}': будущая дата релиза {det_rel_str} (по деталям).")
                    return None
            except ValueError:
                pass

    transformed = transform_data_pre_checks(details, category, media_type)
    if not transformed.get('description'):
        print(f"У '{transformed.get('title')}' отсутствует описание. Пропускаем.")
        return None
    if not transformed.get('year'):
        print(f"У '{title}' нет года выпуска. Пропускаем.")
        return None

    print(
        'Ищем Kinopoisk ID для: '
        f'"{transformed.get("title")}" ({transformed.get("year")}) | '
        f'Оригинал: "{transformed.get("originalTitle")}" | '
        f'Тип: {media_type} | Категория: {transformed.get("category")}'
    )
    kp_id = await find_kinopoisk_id(transformed)
    if not kp_id:
        print(f"Kinopoisk ID не найден. Пропускаем '{transformed.get('title')}'.")
        return None
    if kp_id in existing_kp_ids:
        print(f"Контент с Kinopoisk ID {kp_id} уже есть в базе. Пропуск.")
        return None

    transformed['kinopoiskId'] = kp_id
    print(f"Найден Kinopoisk ID: {kp_id}")

    original_desc = transformed.get('description')
    
    print("Переписываем описание...")
    
    rewritten_desc = ""
    max_rewrite_retries = 3
    for attempt in range(1, max_rewrite_retries + 1):
        if shutdown_requested:
            break
            
        print(f"  - Попытка рерайта #{attempt}/{max_rewrite_retries}...")
        desc_candidate = await asyncio.to_thread(rewrite_description_sync, original_desc)

        if desc_candidate is None: # Контент заблокирован API
            print(f"    - Контент заблокирован API. Рерайт невозможен.")
            rewritten_desc = None # специальный маркер для блокировки
            break 
        
        if desc_candidate.strip(): # Успех, есть текст
            rewritten_desc = desc_candidate
            break
        
        # Пустой ответ, но не заблокировано
        if attempt < max_rewrite_retries:
            print(f"    - API вернул пустой текст. Пауза 5с перед повторной попыткой...")
            await asyncio.sleep(5)

    if rewritten_desc is None:
        print(f"Не удалось переписать описание для '{transformed.get('title')}' (контент заблокирован). Пропуск.")
        return None
        
    if not rewritten_desc: # Все попытки вернули пустую строку или был shutdown
        if shutdown_requested:
            print(f"Рерайт для '{transformed.get('title')}' прерван пользователем. Пропуск элемента.")
        else:
            print(f"Не удалось переписать описание для '{transformed.get('title')}' после {max_rewrite_retries} попыток. Пропуск.")
        return None

    print("  - Описание успешно переписано.")
    transformed['description'] = rewritten_desc

    finalized = download_and_finalize_movie(transformed)
    # если download_and_finalize_movie вернёт None при тяжёлой ошибке — пропустим элемент
    return finalized

async def main():
    target_new_movie_count = float('inf') # Устанавливаем бесконечность для непрерывной работы

    all_existing_movies = load_existing_data(JSON_DATA_FILE, NDJSON_OUTPUT_FILE)
    existing_kp_ids = {m.get('kinopoiskId') for m in all_existing_movies if m.get('kinopoiskId')}
    existing_slug_ids = {m.get('id') for m in all_existing_movies}
    print(f"В базе (JSON + NDJSON) уже {len(existing_slug_ids)} записей. С Kinopoisk ID: {len(existing_kp_ids)}.")

    current_movie_page = 1
    current_tv_page = 1

    added = 0
    total_movie_pages = float('inf')
    total_tv_pages = float('inf')

    while added < target_new_movie_count and (current_movie_page <= total_movie_pages or current_tv_page <= total_tv_pages):
        if shutdown_requested:
            break
        # страница фильмов
        if current_movie_page <= total_movie_pages:
            mp = fetch_page_current_month(TMDB_API_KEY, current_movie_page, media_type='movie')
            
            if mp is None:
                print("Остановка из-за критической ошибки сети.")
                sys.exit(1)

            if not mp or not mp.get('results'):
                print("Фильмы за текущий месяц закончились или не найдены.")
                total_movie_pages = -1
            else:
                total_movie_pages = mp.get('total_pages', total_movie_pages)
                for item in mp['results']:
                    if shutdown_requested:
                        break
                    fin = await process_item(item, 'movie', existing_slug_ids, existing_kp_ids)
                    
                    if fin:
                        append_to_ndjson(NDJSON_OUTPUT_FILE, fin)
                        existing_kp_ids.add(fin['kinopoiskId'])
                        existing_slug_ids.add(fin['id'])
                        added += 1
                        print(f"-> '{fin.get('title')}' добавлен в ndjson. Всего за сессию: {added}.")
                    if added >= target_new_movie_count: break
                if shutdown_requested:
                    break
                # save_progress(current_movie_page, current_tv_page - 1)
                current_movie_page += 1
                time.sleep(1)
        if added >= target_new_movie_count: break
        if shutdown_requested:
            break

        # страница сериалов
        if current_tv_page <= total_tv_pages:
            tp = fetch_page_current_month(TMDB_API_KEY, current_tv_page, media_type='tv')

            if tp is None:
                print("Остановка из-за критической ошибки сети.")
                sys.exit(1)

            if not tp or not tp.get('results'):
                print("Сериалы за текущий месяц закончились или не найдены.")
                total_tv_pages = -1
            else:
                total_tv_pages = tp.get('total_pages', total_tv_pages)
                for item in tp['results']:
                    if shutdown_requested:
                        break
                    fin = await process_item(item, 'tv', existing_slug_ids, existing_kp_ids)
                    
                    if fin:
                        append_to_ndjson(NDJSON_OUTPUT_FILE, fin)
                        existing_kp_ids.add(fin['kinopoiskId'])
                        existing_slug_ids.add(fin['id'])
                        added += 1
                        print(f"-> '{fin.get('title')}' добавлен в ndjson. Всего за сессию: {added}.")
                    if added >= target_new_movie_count: break
                if shutdown_requested:
                    break
                # save_progress(current_movie_page - 1, current_tv_page)
                current_tv_page += 1
                time.sleep(1)

    print(f"\nГотово! За сессию добавлено {added} новых записей в {NDJSON_OUTPUT_FILE}.")
    if shutdown_requested:
        print("Скрипт был остановлен пользователем.")

if __name__ == "__main__":
    asyncio.run(main())
