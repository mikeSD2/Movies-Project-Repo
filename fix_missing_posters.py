import json
import os
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# наверху файла рядом с остальными константами
import random
from urllib.parse import urlparse, urlunparse

RETRIES = int(os.environ.get("POSTER_DL_RETRIES", "5"))
BACKOFF_BASE = float(os.environ.get("POSTER_DL_BACKOFF_BASE", "0.8"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/127.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
    "Referer": "https://shikimori.one/",
    "Connection": "keep-alive",
}

try:
    import requests
except ImportError:
    raise SystemExit("Требуется пакет 'requests'. Установите: pip install requests")

MOVIES_PATH = "movies-data-without-pop-pretty-updated.json"
SERIALS_PATH = "serials.json"
FILMS_PATH = "films.json"

IMAGES_DIR = os.path.join("uploads", "images")

# Параллельность
MAX_WORKERS = int(os.environ.get("POSTER_DL_WORKERS", "16"))

TIMEOUT = 20
# RETRIES уже объявлен выше через окружение (POSTER_DL_RETRIES)
# SLEEP_BETWEEN_RETRIES не используется; можно удалить или оставить закомментированным

# Нужны только «реальные» новые постеры: локальная заглушка — это nokp-untitled.*
UNTITLED_PAT = re.compile(r"(?:^|[/\\])(?:nokp-)?untitled\.(?:jpe?g|png)$", re.IGNORECASE)

# Ключи, где можем встретить постер в sources
POSSIBLE_POSTER_KEYS = ("anime_poster_url", "poster_url", "image", "poster")

def ensure_dir(path: str):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

def norm_title(title: str) -> str:
    if not title:
        return ""
    t = title.strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t

def extract_kp_from_composite_id(item_id: str) -> str | None:
    if not item_id:
        return None
    m = re.match(r"^(\d+)", item_id)
    return m.group(1) if m else None

def guess_ext_from_ct_or_url(ct: str, url: str) -> str:
    if ct:
        ct = ct.lower()
        if "jpeg" in ct:
            return ".jpg"
        if "png" in ct:
            return ".png"
        if "webp" in ct:
            return ".webp"
    m = re.search(r"\.(jpe?g|png|webp)(?:\?|$)", url.lower())
    if m:
        ext = m.group(1)
        return ".jpg" if ext.startswith("jp") else f".{ext}"
    return ".jpg"

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_poster_in_obj(obj: dict) -> str | None:
    # ищем по набору ключей в корне и в material_data
    for key in POSSIBLE_POSTER_KEYS:
        v = obj.get(key)
        if isinstance(v, str) and v.startswith("http"):
            return v
    md = obj.get("material_data") or {}
    if isinstance(md, dict):
        for key in POSSIBLE_POSTER_KEYS:
            v = md.get(key)
            if isinstance(v, str) and v.startswith("http"):
                return v
    return None

def build_poster_maps_from_sources():
    """
    Читаем ТОЛЬКО serials.json и films.json.
    Возвращаем:
      - map_kp_to_poster: {kp_id(str): poster_url(str)}
      - map_title_year_to_poster: {(norm_title, year): poster_url(str)}
    """
    map_kp_to_poster = {}
    map_title_year_to_poster = {}

    def ingest(path: str):
        if not os.path.exists(path):
            return
        try:
            data = load_json(path)
        except Exception as e:
            print(f"Не удалось прочитать {path}: {e}")
            return
        if not isinstance(data, list):
            return
        for it in data:
            if not isinstance(it, dict):
                continue
            poster = find_poster_in_obj(it)
            if not poster:
                continue
            # ключи
            kp = it.get("kinopoisk_id") or it.get("kp_link")
            if kp:
                map_kp_to_poster[str(kp)] = poster
            title = it.get("title") or (it.get("material_data") or {}).get("title")
            year = it.get("year") or (it.get("material_data") or {}).get("year")
            if title and year:
                try:
                    map_title_year_to_poster[(norm_title(title), int(year))] = poster
                except Exception:
                    pass

    ingest(SERIALS_PATH)
    ingest(FILMS_PATH)
    return map_kp_to_poster, map_title_year_to_poster

# замените вашу функцию download_with_retries(...) на эту
def download_with_retries(url: str) -> tuple[bytes | None, str]:
    """
    Возвращает (content | None, error_str).
    Делает несколько попыток, на 403/429/5xx ждёт и пробует альтернативный хост без 'dere.'.
    """
    def alternates(u: str) -> list[str]:
        try:
            p = urlparse(u)
            if p.netloc.startswith("dere.") and p.netloc.endswith("shikimori.one"):
                alt_netloc = p.netloc.replace("dere.", "", 1)  # shikimori.one
                return [u, urlunparse((p.scheme, alt_netloc, p.path, p.params, p.query, p.fragment))]
        except Exception:
            pass
        return [u]

    last_err = ""
    for attempt in range(1, RETRIES + 1):
        for alt in alternates(url):
            try:
                r = requests.get(alt, timeout=TIMEOUT, headers=HEADERS)
                if r.status_code == 200:
                    return r.content, r.headers.get("Content-Type", "")
                last_err = f"HTTP {r.status_code}"
                # На 403/429/5xx — подождать и повторить
                if r.status_code in (403, 429) or 500 <= r.status_code < 600:
                    # попробуем следующую альтернативу/попытку
                    continue
            except Exception as e:
                last_err = str(e)
                continue

        # экспоненциальный бэкофф с джиттером
        sleep_s = BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 0.5)
        time.sleep(sleep_s)

    return None, last_err

