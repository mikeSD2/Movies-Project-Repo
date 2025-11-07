# apply_rewrites_to_movies_json.py
import os
import json
from datetime import datetime

MOVIES_JSON = "movies-data-sorted.json"
REWRITES_NDJSON = "rewritten-descriptions.ndjson"

def load_rewrites_map(ndjson_path: str) -> dict[str, str]:
    res = {}
    if not os.path.exists(ndjson_path):
        return res
    with open(ndjson_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                mid = obj.get("id")
                desc = obj.get("description", "")
                if mid:
                    res[mid] = desc if desc is not None else ""
            except Exception:
                continue
    return res

def main():
    if not os.path.exists(MOVIES_JSON):
        raise FileNotFoundError(MOVIES_JSON)

    rewrites = load_rewrites_map(REWRITES_NDJSON)
    print(f"Загружено переписей: {len(rewrites)}")

    with open(MOVIES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    movies = data.get("movies") if isinstance(data, dict) else None
    if movies is None or not isinstance(movies, list):
        raise RuntimeError("Ожидался формат { 'movies': [ ... ] }")

    updated = 0
    for m in movies:
        mid = m.get("id")
        if not mid:
            continue
        if mid in rewrites:
            m["description"] = rewrites[mid]
            updated += 1

    if updated == 0:
        print("Совпадений по id не найдено. Файл оставлен без изменений.")
        return

    backup_path = f"{MOVIES_JSON}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    tmp_path = f"{MOVIES_JSON}.tmp"

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(tmp_path, MOVIES_JSON)
    print(f"Готово. Обновлено записей: {updated}. Бэкап: {backup_path}")

if __name__ == "__main__":
    main()