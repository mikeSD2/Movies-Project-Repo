# save as publish_rewritten_to_movies_data.py
import json
import sys
import time
import pathlib
import re
from html import unescape

BASE = pathlib.Path(__file__).resolve().parent
MOVIES_DATA_JSON = BASE / "movies-data.json"
NDJSON_IN = BASE / "rewritten-items.ndjson"
BACKUP = BASE / "movies-data.json.bak"

def norm_kp(v):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None

SEASON_PATTERNS = [
    r"\b\d+\s*сезон(?:[аы])?\b",
    r"\b\d+\s*-\s*\d+\s*сезон(?:[аы])?\b",
    r"\bвсе\s+серии\s+подряд\b",
    r"\bсезон\b",
]
SEASON_RE = re.compile("|".join(SEASON_PATTERNS), re.IGNORECASE)

def normalize_title_key(s: str | None) -> str | None:
    if not s:
        return None
    t = unescape(s)
    t = t.replace("«", "").replace("»", "").replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("*", "").replace("★", "")
    t = SEASON_RE.sub("", t)
    t = re.sub(r"\(\s*(19|20)\d{2}\s*\)", "", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t or None

# replace in publish_rewritten_to_movies_data.py

def load_movies_object(path: pathlib.Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not isinstance(data.get("movies"), list):
        raise ValueError("movies-data.json must be an object with 'movies' array")
    return data, data["movies"]

def save_movies_object(path: pathlib.Path, root: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        # сохранит исходные ключи (categories/genres/years) как есть
        json.dump(root, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def build_indices(items):
    # kp -> index
    kp_to_index = {}
    # (norm_title, year_str) -> index; учитываем и title, и originalTitle
    title_year_to_index = {}

    for i, it in enumerate(items):
        kp = norm_kp(it.get("kinopoiskId"))
        if kp and kp not in kp_to_index:
            kp_to_index[kp] = i

        y_str = str(it.get("year") or "").strip()
        for k in (normalize_title_key(it.get("title")),
                  normalize_title_key(it.get("originalTitle"))):
            if k:
                title_year_to_index.setdefault((k, y_str), i)
    return kp_to_index, title_year_to_index

def main():
    root, movies = load_movies_object(MOVIES_DATA_JSON)
    kp_to_index, title_year_to_index = build_indices(movies)
    root["movies"] = movies

    # Подсчёт строк для прогресса
    total_lines = 0
    with open(NDJSON_IN, "r", encoding="utf-8", errors="ignore") as f:
        for _ in f:
            total_lines += 1

    print(f"Publishing rewritten items from {NDJSON_IN} into {MOVIES_DATA_JSON}")
    print(f"Existing items: {len(movies)}, NDJSON lines: {total_lines}")

    processed = 0
    added_kp = 0
    added_no_kp = 0
    replaced_kp = 0
    replaced_title_year = 0
    parse_errors = 0

    start = time.time()
    last_tick = start

    with open(NDJSON_IN, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            processed += 1
            now = time.time()
            if processed % 1000 == 0 or (now - last_tick) >= 1.0:
                last_tick = now
                elapsed = now - start
                rate = (processed / elapsed) if elapsed > 0 else 0.0
                eta = int(((total_lines - processed) / rate)) if rate > 0 else 0
                sys.stdout.write(f"\rProcessed {processed}/{total_lines} | {rate:.1f}/s | ETA {eta}s")
                sys.stdout.flush()

            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                parse_errors += 1
                continue

            kp = norm_kp(obj.get("kinopoiskId"))
            if kp:
                if kp in kp_to_index:
                    idx = kp_to_index[kp]
                    # Preserve existing slug/id and trailer fields so URLs and trailers don't change
                    old_item = movies[idx]
                    old_id = old_item.get("id")
                    if old_id:
                        obj["id"] = old_id
                    # Preserve trailer-related fields exactly as they were in existing movie
                    for k in ("youtubeId", "trailer"):
                        if k in old_item:
                            obj[k] = old_item[k]
                        else:
                            obj.pop(k, None)
                    movies[idx] = obj
                    replaced_kp += 1
                else:
                    movies.append(obj)
                    new_idx = len(movies) - 1
                    kp_to_index[kp] = new_idx
                    added_kp += 1
                # обновим индекс по (title, year)
                y_str = str(obj.get("year") or "").strip()
                for k in (normalize_title_key(obj.get("title")),
                          normalize_title_key(obj.get("originalTitle"))):
                    if k:
                        title_year_to_index[(k, y_str)] = kp_to_index[kp]
                continue

            # без kp: замена по (title+year) или (originalTitle+year)
            y_str = str(obj.get("year") or "").strip()
            t_key = normalize_title_key(obj.get("title"))
            o_key = normalize_title_key(obj.get("originalTitle"))
            idx = None
            if t_key and (t_key, y_str) in title_year_to_index:
                idx = title_year_to_index[(t_key, y_str)]
            elif o_key and (o_key, y_str) in title_year_to_index:
                idx = title_year_to_index[(o_key, y_str)]

            if idx is not None:
                # Preserve existing slug/id and trailer fields so URLs and trailers don't change
                old_item = movies[idx]
                old_id = old_item.get("id")
                if old_id:
                    obj["id"] = old_id
                for k in ("youtubeId", "trailer"):
                    if k in old_item:
                        obj[k] = old_item[k]
                    else:
                        obj.pop(k, None)
                movies[idx] = obj
                replaced_title_year += 1
                # если внезапно появился kp — заиндексируем
                kp2 = norm_kp(obj.get("kinopoiskId"))
                if kp2:
                    kp_to_index[kp2] = idx
                # и обновим (title,year)
                for k in (normalize_title_key(obj.get("title")),
                          normalize_title_key(obj.get("originalTitle"))):
                    if k:
                        title_year_to_index[(k, y_str)] = idx
            else:
                movies.append(obj)
                added_no_kp += 1
                new_idx = len(movies) - 1
                # индексировать по названию не обязательно, но можно:
                if t_key:
                    title_year_to_index[(t_key, y_str)] = new_idx
                if o_key:
                    title_year_to_index[(o_key, y_str)] = new_idx
                    
    print()  # newline

    # Бэкап и атомарная запись
    try:
        if MOVIES_DATA_JSON.exists():
            MOVIES_DATA_JSON.replace(BACKUP)
            print(f"Backup saved to {BACKUP}")
    except Exception:
        print("Backup failed (continuing)...")

    save_movies_object(MOVIES_DATA_JSON, root)

    print(
        f"Done. Replaced by kp: {replaced_kp}, Replaced by title+year: {replaced_title_year}, "
        f"Added with kp: {added_kp}, Added without kp: {added_no_kp}, "
        f"ParseErrors: {parse_errors}, Final: {len(movies)}"
    )

if __name__ == "__main__":
    main()