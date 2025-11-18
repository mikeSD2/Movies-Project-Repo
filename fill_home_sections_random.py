#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_home_sections_random.py

Назначение:
  Дозаполняет разделы главной страницы (latest) для 4 категорий
  (filmy, serialy, multfilmy, anime) до нужного количества элементов
  (по умолчанию 24), выбирая недостающие случайно среди произведений
  с popularity > min_popularity (по умолчанию 10).

Результат сохраняется в JSON формате совместимом по структуре с сервером:
{
  "popular": [],
  "sections": {
     "filmy": { "latest": [...] },
     "serialy": { "latest": [...] },
     "multfilmy": { "latest": [...] },
     "anime": { "latest": [...] }
  }
}

Пример:
  python fill_home_sections_random.py \
    -i movies-data.json \
    -o server-data/home-feed.fill.json \
    --count 24 \
    --min-popularity 10

Примечания:
  - Скрипт НЕ вносит изменения в исходный movies-data.json, только читает.
  - В выдачу включаются "карточочные" поля, как на сервере (id, title и т.д.).
  - Если в какой-то категории меньше, чем нужно, берём всё, что есть (без падения).
  - По умолчанию "popular" оставляем пустым (можно дополнить логикой при желании).
"""

import argparse
import json
import os
import random
from typing import Any, Dict, List

CATEGORIES = ["filmy", "serialy", "multfilmy", "anime"]

CARD_FIELDS = [
    "id",
    "category",
    "title",
    "year",
    "image",
    "kpRating",
    "imdbRating",
    "genres",
    "country",
    "premiere",
    "season",
    "episode",
]


def card_fields(m: Dict[str, Any]) -> Dict[str, Any]:
    return {k: m.get(k) for k in CARD_FIELDS}


def is_hidden(m: Dict[str, Any]) -> bool:
    return bool(m.get("hidden"))


def pick_random_topup(candidates: List[Dict[str, Any]], need: int) -> List[Dict[str, Any]]:
    if need <= 0:
        return []
    if len(candidates) <= need:
        # Перемешаем, но вернем всех
        random.shuffle(candidates)
        return candidates
    return random.sample(candidates, need)


def _parse_russian_premiere(date_str: Any) -> int:
    if not date_str:
        return 0
    s = str(date_str)
    parts = s.split()
    # ожидаем формату вида: "12 января 2025"
    if len(parts) < 3:
        return 0
    day = parts[0]
    month = parts[1].lower()
    year = parts[2]
    ru_month = {
        "января": "01",
        "февраля": "02",
        "марта": "03",
        "апреля": "04",
        "мая": "05",
        "июня": "06",
        "июля": "07",
        "августа": "08",
        "сентября": "09",
        "октября": "10",
        "ноября": "11",
        "декабря": "12",
    }
    mm = ru_month.get(month)
    if not mm:
        return 0
    try:
        from datetime import datetime
        dt = datetime.strptime(f"{year}-{mm}-{day.zfill(2)}", "%Y-%m-%d")
        return int(dt.timestamp())
    except Exception:
        return 0


def _time_of_movie(m: Dict[str, Any]) -> int:
    ts = _parse_russian_premiere(m.get("premiere"))
    if ts:
        return ts
    try:
        y = int(m.get("year") or 0)
    except Exception:
        y = 0
    if y > 0:
        from datetime import datetime
        return int(datetime.strptime(f"{y}-01-01", "%Y-%m-%d").timestamp())
    return 0


def build_topup_feed(data: Dict[str, Any], count: int, min_pop: float) -> Dict[str, Any]:
    movies = [m for m in (data.get("movies") or []) if m.get("id") != "index" and not is_hidden(m)]

    # Индекс по категориям
    by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CATEGORIES}
    for m in movies:
        c = m.get("category")
        if c in by_cat:
            by_cat[c].append(m)

    def with_min_pop(cat: str) -> List[Dict[str, Any]]:
        arr = by_cat.get(cat, [])
        out: List[Dict[str, Any]] = []
        for m in arr:
            try:
                p = float(m.get("popularity") or 0)
            except Exception:
                p = 0.0
            if p > min_pop:
                out.append(m)
        return out

    sections: Dict[str, Any] = {}
    for cat in CATEGORIES:
        arr = by_cat.get(cat, [])
        # 1) latest по дате премьеры/году как на сервере
        latest_sorted = sorted(arr, key=_time_of_movie, reverse=True)
        latest = latest_sorted[:count]

        # 2) если не хватает, добираем случайными по popularity>min_pop, исключая уже выбранные
        if len(latest) < count:
            chosen_ids = set(m.get("id") for m in latest)
            candidates = [m for m in with_min_pop(cat) if m.get("id") not in chosen_ids]
            need = count - len(latest)
            topup = pick_random_topup(candidates, need)
            latest = latest + topup

        sections[cat] = {"latest": [card_fields(m) for m in latest]}

    return {"popular": [], "sections": sections}


def main():
    parser = argparse.ArgumentParser(description="Fill home sections with random items over popularity threshold.")
    parser.add_argument("-i", "--input", dest="input", default="movies-data.json", help="Path to movies-data.json (default: movies-data.json)")
    parser.add_argument("-o", "--output", dest="output", default=os.path.join("server-data", "home-feed.fill.json"), help="Output JSON path (default: server-data/home-feed.fill.json)")
    parser.add_argument("-n", "--count", dest="count", type=int, default=24, help="How many items per category (default: 24)")
    parser.add_argument("--min-popularity", dest="min_popularity", type=float, default=10.0, help="Popularity threshold (strictly greater than this value) (default: 10.0)")
    parser.add_argument("--seed", dest="seed", type=int, default=None, help="Random seed for reproducibility (optional)")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Read input
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}")
        return 1

    feed = build_topup_feed(data, count=args.count, min_pop=args.min_popularity)

    # Ensure output dir
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print(f"Home feed filled and saved to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
