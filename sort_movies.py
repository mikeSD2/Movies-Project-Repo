# save as: sort_movies.py
import json
import argparse
import re
from datetime import date

RU_MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

iso_re = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")
ru_re  = re.compile(r"^\s*(\d{1,2})\s+([А-Яа-яЁё]+)\s+(\d{4})\s*$")
dot_re = re.compile(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s*$")

def to_int(x):
    try:
        return int(x)
    except:
        return None

def parse_premiere(premiere, year):
    # Возвращает datetime.date: как можно более «свежую» дату, иначе fallback на year, иначе минимально возможную
    if isinstance(premiere, str):
        s = premiere.strip()
        m = iso_re.match(s)
        if m:
            y, mo, d = map(int, m.groups())
            return safe_date(y, mo, d)
        m = ru_re.match(s)
        if m:
            d = int(m.group(1))
            mon_name = m.group(2).lower()
            y = int(m.group(3))
            mo = RU_MONTHS.get(mon_name)
            if mo:
                return safe_date(y, mo, d)
        m = dot_re.match(s)
        if m:
            d, mo, y = map(int, m.groups())
            return safe_date(y, mo, d)

        # Если строка содержит только год
        y_only = to_int(s)
        if y_only:
            return safe_date(y_only, 1, 1)

    y = to_int(year)
    if y:
        return safe_date(y, 1, 1)
    # Минимальная дата, чтобы записи без даты были в самом низу при сортировке по убыванию
    return date.min

def safe_date(y, m, d):
    # Гарантированная корректная дата в диапазоне 1..9999
    y = min(max(int(y), 1), 9999)
    m = min(max(int(m), 1), 12)
    d = min(max(int(d), 1), 28)  # 28 хватает для сравнения и всегда валидна
    return date(y, m, d)

def popularity_value(val):
    if val is None:
        return float("-inf")
    try:
        return float(val)
    except:
        return float("-inf")

def sort_key(movie):
    pop = popularity_value(movie.get("popularity"))
    dt  = parse_premiere(movie.get("premiere"), movie.get("year"))
    # Сортируем по убыванию: popularity, потом дата
    return (pop, dt.toordinal())

def main():
    ap = argparse.ArgumentParser(description="Sort movies by popularity and premiere/year (desc).")
    ap.add_argument("-i", "--input", default="movies-data-without-pop-pretty-updated.json", help="Input JSON file")
    ap.add_argument("-o", "--output", default="movies-data-sorted.json", help="Output JSON file")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    movies = data.get("movies", [])
    movies_sorted = sorted(movies, key=sort_key, reverse=True)

    # Сохраняем исходные остальные поля, заменяя только movies
    data["movies"] = movies_sorted
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()

# python sort_movies.py -i "C:\Users\Пользователь\Desktop\sdfsdfsdf\fgfdgsdg\movies-data-without-pop-pretty-updated.json" -o "C:\Users\Пользователь\Desktop\sdfsdfsdf\fgfdgsdg\movies-data-sorted.json"