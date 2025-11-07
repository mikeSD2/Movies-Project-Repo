import json
import os
import re
import random
from html import unescape
from typing import Iterator, Dict, Any, Optional, Set, Tuple

SOURCE_PATH = "movies-data-sorted.json"
DEST_PATH = "movies-data.json"
BATCH_SIZE = random.randint(5, 10)  # было: 50

YEAR_RE = re.compile(r"(\d{4})")

SEASON_PATTERNS = [
    r"\b\d+\s*сезон(?:[аы])?\b",
    r"\b\d+\s*-\s*\d+\s*сезон(?:[аы])?\b",
    r"\bвсе\s+серии\s+подряд\b",
    r"\bсезон\b",
]
SEASON_RE = re.compile("|".join(SEASON_PATTERNS), re.IGNORECASE)


def norm_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def normalize_title_key(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    t = unescape(s)
    t = t.replace("«", "").replace("»", "").replace("“", "").replace("”", "").replace('"', "")
    t = t.replace("*", "").replace("★", "")
    t = SEASON_RE.sub("", t)
    t = re.sub(r"\(\s*(19|20)\d{2}\s*\)", "", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t or None


def extract_year(item: Dict[str, Any]) -> Optional[str]:
    # year в виде строки; используем как ключ для сопоставления
    y = item.get("year")
    if isinstance(y, int):
        return str(y)
    if isinstance(y, str):
        s = y.strip()
        if s:
            m = re.search(r"(19|20)\d{2}", s)
            if m:
                return m.group(0)
    # попытка вытащить из premiere при необходимости
    prem = item.get("premiere")
    if isinstance(prem, str):
        m = None
        for m in YEAR_RE.finditer(prem):
            pass
        if m:
            return m.group(1)
    return None


def title_year_keys(item: Dict[str, Any]) -> Set[Tuple[str, str]]:
    keys: Set[Tuple[str, str]] = set()
    y = extract_year(item) or ""
    t1 = normalize_title_key(item.get("title"))
    t2 = normalize_title_key(item.get("originalTitle"))
    if t1:
        keys.add((t1, y))
    if t2:
        keys.add((t2, y))
    return keys


def iter_movies_from_pretty_json(path: str) -> Iterator[Dict[str, Any]]:
    started = False
    capturing = False
    in_string = False
    escape = False
    depth = 0
    buf_chars = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            i = 0
            L = len(line)
            while i < L:
                ch = line[i]

                if not started:
                    idx = line.find('"movies"', i)
                    if idx == -1:
                        break
                    i = idx + len('"movies"')
                    while i < L and line[i] != '[':
                        i += 1
                    if i < L and line[i] == '[':
                        started = True
                        i += 1
                    continue

                if not capturing:
                    if ch in " \t\r\n,":
                        i += 1
                        continue
                    if ch == ']':
                        return
                    if ch == '{':
                        capturing = True
                        buf_chars = ['{']
                        depth = 1
                        in_string = False
                        escape = False
                        i += 1
                        continue
                    i += 1
                    continue

                buf_chars.append(ch)
                if in_string:
                    if escape:
                        escape = False
                    else:
                        if ch == '\\':
                            escape = True
                        elif ch == '"':
                            in_string = False
                else:
                    if ch == '"':
                        in_string = True
                    elif ch == '{':
                        depth += 1
                    elif ch == '}':
                        depth -= 1
                        if depth == 0:
                            obj_text = "".join(buf_chars)
                            try:
                                yield json.loads(obj_text)
                            except Exception as e:
                                raise RuntimeError(f"Ошибка парсинга объекта: {e}")
                            capturing = False
                            buf_chars = []
                i += 1


def load_or_init_dest(path: str) -> Dict[str, Any]:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {"movies": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, dict) or "movies" not in data or not isinstance(data["movies"], list):
            raise RuntimeError("Файл назначения должен быть объектом с ключом 'movies' (массив).")
        return data


def safe_write_json(path: str, data: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def build_dest_indices(dest_movies: list) -> Tuple[Set[str], Set[str], Set[Tuple[str, str]]]:
    ids: Set[str] = set()
    kps: Set[str] = set()
    tyears: Set[Tuple[str, str]] = set()
    for m in dest_movies:
        mid = norm_str(m.get("id"))
        if mid:
            ids.add(mid)
        kp = norm_str(m.get("kinopoiskId"))
        if kp:
            kps.add(kp)
        for key in title_year_keys(m):
            tyears.add(key)
    return ids, kps, tyears


def is_duplicate(item: Dict[str, Any], ids: Set[str], kps: Set[str], tyears: Set[Tuple[str, str]]) -> bool:
    # 1) по id
    mid = norm_str(item.get("id"))
    if mid and mid in ids:
        return True
    # 2) по kinopoiskId
    kp = norm_str(item.get("kinopoiskId"))
    if kp and kp in kps:
        return True
    # 3) по (title|originalTitle, year)
    for key in title_year_keys(item):
        if key in tyears:
            return True
    return False


def main():
    dest = load_or_init_dest(DEST_PATH)
    dest_movies = dest["movies"]
    ids, kps, tyears = build_dest_indices(dest_movies)

    batch = []
    added = 0

    for item in iter_movies_from_pretty_json(SOURCE_PATH):
        if is_duplicate(item, ids, kps, tyears):
            continue

        batch.append(item)
        added += 1

        # обновляем индексы, чтобы не добавлять дубль в рамках той же порции
        mid = norm_str(item.get("id"))
        if mid:
            ids.add(mid)
        kp = norm_str(item.get("kinopoiskId"))
        if kp:
            kps.add(kp)
        for key in title_year_keys(item):
            tyears.add(key)

        if added >= BATCH_SIZE:
            break

    if not batch:
        print("Нечего добавить: всё из источника уже присутствует или источник пуст.")
        return

    dest_movies.extend(batch)
    safe_write_json(DEST_PATH, dest)

    print(f"Добавлено записей: {added}. Текущий итоговый размер: {len(dest_movies)}.")


if __name__ == "__main__":
    main()