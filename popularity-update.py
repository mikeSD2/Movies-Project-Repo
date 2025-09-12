import json
import os
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import deque
from requests.adapters import HTTPAdapter

TMDB_API_KEY = os.getenv('TMDB_API_KEY', '636c87f3e6bbd33eae8ee8265c83082e')

SEARCH_MOVIE_URL = 'https://api.themoviedb.org/3/search/movie'
SEARCH_TV_URL = 'https://api.themoviedb.org/3/search/tv'
MOVIE_DETAILS_URL = 'https://api.themoviedb.org/3/movie/{}'
TV_DETAILS_URL = 'https://api.themoviedb.org/3/tv/{}'

POPULARITY_MAX_WORKERS = int(os.getenv('POPULARITY_MAX_WORKERS', '8'))  # параллельные тайтлы
TMDB_RPS = int(os.getenv('TMDB_RPS', '20'))                              # лимит запросов/сек
FORCE_REFRESH = os.getenv('POPULARITY_FORCE_REFRESH', '0') == '1'

_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=POPULARITY_MAX_WORKERS * 4, pool_maxsize=POPULARITY_MAX_WORKERS * 4)
_session.mount('https://', _adapter)
_session.mount('http://', _adapter)

_write_lock = threading.Lock()

class RateLimiter:
    def __init__(self, rps: int):
        self.rps = max(1, rps)
        self.lock = threading.Lock()
        self.ts = deque()

    def acquire(self):
        while True:
            with self.lock:
                now = time.monotonic()
                while self.ts and (now - self.ts[0]) >= 1.0:
                    self.ts.popleft()
                if len(self.ts) < self.rps:
                    self.ts.append(now)
                    return
                sleep_for = 1.0 - (now - self.ts[0])
            if sleep_for > 0:
                time.sleep(sleep_for)

_rate_limiter = RateLimiter(TMDB_RPS)

def http_get(url: str, params: dict):
    _rate_limiter.acquire()
    resp = _session.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp

def load_all_movies(movies_data_path: str) -> list[dict]:
    try:
        with open(movies_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{movies_data_path}' не найден.")
        return []
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось прочитать JSON из файла '{movies_data_path}'.")
        return []

    if isinstance(data, dict) and "movies" in data:
        return data["movies"]
    elif isinstance(data, dict):
        all_movies = []
        for v in data.values():
            if isinstance(v, list):
                all_movies.extend(v)
        return all_movies
    else:
        print("Ошибка: Неподдерживаемый формат JSON.")
        return []

def append_to_ndjson(filename: str, item: dict):
    try:
        with _write_lock:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    except IOError as e:
        print(f"  -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать в '{filename}'! {e}")

def is_tv_item(m: dict) -> bool:
    cat = (m.get('category') or '').strip().lower()
    return cat in ('serialy', 'anime')

def parse_year(m: dict) -> int | None:
    try:
        y = m.get('year')
        if y is None:
            return None
        return int(y)
    except Exception:
        return None

def tmdb_search_movie(query: str, year: int | None) -> dict | None:
    if not query:
        return None
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ru-RU',
        'page': 1,
        'include_adult': 'false',
    }
    if year:
        params['primary_release_year'] = year
    try:
        data = http_get(SEARCH_MOVIE_URL, params).json() or {}
        results = data.get('results') or []
        if not results:
            return None
        return results[0]
    except requests.RequestException as e:
        print(f"  -> Ошибка поиска TMDB (/search/movie): {e}")
        return None

def tmdb_search_tv(query: str, year: int | None) -> dict | None:
    if not query:
        return None
    params = {
        'api_key': TMDB_API_KEY,
        'query': query,
        'language': 'ru-RU',
        'page': 1,
        'include_adult': 'false',
    }
    if year:
        params['first_air_date_year'] = year
    try:
        data = http_get(SEARCH_TV_URL, params).json() or {}
        results = data.get('results') or []
        if not results:
            return None
        return results[0]
    except requests.RequestException as e:
        print(f"  -> Ошибка поиска TMDB (/search/tv): {e}")
        return None

