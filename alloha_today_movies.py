# save as: fetch_alloha_last_movies.py
import re
import json
import html
import time
import shutil
import random
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from PIL import Image
import io

import requests

import signal
import os
import ctypes
import sys

if sys.platform == "win32":
    import msvcrt  # доступен в PowerShell/ConHost
else:
    msvcrt = None

def _hotkey_exit_poll():
    try:
        if msvcrt and msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'q', b'Q'):
                try: log("Hotkey 'q' pressed. Forcing exit.")
                except Exception: pass
                os._exit(130)
    except Exception:
        pass

def _stop_requested() -> bool:
    # поддержка STOP-файла как запасной канал
    return (WORKDIR / "STOP").exists()

def _force_exit_win(code=130):
    try:
        h = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.TerminateProcess(h, code)
    except Exception:
        os._exit(code)

def _on_sigint(signum, frame):
    try:
        log("Stop requested (Ctrl+C). Forcing exit (WinAPI).")
    except Exception:
        pass
    _force_exit_win(130)

# сигналы
try:
    signal.signal(signal.SIGINT, _on_sigint)
except Exception:
    pass
try:
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _on_sigint)
    if hasattr(signal, "SIGBREAK"):  # Windows Ctrl+Break
        signal.signal(signal.SIGBREAK, _on_sigint)
except Exception:
    pass

# -------- Config --------
WORKDIR = Path(__file__).resolve().parent
CONFIG_PATHS = [
    WORKDIR / "alloha" / "DLE 13-17.0" / "engine" / "data" / "alloha.config",
    WORKDIR / "alloha" / "Dle 11x" / "engine" / "data" / "alloha.config",
]
ALLOHA_BASE = "https://api.apbugall.org/"
MOVIES_JSON = WORKDIR / "movies-data.json"
NDJSON_OUTPUT = WORKDIR / "movies-data.ndjson"
UPLOADS_DIR = WORKDIR / "uploads" / "media"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Сколько страниц ленты last=movie собрать
PAGES = 3
# Сколько итогово добавить максимум за запуск
MAX_ADD = 100

# TMDB popularity (по id_tmdb из Alloha)
TMDB_API_KEY = os.getenv("TMDB_API_KEY") or "636c87f3e6bbd33eae8ee8265c83082e"

# Временный режим: вывести первые 100 позиций в NDJSON без сортировки/переписывания
DEBUG_DUMP_100 = True

VERBOSE = True

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# Добавить вверху файла (рядом с остальными try-import):
try:
    from gettrailer import youtube_search, get_best_trailer
except Exception:
    youtube_search = get_best_trailer = None

def find_trailer_via_youtube(title, original_title, year):
    if not youtube_search or not get_best_trailer:
        return None, None
    queries = []
    if title:
        queries += [f"{title} {year} официальный трейлер", f"{title} {year} тизер"]
    if original_title:
        queries += [f"{original_title} {year} official trailer", f"{original_title} {year} teaser"]
    if VERBOSE: log(f"  yt search: queries={len(queries)}")
    seen, candidates = set(), []
    for q in queries:
        region = "RU" if "официальный" in q or "тизер" in q else "US"
        try:
            results = youtube_search(q, limit=8, region=region)
            if VERBOSE: log(f"    yt query='{q}' results={len(results)}")
            for v in results:
                vid = v.get("id")
                if vid and vid not in seen:
                    candidates.append(v); seen.add(vid)
        except Exception:
            continue
    movie_stub = {"title": title, "originalTitle": original_title, "year": year}
    best, score = get_best_trailer(movie_stub, candidates)
    if VERBOSE: log(f"  yt candidates={len(candidates)} best_score={score if score is not None else '-'}")
    if best and best.get("id"):
        vid = best["id"]
        return f"https://www.youtube.com/watch?v={vid}", vid
    return None, None

# -------- Gemini rewrite --------
try:
    from fetch_tmdb_last_movies import GEMINI_API_KEY as _GEMINI_FROM_FETCH
    # используем ключ из fetch как дефолт, но не перетираем уже заданные ключи (для ротации через запятую)
    os.environ["GEMINI_API_KEYS"] = os.environ.get("GEMINI_API_KEYS") or "AIzaSyCrgDaMYgIZG-SKxJTJ1ShoE1YaG3mwMSw, AIzaSyAmD3Nv6WcdBK3aoLAlARcQsvqv-RqTSCo, AIzaSyDJKKtMCmM-_YOsWZ-p2MMfwRwtwOyMXvI"
except Exception:
    pass

