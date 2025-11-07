# save as: rename_images_and_update_json.py
import argparse
import json
import os
import secrets
from pathlib import Path, PurePosixPath
from typing import Dict, Set

def gen_name_10() -> str:
    return f"{secrets.randbelow(10_000_000_000):010d}"

def print_progress(processed: int, total: int, renamed: int, skipped_missing: int, skipped_errors: int, unchanged: int):
    if total <= 0:
        msg = f"\rProcessed: {processed}  renamed:{renamed}  missing:{skipped_missing}  errors:{skipped_errors}  unchanged:{unchanged}"
    else:
        pct = (processed / total) * 100.0
        msg = f"\rProcessed: {processed}/{total} ({pct:5.1f}%)  renamed:{renamed}  missing:{skipped_missing}  errors:{skipped_errors}  unchanged:{unchanged}"
    print(msg, end="", flush=True)

def main():
    ap = argparse.ArgumentParser(description="Переименовать изображения и обновить пути в JSON.")
    ap.add_argument("-i", "--input", required=True, help="Входной JSON (с полем movies[].image)")
    ap.add_argument("-o", "--output", required=True, help="Выходной JSON")
    ap.add_argument("--images-root", default=".", help="Корневая папка, относительно которой хранятся image-пути из JSON")
    ap.add_argument("--dry-run", action="store_true", help="Только показать, без переименования/записи")
    ap.add_argument("--progress-every", type=int, default=5000, help="Как часто обновлять прогресс (в кол-ве записей)")
    args = ap.parse_args()

    step = max(1, int(args.progress_every))
    images_root = Path(args.images_root)

    with open(args.input, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    movies = data.get("movies", [])
    rewritten: Dict[str, str] = {}

    renamed = 0
    skipped_missing = 0
    skipped_errors = 0
    unchanged = 0
    processed = 0
    total = len(movies)

    used_in_dir: Dict[str, Set[str]] = {}

    for m in movies:
        processed += 1
        img = m.get("image")
        if not isinstance(img, str) or not img.strip():
            unchanged += 1
            if processed % step == 0:
                print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
            continue

        img_posix = img.strip()
        if img_posix in rewritten:
            m["image"] = rewritten[img_posix]
            unchanged += 1
            if processed % step == 0:
                print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
            continue

        p_posix = PurePosixPath(img_posix)
        src_path = images_root.joinpath(*p_posix.parts)

        if not src_path.exists() or not src_path.is_file():
            skipped_missing += 1
            if processed % step == 0:
                print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
            continue

        dir_posix = str(p_posix.parent)
        ext = p_posix.suffix or src_path.suffix
        if not ext:
            ext = ".jpg"

        if dir_posix not in used_in_dir:
            dir_fs = images_root.joinpath(*p_posix.parent.parts)
            taken = set()
            if dir_fs.exists():
                for child in dir_fs.iterdir():
                    if child.is_file():
                        taken.add(child.name)
            used_in_dir[dir_posix] = taken

        for _ in range(200):
            new_base = gen_name_10() + ext.lower()
            if new_base not in used_in_dir[dir_posix]:
                break
        else:
            skipped_errors += 1
            if processed % step == 0:
                print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
            continue

        dst_posix = str(p_posix.parent.joinpath(new_base))
        dst_path = images_root.joinpath(*PurePosixPath(dst_posix).parts)

        try:
            if not args.dry_run:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                src_path.replace(dst_path)
            used_in_dir[dir_posix].add(new_base)
            rewritten[img_posix] = dst_posix
            m["image"] = dst_posix
            renamed += 1
        except Exception:
            skipped_errors += 1

        if processed % step == 0:
            print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)

    # финальный прогресс и перевод строки
    print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
    print()

    if not args.dry_run:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Готово. Переименовано: {renamed}, пропущено (нет файла): {skipped_missing}, ошибки: {skipped_errors}, без изменений: {unchanged}.")
    if args.dry_run:
        print("Режим --dry-run: файлы и JSON не изменялись.")

if __name__ == "__main__":
    main()