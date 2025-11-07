import os
import re
import sys
import json
import time
from typing import Optional, Iterable, Tuple, List
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

TMDB_API_KEY = os.getenv("TMDB_API_KEY") or "636c87f3e6bbd33eae8ee8265c83082e"

# --- Logging & stats ---
VERBOSE_LEVEL = 1  # 0=quiet, 1=normal, 2=verbose
STATS = {"read": 0, "fixed_imdb": 0, "fixed_kp": 0}

def log(msg: str, level: int = 1):
    if VERBOSE_LEVEL >= level:
        print(msg)

# --- TMDB helpers (inspired by alloha_today_movies.py) ---

def _http_get_json(url: str, params: dict, timeout: float = 15.0) -> Optional[dict]:
    for _ in range(3):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(1.5)
    return None

def tmdb_get_vote_average_by_id(tmdb_id: str, media_type_hint: Optional[str]) -> Optional[float]:
    if not tmdb_id:
        return None
    types: list[str] = []
    if media_type_hint in ("movie", "tv"):
        types.append(media_type_hint)
    for t in ("movie", "tv"):
        if t not in types:
            types.append(t)
    for mt in types:
        base = "https://api.themoviedb.org/3/movie/" if mt == "movie" else "https://api.themoviedb.org/3/tv/"
        obj = _http_get_json(base + str(tmdb_id), {"api_key": TMDB_API_KEY, "language": "ru-RU"}, timeout=6)
        if obj and obj.get("vote_average") is not None:
            try:
                v = float(obj["vote_average"])  # 0..10
                if v == 0.0:
                    return None
                return v
            except Exception:
                pass
    return None

def tmdb_search_best_match(title: Optional[str], original_title: Optional[str], year: Optional[int]) -> Optional[Tuple[str, str]]:
    """
    Returns (tmdb_id, media_type) or None. Tries search/movie then search/tv.
    Uses simple heuristics: year match preferred, then token overlap on titles, then popularity.
    """
    title = (title or "").strip()
    original_title = (original_title or "").strip()
    q_candidates = [t for t in [title, original_title] if t]
    if not q_candidates:
        return None

    def _norm(s: str) -> str:
        s = s.lower().replace('ё','е')
        # Remove common quote/dash characters in a safe ASCII-only regex
        s = re.sub(r'["\'`-]', '', s)
        s = re.sub(r"\s+", " ", s).strip()
        return s
    def _tokens(s: str) -> set:
        return set(re.findall(r"[a-zа-яё0-9]+", _norm(s), flags=re.I))
    exp_sets = [(_tokens(title), title), (_tokens(original_title), original_title)]

    def _score(cand_title: str, cand_pop: float, cand_year: Optional[int]) -> float:
        score = 0.0
        if year and cand_year:
            if cand_year == year:
                score += 3.0
            elif abs(cand_year - year) == 1:
                score += 1.0
        tset = _tokens(cand_title)
        for es, _exp in exp_sets:
            if es:
                overlap = len(tset & es) / max(1, len(es))
                score += overlap * 2.0
        score += min(2.0, (cand_pop or 0.0) / 50.0)
        return score

    best: Optional[Tuple[str, str, float]] = None  # (id, media_type, score)

    for media_type, endpoint in (("movie", "https://api.themoviedb.org/3/search/movie"),
                                 ("tv",    "https://api.themoviedb.org/3/search/tv")):
        for q in q_candidates:
            params = {
                "api_key": TMDB_API_KEY,
                "language": "ru-RU",
                "query": q,
                "include_adult": True,
            }
            if year:
                params["year" if media_type == "movie" else "first_air_date_year"] = year
            data = _http_get_json(endpoint, params, timeout=8)
            if not data or not data.get("results"):
                continue
            for it in data["results"]:
                cand_title = it.get("title") or it.get("name") or ""
                cand_pop = it.get("popularity") or 0.0
                cand_year = None
                dstr = it.get("release_date") if media_type == "movie" else it.get("first_air_date")
                if dstr and len(dstr) >= 4:
                    try:
                        cand_year = int(dstr[:4])
                    except Exception:
                        cand_year = None
                s = _score(cand_title, float(cand_pop) if isinstance(cand_pop, (int,float)) else 0.0, cand_year)
                if not best or s > best[2]:
                    best = (str(it.get("id")), media_type, s)
        # Quick short-circuit if we already have a good score
        if best and best[2] >= 3.5:
            break

    if best:
        return best[0], best[1]
    return None

# --- Streaming readers/writers ---

