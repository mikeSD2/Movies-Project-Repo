# save as: select_top_per_category.py
import argparse
import json
import re
from datetime import date
from heapq import heappush, heappop
from typing import Dict, List, Tuple, Any
from decimal import Decimal

# Можем стримить огромный JSON массив "movies" с ijson, если установлен.
def iter_movies_stream(path):
    try:
        import ijson
    except ImportError:
        return None  # сообщим вызывающему, что ijson недоступен
    f = open(path, "r", encoding="utf-8-sig")
    # ВАЖНО: возвращаем генератор, чтобы корректно закрыть файл по завершению
    def gen():
        try:
            for obj in ijson.items(f, "movies.item"):
                yield obj
        finally:
            f.close()
    return gen()

# Если ijson недоступен — fallback: грузим весь JSON (тяжело для памяти на больших файлах).
def iter_movies_fallback(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    movies = data.get("movies", [])
    for obj in movies:
        yield obj

RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

_iso_re = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")
_ru_re  = re.compile(r"^\s*(\d{1,2})\s+([А-Яа-яЁё]+)\s+(\d{4})\s*$")
_dot_re = re.compile(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$")

def safe_date(y: int, m: int, d: int) -> date:
    y = min(max(int(y), 1), 9999)
    m = min(max(int(m), 1), 12)
    d = min(max(int(d), 1), 28)
    return date(y, m, d)

def to_int(x):
    try:
        return int(x)
    except:
        return None

def parse_premiere(premiere, year) -> date:
    if isinstance(premiere, str):
        s = premiere.strip()
        m = _iso_re.match(s)
        if m:
            y, mo, d = map(int, m.groups())
            return safe_date(y, mo, d)
        m = _ru_re.match(s)
        if m:
            d = int(m.group(1))
            mon_name = m.group(2).lower()
            y = int(m.group(3))
            mo = RU_MONTHS.get(mon_name)
            if mo:
                return safe_date(y, mo, d)
        m = _dot_re.match(s)
        if m:
            d, mo, y = map(int, m.groups())
            return safe_date(y, mo, d)
        y_only = to_int(s)
        if y_only:
            return safe_date(y_only, 1, 1)
    y = to_int(year)
    if y:
        return safe_date(y, 1, 1)
    return date.min

def popularity_value(val) -> float:
    if val is None:
        return float("-inf")
    try:
        return float(val)
    except:
        return float("-inf")

def score_tuple(item: Dict[str, Any]) -> Tuple[int, float]:
    dt = parse_premiere(item.get("premiere"), item.get("year"))
    pop = popularity_value(item.get("popularity"))
    # приоритет: свежесть, затем популярность
    return (dt.toordinal(), pop)

def within_years(dt: date, years: int | None) -> bool:
    if years is None:
        return True
    today = date.today()
    cutoff = date(today.year - years, 1, 1)
    return dt >= cutoff

def key_for_dedupe(item: Dict[str, Any]) -> Tuple[str, str, str]:
    # разумный ключ для дедупликации
    return (
        str(item.get("id") or "").lower(),
        str(item.get("title") or "").lower(),
        str(item.get("year") or ""),
    )

def _json_default(o):
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError

def main():
    ap = argparse.ArgumentParser(description="Топ-N из каждой категории по свежести и популярности, с умным ослаблением фильтров.")
    ap.add_argument("-i", "--input", default="movies-data-sorted.json", help="Входной JSON файл")
    ap.add_argument("-o", "--output", default="movies-data.json", help="Выходной JSON файл")
    ap.add_argument("-n", "--top", type=int, default=50, help="Сколько элементов на категорию")
    ap.add_argument("--min-popularity", type=float, default=70.0, help="Минимальная популярность в базовом шаге")
    ap.add_argument("--recent-years", type=int, default=1, help="Сколько последних лет считается «свежим» в базовом шаге")
    ap.add_argument("--min-pop-floor", type=float, default=5.0, help="Минимальный нижний порог популярности")
    args = ap.parse_args()

    target_categories = {"anime", "multfilmy", "filmy", "serialy"}

    # Каскад шагов ослабления: сначала строго (последний год, pop>=70),
    # дальше расширяем окно лет, потом снижаем порог populariy, затем «любые годы».
    steps: List[Tuple[int | None, float]] = []
    steps.append((args.recent_years, args.min_popularity))  # напр.: 1 год, >=70
    for y in (2, 3, 5):
        if y > args.recent_years:
            steps.append((y, args.min_popularity))          # 2/3/5 лет, >=70
    for delta in (5.0, 10.0, 20.0, 30.0):
        steps.append((None, max(args.min_popularity - delta, args.min_pop_floor)))  # любые годы, >=60/50/40, но не ниже floor
    steps.append((None, args.min_pop_floor))  # финальный fallback: любые годы, но не ниже floor

    # Кучи по категориям и шагам: (ord_dt, pop, seq, item)
    heaps: Dict[str, Dict[int, List[Tuple[int, float, int, Dict[str, Any]]]]] = {
        c: {i: [] for i in range(len(steps))} for c in target_categories
    }
    seq = 0

    it = iter_movies_stream(args.input)
    if it is None:
        print("Внимание: модуль ijson не установлен; будет использоваться полная загрузка JSON (может потребоваться много памяти).")
        it = iter_movies_fallback(args.input)

    for obj in it:
        cat = obj.get("category") or obj.get("type")
        if cat not in target_categories:
            continue
        ord_dt, pop = score_tuple(obj)
        dt = parse_premiere(obj.get("premiere"), obj.get("year"))

        # Кладём в те шаги, чьи условия выполняются (окно лет и порог популярности)
        for idx, (yrs, min_pop) in enumerate(steps):
            if pop >= min_pop and within_years(dt, yrs):
                h = heaps[cat][idx]
                heappush(h, (ord_dt, pop, seq, obj))
                if len(h) > args.top:
                    heappop(h)
        seq += 1

    # Собираем результат: по категории идём по шагам, добирая до N уникальных
    selected: List[Dict[str, Any]] = []
    for cat in sorted(target_categories):
        chosen_keys = set()
        taken: List[Dict[str, Any]] = []
        for idx in range(len(steps)):
            bucket = heaps[cat][idx]
            bucket_sorted = sorted(bucket, key=lambda t: (t[0], t[1]), reverse=True)
            for _, _, _, item in bucket_sorted:
                k = key_for_dedupe(item)
                if k in chosen_keys:
                    continue
                chosen_keys.add(k)
                taken.append(item)
                if len(taken) >= args.top:
                    break
            if len(taken) >= args.top:
                break
        selected.extend(taken)

    # Подсчёт распределения по годам среди отобранных
    year_counts: Dict[Any, int] = {}
    for it in selected:
        dt = parse_premiere(it.get("premiere"), it.get("year"))
        if dt != date.min:
            y = dt.year
        else:
            y = to_int(it.get("year"))
        if y is None:
            y = "unknown"
        year_counts[y] = year_counts.get(y, 0) + 1
    out_obj = {"movies": selected}
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out_obj, f, ensure_ascii=False, indent=2, default=_json_default)

    print("Распределение по годам среди выбранных:")
    for y in sorted([k for k in year_counts.keys() if isinstance(k, int)], reverse=True):
        print(f"  {y}: {year_counts[y]}")
    if "unknown" in year_counts:
        print(f"  unknown: {year_counts['unknown']}")

    print("Готово. Сохранено по категориям:", ", ".join(
        f"{cat}:{sum(len(heaps[cat][i]) for i in heaps[cat])}" for cat in sorted(target_categories)
    ))
    print(f"Итоговый размер: {len(selected)} в {args.output}")

if __name__ == "__main__":
    main()

# python select_top_per_category.py -i "...\movies-data-without-pop-pretty-updated.json" -o "...\movies-data.json" -n 50 --min-popularity 70 --recent-years 1 --min-pop-floor 10