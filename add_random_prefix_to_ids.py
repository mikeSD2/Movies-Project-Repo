# save as: add_random_prefix_to_ids.py
import argparse
import json
import random
import re
from typing import Any, Dict, Set

YEAR_ONLY_RE = re.compile(r"^\s*(\d{4})\s*$")
STARTS_WITH_DIGIT_RE = re.compile(r"^\s*\d")
ID_PREFIX_RE = re.compile(r"^(\d+)-(.*)$")  # numeric-prefix + '-' + rest

def title_is_year(title: Any) -> bool:
    if not isinstance(title, str):
        return False
    m = YEAR_ONLY_RE.match(title)
    if not m:
        return False
    y = int(m.group(1))
    return 1900 <= y <= 2100

def title_starts_with_digit(title: Any) -> bool:
    return isinstance(title, str) and bool(STARTS_WITH_DIGIT_RE.match(title))

def main():
    ap = argparse.ArgumentParser(description="Добавить/обновить случайный числовой префикс (до 7 цифр) у id фильмов.")
    ap.add_argument("-i", "--input", default="movies-data-sorted.json", help="Входной JSON")
    ap.add_argument("-o", "--output", default="movies-data-sorted.updated.json", help="Выходной JSON")
    ap.add_argument("--seed", type=int, default=None, help="Seed генератора случайных чисел (опционально)")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

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

    for m in movies:
        title = m.get("title")
        _id = m.get("id")

        if not isinstance(_id, str) or not _id.strip():
            skipped += 1
            continue
        if title_is_year(title) or title_starts_with_digit(title):
            skipped += 1
            continue

        base = _id.strip()
        mm = ID_PREFIX_RE.match(base)
        remainder = mm.group(2) if mm else base  # если был префикс — заменяем; иначе добавляем

        # Генерируем уникальный новый префикс 1..9_999_999
        for _ in range(100):
            n = random.randint(1, 9_999_999)
            new_id = f"{n}-{remainder}"
            key = new_id.lower()
            if key not in used_ids:
                # освободим текущее значение id в сете (не обязательно, но аккуратно)
                used_ids.discard(base.lower())
                m["id"] = new_id
                used_ids.add(key)
                changed += 1
                break
        else:
            skipped += 1  # не удалось найти уникальный вариант (крайне маловероятно)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Готово. Изменено id: {changed}, пропущено: {skipped}. Результат: {args.output}")

if __name__ == "__main__":
    main()