def plan_items(movies_data: dict | list):
    if isinstance(movies_data, dict) and isinstance(movies_data.get("movies"), list):
        return movies_data["movies"], True
    if isinstance(movies_data, list):
        return movies_data, False
    raise SystemExit("Неожиданная структура JSON: ожидается массив или объект с ключом 'movies'")

def main():
    if not os.path.exists(MOVIES_PATH):
        raise SystemExit(f"Не найден файл: {MOVIES_PATH}")

    ensure_dir(IMAGES_DIR)

    # Бэкап целиком
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{MOVIES_PATH}.bak.{ts}"
    try:
        with open(MOVIES_PATH, "r", encoding="utf-8") as rf, open(backup_path, "w", encoding="utf-8") as wf:
            wf.write(rf.read())
        print(f"Сделан бэкап: {backup_path}")
    except Exception as e:
        print(f"Не удалось создать бэкап: {e}")

    # Карты постеров ТОЛЬКО из serials.json и films.json
    map_kp_to_poster, map_title_year_to_poster = build_poster_maps_from_sources()
    print(f"Карты постеров: by_kp={len(map_kp_to_poster)}, by_title_year={len(map_title_year_to_poster)}")

    # Загружаем целевой
    data = load_json(MOVIES_PATH)
    items, is_wrapped = plan_items(data)
    total = len(items)
    print(f"Всего записей: {total}")

    # Собираем индексы с отсутствующими постерами
    missing = []
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            continue
        img = it.get("image") or ""
        if (not img) or UNTITLED_PAT.search(img):
            missing.append(i)

    print(f"К обновлению: {len(missing)}")

    # Планирование задач
    def resolve_poster_url(it: dict):
        kp_id = it.get("kinopoiskId") or extract_kp_from_composite_id(it.get("id") or "")
        title = it.get("title")
        year = it.get("year")
        # 1) по kp
        if kp_id and str(kp_id) in map_kp_to_poster:
            return map_kp_to_poster[str(kp_id)], str(kp_id)
        # 2) по (title, year)
        if title and year:
            u = map_title_year_to_poster.get((norm_title(title), int(year)))
            if u:
                return u, str(kp_id) if kp_id else None
        return None, None

    # Рабочая функция для потока
    def task(idx: int):
        it = items[idx]
        url, save_kp = resolve_poster_url(it)
        if not url:
            return idx, False, None, f"FAIL: {it.get('id') or ''} — постер в sources не найден"

        # имя файла
        base_name = save_kp or re.sub(r"[^a-z0-9]+", "-", norm_title(it.get("title") or "")) or f"idx-{idx}"
        dest_base = os.path.join(IMAGES_DIR, base_name)

        # если уже существует любой подходящий файл — не качаем
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = dest_base + ext
            if os.path.exists(p):
                rel = p.replace("\\", "/")
                return idx, True, rel, f"OK(local): {it.get('id') or ''} → {rel}"

        content, meta = download_with_retries(url)
        if not content:
            return idx, False, None, f"FAIL: {it.get('id') or ''} — загрузка не удалась ({meta})"

        ext = guess_ext_from_ct_or_url(meta if isinstance(meta, str) else "", url)
        final_path = dest_base + ext
        try:
            with open(final_path, "wb") as f:
                f.write(content)
        except Exception as e:
            return idx, False, None, f"FAIL: {it.get('id') or ''} — запись файла: {e}"

        rel = final_path.replace("\\", "/")
        return idx, True, rel, f"OK: {it.get('id') or ''} → {rel}"

    updated = 0
    errors = 0
    skipped = total - len(missing)
    processed = skipped

    # Параллельная загрузка только для нужных элементов
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(task, i) for i in missing]
        for fut in as_completed(futures):
            idx, ok, rel, msg = fut.result()
            processed += 1
            if ok and rel:
                items[idx]["image"] = rel
                updated += 1
            else:
                errors += 1
            print(f"[{processed}/{total}] {msg}")
            if processed % 200 == 0:
                print(f"== Прогресс: processed={processed}, updated={updated}, skipped={skipped}, errors={errors}")

    # Сохраняем
    out_obj = {"movies": items} if is_wrapped else items
    with open(MOVIES_PATH, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2)
    print(f"Готово. updated={updated}, skipped={skipped}, errors={errors}")

if __name__ == "__main__":
    main()