def tmdb_get_movie_details(movie_id: int) -> dict | None:
    params = {'api_key': TMDB_API_KEY, 'language': 'ru-RU'}
    try:
        return http_get(MOVIE_DETAILS_URL.format(movie_id), params).json()
    except requests.RequestException as e:
        print(f"  -> Ошибка запроса деталей TMDB (/movie/{movie_id}): {e}")
        return None

def tmdb_get_tv_details(tv_id: int) -> dict | None:
    params = {'api_key': TMDB_API_KEY, 'language': 'ru-RU'}
    try:
        return http_get(TV_DETAILS_URL.format(tv_id), params).json()
    except requests.RequestException as e:
        print(f"  -> Ошибка запроса деталей TMDB (/tv/{tv_id}): {e}")
        return None

def pick_tmdb_match(title_ru: str, title_orig: str, year: int | None, media_type: str) -> dict | None:
    if media_type == 'movie':
        s1 = tmdb_search_movie(title_orig, year)
        if s1: return s1
        s2 = tmdb_search_movie(title_ru, year)
        if s2: return s2
        if year:
            return tmdb_search_movie(title_orig, None) or tmdb_search_movie(title_ru, None)
        return None
    else:
        s1 = tmdb_search_tv(title_orig, year)
        if s1: return s1
        s2 = tmdb_search_tv(title_ru, year)
        if s2: return s2
        if year:
            return tmdb_search_tv(title_orig, None) or tmdb_search_tv(title_ru, None)
        return None

def process_one(m: dict, idx: int, total: int, update_file_path: str) -> bool:
    title_ru = (m.get('title') or '').strip()
    title_orig = (m.get('originalTitle') or '').strip()
    year = parse_year(m)
    media_type = 'tv' if is_tv_item(m) else 'movie'

    if not FORCE_REFRESH and isinstance(m.get('popularity'), (int, float)):
        print(f"[{idx}/{total}] '{title_ru or title_orig}' — уже есть popularity, пропуск.")
        return False

    print(f"[{idx}/{total}] '{title_ru or title_orig}' ({year or 'год ?'}) — поиск TMDB ({media_type})...")

    summary = pick_tmdb_match(title_ru, title_orig, year, media_type)
    if not summary:
        print("  -> Не найдено в TMDB.")
        return False

    tmdb_id = summary.get('id')
    details = tmdb_get_tv_details(tmdb_id) if media_type == 'tv' else tmdb_get_movie_details(tmdb_id)
    if not details:
        return False

    popularity = details.get('popularity')
    if popularity is None:
        print("  -> В деталях TMDb нет поля popularity. Пропуск.")
        return False

    # Если уже есть такое же значение и не форсим — пропустим
    if not FORCE_REFRESH and isinstance(m.get('popularity'), (int, float)):
        try:
            if abs(float(m['popularity']) - float(popularity)) < 1e-9:
                print("  -> Без изменений.")
                return False
        except Exception:
            pass

    m_out = dict(m)
    m_out['popularity'] = popularity

    append_to_ndjson(update_file_path, m_out)
    print(f"  -> Обновлено: popularity={popularity!r} (записано в NDJSON).")
    return True

def update_popularity(movies_data_path="movies-data.json", update_file_path="popularity-update.ndjson"):
    movies = load_all_movies(movies_data_path)
    if not movies:
        return

    targets = movies if FORCE_REFRESH else [m for m in movies if not isinstance(m.get('popularity'), (int, float))]
    if not targets:
        print("Все записи уже имеют поле 'popularity'.")
        return

    total = len(targets)
    print(f"Найдено {total} записей для обновления popularity. Пишу в: {update_file_path}")
    updated = 0

    with ThreadPoolExecutor(max_workers=POPULARITY_MAX_WORKERS) as ex:
        futures = []
        for i, m in enumerate(targets, start=1):
            futures.append(ex.submit(process_one, m, i, total, update_file_path))
        for fut in as_completed(futures):
            try:
                if fut.result():
                    updated += 1
            except Exception as e:
                print(f"  -> Ошибка обработки: {e}")

    print(f"\nГотово. Записано обновлений: {updated}. Затем примените обновления к основной базе (merge).")

if __name__ == "__main__":
    update_popularity()