def is_ndjson(path: str) -> bool:
    # Heuristic: look at first 2 non-empty lines; if they start with '{' it's likely NDJSON
    try:
        with open(path, 'r', encoding='utf-8') as f:
            seen = 0
            for line in f:
                s = line.strip()
                if not s:
                    continue
                if s.startswith('{') and (s.endswith('}') or s.endswith('},') or '"id"' in s or '"title"' in s):
                    seen += 1
                else:
                    return False
                if seen >= 2:
                    return True
    except Exception:
        pass
    return False


def iter_json_array_items(path: str) -> Iterable[Tuple[str, Optional[str]]]:
    """
    Iterate items of a top-level JSON array, yielding (raw_object_json, delim)
    where delim is the trailing comma if present ("," or None for last).
    This is a light-weight brace balancer to avoid loading the full file.
    """
    with open(path, 'r', encoding='utf-8') as f:
        # Skip leading whitespace
        ch = f.read(1)
        while ch and ch.isspace():
            ch = f.read(1)
        if ch != '[':
            raise ValueError('File is not a top-level JSON array')
        buf = []
        depth = 0
        in_str = False
        esc = False
        while True:
            ch = f.read(1)
            if not ch:
                break
            if in_str:
                buf.append(ch)
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                buf.append(ch)
                in_str = True
                continue
            if ch == '{':
                depth += 1
                buf.append(ch)
                continue
            if ch == '}':
                depth -= 1
                buf.append(ch)
                if depth == 0:
                    # Peek next non-space to see comma
                    post = []
                    while True:
                        p = f.read(1)
                        if not p:
                            break
                        if p.isspace():
                            post.append(p)
                            continue
                        if p == ',':
                            yield (''.join(buf), ',')
                            buf.clear()
                            post.clear()
                            break
                        if p == ']':
                            yield (''.join(buf), None)
                            return
                        # Unexpected char inside array
                        post.append(p)
                        # push back? Not supported; treat as error
                        raise ValueError('Unexpected character after object in array: ' + ''.join(post))
                continue
            if depth > 0:
                buf.append(ch)
            else:
                if ch == ']':
                    return
                # skip spaces/commas between items
                continue


def iter_object_movies_array(path: str) -> Tuple[dict, Iterable[Tuple[str, Optional[str]]]]:
    """
    Returns (header_obj, iterator) where header_obj is the parsed head object except the movies array,
    and iterator yields items JSON string and trailing delimiter from the movies array.
    Implements small parser that reads until '"movies"\s*:' then an array.
    """
    with open(path, 'r', encoding='utf-8') as f:
        text_prefix = []
        # Read the full header object minimally by loading until movies array begins
        data = f.read()
    # Try a cheap parse: load JSON fully but remove the heavy movies list -> not allowed for huge files.
    # Instead do a regex to find the movies array boundaries
    m = re.search(r'\"movies\"\s*:\s*\[', data)
    if not m:
        # Not an object with movies
        raise ValueError('No "movies" array found at top level')
    start = m.end()  # points at first char after '['
    header_json = data[:m.start()] + '"movies": ['
    tail_data = data[start:]
    # Now stream parse the array part only using the balancer on tail_data
    def _iter_items_from_tail() -> Iterable[Tuple[str, Optional[str]]]:
        buf = []
        depth = 0
        in_str = False
        esc = False
        i = 0
        n = len(tail_data)
        while i < n:
            ch = tail_data[i]
            i += 1
            if in_str:
                buf.append(ch)
                if esc:
                    esc = False
                elif ch == '\\':
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                buf.append(ch)
                in_str = True
                continue
            if ch == '{':
                depth += 1
                buf.append(ch)
                continue
            if ch == '}':
                depth -= 1
                buf.append(ch)
                if depth == 0:
                    # Lookahead for comma or closing ]
                    j = i
                    while j < n and tail_data[j].isspace():
                        j += 1
                    if j < n and tail_data[j] == ',':
                        yield (''.join(buf), ',')
                        buf.clear()
                        i = j + 1
                        continue
                    elif j < n and tail_data[j] == ']':
                        yield (''.join(buf), None)
                        # return; the rest is the suffix after the movies array
                        return
                    else:
                        raise ValueError('Unexpected char after object in movies array')
                continue
            if depth > 0:
                buf.append(ch)
            else:
                # outside items, expect closing ] and suffix
                if ch == ']':
                    # Empty array
                    return
                # skip spaces/commas before first item
                continue
    # Compute suffix after the movies array closing bracket
    # Find matching closing ']' from start position using a stack
    stack = 1
    i = start
    n = len(data)
    in_str = False
    esc = False
    while i < n:
        ch = data[i]
        i += 1
        if in_str:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == '[':
            stack += 1
        elif ch == ']':
            stack -= 1
            if stack == 0:
                suffix = data[i:]
                break
    else:
        suffix = ''
    header_obj = {"__prefix__": header_json, "__suffix__": suffix}
    return header_obj, _iter_items_from_tail()


