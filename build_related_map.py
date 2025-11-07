import json, os
from collections import defaultdict

DATA_FILE = "movies-data.json"        # при необходимости укажите свой путь
OUT_FILE  = os.path.join("server-data", "related-map.json")
TOP_K = 6

GENRE_MAP = {
  'триллер':'Триллер','триллеры':'Триллер',
  'ужасы':'Ужасы','ужас':'Ужасы','хоррор':'Ужасы','horror':'Ужасы',
  'комедия':'Комедия','комедии':'Комедия',
  'драма':'Драма','драмы':'Драма',
  'детектив':'Детектив','детективы':'Детектив',
  'детский':'Детский','детские':'Детский',
  'фантастика':'Фантастика','sci-fi':'Фантастика','научная фантастика':'Фантастика',
  'фэнтези':'Фэнтези','фентези':'Фэнтези',
  'боевик':'Боевик','боевики':'Боевик',
  'приключения':'Приключения','приключение':'Приключения',
  'мелодрама':'Мелодрама','мелодрамы':'Мелодрама',
  'криминал':'Криминал','история':'История','исторический':'История','исторические':'История',
  'семейный':'Семейный','семейные':'Семейный',
  'спорт':'Спорт','музыка':'Музыка','аниме':'Аниме',
  'мультфильмы':'Мультфильмы','мультфильм':'Мультфильмы',
  'дорама':'Дорамы','дорамы':'Дорамы','турецкие сериалы':'Турецкие сериалы',
}

def norm_genre(g):
    k = str(g or '').strip().lower()
    if not k: return ''
    return GENRE_MAP.get(k, k.capitalize())

def norm_genres(gl):
    out, seen = [], set()
    for g in (gl or []):
        cg = norm_genre(g)
        if cg and cg not in seen:
            seen.add(cg); out.append(cg)
    return out

def jaccard(a, b):
    A, B = set(a), set(b)
    if not A or not B: return 0.0
    return len(A & B) / max(1, len(A | B))

def year_score(a, b):
    try:
        da = int(a or 0); db = int(b or 0)
        d = abs(da - db)
        return max(0.0, 1.0 - d/10.0)
    except:
        return 0.0

def country_match(a, b):
    if not a or not b: return 0.0
    return 1.0 if str(a).strip().lower() == str(b).strip().lower() else 0.0

def score(m1, m2):
    if not m1 or not m2: return 0.0
    g = 3.0 * jaccard(m1.get('genres_n', []), m2.get('genres_n', []))
    c = 1.0 * country_match(m1.get('country'), m2.get('country'))
    y = 0.5 * year_score(m1.get('year'), m2.get('year'))
    return g + c + y

def sanitize_and_topup_list(mid, lst, global_by_id, by_cat, TOP_K):
    m = global_by_id.get(mid)
    if not m:
        return []
    cat = m.get('category')
    seen = {mid}
    # 1) фильтрация битых и чужих по категории
    valid = []
    for x in lst or []:
        xm = global_by_id.get(x)
        if not xm:
            continue
        if xm.get('category') != cat:
            continue
        if x in seen:
            continue
        valid.append(x)
        seen.add(x)
    # 2) дозаполнение до TOP_K по скору в своей категории
    if len(valid) < TOP_K:
        cands = []
        for n in by_cat.get(cat, []):
            nid = n['id']
            if nid in seen:
                continue
            s = score(m, n)
            if s <= 0:
                continue
            cands.append((-s, nid))
        cands.sort()
        for _, nid in cands:
            valid.append(nid)
            seen.add(nid)
            if len(valid) >= TOP_K:
                break
    return valid[:TOP_K]

def main():
    os.makedirs("server-data", exist_ok=True)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    movies = [m for m in data.get("movies", []) if m.get("id") not in (None,"index") and not m.get("hidden")]
    for m in movies:
        m['genres_n'] = norm_genres(m.get('genres', []))

    by_cat = defaultdict(list)
    for m in movies:
        by_cat[m['category']].append(m)

    # глобальный индекс по id (на всякий случай)
    global_by_id = {m['id']: m for m in movies}

    # инкрементальная подмешка: читаем старую карту, если есть
    try:
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            related_map = json.load(f)
    except:
        related_map = {}

    # удалить ключи фильмов, которых больше нет
    related_map = {mid: lst for mid, lst in related_map.items() if mid in global_by_id}

    # почистить и дозаполнить каждый список по актуальным данным
    for mid, lst in list(related_map.items()):
        if isinstance(lst, list):
            related_map[mid] = sanitize_and_topup_list(mid, lst, global_by_id, by_cat, TOP_K)

    # базовые топ-K по категории
    for cat, arr in by_cat.items():
        idx = {m['id']: m for m in arr}
        for m in arr:
            mid = m['id']
            existing = related_map.get(mid)
            if isinstance(existing, list) and len(existing) >= TOP_K:
                continue
            cands = []
            for n in arr:
                if n['id'] == mid: continue
                s = score(m, n)
                if s <= 0: continue
                cands.append((-s, n['id']))
            cands.sort()
            related_map[mid] = [nid for _, nid in cands][:TOP_K]

    # покрытие: хотя бы 1 входящая ссылка на каждый фильм
    indeg = defaultdict(int)
    for v in related_map.values():
        if isinstance(v, list):
            for nid in v:
                indeg[nid] += 1

    for cat, arr in by_cat.items():
        idx = {m['id']: m for m in arr}  # индекс для этой категории
        for m in arr:
            mid = m['id']
            if indeg[mid] > 0:
                continue

            # выбираем лучшего «соседа» в своей категории
            best_id, best_s = None, -1e9
            for n in arr:
                if n['id'] == mid: continue
                s = score(m, n)
                if s > best_s:
                    best_s, best_id = s, n['id']

            if not best_id:
                continue  # не удалось подобрать — пропускаем

            lst = related_map.get(best_id, [])
            # сформируем новый список, добавив mid
            lst2 = list(lst) + [mid]
            # уберём дубликаты, сохраним порядок
            seen, uniq = set(), []
            for x in lst2:
                if x not in seen:
                    seen.add(x); uniq.append(x)
            lst2 = uniq

            best_m = idx.get(best_id) or global_by_id.get(best_id)
            if not best_m:
                # если нет данных о best — просто обрежем по порядку
                related_map[best_id] = lst2[:TOP_K]
                continue

            # пересчитаем веса best -> x и оставим сильнейшие TOP_K
            scored = []
            for x in lst2:
                if x == best_id:  # на всякий
                    continue
                xm = idx.get(x) or global_by_id.get(x)
                if not xm:
                    continue
                scored.append((-score(best_m, xm), x))
            scored.sort()
            related_map[best_id] = [x for _, x in scored][:TOP_K]

            # обновим входящую степень для mid (на будущее)
            indeg[mid] += 1

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(related_map, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()