try:
    from rewrite_descriptions_with_gemini import rewrite_description_sync as gemini_rewrite
except Exception:
    gemini_rewrite = None

# -------- Helpers --------

# RU date formatting and RU production filter
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

def format_date_ru(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    # ожидаем YYYY-MM-DD
    try:
        y, m, d = s[:10].split("-")
        y = int(y); m = int(m); d = int(d)
        if 1 <= m <= 12 and 1 <= d <= 31:
            return f"{d} {MONTHS_RU[m]} {y}"
    except Exception:
        pass
    return s  # если формат иной — вернуть как есть

def is_russian_production(country: str | None) -> bool:
    s = (country or "").lower()
    # проверяем по элементам списка стран
    parts = [x.strip() for x in re.split(r"[;,/]", s) if x.strip()]
    for p in parts or [s]:
        if "россия" in p or "russia" in p or "russian federation" in p:
            return True
    return False

def extract_api_token(text: str) -> Optional[str]:
    m = re.search(r's:9:"api_token";s:\d+:"([^"]+)"', text)
    return m.group(1) if m and m.group(1) else None

def load_alloha_token() -> Optional[str]:
    for p in CONFIG_PATHS:
        if p.exists():
            s = p.read_text(encoding="utf-8", errors="ignore")
            token = extract_api_token(s)
            if token:
                return token
    return os.getenv("ALLOHA_TOKEN")

def fetch_tmdb_vote_average(tmdb_id: str, media_type_hint: Optional[str]) -> Optional[float]:
    if not tmdb_id:
        return None
    # пробуем указанный тип, потом альтернативный
    types = []
    if media_type_hint in ("movie", "tv"):
        types.append(media_type_hint)
    types += [t for t in ("movie", "tv") if t not in types]

    for mt in types:
        base = "https://api.themoviedb.org/3/movie/" if mt == "movie" else "https://api.themoviedb.org/3/tv/"
        try:
            r = requests.get(
                base + str(tmdb_id),
                params={"api_key": TMDB_API_KEY, "language": "ru-RU"},
                timeout=2
            )
            if r.status_code == 200:
                obj = r.json()
                va = obj.get("vote_average")
                if va is not None:
                    return float(va)
        except Exception:
            continue
    return None

TRANSLIT_MAP = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
    'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'shch',
    'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
}
def slugify(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    translit = "".join(TRANSLIT_MAP.get(ch, ch) for ch in text)
    slug = re.sub(r'[^a-z0-9\s-]', '', translit)
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return slug

def norm_title(s: str | None) -> str:
    s = (s or '').lower().replace('ё', 'е')
    s = re.sub(r'["“”«»\'`’‘-]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def titlecase_genres(genres_csv: str | None) -> list[str]:
    if not genres_csv:
        return []
    out = []
    for g in [x.strip() for x in genres_csv.split(",") if x.strip()]:
        # первая буква заглавная
        out.append(g[:1].upper() + g[1:])
    # убрать дубли, сохранить порядок
    return list(dict.fromkeys(out))

def fetch_tmdb_popularity_only(tmdb_id: str, media_type_hint: Optional[str]) -> Optional[float]:
    if not tmdb_id:
        return None
    # умный порядок: по категории лучше подать hint="tv" для сериалов
    types = []
    if media_type_hint in ("movie", "tv"):
        types.append(media_type_hint)
    types += ["movie", "tv"]
    # убрать дубликаты, сохраняя порядок
    uniq = []
    for t in types:
        if t and t not in uniq:
            uniq.append(t)

    attempts = 2  # быстрые повторы без sleep
    t0_all = time.time()
    for i in range(1, attempts + 1):
        for mt in uniq:
            t0 = time.time()
            try:
                r = requests.get(
                    ("https://api.themoviedb.org/3/movie/" if mt == "movie" else "https://api.themoviedb.org/3/tv/") + str(tmdb_id),
                    params={"api_key": TMDB_API_KEY, "language": "ru-RU"},
                    timeout=2
                )
                r.raise_for_status()
                data = r.json()
                pop = data.get("popularity")
                if pop is not None:
                    if VERBOSE:
                        log(f"  tmdb pop attempt#{i} ({mt}) ok in {time.time()-t0:.1f}s pop={float(pop)}")
                    return float(pop)
                if VERBOSE:
                    log(f"  tmdb pop attempt#{i} ({mt}) no 'popularity' in {time.time()-t0:.1f}s")
            except Exception as e:
                if VERBOSE:
                    log(f"  tmdb pop attempt#{i} ({mt}) error in {time.time()-t0:.1f}s: {e}")
    if VERBOSE:
        log(f"  tmdb pop done in {time.time()-t0_all:.1f}s (no data)")
    return None

def season_str_from_count(n: int | None):
    if not n or n <= 0:
        return None
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        suf = "сезон"
    elif n10 in (2, 3, 4) and n100 not in (12, 13, 14):
        suf = "сезона"
    else:
        suf = "сезонов"
    return f"{n} {suf}"

def episode_str(n: int | None):
    if not n or n <= 0:
        return None
    return f"{n} серия"

def parse_youtube_from_iframe(url: str | None) -> tuple[Optional[str], Optional[str]]:
    if not url:
        return None, None
    url = url.strip()
    # youtu.be/<id>
    m = re.search(r'youtu\.be/([A-Za-z0-9_\-]{6,})', url)
    if m:
        yt = m.group(1)
        return f"https://www.youtube.com/watch?v={yt}", yt
    # youtube.com/watch?v=<id>
    m = re.search(r'[?&]v=([A-Za-z0-9_\-]{6,})', url)
    if m:
        yt = m.group(1)
        return f"https://www.youtube.com/watch?v={yt}", yt
    # youtube-nocookie/embed/<id>
    m = re.search(r'/embed/([A-Za-z0-9_\-]{6,})', url)
    if m:
        yt = m.group(1)
        return f"https://www.youtube.com/watch?v={yt}", yt
    return None, None

def http_get_json(url: str, params: dict, timeout=30) -> Optional[dict]:
    _hotkey_exit_poll()
    if _stop_requested():
        return None
    for _ in range(3):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(2)
    return None

def fetch_tmdb_poster_url(tmdb_id: str, media_type_hint: Optional[str]) -> Optional[str]:
    if not tmdb_id:
        return None
    types = []
    if media_type_hint in ("movie", "tv"):
        types.append(media_type_hint)
    types += [t for t in ("movie", "tv") if t not in types]
    for mt in types:
        base = "https://api.themoviedb.org/3/movie/" if mt == "movie" else "https://api.themoviedb.org/3/tv/"
        try:
            r = requests.get(
                base + str(tmdb_id),
                params={"api_key": TMDB_API_KEY, "language": "ru-RU"},
                timeout=2
            )
            if r.status_code == 200:
                obj = r.json()
                pp = obj.get("poster_path")
                if pp:
                    # можно заменить 'original' на 'w780', если хочешь поменьше
                    return f"https://image.tmdb.org/t/p/original{pp}"
        except Exception:
            continue
    return None

# Заменить fetch_tmdb_popularity_and_trailer на версию с приоритетом RU:
def fetch_tmdb_popularity_and_trailer(tmdb_id: str, media_type_hint: Optional[str]) -> tuple[Optional[float], Optional[str], Optional[str]]:
    if not tmdb_id:
        return None, None, None
    pop = None
    for mt in (media_type_hint, "movie", "tv"):
        if not mt:
            continue
        base = "https://api.themoviedb.org/3/movie/" if mt == "movie" else "https://api.themoviedb.org/3/tv/"
        obj = http_get_json(base + str(tmdb_id), {"api_key": TMDB_API_KEY, "language": "ru-RU"})
        if obj and obj.get("popularity") is not None:
            try:
                pop = float(obj["popularity"])
            except Exception:
                pop = None
        vids = http_get_json(base + str(tmdb_id) + "/videos", {
            "api_key": TMDB_API_KEY,
            "language": "ru-RU",
            "include_video_language": "ru,en,null"
        })
        results = (vids or {}).get("results", [])

        def rank(v):
            lang = (v.get("iso_639_1") or "").lower()
            good = (v.get("site") == "YouTube" and v.get("key") and v.get("type") in ("Trailer","Teaser"))
            if not good:
                return (-1, -1, -1)
            return (
                2 if lang == "ru" else 1 if lang in ("en", "") else 0,  # RU > EN > прочее
                1 if v.get("official") else 0,                           # official выше
                1 if v.get("type") == "Trailer" else 0,                  # Trailer выше Teaser
            )

        best = max(results, key=rank, default=None)
        if best and best.get("key"):
            yt_id = best["key"]
            return pop, f"https://www.youtube.com/watch?v={yt_id}", yt_id
    return pop, None, None

def download_image(url: str, slug_base: str) -> Optional[str]:
    if not url:
        return None
    try:
        # Добавляем случайный трехзначный суффикс к имени файла, чтобы снизить шанс коллизии
        rand_suffix = f"{random.randint(0, 999):03d}"
        webp_name = f"{slug_base}-{rand_suffix}.webp"
        webp_path = UPLOADS_DIR / webp_name
        if not webp_path.exists():
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            b = r.content
            try:
                im = Image.open(io.BytesIO(b))
                if im.mode in ("RGBA","P"):
                    im = im.convert("RGB")
                im.save(webp_path, "WEBP", quality=85, method=6)
                return f"uploads/media/{webp_name}"
            except Exception:
                # конвертация не удалась — сохраняем как есть с исходным расширением
                ext = os.path.splitext(url.split("?")[0].split("#")[0])[-1].lower()
                if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                    ext = ".jpg"
                raw_name = f"{slug_base}-{rand_suffix}{ext}"
                raw_path = UPLOADS_DIR / raw_name
                with open(raw_path, "wb") as f:
                    f.write(b)
                return f"uploads/media/{raw_name}"
        return f"uploads/media/{webp_name}"
    except Exception:
        return None

def load_existing(json_file: Path, ndjson_file: Path) -> tuple[set[str], set[str], set[str], set[str]]:
    slug_ids, kp_ids, ty_keys, oy_keys = set(), set(), set(), set()

    def _add_record(rec: dict):
        mid = rec.get("id")
        if mid:
            slug_ids.add(mid)
        kpid = rec.get("kinopoiskId")
        if kpid:
            kp_ids.add(str(kpid))
        y = rec.get("year")
        if y:
            t = rec.get("title")
            if t:
                ty_keys.add(f"{norm_title(t)}|{y}")
            ot = rec.get("originalTitle")
            if ot:
                oy_keys.add(f"{norm_title(ot)}|{y}")

    # JSON
    if json_file.exists() and json_file.stat().st_size > 0:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                movies = []
                if isinstance(data, dict) and "movies" in data:
                    movies = data["movies"]
                elif isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, list):
                            movies.extend(v)
                for it in movies:
                    if isinstance(it, dict):
                        _add_record(it)
        except Exception:
            pass

    # NDJSON
    if ndjson_file.exists():
        try:
            with open(ndjson_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        it = json.loads(line)
                        if isinstance(it, dict):
                            _add_record(it)
                    except Exception:
                        continue
        except Exception:
            pass

    return slug_ids, kp_ids, ty_keys, oy_keys

def append_ndjson(path: Path, obj: dict):
    line = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)

def decide_category(det: dict) -> str:
    genre = (det.get("genre") or "").lower()
    cat_num = str(det.get("category") or "")
    seasons_count = int(det.get("seasons_count") or 0)
    if "аниме" in genre or cat_num == "4":
        return "anime"
    if "мульт" in genre:
        return "multfilmy"
    if seasons_count > 0 or cat_num in ("2", "5"):
        return "serialy"
    return "filmy"

def details_by_kp_or_token(token: str, id_kp: Optional[str], token_movie: Optional[str]) -> Optional[dict]:
    params = {"token": token}
    if id_kp:
        params["kp"] = id_kp
    elif token_movie:
        params["token_movie"] = token_movie
    else:
        return None
    data = http_get_json(ALLOHA_BASE, params)
    if not data or "data" not in data:
        return None
    return data["data"]

def run_debug_dump(api_token: str):
    log("DEBUG DUMP MODE: writing up to 100 items to NDJSON without sorting/rewrite")

    FEED_TYPES = ["movie", "serial", "anime-serial", "tv-show"]
    feed = []
    for t in FEED_TYPES:
        for page in range(1, PAGES + 1):
            log(f"Fetch feed: type={t}, page={page}")
            payload = http_get_json(ALLOHA_BASE, {"token": api_token, "last": t, "order": "date", "page": page})
            if not payload or not payload.get("data"):
                break
            feed.extend(payload["data"])
    log(f"Feed collected: {len(feed)} items")

    if not feed:
        print("Пустая лента Alloha.")
        return

    existing_slug_ids, existing_kp_ids, existing_ty_keys, existing_oy_keys = load_existing(MOVIES_JSON, NDJSON_OUTPUT)
    added = 0
    seen_pairs = {}

    for item in feed:
        _hotkey_exit_poll()
        if _stop_requested():
            break
        if added >= 100:
            break
        try:
            id_kp = str(item.get("id_kp") or "") or None
            if not id_kp:
                if VERBOSE: log("  → no kp id. skip")
                continue
            token_movie = item.get("token_movie") or None
            key = (id_kp or "", token_movie or "")
            cnt = seen_pairs.get(key, 0)
            if cnt > 0:
                if VERBOSE: log(f"skip: seen pair kp={id_kp or '-'}, token={token_movie or '-'}, repeat={cnt+1}")
                seen_pairs[key] = cnt + 1
                continue
            seen_pairs[key] = 1

            det = details_by_kp_or_token(api_token, id_kp, token_movie)
            if not det:
                continue

            raw_desc = html.unescape(det.get("description") or "").strip()
            if not raw_desc:
                continue

            title = det.get("name") or ""
            original_title = det.get("original_name") or ""
            year = det.get("year")
            country = det.get("country") or ""
            category = decide_category(det)
            # исключаем российские производства
            if is_russian_production(country):
                if VERBOSE: log("  → russian production. skip")
                continue

            if category in ("serialy", "anime"):
                seas_count = det.get("seasons_count")
                cur_season = det.get("season")
                last_episode = det.get("last_episode") or det.get("episode")
                season_val = season_str_from_count(int(seas_count or cur_season or 0))
                episode_val = episode_str(int(last_episode or 0))
            else:
                season_val = None
                episode_val = None

            # Ранний дедуп по содержанию
            ty_key = f"{norm_title(title)}|{year}" if title and year else None
            oy_key = f"{norm_title(original_title)}|{year}" if original_title and year else None

            if id_kp and (id_kp in existing_kp_ids):
                continue
            if ty_key and ty_key in existing_ty_keys:
                continue
            if oy_key and oy_key in existing_oy_keys:
                continue

            # Формирование ID: kp → tmdb → fallback-хэш
            tmdb_id = str(det.get("id_tmdb") or "") or None
            slug_base = slugify(title) or slugify(original_title) or hashlib.md5((title or original_title).encode("utf-8", "ignore")).hexdigest()[:10]

            if id_kp:
                mid = f"kp{id_kp}-{slug_base}"
                mid_origin = "kp"
            elif tmdb_id:
                mid = f"tmdb{tmdb_id}-{slug_base}"
                mid_origin = "tmdb"
            else:
                base = "|".join([
                    norm_title(title) or norm_title(original_title) or "",
                    str(year or ""),
                    norm_title(original_title) or "",
                ])
                h = hashlib.sha1(base.encode("utf-8", "ignore")).hexdigest()[:8]
                mid = f"{h}-{slug_base}"
                mid_origin = "hash"
            if VERBOSE: log(f"  mid: {mid} (source={mid_origin})")

            if mid in existing_slug_ids:
                continue

            # Поля рейтингов (без TMDB popularity/трейлера/картинки)
            try:
                kp_rating = float(det["rating_kp"]) if det.get("rating_kp") not in (None, "", "null") else None
            except Exception:
                kp_rating = None
            try:
                imdb_rating = float(det["rating_imdb"]) if det.get("rating_imdb") not in (None, "", "null") else None
            except Exception:
                imdb_rating = None
            if imdb_rating is None:
                va = fetch_tmdb_vote_average(tmdb_id, "movie")
                if va is not None:
                    imdb_rating = va

            premiere_raw = det.get("premiere_ru") or det.get("premiere") or None
            premiere = format_date_ru(premiere_raw)

            record = {
                "id": mid,
                "category": category,
                "title": title,
                "year": year,
                "season": season_val,
                "image": None,  # без скачивания
                "description": raw_desc,  # без переписывания
                "originalTitle": original_title or "",
                "country": country or "",
                "premiere": premiere,
                "director": ((det.get("directors") or "").split(",")[0].strip() or None),
                "genres": titlecase_genres(det.get("genre")),
                "translation": det.get("translation") or None,
                "actors": det.get("actors") or "",
                "kpRating": kp_rating,
                "imdbRating": imdb_rating,
                "youtubeId": None,
                "trailer": None,
                "kinopoiskId": id_kp,
                "ageRating": det.get("age_restrictions") or None,
                "comments": [],
                "popularity": None,
            }
            if episode_val:
                record["episode"] = episode_val

            append_ndjson(NDJSON_OUTPUT, record)

            # обновим индексы для дедупа
            existing_slug_ids.add(mid)
            if id_kp:
                existing_kp_ids.add(id_kp)
            if ty_key:
                existing_ty_keys.add(ty_key)
            if oy_key:
                existing_oy_keys.add(oy_key)

            added += 1
            if added % 10 == 0:
                log(f"DEBUG: written {added} records")
        except Exception:
            continue

    log(f"DEBUG DUMP DONE: written {added} records to {NDJSON_OUTPUT.name}")

# -------- Main --------
def main():
    try:
        # if gemini_rewrite is None and not DEBUG_DUMP_100:
        #     raise SystemExit("Останов: модуль переписывания описаний (Gemini) недоступен — добавление запрещено.")
        if gemini_rewrite is None:
            raise SystemExit("Останов: модуль переписывания описаний (Gemini) недоступен — добавление запрещено.")
        api_token = load_alloha_token()
        if not api_token:
            raise SystemExit("Не найден api_token (alloha.config или ALLOHA_TOKEN).")

        # if DEBUG_DUMP_100:
        #     run_debug_dump(api_token)
        #     return

        # Собираем ленту последних фильмов и сериалов
        FEED_TYPES = ["movie", "serial", "anime-serial", "tv-show"]
        feed = []
        for t in FEED_TYPES:
            for page in range(1, PAGES + 1):
                log(f"Fetch feed: type={t}, page={page}")
                payload = http_get_json(ALLOHA_BASE, {"token": api_token, "last": t, "order": "date", "page": page})
                cnt = len((payload or {}).get("data") or [])
                log(f"  → received {cnt} items")
                if not payload or not payload.get("data"):
                    break
                feed.extend(payload["data"])
        log(f"Feed total: {len(feed)} items")

        if not feed:
            print("Пустая лента Alloha.")
            return

        existing_slug_ids, existing_kp_ids, existing_ty_keys, existing_oy_keys = load_existing(MOVIES_JSON, NDJSON_OUTPUT)
        log(f"Existing IDs: slug={len(existing_slug_ids)}, kp={len(existing_kp_ids)}, title+year={len(existing_ty_keys)}, orig+year={len(existing_oy_keys)}")

        # случайная цель на запуск
        target_add = random.randint(5, 10)

        # для разнообразия перемешаем ленту
        random.shuffle(feed)

        added = 0
        seen_pairs = {} # (id_kp, token_movie)

        # 1) собираем кандидатов (быстрая оценка “горячести”)
        candidates = []
        MAX_CANDIDATES = 60

        for item in feed:
            _hotkey_exit_poll()
            if _stop_requested():
                break
            if len(candidates) >= MAX_CANDIDATES:
                break
            try:
                id_kp = str(item.get("id_kp") or "") or None
                if not id_kp:
                    if VERBOSE: log("  → no kp id. skip")
                    continue
                token_movie = item.get("token_movie") or None
                key = (id_kp or "", token_movie or "")
                cnt = seen_pairs.get(key, 0)
                if cnt > 0:
                    if VERBOSE: log(f"skip: seen pair kp={id_kp or '-'}, token={token_movie or '-'}, repeat={cnt+1}")
                    seen_pairs[key] = cnt + 1
                    continue
                seen_pairs[key] = 1

                if VERBOSE: log(f"Details request: kp={id_kp}, token_movie={token_movie}")
                det = details_by_kp_or_token(api_token, id_kp, token_movie)
                if not det:
                    log("  → no details. skip")
                    continue

                raw_desc = html.unescape(det.get("description") or "").strip()
                if not raw_desc:
                    if VERBOSE: log("  → empty description. skip")
                    continue

                title = det.get("name") or ""
                original_title = det.get("original_name") or ""
                year = det.get("year")
                country = det.get("country") or ""
                category = decide_category(det)
                # исключаем российские производства
                if is_russian_production(country):
                    if VERBOSE: log("  → russian production. skip")
                    continue

                if category in ("serialy", "anime"):
                    seas_count = det.get("seasons_count")
                    cur_season = det.get("season")
                    last_episode = det.get("last_episode") or det.get("episode")
                    season_val = season_str_from_count(int(seas_count or cur_season or 0))
                    episode_val = episode_str(int(last_episode or 0))
                else:
                    season_val = None
                    episode_val = None

                # до трейлера
                tmdb_popularity = None
                tmdb_id = str(det.get("id_tmdb") or "") or None

                # Берём только iframe от Alloha, остальное (YouTube/TMDB-видео) — позже
                trailer_url, youtube_id = parse_youtube_from_iframe(det.get("iframe_trailer"))
                if VERBOSE:
                    src = "alloha" if trailer_url else "none"
                    log(f"  trailer (candidates): source={src}")

                # popularity быстро, без /videos
                _hotkey_exit_poll()
                pop = fetch_tmdb_popularity_only(tmdb_id, "movie")
                tmdb_popularity = pop if pop is not None else tmdb_popularity

                score = 0.0
                if tmdb_popularity:
                    score = float(tmdb_popularity)
                elif det.get("rating_kp") not in (None, "", "null"):
                    try: score = float(det.get("rating_kp"))
                    except: score = 0.0
                elif det.get("rating_imdb") not in (None, "", "null"):
                    try: score = float(det.get("rating_imdb"))
                    except: score = 0.0

                slug_base = slugify(title) or slugify(original_title) or hashlib.md5((title or original_title).encode("utf-8", "ignore")).hexdigest()[:10]
                tmdb_id = str(det.get("id_tmdb") or "") or None

                # ключи для дедупа по содержанию
                ty_key = f"{norm_title(title)}|{year}" if title and year else None
                oy_key = f"{norm_title(original_title)}|{year}" if original_title and year else None

                # ранний дедуп: kp / title|year / originalTitle|year
                if id_kp and (id_kp in existing_kp_ids):
                    if VERBOSE: log(f"  → dup by kp: {id_kp}. skip")
                    continue
                if ty_key and ty_key in existing_ty_keys:
                    if VERBOSE: log(f"  → dup by title+year: {ty_key}. skip")
                    continue
                if oy_key and oy_key in existing_oy_keys:
                    if VERBOSE: log(f"  → dup by origTitle+year: {oy_key}. skip")
                    continue

                # формирование mid: kp → tmdb → fallback-хэш
                tmdb_id = str(det.get("id_tmdb") or "") or None
                slug_base = slugify(title) or slugify(original_title) or hashlib.md5((title or original_title).encode("utf-8", "ignore")).hexdigest()[:10]

                if id_kp:
                    mid = f"kp{id_kp}-{slug_base}"
                    mid_origin = "kp"
                elif tmdb_id:
                    mid = f"tmdb{tmdb_id}-{slug_base}"
                    mid_origin = "tmdb"
                else:
                    base = "|".join([
                        norm_title(title) or norm_title(original_title) or "",
                        str(year or ""),
                        norm_title(original_title) or "",
                    ])
                    h = hashlib.sha1(base.encode("utf-8", "ignore")).hexdigest()[:8]
                    mid = f"{h}-{slug_base}"
                    mid_origin = "hash"
                if VERBOSE: log(f"  mid: {mid} (source={mid_origin})")

                # защита от редкой коллизии mid: в нашей модели — просто скипаем
                if mid in existing_slug_ids:
                    if VERBOSE: log(f"  → dup by id: {mid}. skip")
                    continue

                genres = titlecase_genres(det.get("genre"))
                premiere_raw = det.get("premiere_ru") or det.get("premiere") or None
                premiere_fmt = format_date_ru(premiere_raw)

                candidates.append({
                    "score": score,
                    "mid": mid,
                    "title": title,
                    "original_title": original_title,
                    "year": year,
                    "country": country,
                    "category": category,
                    "season_val": season_val,
                    "episode_val": episode_val,
                    "genres": genres,
                    "translation": det.get("translation") or None,
                    "actors": det.get("actors") or "",
                    "kpRating": (float(det["rating_kp"]) if det.get("rating_kp") not in (None, "", "null") else None),
                    "imdbRating": (float(det["rating_imdb"]) if det.get("rating_imdb") not in (None, "", "null") else None),
                    "ageRating": det.get("age_restrictions") or None,
                    "trailer_url": trailer_url,
                    "youtube_id": youtube_id,
                    "tmdb_popularity": tmdb_popularity,
                    "directors_csv": det.get("directors") or "",
                    "poster_url": det.get("poster"),
                    "raw_desc": raw_desc,
                    "id_kp": id_kp,
                    "token_movie": token_movie,
                    "slug_base": slug_base,
                    "premiere": premiere_fmt,
                    "ty_key": ty_key,
                    "oy_key": oy_key,
                    "tmdb_id": tmdb_id,  # ← добавь эту строку
                })
                if VERBOSE and len(candidates) % 10 == 0:
                    log(f"Candidates collected: {len(candidates)}")
            except Exception as e:
                log(f"  error on candidate: {e}")
                continue
    except KeyboardInterrupt:
        log("Stopped by user (Ctrl+C).")
        return

    if not candidates:
        print("Нет подходящих кандидатов (нет описаний).")
        return

    # 2) сортируем по горячести и набираем сверху нужное количество (пропуская уже существующие)
    log(f"Candidates total: {len(candidates)}; selecting top-{min(MAX_CANDIDATES, len(candidates))}")
    def sort_key(c):
        pop = c.get("tmdb_popularity")
        kp = c.get("kpRating")
        imdb = c.get("imdbRating")
        return (
            1 if pop is not None else 0,           # сначала у кого вообще есть popularity
            pop or 0.0,                             # по величине popularity
            (kp/10.0) if isinstance(kp, float) else -1.0,    # затем KP 0..1
            (imdb/10.0) if isinstance(imdb, float) else -1.0 # затем IMDB 0..1
        )

    candidates.sort(key=sort_key, reverse=True)
    k = target_add
    selected = []
    for c in candidates[:MAX_CANDIDATES]:
        if len(selected) >= k:
            break
        selected.append(c)
    log(f"Target add (random): {k}")
    if VERBOSE and selected:
        top_preview = ", ".join([f"{(c['score'] or 0):.1f}" for c in selected[:5]])
        log(f"Selected scores preview: {top_preview}")

    for c in selected:
        _hotkey_exit_poll()
        if _stop_requested():
            break
        if added >= k:
            break
        try:
            log(f"Process: {c['title']} ({c['year']}) id={c['mid']}")
            if not c.get("id_kp"):
                if VERBOSE: log("  → no kp id. skip")
                continue
            description = c["raw_desc"]
            # Определяем трейлер только для финально выбранных
            trailer_url = c.get("trailer_url")
            youtube_id = c.get("youtube_id")

            if trailer_url:
                if VERBOSE: log(f"  trailer: source=alloha youtubeId={youtube_id}")
            else:
                tu, ty = find_trailer_via_youtube(c["title"], c["original_title"], c["year"])
                if tu:
                    trailer_url, youtube_id = tu, ty
                    if VERBOSE: log(f"  trailer: source=youtube youtubeId={youtube_id}")
                else:
                    pop2, t_url, t_yid = fetch_tmdb_popularity_and_trailer(c.get("tmdb_id"), "movie")
                    if t_url:
                        trailer_url, youtube_id = t_url, t_yid
                        if VERBOSE: log(f"  trailer: source=tmdb youtubeId={youtube_id}")
                    else:
                        if VERBOSE: log("  trailer: source=none")

            # Обновим в словаре кандидата для записи
            c["trailer_url"] = trailer_url
            c["youtube_id"] = youtube_id
            if not c.get("imdbRating"):
                va = fetch_tmdb_vote_average(c.get("tmdb_id"), "movie")
                if va is not None:
                    c["imdbRating"] = va
            
            if gemini_rewrite:
                log("  rewrite start")
                rewritten = gemini_rewrite(description, c["title"], c["year"], c["original_title"], c["country"], c["category"])
                log("  rewrite done")
                if rewritten is not None and rewritten.strip():
                    description = rewritten.strip()
            if not description:
                log("  → empty rewritten description. skip")
                continue

            image_path = download_image(c["poster_url"], c["slug_base"])
            if image_path:
                log(f"  poster saved: {image_path}")
            else:
                # fallback: пробуем постер из TMDB
                mt_hint = "tv" if c["category"] in ("serialy", "anime") else "movie"
                tmdb_poster = fetch_tmdb_poster_url(c.get("tmdb_id"), mt_hint)
                if tmdb_poster:
                    image_path = download_image(tmdb_poster, c["slug_base"])
                    if image_path and VERBOSE:
                        log(f"  poster saved (tmdb): {image_path}")
                if not image_path:
                    if VERBOSE: log("  poster not saved (no url or error) — skip")
                    continue

            record = {
                "id": c["mid"],
                "category": c["category"],
                "title": c["title"],
                "year": c["year"],
                "season": c["season_val"],
                "image": image_path,
                "description": description,
                "originalTitle": c["original_title"] or "",
                "country": c["country"] or "",
                "premiere": c["premiere"],
                "director": ((c["directors_csv"] or "").split(",")[0].strip() or None),
                "genres": c["genres"],
                "translation": c["translation"],
                "actors": c["actors"],
                "kpRating": c["kpRating"],
                "imdbRating": c["imdbRating"],
                "youtubeId": c["youtube_id"],
                "trailer": c["trailer_url"],
                "kinopoiskId": c["id_kp"],
                "ageRating": c["ageRating"],
                "comments": [],
                "popularity": c["tmdb_popularity"],
            }
            if c["episode_val"]:
                record["episode"] = c["episode_val"]

            append_ndjson(NDJSON_OUTPUT, record)
            log(f"  written to {NDJSON_OUTPUT.name}")

            existing_slug_ids.add(c["mid"])
            if c["id_kp"]:
                existing_kp_ids.add(c["id_kp"])
            if c["ty_key"]:
                existing_ty_keys.add(c["ty_key"])
            if c["oy_key"]:
                existing_oy_keys.add(c["oy_key"])

            added += 1
        except Exception as e:
            log(f"  error on write: {e}")
            continue

    log(f"Done. Added: {added} (from {len(candidates)} candidates).")

if __name__ == "__main__":
    main()