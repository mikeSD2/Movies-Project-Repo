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
    ap.add_argument("--also-update", nargs="*", default=[], help="Список дополнительных JSON-файлов, где нужно обновить поле image по совпадающему id")
    ap.add_argument("--log-missing", type=int, default=30, help="Показать до N примеров записей, где файл изображения не найден")
    args = ap.parse_args()

    step = max(1, int(args.progress_every))
    images_root = Path(args.images_root)

    with open(args.input, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    movies = data.get("movies", [])
    rewritten: Dict[str, str] = {}
    id_to_new_image: Dict[str, str] = {}

    renamed = 0
    skipped_missing = 0
    skipped_errors = 0
    unchanged = 0
    processed = 0
    total = len(movies)

    used_in_dir: Dict[str, Set[str]] = {}

    # Список примеров пропущенных (не найденных) файлов
    missing_examples = []

    for m in movies:
        processed += 1
        img = m.get("image")
        mid = m.get("id")
        if not isinstance(img, str) or not img.strip():
            unchanged += 1
            if processed % step == 0:
                print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
            continue

        img_posix = img.strip()
        if img_posix in rewritten:
            # JSON у текущего фильма нужно обновить на уже вычисленное новое имя
            m["image"] = rewritten[img_posix]
            if isinstance(mid, str) and mid:
                id_to_new_image[mid] = rewritten[img_posix]
            # Счётчики оставим без изменения логики, чтобы не путать статистику
            unchanged += 1
            if processed % step == 0:
                print_progress(processed, total, renamed, skipped_missing, skipped_errors, unchanged)
            continue

        p_posix = PurePosixPath(img_posix)
        src_path = images_root.joinpath(*p_posix.parts)

        if not src_path.exists() or not src_path.is_file():
            skipped_missing += 1
            if len(missing_examples) < max(0, int(args.log_missing)):
                missing_examples.append({
                    "id": mid,
                    "image": img_posix,
                    "resolved_path": str(src_path)
                })
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
            if isinstance(mid, str) and mid:
                id_to_new_image[mid] = dst_posix
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

    # Вывести примеры пропусков (missing)
    if missing_examples:
        print(f"Примеры отсутствующих файлов изображений (показано до {args.log_missing}):")
        for ex in missing_examples:
            print(f" - id={ex.get('id')} image='{ex.get('image')}' resolved='{ex.get('resolved_path')}'")

    # Дополнительно обновим переданные файлы по соответствующим id
    total_updated_files = 0
    total_updates = 0
    if args.also_update and id_to_new_image:
        for path in args.also_update:
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    other = json.load(f)
                changed_here = 0
                movies2 = other.get("movies", [])
                for m2 in movies2:
                    mid2 = m2.get("id")
                    if isinstance(mid2, str) and mid2 in id_to_new_image:
                        new_img = id_to_new_image[mid2]
                        if m2.get("image") != new_img:
                            m2["image"] = new_img
                            changed_here += 1
                if not args.dry_run and changed_here > 0:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(other, f, ensure_ascii=False, indent=2)
                total_updated_files += 1
                total_updates += changed_here
                print(f"Обновлён файл {path}: изменено записей: {changed_here}.")
            except Exception as ex:
                print(f"Не удалось обновить {path}: {ex}")

    print(f"Готово. Переименовано: {renamed}, пропущено (нет файла): {skipped_missing}, ошибки: {skipped_errors}, без изменений: {unchanged}.")
    if args.also_update:
        print(f"Дополнительно: обработано файлов для синхронизации: {total_updated_files}, всего обновлений изображений: {total_updates}.")
    if args.dry_run:
        print("Режим --dry-run: файлы и JSON не изменялись.")

if __name__ == "__main__":
    main()

# python rename_images_and_update_json.py -i movies-data-sorted.json -o movies-data-sorted.out.json --images-root . --also-update movies-data.json movies-data-extra.json