import json
import re
import argparse
import unicodedata
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# --------------------------
# Helpers
# --------------------------

RU_TO_LAT = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i',
    'й':'j','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
    'у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'shch','ъ':'','ы':'y','ь':'',
    'э':'e','ю':'yu','я':'ya',
    'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E','Ж':'Zh','З':'Z','И':'I',
    'Й':'J','К':'K','Л':'L','М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T',
    'У':'U','Ф':'F','Х':'H','Ц':'C','Ч':'Ch','Ш':'Sh','Щ':'Shch','Ъ':'','Ы':'Y','Ь':'',
    'Э':'E','Ю':'Yu','Я':'Ya'
}

def translit_ru(text: str) -> str:
    return ''.join(RU_TO_LAT.get(ch, ch) for ch in text)

def slugify(text: str) -> str:
    text = translit_ru(text or '')
    import unicodedata as _u
    text = _u.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    text = re.sub(r'-{2,}', '-', text)
    return text

def first_non_empty(d: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for k in keys:
        if k in d and d[k] not in (None, '', [], {}):
            return d[k]
    return None

def as_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return str(x)
    if isinstance(x, str):
        s = x.strip()
        return s if s else None
    return None

def as_float(x: Any) -> Optional[float]:
    if x in (None, '', [], {}):
        return None
    try:
        return float(x)
    except Exception:
        return None

# вверху файла (если ещё нет)
MONTHS_RU = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]

def format_date_ru(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    s = date_str.strip()
    if 'T' in s:
        s = s.split('T', 1)[0]
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)
    if not m:
        return date_str
    y, mm, dd = m.groups()
    try:
        month_idx = int(mm)
        day = int(dd)
        if 1 <= month_idx <= 12:
            return f"{day} {MONTHS_RU[month_idx-1]} {y}"
    except Exception:
        pass
    return date_str

def normalize_url(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    s = u.strip()
    if s.startswith('//'):
        return 'https:' + s
    return s

def ensure_list_of_str(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i) for i in x if i not in (None, '')]
    if isinstance(x, str):
        return [x] if x.strip() else []
    return []

def join_people_list(x: Any) -> List[str]:
    res: List[str] = []
    if x is None:
        return res
    if isinstance(x, list):
        for i in x:
            if isinstance(i, dict):
                name = first_non_empty(i, ['name', 'fullName', 'enName', 'ruName', 'title'])
                if name:
                    res.append(str(name))
            else:
                s = str(i).strip()
                if s:
                    res.append(s)
    elif isinstance(x, str):
        s = x.strip()
        if s:
            res = [s]
    return res

def get_nested(d: Dict[str, Any], path: str) -> Any:
    cur: Any = d
    for p in path.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur

YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{6,})'
)

def youtube_id_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = YOUTUBE_ID_RE.search(url)
    return m.group(1) if m else None

