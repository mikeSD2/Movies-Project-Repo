# save as rewrite_descriptions_local.py
import json
import sys
import time
import signal
import pathlib
from typing import Optional

# Использует вашу функцию из fetch_tmdb_movies.py (ключи/лимиты уже там)
from fetch_tmdb_movies import rewrite_description_sync

BASE = pathlib.Path(__file__).resolve().parent
MOVIES_JSON = BASE / "movies.json"
NDJSON_OUT = BASE / "rewritten-items.ndjson"
PROGRESS_JSON = BASE / "rewritten-progress.json"

# Режимы: 'all' | 'missing_or_short' | 'iskodik'
MODE = 'all'
SHORT_THRESHOLD = 80
SAVE_EVERY = 200  # как часто сохранять прогресс (успешных рерайтов)

shutdown = False
def on_sigint(sig, frame):
    global shutdown
    shutdown = True
signal.signal(signal.SIGINT, on_sigint)

def should_rewrite(item: dict) -> bool:
    if MODE == 'iskodik':
        return bool(item.get('iskodik'))
    desc = (item.get('description') or '').strip()
    if MODE == 'missing_or_short':
        return (not desc) or (len(desc) < SHORT_THRESHOLD)
    return bool(desc)

def item_key(item: dict) -> str:
    kp = str(item.get('kinopoiskId') or '').strip()
    if kp:
        return f"kp:{kp}"
    id_ = (item.get('id') or '').strip().lower()
    yr = str(item.get('year') or '')
    return f"id:{id_}|y:{yr}"

def load_progress() -> set[str]:
    keys = set()
    # Прогресс-файл
    if PROGRESS_JSON.exists():
        try:
            data = json.loads(PROGRESS_JSON.read_text(encoding='utf-8') or "[]")
            if isinstance(data, list):
                keys.update(data)
        except Exception:
            pass
    # Уже переписанные элементы из NDJSON
    if NDJSON_OUT.exists():
        try:
            with open(NDJSON_OUT, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        keys.add(item_key(obj))
                    except Exception:
                        continue
        except Exception:
            pass
    return keys

def save_progress(keys: set[str]):
    try:
        PROGRESS_JSON.write_text(json.dumps(list(keys), ensure_ascii=False, indent=0), encoding='utf-8')
    except Exception:
        pass

def append_ndjson(path: pathlib.Path, item: dict):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(item, ensure_ascii=False))
        f.write('\n')

def main():
    # Читаем массив фильмов (без изменений файла)
    with open(MOVIES_JSON, 'r', encoding='utf-8') as f:
        movies = json.load(f)
    if not isinstance(movies, list):
        print("movies.json должен быть массивом.")
        sys.exit(1)

    done_keys = load_progress()
    total = len(movies)
    print(f"Rewriting descriptions for {total} items (mode={MODE})")
    print(f"Already done (from progress/ndjson): {len(done_keys)}")

    processed = 0
    rewritten = 0
    skipped = 0
    failed = 0
    already_done = 0
    start = time.time()
    last_tick = start
    since_last_save = 0

    for idx, item in enumerate(movies):
        if shutdown:
            break

        processed += 1
        k = item_key(item)
        if k in done_keys:
            already_done += 1
            continue

        now = time.time()
        if processed % 500 == 0 or (now - last_tick) >= 1.0:
            last_tick = now
            elapsed = now - start
            rate = (processed / elapsed) if elapsed > 0 else 0.0
            eta = int(((total - processed) / rate)) if rate > 0 else 0
            sys.stdout.write(f"\rProcessed {processed}/{total} | rewritten {rewritten} | already {already_done} | {rate:.1f}/s | ETA {eta}s")
            sys.stdout.flush()

        if not should_rewrite(item):
            skipped += 1
            # ПО ЖЕЛАНИЮ: если не хотите помечать такие как "done", закомментируйте следующую строку
            done_keys.add(k)
            continue

        orig_desc = (item.get('description') or '').strip()
        try:
            new_desc = rewrite_description_sync(orig_desc)
        except Exception:
            failed += 1
            continue

        if new_desc is None:
            failed += 1
            continue

        new_desc = (new_desc or '').strip()
        if not new_desc:
            failed += 1
            continue

        # Не меняем movies.json — формируем объект для ndjson
        out_item = dict(item)
        out_item['description'] = new_desc

        try:
            append_ndjson(NDJSON_OUT, out_item)
        except Exception:
            # Даже если ndjson не записался — считаем переписанным, но можно убрать if нужно строго
            pass

        done_keys.add(k)
        rewritten += 1
        since_last_save += 1
        if since_last_save >= SAVE_EVERY:
            save_progress(done_keys)
            since_last_save = 0

    print()  # newline
    save_progress(done_keys)

    print(f"Done. Rewritten: {rewritten}, Skipped(by mode): {skipped}, Failed(API): {failed}, AlreadyDone: {already_done}, Total: {total}")
    print(f"Progress saved to: {PROGRESS_JSON}")
    print(f"Rewritten items appended to: {NDJSON_OUT}")

if __name__ == '__main__':
    main()