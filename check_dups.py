#!/usr/bin/env python3
import json
import sys
import argparse
from collections import defaultdict

def iter_movies(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        first = f.read(1)
        if not first:
            return []
        f.seek(0)
        if first in '[{':
            data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                if isinstance(data.get('movies'), list):
                    return data['movies']
                return list(data.values())
            return []
        else:
            movies = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    movies.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            return movies

def get_first(d, keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, str):
            s = v.strip()
            if s:
                return s
    return None

def main(path):
    movies = iter_movies(path)
    title_keys = ['title', 'Title']
    orig_keys = ['original_title', 'originalTitle']
    by_title = defaultdict(list)
    by_original = defaultdict(list)

    for idx, m in enumerate(movies):
        t = get_first(m, title_keys)
        o = get_first(m, orig_keys)
        if t:
            by_title[t].append(idx)
        if o:
            by_original[o].append(idx)

    any_dup = False

    def print_dups(label, mapping):
        nonlocal any_dup
        dups = [(k, v) for k, v in mapping.items() if len(v) > 1]
        if dups:
            any_dup = True
            print(f'== Duplicates by {label} ({len(dups)} groups) ==')
            for name, idxs in sorted(dups, key=lambda x: -len(x[1])):
                head = ', '.join(map(str, idxs[:10]))
                tail = '...' if len(idxs) > 10 else ''
                print(f'{name} -> {len(idxs)} items at indexes [{head}]{tail}')
        else:
            print(f'No duplicates by {label}.')

    print_dups('title', by_title)
    print_dups('original title', by_original)
    sys.exit(1 if any_dup else 0)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Check duplicate movies by title or original title')
    ap.add_argument('path', nargs='?', default='movies-data.json', help='Path to movies JSON (array or NDJSON)')
    args = ap.parse_args()
    main(args.path)