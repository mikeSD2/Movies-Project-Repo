import json
import time
import os
import requests
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import deque
from requests.adapters import HTTPAdapter

TMDB_API_KEY = os.getenv('TMDB_API_KEY', '636c87f3e6bbd33eae8ee8265c83082e')

SEARCH_TV_URL = 'https://api.themoviedb.org/3/search/tv'
TV_DETAILS_URL = 'https://api.themoviedb.org/3/tv/{}'

SEASONS_MAX_WORKERS = int(os.getenv('SEASONS_MAX_WORKERS', '8'))   # параллельные тайтлы
TMDB_RPS = int(os.getenv('TMDB_RPS', '20'))                        # лимит запросов/сек (безопасно начни с 20)

# Глобальная сессия HTTP с пулом соединений
_session = requests.Session()
_adapter = HTTPAdapter(pool_connections=SEASONS_MAX_WORKERS * 4, pool_maxsize=SEASONS_MAX_WORKERS * 4)
_session.mount('https://', _adapter)
_session.mount('http://', _adapter)

# Потокобезопасная запись в NDJSON
_write_lock = threading.Lock()

class RateLimiter:
    def __init__(self, rps: int):
        self.rps = max(1, rps)
        self.lock = threading.Lock()
        self.ts = deque()  # метки времени за последнюю секунду

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

def format_season(n: int | None) -> str | None:
    if not n or n <= 0:
        return None
    return f"{n} сезон"

def format_episode(n: int | None) -> str | None:
    if not n or n <= 0:
        return None
    return f"{n} серия"

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

def tmdb_get_tv_details(tv_id: int) -> dict | None:
    params = {
        'api_key': TMDB_API_KEY,
        'language': 'ru-RU',
    }
    url = TV_DETAILS_URL.format(tv_id)
    try:
        return http_get(url, params).json()
    except requests.RequestException as e:
        print(f"  -> Ошибка запроса деталей TMDB (/tv/{tv_id}): {e}")
        return None

def pick_tmdb_match(title_ru: str, title_orig: str, year: int | None) -> dict | None:
    r = tmdb_search_tv(title_orig, year)
    if r:
        return r
    r = tmdb_search_tv(title_ru, year)
    if r:
        return r
    if year:
        return tmdb_search_tv(title_orig, None) or tmdb_search_tv(title_ru, None)
    return None

def append_to_ndjson(filename: str, item: dict):
    try:
        with _write_lock:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    except IOError as e:
        print(f"  -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать в '{filename}'! {e}")

def process_one(m: dict, idx: int, total: int, update_file_path: str) -> bool:
    title_ru = (m.get('title') or '').strip()
    title_orig = (m.get('originalTitle') or '').strip()
    year = None
    try:
        if m.get('year'):
            year = int(m['year'])
    except Exception:
        pass

    print(f"[{idx}/{total}] '{title_ru or title_orig}' ({year or 'год ?'}) — поиск TMDB...")

    summary = pick_tmdb_match(title_ru, title_orig, year)
    if not summary:
        print("  -> Не найдено в TMDB.")
        return False

    tv_id = summary.get('id')
    details = tmdb_get_tv_details(tv_id)
    if not details:
        return False

    def _parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except Exception:
            return None

    def _get_aired_episode_count(tv_id: int, season_number: int) -> int | None:
        # /tv/{tv_id}/season/{season_number}
        url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}"
        params = {'api_key': TMDB_API_KEY, 'language': 'ru-RU'}
        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json() or {}
            today = date.today()
            eps = data.get('episodes') or []
            aired_eps = [ep for ep in eps if _parse_date(ep.get('air_date') or '') and _parse_date(ep['air_date']) <= today]
            if not aired_eps:
                return 0
            # Максимальный реально вышедший номер серии
            return max((ep.get('episode_number') or 0) for ep in aired_eps)
        except requests.RequestException:
            return None

    # --- вместо прежнего куска ---
    last_ep = (details.get('last_episode_to_air') or {}) if isinstance(details.get('last_episode_to_air'), dict) else {}
    today = date.today()
    last_air_date = _parse_date(last_ep.get('air_date') or '')

    season_num = last_ep.get('season_number')  # предпочтительно: сезон последней вышедшей серии
    episode_num = last_ep.get('episode_number')

    # Если TMDb вдруг вернул будущую дату — пересчитаем по данным сезона
    if last_air_date and last_air_date > today and season_num:
        safe_ep_count = _get_aired_episode_count(tv_id, season_num)
        if safe_ep_count is not None:
            episode_num = safe_ep_count

    # Если по какой-то причине нет last_episode_to_air, выберем последний сезон, чей air_date <= сегодня
    if not season_num:
        seasons_list = [s for s in (details.get('seasons') or []) if isinstance(s, dict)]
        seasons_list = [s for s in seasons_list if (s.get('season_number') or 0) > 0]  # исключаем спецвыпуски (0)
        seasons_list = sorted(seasons_list, key=lambda s: s.get('season_number') or 0)
        # выбираем максимум с прошедшей датой
        past_seasons = [s for s in seasons_list if _parse_date(s.get('air_date') or '') and _parse_date(s['air_date']) <= today]
        if past_seasons:
            season_num = past_seasons[-1].get('season_number')

    # Форматируем для базы
    season_str_new = format_season(season_num if isinstance(season_num, int) else None)
    episode_str_new = format_episode(episode_num if isinstance(episode_num, int) else None)

    season_old = m.get('season')
    episode_old = m.get('episode')

    if season_str_new == season_old and episode_str_new == episode_old:
        print("  -> Без изменений.")
        return False

    m_out = dict(m)
    m_out['season'] = season_str_new
    if episode_str_new:
        m_out['episode'] = episode_str_new

    append_to_ndjson(update_file_path, m_out)
    print(f"  -> Обновлено: season={season_str_new!r}, episode={episode_str_new!r} (записано в NDJSON).")
    return True

def update_seasons(movies_data_path="movies-data.json", update_file_path="seasons-update.ndjson"):
    movies = load_all_movies(movies_data_path)
    if not movies:
        return

    targets = [m for m in movies if m.get('season')]
    if not targets:
        print("Нет сериалов с непустым полем 'season'.")
        return

    total = len(targets)
    print(f"Найдено {total} сериалов для обновления сезона/серии. Пишу в: {update_file_path}")
    updated = 0

    with ThreadPoolExecutor(max_workers=SEASONS_MAX_WORKERS) as ex:
        futures = []
        for i, m in enumerate(targets, start=1):
            futures.append(ex.submit(process_one, m, i, total, update_file_path))
        for fut in as_completed(futures):
            try:
                if fut.result():
                    updated += 1
            except Exception as e:
                print(f"  -> Ошибка обработки: {e}")

    print(f"\nГотово. Записано обновлений: {updated}. Теперь запустите 'merge_seasons.py'.")

if __name__ == "__main__":
    update_seasons()
