# save as: remove_numeric_prefix_from_ids.py
import argparse
import json
import re
from typing import Any, Set

ID_PREFIX_RE = re.compile(r"^(\d+)-(.*)$")
STARTS_WITH_DIGIT_RE = re.compile(r"^\s*\d")

def title_starts_with_digit(title: Any) -> bool:
    return isinstance(title, str) and bool(STARTS_WITH_DIGIT_RE.match(title))

def is_year_like(prefix: str) -> bool:
    if len(prefix) == 4 and prefix.isdigit():
        y = int(prefix)
        return 1900 <= y <= 2100
    return False

def main():
    ap = argparse.ArgumentParser(description="Удалить незначимые числовые префиксы из id фильмов.")
    ap.add_argument("-i", "--input", default="movies-data.json", help="Входной JSON")
    ap.add_argument("-o", "--output", default="movies-data.cleaned.json", help="Выходной JSON")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    movies = data.get("movies", [])
    used_ids: Set[str] = set()
    for m in movies:
        _id = m.get("id")
        if isinstance(_id, str) and _id.strip():
            used_ids.add(_id.strip().lower())

    changed = 0
    skipped = 0
    collisions = 0

    for m in movies:
        title = m.get("title")
        base = m.get("id")
        if not isinstance(base, str) or not base.strip():
            skipped += 1
            continue

        mm = ID_PREFIX_RE.match(base.strip())
        if not mm:
            # нет числового префикса — нечего удалять
            skipped += 1
            continue

        prefix, remainder = mm.group(1), mm.group(2)

        # 1) если заголовок начинается с цифры — это часть названия, не трогаем
        if title_starts_with_digit(title):
            skipped += 1
            continue

        # 2) если префикс выглядит как год (1900..2100) — не трогаем
        if is_year_like(prefix):
            skipped += 1
            continue

        # Кандидат на новый id
        new_id = remainder.strip()
        if not new_id:
            skipped += 1
            continue

        old_key = base.strip().lower()
        new_key = new_id.lower()

        if new_key != old_key and new_key in used_ids:
            # Столкновение — пропускаем, чтобы не ломать уникальность
            collisions += 1
            skipped += 1
            continue

        # Применяем замену
        used_ids.discard(old_key)
        used_ids.add(new_key)
        m["id"] = new_id
        changed += 1

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Готово. Изменено id: {changed}, пропущено: {skipped}, коллизий: {collisions}. Результат: {args.output}")

if __name__ == "__main__":
    main()