# --- Processing ---

def process_record(obj: dict) -> dict:
    # Normalize malformed comments
    if not isinstance(obj.get('comments'), list):
        obj['comments'] = []

    # Handle kpRating: if numeric zero, set to None (unknown)
    kp = obj.get('kpRating')
    if isinstance(kp, (int, float)) and float(kp) == 0.0:
        obj['kpRating'] = None
        STATS["fixed_kp"] += 1

    # Handle imdbRating: if numeric zero, try TMDB
    imdb = obj.get('imdbRating')
    if isinstance(imdb, (int, float)) and float(imdb) == 0.0:
        tmdb_id = None
        media_hint = None
        rec_id = str(obj.get('id') or '')
        m = re.match(r'^tmdb(\d+)-', rec_id)
        if m:
            tmdb_id = m.group(1)
        # Guess media type from category
        cat = (obj.get('category') or '').lower()
        if cat in ('serialy', 'anime'):
            media_hint = 'tv'
        elif cat in ('filmy', 'multfilmy'):
            media_hint = 'movie'
        # Try by id first
        val = None
        if tmdb_id:
            val = tmdb_get_vote_average_by_id(tmdb_id, media_hint)
            log(f"imdb fix: via tmdb id={tmdb_id} ({media_hint or 'unknown'})", level=2)
        if val is None:
            # Fallback: search by title/year
            title = obj.get('title')
            original = obj.get('originalTitle') or obj.get('original_title')
            year = obj.get('year')
            try:
                year = int(year) if year is not None else None
            except Exception:
                year = None
            found = tmdb_search_best_match(title, original, year)
            if found:
                tid, mt = found
                log(f"imdb fix: via search title='{title}' year={year} -> id={tid} ({mt})", level=1)
                val = tmdb_get_vote_average_by_id(tid, mt)
        if val is not None and float(val) != 0.0:
            log(f"imdb fix: 0.0 -> {val}", level=1)
            obj['imdbRating'] = float(val)
            STATS["fixed_imdb"] += 1
        else:
            log("imdb fix: no data or 0.0 from TMDB -> set null", level=1)
            obj['imdbRating'] = None
    return obj


def process_ndjson(input_path: str, output_path: str, workers: int = 8) -> None:
    log(f"Start NDJSON: input='{input_path}', output='{output_path}', workers={workers}", level=1)
    # We will parse lines, then process in a bounded thread pool, writing results in order
    with open(input_path, 'r', encoding='utf-8') as fin:
        lines = [line for line in fin if line.strip()]
    total = len(lines)
    log(f"NDJSON lines: {total}", level=1)
    results: List[Optional[dict]] = [None] * total

    def _task(idx: int, s: str) -> Tuple[int, Optional[dict]]:
        try:
            obj = json.loads(s)
        except Exception:
            return idx, None
        res = process_record(obj)
        return idx, res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_task, i, lines[i].strip()) for i in range(total)]
        for k, fut in enumerate(as_completed(futs), start=1):
            idx, obj = fut.result()
            if obj is not None:
                results[idx] = obj
            STATS['read'] += 1
            if k % 200 == 0:
                log(f"Progress: scheduled={k}/{total} fixed_imdb={STATS['fixed_imdb']} fixed_kp={STATS['fixed_kp']}", level=1)

    with open(output_path, 'w', encoding='utf-8') as fout:
        for obj in results:
            if obj is None:
                continue
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '\n')
    log(f"Done NDJSON: read={STATS['read']} fixed_imdb={STATS['fixed_imdb']} fixed_kp={STATS['fixed_kp']}", level=1)


def process_json_array(input_path: str, output_path: str, workers: int = 8) -> None:
    log(f"Start JSON array: input='{input_path}', output='{output_path}', workers={workers}", level=1)
    # Read and split array items into memory indexes, then process in thread pool, then write in order
    items: List[str] = []
    for raw, _ in iter_json_array_items(input_path):
        items.append(raw)
    total = len(items)
    log(f"Array items: {total}", level=1)
    results: List[Optional[dict]] = [None] * total

    def _task(idx: int, raw: str) -> Tuple[int, Optional[dict]]:
        try:
            obj = json.loads(raw)
        except Exception:
            return idx, None
        res = process_record(obj)
        return idx, res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_task, i, items[i]) for i in range(total)]
        for k, fut in enumerate(as_completed(futs), start=1):
            idx, obj = fut.result()
            if obj is not None:
                results[idx] = obj
            STATS['read'] += 1
            if k % 200 == 0:
                log(f"Progress: scheduled={k}/{total} fixed_imdb={STATS['fixed_imdb']} fixed_kp={STATS['fixed_kp']}", level=1)

    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write('[')
        first = True
        for obj in results:
            if obj is None:
                continue
            if not first:
                fout.write(',')
            first = False
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
        fout.write(']')
    log(f"Done JSON array: read={STATS['read']} fixed_imdb={STATS['fixed_imdb']} fixed_kp={STATS['fixed_kp']}", level=1)