def iter_source_items(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    if not text:
        return []
    if text.startswith('{') or text.startswith('['):
        try:
            data = json.loads(text)
        except Exception:
            data = None
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    yield item
        elif isinstance(data, dict):
            for key in ['movies', 'items', 'data', 'docs', 'results']:
                arr = data.get(key)
                if isinstance(arr, list):
                    for item in arr:
                        if isinstance(item, dict):
                            yield item
            if all(not isinstance(v, list) for v in data.values()):
                yield data
        else:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        yield obj
                except Exception:
                    continue
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    yield obj
            except Exception:
                continue

# --------------------------
# Field mapping (incl. material_data.*)
# --------------------------

CANDIDATES = {
    'kinopoiskId': ['kinopoiskId', 'kpId', 'kinopoisk_id', 'kp_id', 'id_kp', 'kp', 'material_data.kinopoisk_id'],
    'title_ru': ['title', 'name', 'ruTitle', 'ru_name', 'ru', 'material_data.title'],
    'title_orig': ['originalTitle', 'nameOriginal', 'original_name', 'enTitle', 'title_en', 'orig', 'title_orig', 'material_data.title_orig'],
    'year': ['year', 'productionYear', 'releaseYear', 'material_data.year'],
    'season': ['season', 'seasonNumber', 'season_num'],
    'episode': ['episode', 'episodeTitle', 'lastEpisode', 'episode_num'],
    'image': ['image', 'poster', 'posterUrl', 'cover', 'coverUrl', 'material_data.poster_url'],
    'description': ['description', 'plot', 'overview', 'synopsis', 'material_data.description'],
    'country': ['country', 'countries', 'material_data.countries'],
    'premiere': ['premiere', 'releaseDate', 'premiereRu', 'worldPremiere', 'material_data.premiere_world'],
    'director': ['director', 'directors', 'material_data.directors'],
    'genres': ['genres', 'genre', 'material_data.genres', 'material_data.all_genres'],
    'translate_field': ['translate'],  # alt translation caption
    'translation_obj': ['translation'], # object or list of objects with title/type
    'actors': ['actors', 'cast', 'material_data.actors'],
    'kpRating': ['kpRating', 'ratingKinopoisk', 'kp_rating', 'material_data.kinopoisk_rating'],
    'imdbRating': ['imdbRating', 'ratingImdb', 'imdb_rating', 'material_data.imdb_rating'],
    'trailer': ['trailer', 'trailerUrl', 'teaser', 'teaserUrl', 'youtube'],
    'ageRating': ['ageRating', 'mpaa', 'age', 'ratingAgeLimits', 'material_data.minimal_age'],
    'season': ['season', 'seasonNumber', 'season_num', 'last_season', 'lastSeason'],
    'episode': ['episode', 'episodeTitle', 'lastEpisode', 'episode_num', 'last_episode', 'episodes_count'],
    'type': ['type'],
    'kodik_player': ['player_link', 'link']  # <= добавить
}

def get_value(d: Dict[str, Any], key_group: str) -> Any:
    for key in CANDIDATES[key_group]:
        if '.' in key:
            v = get_nested(d, key)
        else:
            v = d.get(key)
        if v not in (None, '', [], {}):
            return v
    return None

# --------------------------
# Category, translation, normalize, merge
# --------------------------

def determine_category(src: Dict[str, Any]) -> str:
    t = (as_str(get_value(src, 'type')) or '').lower()
    genres = ensure_list_of_str(get_value(src, 'genres'))
    genres_lower = [str(g).lower() for g in genres]

    # признаки аниме: type содержит 'anime', жанр "аниме"/"anime", наличие shikimori_id
    has_shikimori = bool(get_nested(src, 'shikimori_id') or get_nested(src, 'material_data.shikimori_id'))
    is_anime = ('anime' in t) or has_shikimori or any(g in ('аниме', 'anime') for g in genres_lower)

    # признаки мультфильма
    is_mult = (
        ('cartoon' in t or 'animation' in t or 'mult' in t) or
        any(g in ('мультфильм', 'мультфильмы', 'animation', 'cartoon') for g in genres_lower)
    )

    # признаки сериала (для не-аниме/не-мульта)
    has_serial_markers = any(
        get_nested(src, k) not in (None, '', 0)
        for k in ['last_season', 'lastSeason', 'last_episode', 'episodes_count', 'season', 'seasonNumber', 'episode']
    )
    is_serial = ('serial' in t) or has_serial_markers

    # приоритет: ANIME -> MULTFILMY -> SERIALY -> FILMY
    if is_anime:
        return 'anime'
    if is_mult:
        return 'multfilmy'
    if is_serial:
        return 'serialy'
    return 'filmy'

    # refine by genres
    if any(g in genres_lower for g in ['аниме', 'anime']):
        cat = 'anime'
    if any(g in genres_lower for g in ['мультфильм', 'мультфильмы', 'animation', 'cartoon']):
        cat = 'multfilmy'
    return cat

def extract_translations(src: Dict[str, Any]) -> List[str]:
    vals: List[str] = []
    # translation object or list
    tr_obj = get_value(src, 'translation_obj')
    if isinstance(tr_obj, dict):
        t = first_non_empty(tr_obj, ['title', 'name'])
        if t:
            vals.append(str(t))
    elif isinstance(tr_obj, list):
        for it in tr_obj:
            if isinstance(it, dict):
                t = first_non_empty(it, ['title', 'name'])
                if t:
                    vals.append(str(t))
            elif isinstance(it, str):
                s = it.strip()
                if s:
                    vals.append(s)
    # translate string
    tr_txt = as_str(get_value(src, 'translate_field'))
    if tr_txt:
        vals.append(tr_txt)
    # de-dup, keep order
    seen = set()
    out = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out

def normalize_from_raw(src: Dict[str, Any]) -> Dict[str, Any]:
    kp_id = as_str(get_value(src, 'kinopoiskId'))

    title_ru = as_str(get_value(src, 'title_ru')) or as_str(get_value(src, 'title_orig')) or (f"Без названия ({kp_id})" if kp_id else "Без названия")
    orig_title = as_str(get_value(src, 'title_orig'))

    year_raw = get_value(src, 'year')
    try:
        year = int(year_raw) if year_raw is not None and str(year_raw).isdigit() else None
    except Exception:
        year = None

    # season
    season_raw = get_value(src, 'season')
    season = None
    if season_raw is not None:
        s = as_str(season_raw)
        if s and s.isdigit():
            season = f"{int(s)} сезон"
        else:
            # вдруг пришло числом
            try:
                season = f"{int(season_raw)} сезон"
            except Exception:
                season = s

    # episode
    episode_raw = get_value(src, 'episode')
    episode = None
    if episode_raw is not None:
        e = as_str(episode_raw)
        if e and e.isdigit():
            episode = f"{int(e)} серия"
        else:
            try:
                episode = f"{int(episode_raw)} серия"
            except Exception:
                episode = e

    image = as_str(get_value(src, 'image'))
    description = as_str(get_value(src, 'description'))

    country_val = get_value(src, 'country')
    if isinstance(country_val, list):
        country = ', '.join([str(c) for c in country_val if c not in (None, '')])
    else:
        country = as_str(country_val)

    premiere = as_str(get_value(src, 'premiere'))

    directors_list = join_people_list(get_value(src, 'director'))
    actors_list = join_people_list(get_value(src, 'actors'))

    genres = ensure_list_of_str(get_value(src, 'genres'))

    kp_rating = as_float(get_value(src, 'kpRating'))
    imdb_rating = as_float(get_value(src, 'imdbRating'))

    trailer_url = as_str(get_value(src, 'trailer'))
    youtube_id = youtube_id_from_url(trailer_url)

    age_rating = as_str(get_value(src, 'ageRating'))

    category = determine_category(src)

    kodik_url = normalize_url(as_str(get_value(src, 'kodik_player')))  # <= новое

    return {
        "kinopoiskId": kp_id,
        "title": title_ru,
        "originalTitle": orig_title,
        "year": year,
        "season": season,
        "episode": episode,
        "image": image,
        "description": description,
        "country": country,
        "premiere": premiere,
        "directors": directors_list,
        "actors_list": actors_list,
        "genres": genres,
        "kpRating": kp_rating,
        "imdbRating": imdb_rating,
        "trailer": trailer_url,
        "youtubeId": youtube_id,
        "ageRating": age_rating,
        "category": category,
        "translations": extract_translations(src),
        "kodikPlayer": kodik_url  # <= новое
    }

def load_master_kinopoisk_ids(master_path: str) -> Set[str]:
    with open(master_path, 'r', encoding='utf-8') as f:
        master = json.load(f)
    ids: Set[str] = set()
    for m in master.get('movies', []):
        kp = m.get('kinopoiskId')
        if kp not in (None, ''):
            ids.add(str(kp).strip())
    return ids

def choose_text(a: Optional[str], b: Optional[str]) -> Optional[str]:
    # prefer non-empty; if both non-empty, take longer
    if a and not b:
        return a
    if b and not a:
        return b
    if a and b:
        return a if len(a) >= len(b) else b
    return None

def merge_records(base: Dict[str, Any], nxt: Dict[str, Any]) -> Dict[str, Any]:
    # scalar prefer non-empty/longer
    base['title'] = choose_text(base.get('title'), nxt.get('title'))
    base['originalTitle'] = choose_text(base.get('originalTitle'), nxt.get('originalTitle'))
    base['image'] = choose_text(base.get('image'), nxt.get('image'))
    base['description'] = choose_text(base.get('description'), nxt.get('description'))
    base['country'] = choose_text(base.get('country'), nxt.get('country'))
    base['premiere'] = choose_text(base.get('premiere'), nxt.get('premiere'))
    base['trailer'] = choose_text(base.get('trailer'), nxt.get('trailer'))
    base['youtubeId'] = choose_text(base.get('youtubeId'), nxt.get('youtubeId'))
    base['ageRating'] = choose_text(base.get('ageRating'), nxt.get('ageRating'))
    base['kodikPlayer'] = choose_text(base.get('kodikPlayer'), nxt.get('kodikPlayer'))

    # numeric keep max (ratings)
    for k in ['kpRating', 'imdbRating']:
        a = base.get(k); b = nxt.get(k)
        base[k] = max(a, b) if a is not None and b is not None else (a if a is not None else b)

    # year, season, episode keep first non-empty
    for k in ['year', 'season', 'episode', 'category']:
        if base.get(k) in (None, ''):
            base[k] = nxt.get(k) if nxt.get(k) not in (None, '') else base.get(k)

    # lists: union with order
    def _merge_list(dst_key: str, new_vals: List[str]):
        seen = set(base.get(dst_key, []))
        for v in new_vals:
            if v not in seen and v not in (None, ''):
                base.setdefault(dst_key, []).append(v)
                seen.add(v)

    _merge_list('genres', nxt.get('genres', []))
    _merge_list('directors', nxt.get('directors', []))
    _merge_list('actors_list', nxt.get('actors_list', []))
    _merge_list('translations', nxt.get('translations', []))

    return base

def build_group_key(n: Dict[str, Any]) -> str:
    kp = n.get('kinopoiskId')
    if kp:
        return f"kp:{kp}"
    t = (n.get('title') or '').strip().lower()
    y = n.get('year') or ''
    c = n.get('category') or ''
    return f"nokp:{t}|{y}|{c}"

def finalize_record(n: Dict[str, Any]) -> Dict[str, Any]:
    title = n.get('title')
    kp_id = n.get('kinopoiskId')
    year = n.get('year')
    slug = slugify(title)[:80] if title else None
    if kp_id:
        new_id = f"{kp_id}-{slug}" if slug else kp_id
    else:
        yr = f"-{year}" if year else ""
        new_id = f"nokp-{(slug or 'untitled')}{yr}"

    directors_str = ', '.join(n.get('directors', [])) if n.get('directors') else None
    actors_str = ', '.join(n.get('actors_list', [])) if n.get('actors_list') else None
    prem_human = format_date_ru(n.get('premiere'))

    out = {
        "iskodik": True,
        "id": new_id,
        "category": n.get('category'),
        "title": title,
        "year": year,
        "season": n.get('season'),
        "image": n.get('image'),
        "description": n.get('description'),
        "originalTitle": n.get('originalTitle'),
        "country": n.get('country'),
        "premiere": prem_human,
        "director": directors_str,
        "genres": n.get('genres', []),
        "translation": n.get('translations', []),
        "actors": actors_str,
        "kpRating": n.get('kpRating'),
        "imdbRating": n.get('imdbRating'),
        "youtubeId": n.get('youtubeId'),
        "trailer": n.get('trailer'),
        "kinopoiskId": kp_id,
        "ageRating": n.get('ageRating'),
        "comments": [],
        "published": True
    }
    out["episode"] = n.get('episode')

    # Добавляем ссылку на плеер ТОЛЬКО при отсутствии kinopoiskId
    if not kp_id and n.get('kodikPlayer'):
        out["kodikPlayer"] = n.get('kodikPlayer')

    return out

# --------------------------
# Main pipeline (aggregate -> dedup -> write)
# --------------------------

def process_sources(master_path: str, films_path: Optional[str], serials_path: Optional[str], out_path: str) -> None:
    master_ids = load_master_kinopoisk_ids(master_path)

    groups: Dict[str, Dict[str, Any]] = {}

    # ingest helper
    def ingest(path: Optional[str]):
        if not path:
            return
        for raw in iter_source_items(path):
            norm = normalize_from_raw(raw)
            key = build_group_key(norm)
            if key not in groups:
                groups[key] = norm
            else:
                groups[key] = merge_records(groups[key], norm)

    ingest(films_path)
    ingest(serials_path)

    written_with_kp = 0
    written_without_kp = 0
    skipped_vs_master = 0

    with open(out_path, 'w', encoding='utf-8') as out:
        for key, rec in groups.items():
            kp = rec.get('kinopoiskId')
            if kp and kp in master_ids:
                skipped_vs_master += 1
                continue
            final_obj = finalize_record(rec)
            out.write(json.dumps(final_obj, ensure_ascii=False) + '\n')
            if kp:
                written_with_kp += 1
            else:
                written_without_kp += 1

    print(f"Written with kinopoiskId: {written_with_kp}")
    print(f"Written without kinopoiskId: {written_without_kp}")
    print(f"Skipped duplicates vs master (by kinopoiskId): {skipped_vs_master}")
    print(f"Output: {out_path}")

def main():
    ap = argparse.ArgumentParser(description="Aggregate new items from sources into NDJSON, merge translations, map fields incl. material_data.*")
    ap.add_argument("--master", required=True, help="Path to movies-data.json")
    ap.add_argument("--films", help="Path to films.json")
    ap.add_argument("--serials", help="Path to serials.json")
    ap.add_argument("--out", required=True, help="Output NDJSON path, e.g. new-items.ndjson")
    args = ap.parse_args()

    process_sources(args.master, args.films, args.serials, args.out)

if __name__ == "__main__":
    main()