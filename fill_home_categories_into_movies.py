#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_home_categories_into_movies.py

Задача:
  Дозаполнить фильмы в исходном movies-data.json, чтобы на главной в каждой
  из 4 базовых категорий (filmy, serialy, multfilmy, anime) было не меньше
  заданного количества произведений с popularity > threshold. Недостающее
  добирается случайно из movies-data-sorted.json (только те, что popularity > threshold),
  при этом не вставляются дубликаты по id.

Пример использования:
  python fill_home_categories_into_movies.py \
    -i movies-data.json \
    -s movies-data-sorted.json \
    -o movies-data.json \
    -n 24 --min-popularity 10

Опции:
  --dry-run  показать сводку без сохранения
  --seed     фиксировать рандом при отладке

Примечание:
  - Скрипт не удаляет дубликаты в целом; он лишь не вставляет записи, id которых
    уже есть в целевом movies-data.json (аналогично "дедуп" при вставке).
  - Порог сравнивается строго: popularity > threshold.
"""

import argparse
import json
import os
import random
from typing import Any, Dict, List, Set, Optional

CATEGORIES = ["filmy", "serialy", "multfilmy", "anime"]


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _parse_russian_premiere_year(date_str: Any) -> int:
    if not date_str:
        return 0
    s = str(date_str)
    parts = s.split()
    if len(parts) < 3:
        # возможно просто год
        try:
            y = int(s)
            return y
        except Exception:
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
        return int(year)
    except Exception:
        return 0


def _year_of(item: Dict[str, Any]) -> int:
    y = 0
    try:
        y = int(item.get("year") or 0)
    except Exception:
        y = 0
    if y:
        return y
    py = _parse_russian_premiere_year(item.get("premiere"))
    return py or 0


import os
import re

def _is_russian_country(country: Any) -> bool:
    return bool(re.search(r"росси", str(country or ""), flags=re.I))


def _server_pass_popularity(item: Dict[str, Any]) -> bool:
    p = _to_float(item.get("popularity"), 0.0)
    # emulate server defaults
    t_ru = _to_float(os.getenv("HOME_POP_RU", 4), 4)
    t_default = _to_float(os.getenv("HOME_POP_DEFAULT", 12), 12)
    return p >= (t_ru if _is_russian_country(item.get("country")) else t_default)


def _qualifies(item: Dict[str, Any], min_pop: float, min_year: int | None = None, align_server: bool = False) -> bool:
    if item.get("id") == "index":
        return False
    if item.get("hidden"):
        return False
    if align_server:
        if not _server_pass_popularity(item):
            return False
    else:
        if _to_float(item.get("popularity"), 0.0) <= min_pop:
            return False
    if isinstance(min_year, int) and min_year > 0:
        y = _year_of(item)
        if y and y < min_year:
            return False
    return True


def _by_id(items: List[Dict[str, Any]]) -> Set[str]:
    s: Set[str] = set()
    for m in items:
        mid = m.get("id")
        if isinstance(mid, str):
            s.add(mid)
    return s


def _per_category(items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    d: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CATEGORIES}
    for m in items:
        c = m.get("category")
        if c in d:
            d[c].append(m)
    return d


def _pick_random(candidates: List[Dict[str, Any]], need: int) -> List[Dict[str, Any]]:
    if need <= 0:
        return []
    if not candidates:
        return []
    if len(candidates) <= need:
        random.shuffle(candidates)
        return candidates
    return random.sample(candidates, need)


def _not_hidden(m: Dict[str, Any]) -> bool:
    return m.get("id") != "index" and not bool(m.get("hidden"))

def _server_allowed(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # как на сервере: сначала исключаем скрытые и id=index, затем passPopularity
    visible = [m for m in items if _not_hidden(m)]
    return [m for m in visible if _server_pass_popularity(m)]


def _server_pick_latest(items: List[Dict[str, Any]], count: int = 24) -> List[Dict[str, Any]]:
    def _to_time(m: Dict[str, Any]) -> int:
        from datetime import datetime
        # пытаемся как на сервере: premiere по-русски -> дата, иначе год -> 1 янв
        y = _year_of(m)
        # точной даты нам не нужно, порядок задается годом/премьерой
        # если есть корректная дата премьеры — лучше её использовать, но у нас парсится только год
        return y * 10**10  # крупный порядок для сортировки по убыванию

    return sorted(items, key=_to_time, reverse=True)[:count]


def fill_from_source(
    target_data: Dict[str, Any],
    source_data: Dict[str, Any],
    min_popularity: float,
    target_count: int,
    seed: Optional[int] = None,
    min_year: Optional[int] = None,
    align_server: bool = True,
    categories: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if seed is not None:
        random.seed(seed)

    target_movies: List[Dict[str, Any]] = list(target_data.get("movies") or [])
    source_movies: List[Dict[str, Any]] = list(source_data.get("movies") or [])

    # Набор ID уже существующих в целевом файле (для дедуп при вставке)
    existing_ids: Set[str] = _by_id(target_movies)

    # Карта по категориям для целевого
    target_by_cat = _per_category(target_movies)

    # Кандидаты из источника: по категории, проходящие серверный допуск/или ручной порог, не существующие по id
    source_by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CATEGORIES}
    for m in source_movies:
        c = m.get("category")
        if c not in source_by_cat:
            continue
        if not _qualifies(m, min_popularity, min_year=min_year, align_server=align_server):
            continue
        mid = m.get("id")
        if not isinstance(mid, str):
            continue
        if mid in existing_ids:
            continue
        source_by_cat[c].append(m)

    # Для каждой категории проверяем строго как на главной: allowed -> pickLatest
    added: Dict[str, int] = {c: 0 for c in CATEGORIES}
    report: Dict[str, Dict[str, int]] = {}

    cats = categories or CATEGORIES

    for c in CATEGORIES:
        # если указаны ограниченные категории — пропускаем остальные
        if c not in cats:
            report[c] = {"have": 0, "need": 0}
            continue
        # серверная модель: фильтруем целевые фильмы по passPopularity
        allowed_target = _server_allowed(target_by_cat.get(c, [])) if align_server else [m for m in target_by_cat.get(c, []) if _qualifies(m, min_popularity, align_server=False)]
        latest_like_server = _server_pick_latest(allowed_target, target_count)
        have = len(latest_like_server)
        need = max(0, target_count - have)
        report[c] = {"have": have, "need": need}
        if need <= 0:
            continue
        # выбираем из источника кандидатов этой категории (они уже отфильтрованы по align_server/min_year)
        picked = _pick_random(source_by_cat.get(c, [])[:], need)
        # добавляем в конец общего массива фильмов
        for m in picked:
            target_movies.append(m)
            existing_ids.add(m.get("id"))
            added[c] += 1

    # Обновляем target_data.movies
    target_data_out = dict(target_data)
    target_data_out["movies"] = target_movies

    return {"data": target_data_out, "report": {"min_popularity": min_popularity, "target_count": target_count, "categories": report, "added": added}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Top up target movies-data.json for home categories from source sorted file with random picks (popularity > threshold).")
    parser.add_argument("-i", "--input", dest="input", default="movies-data.json", help="Path to target movies-data.json (to be updated)")
    parser.add_argument("-s", "--source", dest="source", default="movies-data-sorted.json", help="Path to source movies-data-sorted.json")
    parser.add_argument("-o", "--output", dest="output", default=None, help="Where to save updated target (default: overwrite input)")
    parser.add_argument("-n", "--count", dest="count", type=int, default=24, help="Minimal qualified items per category (default: 24)")
    parser.add_argument("--min-popularity", dest="min_popularity", type=float, default=10.0, help="Popularity threshold (strictly greater) (default: 10.0). Ignored if --align-server is set.")
    parser.add_argument("--min-year", dest="min_year", type=int, default=None, help="Minimal year of production/premiere to consider (optional)")
    parser.add_argument("--align-server", dest="align_server", action="store_true", help="Use the same popularity thresholds as the server (HOME_POP_DEFAULT/HOME_POP_RU). Overrides --min-popularity.")
    parser.add_argument("--seed", dest="seed", type=int, default=None, help="Random seed for reproducibility (optional)")
    parser.add_argument("--categories", dest="categories", type=str, default=None, help="Comma-separated list of categories to top-up (default: all of filmy,serialy,multfilmy,anime)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Do not write files, only print summary")

    args = parser.parse_args()

    # Read input files
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            target = json.load(f)
    except FileNotFoundError:
        print(f"Target not found: {args.input}")
        return 1
    try:
        with open(args.source, "r", encoding="utf-8") as f:
            source = json.load(f)
    except FileNotFoundError:
        print(f"Source not found: {args.source}")
        return 1

    cats = None
    if args.categories:
        cats = [c.strip() for c in args.categories.split(',') if c.strip() in CATEGORIES]
    result = fill_from_source(target, source, args.min_popularity, args.count, seed=args.seed, min_year=args.min_year, align_server=args.align_server, categories=cats)
    updated = result["data"]
    report = result["report"]

    print("Top-up report:")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.dry_run:
        print("Dry-run mode: no changes written.")
        return 0

    out_path = args.output or args.input
    # Ensure dir exists
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print(f"Saved updated target to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# python fill_home_categories_into_movies.py -i movies-data.json -s movies-data-sorted.json -n 24 --min-popularity 12 --min-year 2023