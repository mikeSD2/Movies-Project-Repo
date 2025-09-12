import requests
import json
import os
import re
import time
from datetime import datetime
import asyncio
from ddgs import DDGS
import sys
from collections import deque

# --- КОНСТАНТЫ И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---

# Ключи API
TMDB_API_KEY = '636c87f3e6bbd33eae8ee8265c83082e'
GEMINI_API_KEY = "AIzaSyCI0qt3OOliBaM_QOztawFqmBMo5AGw_kY" # Из rewrite_descriptions.py

# URL и пути
MOVIE_LIST_BASE_URL = 'https://api.themoviedb.org/3/discover/movie'
MOVIE_DETAILS_BASE_URL = 'https://api.themoviedb.org/3/movie/'
TV_LIST_BASE_URL = 'https://api.themoviedb.org/3/discover/tv'
TV_DETAILS_BASE_URL = 'https://api.themoviedb.org/3/tv/'
OUTPUT_FILE = 'movies-data.json'
UPLOADS_DIR = 'uploads/posts'

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

# --- ФУНКЦИИ РЕРАЙТА ОПИСАНИЯ (адаптировано из rewrite_descriptions.py) ---

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
    Возвращает переписанный текст в случае успеха или None в случае неудачи.
    """
    global current_model_index, last_429_at
    if not description: return ""

    prompt = (
        "Перепиши пожалуйста это описание фильма так чтобы оно звучало проще без эпитетов метафор и поэтичности. Убери все лишнее и оставь описание сюжета в вормате или 'Сюжет разворачивается вокруг...' или 'В центре повествования находится...' или 'Это история о...' или 'История вращается вокруг...' или 'Главный герой этой истории ...' и тому подобное. Чтобы было просто но интригующе чтобы заитересовать человека к просмотру. "
        "Текст:\n" f'"{description}\n"'
        "Текст должен быть размером от 400 до 1000 символов примерно и уникальность ОБЯЗАТЕЛЬНО должна быть БОЛЕЕ 90% поэтому ВАЖНО чтобы ты старался использовать перефразирование и синонимы (особенно в первом абзаце) где они уместны и не делают текст странны."
        "Очень важно чтобы ты не давал никаких предисловий и послесловий к тексту который был тобой переписан, должен быть только переписаный текст согласно тому как я сказал."
    )
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    while True:
        if current_model_index >= len(MODELS):
            print("\nЛимиты всех доступных моделей исчерпаны. Рерайт невозможен.")
            return None

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
                print(f"    - Контент заблокирован (причина: {reason}). Рерайт не удался.")
                return None

            print("    - Не удалось извлечь текст (неизвестная структура ответа). Рерайт не удался.")
            return None

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
    return [t for t in re.findall(r'[a-zа-яё0-9]+', _norm(s), flags=re.I) if len(t) >= 1]

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

def is_informative_name(name: str | None) -> bool:
    if not name:
        return False
    n = name.strip()
    if not n or n.lower() == 'неизвестно':
        return False
    return bool(re.search(r'[A-Za-zА-Яа-яЁё]', n))

def pick_informative_from_csv(csv: str | None) -> str | None:
    if not csv:
        return None
    for item in csv.split(','):
        item = item.strip()
        if is_informative_name(item):
            return item
    return None

def pick_informative_actor(actors_csv: str | None) -> str | None:
    return pick_informative_from_csv(actors_csv)

def _make_kp_query(info: dict, mode: str, is_series: bool) -> str:
    title = info.get('title') or ''
    year = str(info.get('year') or '')
    parts = [f'"{title}"', f'"{year}"']

    if mode == 'director':
        if is_informative_name(info.get('director')):
            parts.append(f'"{info["director"]}"')

    elif mode == 'creator':
        if is_informative_name(info.get('creator')):
            parts.append(f'"{info["creator"]}"')

    elif mode == 'producer':
        prod = pick_informative_from_csv(info.get('producers'))
        if prod:
            parts.append(f'"{prod}"')

    elif mode == 'writer':
        wr = pick_informative_from_csv(info.get('writers'))
        if wr:
            parts.append(f'"{wr}"')

    elif mode == 'actor':
        actor_hint = pick_informative_actor(info.get('actors'))
        if actor_hint:
            parts.append(f'"{actor_hint}"')

    elif mode == 'premiere' and info.get('premiere'):
        parts.append(f'"{info["premiere"]}"')

    if is_series:
        parts.append('"сезон"')
    return ' '.join(parts)

async def find_kinopoisk_id(movie_info: dict) -> str | None:
    is_series = movie_info['category'] in ['serialy', 'anime']
    
    stages = []

    # приоритет персональных подсказок
    if is_informative_name(movie_info.get('director')):
        stages.append('director')
    if is_informative_name(movie_info.get('creator')):
        stages.append('creator')

    if pick_informative_from_csv(movie_info.get('producers')):
        stages.append('producer')
    if pick_informative_from_csv(movie_info.get('writers')):
        stages.append('writer')

    if pick_informative_actor(movie_info.get('actors')):
        stages.append('actor')
    if movie_info.get('premiere'):
        stages.append('premiere')
    if not stages:
        stages.append('basic')

    for round_num in range(1, 3):
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

def fetch_page(api_key, year, page, media_type='movie'):
    """Запрашивает одну страницу (20 единиц контента) с TMDb с ретраями."""
    if media_type == 'movie':
        url = MOVIE_LIST_BASE_URL
        params = {
            'api_key': api_key, 'primary_release_year': year, 'sort_by': 'popularity.desc',
            'page': page, 'language': 'ru-RU'
        }
    else:  # tv
        url = TV_LIST_BASE_URL
        params = {
            'api_key': api_key, 'first_air_date_year': year, 'sort_by': 'popularity.desc',
            'page': page, 'language': 'ru-RU'
        }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"\nЗапрашиваем страницу {page} ({media_type}) за {year} год с TMDb... (попытка {attempt + 1}/{max_retries})")
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
    """Получает детальную информацию о фильме или сериале."""
    params = {
        'api_key': api_key,
        'language': 'ru-RU',
        'append_to_response': 'credits,videos'
    }
    base_url = MOVIE_DETAILS_BASE_URL if media_type == 'movie' else TV_DETAILS_BASE_URL
    try:
        url = f"{base_url}{media_id}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при получении деталей для {media_type} ID {media_id}: {e}")
        return None

def slugify(text):
    if not text:
        return ""
    text = text.lower().strip()
    
    # Транслитерация
    translit_text = ""
    for char in text:
        translit_text += TRANSLIT_MAP.get(char, char)
        
    # Удаляем символы, которые не являются латинскими буквами, цифрами, пробелами или дефисами
    slug = re.sub(r'[^a-z0-9\s-]', '', translit_text)
    # Заменяем пробелы и множественные дефисы на один дефис
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug

# рядом с остальными BASE_URL
PERSON_DETAILS_BASE_URL = 'https://api.themoviedb.org/3/person/'

# кэш, чтобы не дёргать API многократно
_PERSON_CACHE: dict[int, str] = {}

def get_person_name_ru(person_id: int, fallback_name: str) -> str:
    if not person_id:
        return fallback_name or ""
    if person_id in _PERSON_CACHE:
        return _PERSON_CACHE[person_id]
    try:
        # 1) Переводы персоны → берем ru (как на сайте TMDb)
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

        # 2) Детали персоны с языком (на случай, если там есть локализованный name/aka)
        resp = requests.get(
            f"{PERSON_DETAILS_BASE_URL}{person_id}",
            params={'api_key': TMDB_API_KEY, 'language': 'ru-RU'},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json() or {}

        # 2.1) Кириллический алиас
        for alias in (data.get('also_known_as') or []):
            if re.search(r'[А-Яа-яЁё]', alias or ''):
                _PERSON_CACHE[person_id] = alias
                return alias

        # 2.2) Латинский алиас
        for alias in (data.get('also_known_as') or []):
            if re.search(r'[A-Za-z]', alias or ''):
                _PERSON_CACHE[person_id] = alias
                return alias

        # 2.3) Основное имя: если латиница — берем; иначе — фолбэк
        name = (data.get('name') or '').strip()
        if re.search(r'[A-Za-zА-Яа-яЁё]', name):
            _PERSON_CACHE[person_id] = name
            return name

        _PERSON_CACHE[person_id] = fallback_name or ""
        return _PERSON_CACHE[person_id]
    except requests.RequestException:
        return fallback_name or ""

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
    """Собирает все данные о фильме или сериале, КРОМЕ скачивания картинки."""
    # 1) Режиссёр (приоритет: crew с режиссёрскими должностями -> created_by)
    director = "Неизвестно"
    credits = details.get('credits') or {}
    crew = credits.get('crew', []) or []

    # приоритет должностей (для аниме важны Series/Chief Director)
    JOB_WEIGHTS = {
        'Chief Director': 6,
        'Series Director': 5,
        'Director': 4,
        'Supervising Director': 3,
        'Co-Director': 2,
        'Episode Director': 1,
        'Assistant Director': 0,
    }

    def director_job_weight(member) -> int:
        job = (member.get('job') or '').strip()
        if job in JOB_WEIGHTS:
            return JOB_WEIGHTS[job]
        best = 0
        for j in (member.get('jobs') or []):
            jw = JOB_WEIGHTS.get((j.get('job') or '').strip(), -1)
            if jw > best:
                best = jw
        return best

    director_candidates = [m for m in crew if director_job_weight(m) > 0]
    if director_candidates:
        best = max(
            director_candidates,
            key=lambda m: (director_job_weight(m), (m.get('episode_count') or 0))
        )
        director = get_person_name_ru(best.get('id'), best.get('name') or "")
    elif media_type == 'tv' and details.get('created_by'):
        creator = (details.get('created_by') or [])[0]
        director = get_person_name_ru(creator.get('id'), creator.get('name') or "")

    # 2) Актёры (топ-10)
    actors = [a.get('name') for a in (credits.get('cast') or [])[:10] if a.get('name')]

    # 3) Трейлер (YouTube)
    trailer_url, youtube_id = None, None
    for v in (details.get('videos') or {}).get('results', []):
        if v.get('site') == 'YouTube' and v.get('type') == 'Trailer':
            youtube_id = v.get('key')
            if youtube_id:
                trailer_url = f"https://www.youtube.com/watch?v={youtube_id}"
            break

    # 4) Названия/даты/сезоны
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

    # 5) Год и премьера (ru)
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

    # 6) Жанры (без «Сериалы»)
    genres = [GENRE_MAP.get(g['id']) for g in details.get('genres', []) if GENRE_MAP.get(g['id'])]

    # 7) Страна
    country_eng = "Неизвестно"
    if details.get('production_countries'):
        country_eng = details.get('production_countries')[0].get('name') or "Неизвестно"
    country_rus = COUNTRY_TRANSLATION.get(country_eng, country_eng)

    # 8) Слаг
    slug_id = slugify(original_title) or slugify(title)

    # creator (для подсказки в поиске)
    creator_name = None
    if details.get('created_by'):
        c = (details.get('created_by') or [])[0]
        creator_name = get_person_name_ru(c.get('id'), c.get('name') or "")

    # продюсеры/сценаристы (для подсказок)
    PRODUCER_JOBS = {'Executive Producer', 'Producer'}
    WRITER_JOBS = {'Writer', 'Screenplay', 'Series Composition'}

    def _collect_people_by_jobs(jobs: set[str]) -> list[str]:
        seen = set()
        out = []
        for m in crew:
            j = (m.get('job') or '').strip()
            if j in jobs:
                name = get_person_name_ru(m.get('id'), m.get('name') or "")
                if name and name not in seen:
                    seen.add(name)
                    out.append(name)
        return out

    producer_names = _collect_people_by_jobs(PRODUCER_JOBS)
    writer_names = _collect_people_by_jobs(WRITER_JOBS)

    producers_csv = ", ".join(producer_names) if producer_names else None
    writers_csv = ", ".join(writer_names) if writer_names else None

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
        "actors": ", ".join(actors),
        "kpRating": None,
        "imdbRating": details.get('vote_average'),
        "youtubeId": youtube_id,
        "trailer": trailer_url,
        "kinopoiskId": None,
        "ageRating": "18+" if is_adult else None,
        "comments": [],
        "_tmdb_poster_path": details.get('poster_path'),
        "creator": creator_name,
        "producers": producers_csv,
        "writers": writers_csv,
    }

def download_and_finalize_movie(movie_data):
    """Скачивает картинку и завершает формирование данных о фильме."""
    poster_path = movie_data.pop("_tmdb_poster_path", None)
    movie_slug = movie_data['id']
    
    if not poster_path:
        print("  - Постер не найден на TMDb.")
        movie_data['image'] = ""
        return movie_data

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
                print(f"  - Не удалось скачать изображение {image_url} после {max_retries} попыток.")
                movie_data['image'] = "" # Или можно оставить полный URL как фоллбэк: image_url
    
    return movie_data

def determine_movie_category(movie):
    genre_ids = movie.get('genre_ids', [])
    original_language = movie.get('original_language', '')
    if 10770 in genre_ids: return 'serialy' # TV Movie, technically a film
    if 16 in genre_ids and original_language == 'ja': return 'anime'
    if 16 in genre_ids: return 'multfilmy'
    return 'filmy'

def determine_tv_category(tv_show):
    genre_ids = tv_show.get('genre_ids', [])
    original_language = tv_show.get('original_language', '')
    if 16 in genre_ids and original_language == 'ja': return 'anime'
    return 'serialy'

def load_existing_data(filename):
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        return {'movies': []}

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка чтения файла {filename}: {e}. Будет создана новая структура.")
        return {'movies': []}

    if isinstance(data, dict) and 'movies' in data and isinstance(data['movies'], list):
        return data

    if isinstance(data, dict) and all(k in data for k in CATEGORY_GENRE_NAMES.keys()):
        print("Обнаружена структура с категориями. Конвертирую в единый список 'movies'...")
        all_movies = []
        for category, movies_list in data.items():
            for movie in movies_list:
                if 'category' not in movie:
                    movie['category'] = category
                all_movies.append(movie)
        print("Конвертация завершена.")
        return {'movies': all_movies}

    print("Неизвестный формат JSON. Будет создана новая структура.")
    return {'movies': []}

# --- ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ ПРОГРЕССА ---
PROGRESS_FILE = 'progress.json'

def save_progress(year, movie_page_number, tv_page_number):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'year': year, 
            'movie_last_page_processed': movie_page_number,
            'tv_last_page_processed': tv_page_number
        }, f)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                current_year = data.get('year', datetime.now().year)
                movie_page = data.get('movie_last_page_processed', 0)
                tv_page = data.get('tv_last_page_processed', 0)
                return current_year, movie_page, tv_page
        except (json.JSONDecodeError, IOError):
            pass
    return datetime.now().year, 0, 0

# --- ОСНОВНОЙ БЛОК ВЫПОЛНЕНИЯ ---

async def process_item(item_summary, media_type, existing_slug_ids, existing_kp_ids):
    """
    Полный цикл обработки одного элемента (фильма или сериала):
    - Проверка на дубликат по slug
    - Получение деталей
    - Поиск Kinopoisk ID
    - Проверка на дубликат по Kinopoisk ID
    - Рерайт описания
    - Скачивание изображения
    Возвращает готовый для добавления в базу объект dict или None в случае ошибки/пропуска.
    """
    if media_type == 'movie':
        original_title = item_summary.get('original_title', '')
        title = item_summary.get('title', '')
    else: # tv
        original_title = item_summary.get('original_name', '')
        title = item_summary.get('name', '')
    
    prospective_id = slugify(original_title)
    if not prospective_id:
        prospective_id = slugify(title)

    if prospective_id in existing_slug_ids:
        print(f"Контент '{title}' ({prospective_id}) уже есть в базе (проверка по id). Пропуск.")
        return None

    print(f"\n--- Обработка нового контента ({media_type}): {title} ---")
    
    # Предварительный фильтр: пропуск будущих релизов (movie: release_date, tv: first_air_date)
    rel_str = (item_summary.get('release_date') if media_type == 'movie' else item_summary.get('first_air_date')) or ''
    if rel_str:
        try:
            rel_dt = datetime.strptime(rel_str, '%Y-%m-%d').date()
            if rel_dt > datetime.now().date():
                print(f"Пропуск '{title}': будущая дата релиза {rel_str}.")
                return None
        except ValueError:
            pass

    details = get_details(TMDB_API_KEY, item_summary['id'], media_type)
    if not details:
        print(f"Не удалось получить детали для '{title}'. Пропуск.")
        return None

    # Фолбэк: если в списке даты не было — проверим по деталям
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

    if media_type == 'movie':
        category = determine_movie_category(item_summary)
    else:
        category = determine_tv_category(item_summary)
        
    transformed_item = transform_data_pre_checks(details, category, media_type)
    
    if not transformed_item.get('year'):
        print(f"У '{title}' нет года выпуска. Пропускаем.")
        return None

    print("Ищем Kinopoisk ID...")
    kp_id = await find_kinopoisk_id(transformed_item)
    
    if not kp_id:
        print(f"Kinopoisk ID не найден. Пропускаем '{transformed_item.get('title')}'.")
        return None
    
    if kp_id in existing_kp_ids:
        print(f"Контент с Kinopoisk ID {kp_id} уже есть в базе. Пропуск.")
        return None
    
    transformed_item['kinopoiskId'] = kp_id
    print(f"Найден Kinopoisk ID: {kp_id}")

    original_desc = transformed_item.get('description')
    if not original_desc:
        print(f"У '{transformed_item.get('title')}' отсутствует описание. Пропускаем.")
        return None

    rewritten_desc = None
    for attempt in range(1, 3):
        print(f"Переписываем описание (попытка {attempt}/2)...")
        rewritten_desc = await asyncio.to_thread(rewrite_description_sync, original_desc)
        if rewritten_desc is not None:
            print("  - Описание успешно переписано.")
            break
        else:
            if attempt < 2:
                print("  - Не удалось переписать описание. Повторная попытка через 5 секунд...")
                await asyncio.sleep(5)
    
    if rewritten_desc is None:
        print(f"Не удалось переписать описание после 2 попыток. Пропускаем '{transformed_item.get('title')}'.")
        return None
    
    transformed_item['description'] = rewritten_desc
    finalized_item = download_and_finalize_movie(transformed_item)
    
    return finalized_item


async def main():
    target_new_movie_count = float('inf') # Устанавливаем бесконечность для непрерывной работы
    
    existing_data = load_existing_data(OUTPUT_FILE)
    # Собираем существующие ID для точной проверки на дубликаты
    existing_kp_ids = {movie.get('kinopoiskId') for movie in existing_data.get('movies', []) if movie.get('kinopoiskId')}
    existing_slug_ids = {movie.get('id') for movie in existing_data.get('movies', [])}
    print(f"В базе уже {len(existing_slug_ids)} фильмов. Из них с Kinopoisk ID: {len(existing_kp_ids)}.")
    
    current_year, last_processed_movie_page, last_processed_tv_page = load_progress()
    
    added_count = 0
    
    while added_count < target_new_movie_count:
        print(f"\n===== Обработка года: {current_year} =====")
        
        current_movie_page = last_processed_movie_page + 1
        current_tv_page = last_processed_tv_page + 1
        
        total_movie_pages = float('inf')
        total_tv_pages = float('inf')
        
        movies_done_for_year = False
        tv_done_for_year = False

        while added_count < target_new_movie_count and (not movies_done_for_year or not tv_done_for_year):
            
            # --- Шаг 1: Обработка страницы ФИЛЬМОВ ---
            if not movies_done_for_year:
                print("\n----- Обработка страницы ФИЛЬМОВ -----")
                page_data = fetch_page(TMDB_API_KEY, current_year, current_movie_page, media_type='movie')
                
                if page_data is None:
                    print("Остановка из-за критической ошибки сети.")
                    sys.exit(1)
                
                if not page_data.get('results'):
                    print(f"Фильмы за {current_year} год закончились.")
                    movies_done_for_year = True
                else:
                    total_movie_pages = page_data.get('total_pages', total_movie_pages)
                    
                    for item_summary in page_data['results']:
                        finalized_item = await process_item(item_summary, 'movie', existing_slug_ids, existing_kp_ids)
                        
                        if finalized_item:
                            existing_data['movies'].append(finalized_item)
                            existing_kp_ids.add(finalized_item['kinopoiskId'])
                            existing_slug_ids.add(finalized_item['id'])
                            added_count += 1
                            print(f"-> '{finalized_item.get('title')}' успешно обработан. Всего добавлено: {added_count}.")
                            
                            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                                json.dump(existing_data, f, ensure_ascii=False, indent=4)
                        
                        if added_count >= target_new_movie_count:
                            break 

                    save_progress(current_year, current_movie_page, current_tv_page - 1)
                    current_movie_page += 1
                    if current_movie_page > total_movie_pages:
                        movies_done_for_year = True
            
            if added_count >= target_new_movie_count:
                break

            # --- Шаг 2: Обработка страницы СЕРИАЛОВ ---
            if not tv_done_for_year:
                print("\n----- Обработка страницы СЕРИАЛОВ -----")
                page_data = fetch_page(TMDB_API_KEY, current_year, current_tv_page, media_type='tv')

                if page_data is None:
                    print("Остановка из-за критической ошибки сети.")
                    sys.exit(1)

                if not page_data.get('results'):
                    print(f"Сериалы за {current_year} год закончились.")
                    tv_done_for_year = True
                else:
                    total_tv_pages = page_data.get('total_pages', total_tv_pages)
                    
                    for item_summary in page_data['results']:
                        finalized_item = await process_item(item_summary, 'tv', existing_slug_ids, existing_kp_ids)
                        
                        if finalized_item:
                            existing_data['movies'].append(finalized_item)
                            existing_kp_ids.add(finalized_item['kinopoiskId'])
                            existing_slug_ids.add(finalized_item['id'])
                            added_count += 1
                            print(f"-> '{finalized_item.get('title')}' успешно обработан. Всего добавлено: {added_count}.")
                            
                            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                                json.dump(existing_data, f, ensure_ascii=False, indent=4)

                        if added_count >= target_new_movie_count:
                            break
                    
                    save_progress(current_year, current_movie_page - 1, current_tv_page)
                    current_tv_page += 1
                    if current_tv_page > total_tv_pages:
                        tv_done_for_year = True

            if added_count >= target_new_movie_count:
                break
            
            if not movies_done_for_year or not tv_done_for_year:
                time.sleep(1)

        # --- Переход к следующему году ---
        if added_count < target_new_movie_count:
            current_year -= 1
            save_progress(current_year, 0, 0)

    print(f"\nГотово! За сессию добавлено {added_count} новых единиц контента. Общее количество: {len(existing_data['movies'])}.")

if __name__ == "__main__":
    asyncio.run(main())
