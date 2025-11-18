#!/usr/bin/env python3
import argparse
import json
import os
import shutil
from typing import Any, Dict, Optional


def norm_kp(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        s = str(value).strip()
        return s or None
    except Exception:
        return None


def is_empty(val: Any) -> bool:
    if val is None:
        return True
    if isinstance(val, str):
        return not val.strip()
    return False


def load_json(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def build_source_index(source: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    movies = []
    if isinstance(source, dict) and 'movies' in source and isinstance(source['movies'], list):
        movies = source['movies']
    elif isinstance(source, dict):
        # Поддержка старых форматов (на случай наличия других ключей со списками фильмов)
        for v in source.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and 'id' in v[0]:
                movies.extend(v)

    index: Dict[str, Dict[str, Any]] = {}
    for m in movies:
        kp = norm_kp(m.get('kinopoiskId'))
        tr = m.get('trailer')
        if kp and not is_empty(tr):
            index[kp] = m
    return index


def merge_trailers(target_path: str, source_path: str, backup: bool = True, dry_run: bool = False) -> None:
    if not os.path.exists(target_path):
        raise SystemExit(f"Target file not found: {target_path}")
    if not os.path.exists(source_path):
        raise SystemExit(f"Source file not found: {source_path}")

    source = load_json(source_path)
    target = load_json(target_path)

    src_index = build_source_index(source)

    # Собираем список фильмов из целевого файла
    is_new_format = isinstance(target, dict) and 'movies' in target
    tgt_movies = []
    if is_new_format:
        tgt_movies = target['movies']
    elif isinstance(target, dict):
        for v in target.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and 'id' in v[0]:
                tgt_movies.extend(v)

    updated = 0
    skipped_no_kp = 0
    skipped_has_trailer = 0
    matched_missing_in_source = 0

    for m in tgt_movies:
        kp = norm_kp(m.get('kinopoiskId'))
        if not kp:
            skipped_no_kp += 1
            continue
        if not is_empty(m.get('trailer')):
            skipped_has_trailer += 1
            continue
        src = src_index.get(kp)
        if not src:
            matched_missing_in_source += 1
            continue
        # переносим trailer и youtubeId из источника
        src_trailer = src.get('trailer')
        src_youtube = src.get('youtubeId')
        if is_empty(src_trailer):
            matched_missing_in_source += 1
            continue
        m['trailer'] = src_trailer
        if not is_empty(src_youtube):
            m['youtubeId'] = src_youtube
        updated += 1

    print(f"Source entries with trailer: {len(src_index)}")
    print(f"Target movies: {len(tgt_movies)}")
    print(f"Updated target records: {updated}")
    print(f"Skipped (no kinopoiskId): {skipped_no_kp}")
    print(f"Skipped (already had trailer): {skipped_has_trailer}")
    print(f"No matching source or empty trailer in source: {matched_missing_in_source}")

    if updated == 0:
        print("No updates to write.")
        return

    if dry_run:
        print("Dry-run mode: changes are not saved.")
        return

    if backup:
        backup_path = target_path + '.bak'
        shutil.copy(target_path, backup_path)
        print(f"Backup created: {backup_path}")

    save_json(target_path, target)
    print(f"Saved merged data to: {target_path}")


def main():
    parser = argparse.ArgumentParser(description='Merge trailers/youtubeId by kinopoiskId from source JSON into target JSON when target.trailer is null/empty.')
    parser.add_argument('--target', default='movies-data.json', help='Path to target JSON to update (default: movies-data-sorted.json)')
    parser.add_argument('--source', default='movies-data-sorted.json', help='Path to source JSON with correct trailers (default: movies-data-sorted-rightImages.json)')
    parser.add_argument('--no-backup', action='store_true', help='Do not create .bak backup of target before saving')
    parser.add_argument('--dry-run', action='store_true', help='Only report changes, do not write file')

    args = parser.parse_args()

    merge_trailers(
        target_path=args.target,
        source_path=args.source,
        backup=not args.no_backup,
        dry_run=args.dry_run,
    )


if __name__ == '__main__':
    main()
