import os
import re
import sys
import json
from typing import Optional, Iterable, Tuple, Dict, Any

# This script copies updated ratings (kpRating, imdbRating) by id
# from a SOURCE file to a DESTINATION file, preserving DESTINATION structure.
# It supports three formats for both files:
#  - NDJSON (one JSON object per line)
#  - Top-level JSON array [ {...}, {...}, ... ]
#  - Object with top-level field "movies": [ ... ]
#
# Usage:
#   python merge_ratings_by_id.py --src "movies-data-sorted (6).fixed.pretty.json" --dst "movies-data-sorted (9).json" --out "movies-data-sorted (9).merged.json"


def detect_format(path: str) -> str:
    """
    Return one of: 'object_movies', 'array', 'ndjson', 'object'.
    Heuristic based on the first ~8KB.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            head = f.read(8192)
    except Exception:
        return 'object'
    s = head.lstrip()
    # object-with-movies explicit check
    if re.search(r'"movies"\s*:\s*\[', head):
        return 'object_movies'
    if s.startswith('['):
        return 'array'
    # NDJSON: look for another object start after newline early
    if '\n{' in head:
        return 'ndjson'
    return 'object'


def iter_json_array_items_stream(path: str) -> Iterable[str]:
    """Yield raw JSON object strings from a top-level JSON array."""
    with open(path, 'r', encoding='utf-8') as f:
        # Skip leading whitespace and find '['
        ch = f.read(1)
        while ch and ch.isspace():
            ch = f.read(1)
        if ch != '[':
            raise ValueError('Not a top-level JSON array')
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
                    # Check next meaningful char for comma or closing bracket
                    post_ws = []
                    while True:
                        p = f.read(1)
                        if not p:
                            break
                        if p.isspace():
                            post_ws.append(p)
                            continue
                        if p == ',':
                            yield ''.join(buf)
                            buf.clear()
                            post_ws.clear()
                            break
                        if p == ']':
                            yield ''.join(buf)
                            return
                        # Unexpected
                        raise ValueError('Unexpected character after object in array')
                continue
            if depth > 0:
                buf.append(ch)
            else:
                # outside items; wait for next object or closing bracket
                if ch == ']':
                    return
                continue


def iter_object_movies_items(path: str) -> Tuple[str, Iterable[str], str]:
    """Return (prefix_before_open_bracket, iterator_over_raw_item_json, suffix_after_closing_bracket)."""
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    m = re.search(r'"movies"\s*:\s*\[', data)
    if not m:
        raise ValueError('No "movies" array found')
    prefix = data[:m.end()]  # includes '['
    # find matching closing ]
    i = m.end()
    n = len(data)
    depth = 1
    in_str = False
    esc = False
    items = []
    obj_buf = []
    collecting = False
    while i < n:
        ch = data[i]
        i += 1
        if in_str:
            if collecting:
                obj_buf.append(ch)
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
                if depth == 1:
                    items.append(''.join(obj_buf))
                    collecting = False
                continue
        if collecting:
            obj_buf.append(ch)
    suffix = data[i:]

    def _iter():
        for it in items:
            yield it
    return prefix, _iter(), suffix


# --- Building source ratings map ---

def build_ratings_map(path: str) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """Return id -> (kpRating, imdbRating)."""
    ratings: Dict[str, Tuple[Optional[float], Optional[float]]] = {}

    def _upd(obj: Dict[str, Any]):
        mid = str(obj.get('id') or '')
        if not mid:
            return
        kp = obj.get('kpRating', None)
        imdb = obj.get('imdbRating', None)
        ratings[mid] = (
            float(kp) if isinstance(kp, (int, float)) else (None if kp is None else None),
            float(imdb) if isinstance(imdb, (int, float)) else (None if imdb is None else None),
        )

    fmt = detect_format(path)
    if fmt == 'ndjson':
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    obj = json.loads(s)
                    _upd(obj)
                except Exception:
                    continue
        return ratings

    if fmt == 'object_movies':
        _, it, _ = iter_object_movies_items(path)
        for raw in it:
            try:
                obj = json.loads(raw)
                _upd(obj)
            except Exception:
                continue
        return ratings

    if fmt == 'array':
        for raw in iter_json_array_items_stream(path):
            try:
                obj = json.loads(raw)
                _upd(obj)
            except Exception:
                continue
        return ratings

    # Fallback: try full json object (not recommended for huge files)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            if 'movies' in data and isinstance(data['movies'], list):
                for obj in data['movies']:
                    if isinstance(obj, dict):
                        _upd(obj)
            else:
                # maybe a mapping id -> obj
                for _, obj in (data.items() if hasattr(data, 'items') else []):
                    if isinstance(obj, dict):
                        _upd(obj)
        elif isinstance(data, list):
            for obj in data:
                if isinstance(obj, dict):
                    _upd(obj)
    except Exception:
        pass
    return ratings


# --- Writing destination with merged ratings ---

def apply_ratings_to_obj(obj: Dict[str, Any], src_map: Dict[str, Tuple[Optional[float], Optional[float]]]) -> Dict[str, Any]:
    mid = str(obj.get('id') or '')
    if not mid or mid not in src_map:
        return obj
    kp_new, imdb_new = src_map[mid]

    changed = False
    if kp_new is None or isinstance(kp_new, (int, float)):
        if obj.get('kpRating') != kp_new:
            obj['kpRating'] = kp_new
            changed = True
    if imdb_new is None or isinstance(imdb_new, (int, float)):
        if obj.get('imdbRating') != imdb_new:
            obj['imdbRating'] = imdb_new
            changed = True
    return obj


def write_ndjson_with_merge(dst_path: str, out_path: str, src_map: Dict[str, Tuple[Optional[float], Optional[float]]]) -> int:
    changed = 0
    with open(dst_path, 'r', encoding='utf-8') as fin, open(out_path, 'w', encoding='utf-8') as fout:
        for line in fin:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                continue
            before_kp = obj.get('kpRating')
            before_imdb = obj.get('imdbRating')
            obj = apply_ratings_to_obj(obj, src_map)
            if obj.get('kpRating') != before_kp or obj.get('imdbRating') != before_imdb:
                changed += 1
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')) + '\n')
    return changed


def write_array_with_merge(dst_path: str, out_path: str, src_map: Dict[str, Tuple[Optional[float], Optional[float]]]) -> int:
    changed = 0
    with open(out_path, 'w', encoding='utf-8') as fout:
        fout.write('[')
        first = True
        for raw in iter_json_array_items_stream(dst_path):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if obj is None:
                continue
            before_kp = obj.get('kpRating')
            before_imdb = obj.get('imdbRating')
            obj = apply_ratings_to_obj(obj, src_map)
            if obj.get('kpRating') != before_kp or obj.get('imdbRating') != before_imdb:
                changed += 1
            if not first:
                fout.write(',')
            first = False
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
        fout.write(']')
    return changed


def write_object_with_movies_merge(dst_path: str, out_path: str, src_map: Dict[str, Tuple[Optional[float], Optional[float]]]) -> int:
    prefix, it, suffix = iter_object_movies_items(dst_path)
    changed = 0
    with open(out_path, 'w', encoding='utf-8') as fout:
        fout.write(prefix)
        first = True
        for raw in it:
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if obj is None:
                continue
            before_kp = obj.get('kpRating')
            before_imdb = obj.get('imdbRating')
            obj = apply_ratings_to_obj(obj, src_map)
            if obj.get('kpRating') != before_kp or obj.get('imdbRating') != before_imdb:
                changed += 1
            if not first:
                fout.write(',')
            first = False
            fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
        fout.write(']')
        if suffix:
            fout.write(suffix)
    return changed


def main():
    import argparse
    ap = argparse.ArgumentParser(description='Merge kpRating/imdbRating by id from src to dst.')
    ap.add_argument('--src', required=True, help='Source JSON/NDJSON file (provides ratings)')
    ap.add_argument('--dst', required=True, help='Destination JSON/NDJSON file (will be updated)')
    ap.add_argument('--out', required=True, help='Output path to write merged result')
    args = ap.parse_args()

    print(f"Building ratings map from: {args.src}")
    src_map = build_ratings_map(args.src)
    print(f"Ratings in source: {len(src_map)} IDs")

    changed = 0
    try:
        fmt = detect_format(args.dst)
        if fmt == 'ndjson':
            print("Detected NDJSON destination")
            changed = write_ndjson_with_merge(args.dst, args.out, src_map)
        elif fmt == 'object_movies':
            print("Detected object-with-movies destination")
            changed = write_object_with_movies_merge(args.dst, args.out, src_map)
        elif fmt == 'array':
            print("Detected JSON array destination")
            changed = write_array_with_merge(args.dst, args.out, src_map)
        else:
            # fallback: attempt full JSON load and write same structure (array or object)
            with open(args.dst, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                print("Fallback: destination as list")
                with open(args.out, 'w', encoding='utf-8') as fout:
                    fout.write('[')
                    first = True
                    changed = 0
                    for obj in data:
                        if isinstance(obj, dict):
                            before_kp = obj.get('kpRating')
                            before_imdb = obj.get('imdbRating')
                            obj = apply_ratings_to_obj(obj, src_map)
                            if obj.get('kpRating') != before_kp or obj.get('imdbRating') != before_imdb:
                                changed += 1
                        if not first:
                            fout.write(',')
                        first = False
                        fout.write(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
                    fout.write(']')
            elif isinstance(data, dict):
                print("Fallback: destination as object")
                # Try movies field if present
                if 'movies' in data and isinstance(data['movies'], list):
                    out_data = dict(data)
                    out_movies = []
                    changed = 0
                    for obj in data['movies']:
                        if isinstance(obj, dict):
                            before_kp = obj.get('kpRating')
                            before_imdb = obj.get('imdbRating')
                            new_obj = apply_ratings_to_obj(obj, src_map)
                            if new_obj.get('kpRating') != before_kp or new_obj.get('imdbRating') != before_imdb:
                                changed += 1
                            out_movies.append(new_obj)
                        else:
                            out_movies.append(obj)
                    out_data['movies'] = out_movies
                    with open(args.out, 'w', encoding='utf-8') as fout:
                        json.dump(out_data, fout, ensure_ascii=False, separators=(',', ':'))
                else:
                    # Apply to values of object if dicts
                    out_data = {}
                    changed = 0
                    for k, v in data.items():
                        if isinstance(v, dict):
                            before_kp = v.get('kpRating') if isinstance(v, dict) else None
                            before_imdb = v.get('imdbRating') if isinstance(v, dict) else None
                            new_v = apply_ratings_to_obj(v, src_map)
                            if isinstance(new_v, dict) and (new_v.get('kpRating') != before_kp or new_v.get('imdbRating') != before_imdb):
                                changed += 1
                            out_data[k] = new_v
                        else:
                            out_data[k] = v
                    with open(args.out, 'w', encoding='utf-8') as fout:
                        json.dump(out_data, fout, ensure_ascii=False, separators=(',', ':'))
            else:
                raise ValueError('Unsupported destination structure in fallback')
    except Exception as e:
        print(f"Error during merge: {e}")
        sys.exit(1)

    print(f"Done. Changed objects: {changed}. Output: {args.out}")

if __name__ == '__main__':
    main()
