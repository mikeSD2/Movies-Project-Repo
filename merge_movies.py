#!/usr/bin/env python3
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

INPUT_OLD = "movies-data-oldsite.json"
INPUT_NEW = "movies.json"
OUTPUT = "movies-data.json"

PROGRESS_EVERY = int(os.getenv("PROGRESS_EVERY", "50000"))

KP_ID_KEYS = [
    "kinopoiskId", "kinopoiskID", "kinopoiskid",
    "kp_id", "kpId", "kpid", "id_kp", "kinopoisk"
]
YOUTUBE_KEYS = ["youtubeId", "youtubeID", "youtubeid", "yt_id", "youtube"]
TRAILER_KEYS = ["trailer", "trailerUrl", "trailerURL"]

TITLE_KEYS = ["title", "name", "ruTitle", "ru_title"]
ORIG_TITLE_KEYS = ["originalTitle", "original_title", "origTitle", "orig_title"]
CATEGORY_KEYS = ["category", "type"]
SEASON_KEYS = ["season"]
YEAR_KEYS = ["year"]

def normalize_str(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return str(int(v)) if isinstance(v, bool) is False else str(v)
    if isinstance(v, str):
        s = " ".join(v.strip().split())
        return s if s != "" else None
    return str(v)

def lower_norm(v):
    s = normalize_str(v)
    return s.lower() if s is not None else None

def get_first_key(d, keys):
    for k in keys:
        if k in d:
            return k
    return None

def get_field(d, keys):
    k = get_first_key(d, keys)
    return d.get(k) if k else None

def extract_kp_id(item):
    for k in KP_ID_KEYS:
        if k in item:
            return normalize_str(item[k])
    return None

def extract_trailer(item):
    k = get_first_key(item, TRAILER_KEYS)
    return item.get(k) if k else None

def extract_youtube(item):
    k = get_first_key(item, YOUTUBE_KEYS)
    return item.get(k) if k else None

def target_youtube_key(base_item):
    k = get_first_key(base_item, YOUTUBE_KEYS)
    return k if k else "youtubeId"

def target_trailer_key(base_item):
    k = get_first_key(base_item, TRAILER_KEYS)
    return k if k else "trailer"

def keys_for_dedupe(item):
    keys = set()
    title = lower_norm(get_field(item, TITLE_KEYS))
    otitle = lower_norm(get_field(item, ORIG_TITLE_KEYS))
    year = normalize_str(get_field(item, YEAR_KEYS))
    category = lower_norm(get_field(item, CATEGORY_KEYS))
    season = lower_norm(get_field(item, SEASON_KEYS))

    if year:
        def add_keys(name):
            if not name:
                return
            keys.add(f"{name}||{year}")
            if category:
                keys.add(f"{name}||{year}||cat:{category}")
            if season:
                keys.add(f"{name}||{year}||season:{season}")
            if category or season:
                keys.add(f"{name}||{year}||cat:{category or ''}||season:{season or ''}")
        add_keys(title)
        add_keys(otitle)
    return keys

def iter_objects_from_arrays(path, chunk_size=1024*64):
    # Потоково извлекает объекты, являющиеся элементами ЛЮБЫХ массивов (в т.ч. вложенных).
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        in_str = False
        esc = False
        stack = []           # стек контейнеров: '[' или '{'
        capturing = False    # сейчас буферим объект-элемент массива
        buf = []
        obj_brace_depth = 0
        emitted = 0
        saw_array = False

        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            i = 0
            L = len(chunk)
            while i < L:
                ch = chunk[i]

                if capturing:
                    buf.append(ch)
                    if in_str:
                        if esc:
                            esc = False
                        else:
                            if ch == "\\":
                                esc = True
                            elif ch == "\"":
                                in_str = False
                    else:
                        if ch == "\"":
                            in_str = True
                        elif ch == "{":
                            obj_brace_depth += 1
                        elif ch == "}":
                            obj_brace_depth -= 1
                            if obj_brace_depth == 0:
                                try:
                                    yield json.loads("".join(buf))
                                except json.JSONDecodeError:
                                    s = "".join(buf).rstrip().rstrip(",")
                                    yield json.loads(s)
                                buf = []
                                capturing = False
                                emitted += 1
                    i += 1
                    continue

                # not capturing
                if in_str:
                    if esc:
                        esc = False
                    else:
                        if ch == "\\":
                            esc = True
                        elif ch == "\"":
                            in_str = False
                    i += 1
                    continue

                # outside string
                if ch == "\"":
                    in_str = True
                elif ch == "[":
                    stack.append("[")
                    saw_array = True
                elif ch == "]":
                    # pop until matching '['
                    while stack and stack[-1] != "[":
                        stack.pop()
                    if stack and stack[-1] == "[":
                        stack.pop()
                elif ch == "{":
                    # если верх стека — массив, начинаем захват элемента массива
                    if stack and stack[-1] == "[":
                        capturing = True
                        buf = ["{"]
                        obj_brace_depth = 1
                        # ВАЖНО: стек не трогаем, этот объект парсим отдельно
                    else:
                        # это не элемент массива, обычный объект внутри объекта
                        stack.append("{")
                elif ch == "}":
                    # закрываем последний объект в стеке (если есть)
                    if stack and stack[-1] == "{":
                        stack.pop()
                # прочие символы игнорируем
                i += 1

        # если ничего не отдали и массивов не встретили — возможен NDJSON, дадим шанс простому парсеру
        if emitted == 0 and not saw_array:
            for obj in iter_ndjson_lines(path):
                yield obj

def iter_ndjson_lines(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            s = line.strip()
            if not s or s in ("[", "]", ","):
                continue
            if s.endswith(",") and s.startswith("{"):
                s = s[:-1].rstrip()
            try:
                yield json.loads(s)
            except json.JSONDecodeError:
                # пропускаем «мусорные» строки, если вдруг встречаются
                continue

def load_by_kp(path, label):
    by_kp = {}
    unmatched = []
    count = 0
    print(f"[{label}] start parsing: {path}", flush=True)
    for item in iter_objects_from_arrays(path):
        if not isinstance(item, dict):
            continue
        kp = extract_kp_id(item)
        if kp is None:
            unmatched.append(item)
        else:
            if kp not in by_kp:
                by_kp[kp] = item
        count += 1
        if count % PROGRESS_EVERY == 0:
            print(f"[{label}] parsed: {count:,} | with kp: {len(by_kp):,} | no-kp: {len(unmatched):,}", flush=True)
    print(f"[{label}] done. total objects: {count:,}, with kp: {len(by_kp):,}, no-kp: {len(unmatched):,}", flush=True)
    return by_kp, unmatched

def main(inp_old=INPUT_OLD, inp_new=INPUT_NEW, out_path=OUTPUT):
    if not os.path.exists(inp_old):
        print(f"Файл не найден: {inp_old}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(inp_new):
        print(f"Файл не найден: {inp_new}", file=sys.stderr)
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_old = ex.submit(load_by_kp, inp_old, "oldsite")
        fut_new = ex.submit(load_by_kp, inp_new, "movies.json")
        old_by_kp, old_unmatched = fut_old.result()
        new_by_kp, new_unmatched = fut_new.result()

    result_count = 0
    added_kps = set()
    seen_dedupe_keys = set()

    def write_json_array_header(f):
        f.write("[\n")

    def write_json_array_footer(f):
        f.write("\n]\n")

    def write_item(f, obj, is_first):
        if not is_first:
            f.write(",\n")
        json.dump(obj, f, ensure_ascii=False, indent=2)
        for k in keys_for_dedupe(obj):
            seen_dedupe_keys.add(k)

    print("[write] start writing result:", out_path, flush=True)
    with open(out_path, "w", encoding="utf-8") as out:
        write_json_array_header(out)
        first = True

        # Stage 1: всё из movies.json (+замена trailer/youtube из oldsite)
        w1 = 0
        for kp, base in new_by_kp.items():
            merged = dict(base)
            if kp in old_by_kp:
                old = old_by_kp[kp]
                old_trailer = extract_trailer(old)
                old_yt = extract_youtube(old)
                t_trailer_key = target_trailer_key(merged)
                t_yt_key = target_youtube_key(merged)
                if old_trailer is not None:
                    merged[t_trailer_key] = old_trailer
                norm_old_yt = normalize_str(old_yt)
                if norm_old_yt is not None:
                    merged[t_yt_key] = norm_old_yt
            write_item(out, merged, first)
            first = False
            result_count += 1
            added_kps.add(kp)
            w1 += 1
            if w1 % PROGRESS_EVERY == 0:
                print(f"[write:stage1] written: {w1:,} (from movies.json), total: {result_count:,}", flush=True)
        print(f"[write:stage1] done. written: {w1:,}", flush=True)

        # Stage 2: новые kp из oldsite
        w2 = 0
        for kp, obj in old_by_kp.items():
            if kp in added_kps:
                continue
            write_item(out, obj, first)
            first = False
            result_count += 1
            added_kps.add(kp)
            w2 += 1
            if w2 % PROGRESS_EVERY == 0:
                print(f"[write:stage2] extras from oldsite: {w2:,}, total: {result_count:,}", flush=True)
        print(f"[write:stage2] done. added from oldsite by new kp: {w2:,}", flush=True)

        # Stage 3a: без kp из movies.json с дедупом
        w3a = 0
        skipped3a = 0
        for obj in new_unmatched:
            kset = keys_for_dedupe(obj)
            if kset and any(k in seen_dedupe_keys for k in kset):
                skipped3a += 1
                continue
            write_item(out, obj, first)
            first = False
            result_count += 1
            w3a += 1
            if w3a % PROGRESS_EVERY == 0:
                print(f"[write:stage3a] no-kp from movies.json: {w3a:,}, skipped: {skipped3a:,}, total: {result_count:,}", flush=True)
        print(f"[write:stage3a] done. no-kp written: {w3a:,}, skipped: {skipped3a:,}", flush=True)

        # Stage 3b: без kp из oldsite с дедупом
        w3b = 0
        skipped3b = 0
        for obj in old_unmatched:
            kset = keys_for_dedupe(obj)
            if kset and any(k in seen_dedupe_keys for k in kset):
                skipped3b += 1
                continue
            write_item(out, obj, first)
            first = False
            result_count += 1
            w3b += 1
            if w3b % PROGRESS_EVERY == 0:
                print(f"[write:stage3b] no-kp from oldsite: {w3b:,}, skipped: {skipped3b:,}, total: {result_count:,}", flush=True)
        print(f"[write:stage3b] done. no-kp written: {w3b:,}, skipped: {skipped3b:,}", flush=True)

        write_json_array_footer(out)

    print("[write] done.", flush=True)
    print(f"Готово: {out_path}")
    print(f"- Из movies.json (с kp): {len(new_by_kp)}")
    print(f"- Добавлено из oldsite по новым kp: {w2}")
    print(f"- Без kpId (movies.json) записано: {w3a}, пропущено (дублей): {skipped3a}")
    print(f"- Без kpId (oldsite) записано: {w3b}, пропущено (дублей): {skipped3b}")
    print(f"- Всего записей в результате: {result_count}")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        INPUT_OLD = sys.argv[1]
    if len(sys.argv) >= 3:
        INPUT_NEW = sys.argv[2]
    if len(sys.argv) >= 4:
        OUTPUT = sys.argv[3]
    main(INPUT_OLD, INPUT_NEW, OUTPUT)