def process_object_with_movies(input_path: str, output_path: str, workers: int = 8) -> None:
    """
    Stream a big JSON object with a top-level field "movies": [...].
    Copy header up to '[' of movies array, collect item JSONs, process them in a thread pool,
    then write processed items and copy the suffix verbatim.
    """
    log(f"Start object-with-movies: input='{input_path}', output='{output_path}', workers={workers}", level=1)
    with open(input_path, 'r', encoding='utf-8') as fin:
        data = fin.read()
    # Find movies array boundaries
    m = re.search(r'"movies"\s*:\s*\[', data)
    if not m:
        raise ValueError('No "movies" array found at top level')
    prefix = data[:m.end()]  # includes '['
    # Find matching closing bracket for the movies array
    i = m.end()
    n = len(data)
    depth = 1
    in_str = False
    esc = False
    items_raw: List[str] = []
    obj_buf = []
    collecting = False
    while i < n:
        ch = data[i]
        i += 1
        if in_str:
            obj_buf.append(ch) if collecting else None
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            if collecting:
                obj_buf.append(ch)
            continue
        if ch == '[':
            depth += 1
            if collecting:
                obj_buf.append(ch)
            continue
        if ch == ']':
            depth -= 1
            if collecting:
                obj_buf.append(ch)
            if depth == 0:
                break
            continue
        if ch == '{':
            if depth == 1 and not collecting:
                collecting = True
                obj_buf = ['{']
                continue
            if collecting:
                obj_buf.append(ch)
            continue
        if ch == '}':
            if collecting:
                obj_buf.append(ch)
                # end of one object at top level of movies array
                if depth == 1:
                    items_raw.append(''.join(obj_buf))
                    collecting = False
                continue
        if collecting:
            obj_buf.append(ch)
    suffix = data[i:]

    total = len(items_raw)
    log(f"Movies items: {total}", level=1)
    results: List[Optional[dict]] = [None] * total

    def _task(idx: int, raw: str) -> Tuple[int, Optional[dict]]:
        try:
            obj = json.loads(raw)
        except Exception:
            return idx, None
        res = process_record(obj)
        return idx, res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_task, i, items_raw[i]) for i in range(total)]
        for k, fut in enumerate(as_completed(futs), start=1):
            idx, obj = fut.result()
            if obj is not None:
                results[idx] = obj
            STATS['read'] += 1
            if k % 200 == 0:
                log(f"Progress: scheduled={k}/{total} fixed_imdb={STATS['fixed_imdb']} fixed_kp={STATS['fixed_kp']}", level=1)

    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(prefix)
        first = True
        for obj in results:
            if obj is None:
                continue
            if not first:
                fout.write(',')
            first = False
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
        fout.write(']')
        if suffix:
            fout.write(suffix)
    log(f"Done object-with-movies: read={STATS['read']} fixed_imdb={STATS['fixed_imdb']} fixed_kp={STATS['fixed_kp']}", level=1)


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Fix 0.0 imdb/kp ratings by querying TMDB (streaming).')
    ap.add_argument('input', help='Path to input JSON/NDJSON file')
    ap.add_argument('-o', '--output', help='Path to write output (default: <input>.fixed.json or .fixed.ndjson)')
    ap.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity (-v or -vv)')
    ap.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (overrides -v)')
    args = ap.parse_args()

    global VERBOSE_LEVEL
    if args.quiet:
        VERBOSE_LEVEL = 0
    else:
        VERBOSE_LEVEL = 1 + min(2, args.verbose)
    log(f"Verbosity level: {VERBOSE_LEVEL}")

    inp = args.input
    if not os.path.exists(inp):
        print(f"Input not found: {inp}")
        sys.exit(2)
    # Decide output path
    if args.output:
        outp = args.output
    else:
        base, ext = os.path.splitext(inp)
        outp = base + '.fixed' + ext

    try:
        # Pick workers from env or default
        workers = int(os.getenv('FIX_RATINGS_WORKERS', '8'))
        if is_ndjson(inp):
            process_ndjson(inp, outp, workers=workers)
        else:
            try:
                process_object_with_movies(inp, outp, workers=workers)
            except Exception:
                process_json_array(inp, outp, workers=workers)
        print(f"Done. Written: {outp}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
