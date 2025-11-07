#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pip install ijson requests
# Примеры:
#   python fix_nokp_images.py --movies movies-data-sorted.json
#   python fix_nokp_images.py --movies movies-data-sorted.json --replace --backup --workers 16

import os
import sys
import json
import argparse
import re
import decimal
import mimetypes
import shutil
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import ijson
except ImportError:
    print("Требуется пакет ijson. Установите: pip install ijson", file=sys.stderr)
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Требуется пакет requests. Установите: pip install requests", file=sys.stderr)
    sys.exit(1)

def json_default(o):
    if isinstance(o, decimal.Decimal):
        return float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

def normalize_title(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE).strip()
    s = re.sub(r"[\"'’`´“”„«»()\[\]{}:;.,!?/~@#$%^&*+=|\\-]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s, flags=re.UNICODE).strip()
    return s

def pick_poster(rec: dict) -> str | None:
    poster = rec.get("poster_url") or rec.get("anime_poster_url")
    if poster and isinstance(poster, str) and poster.strip():
        return poster.strip()
    md = rec.get("material_data") or {}
    poster = md.get("poster_url") or md.get("anime_poster_url")
    if poster and isinstance(poster, str) and poster.strip():
        return poster.strip()
    return None

SOURCE_ORIG_TITLE_KEYS = [
    "originalTitle", "original_title",
    "originalName", "original_name",
    "nameOriginal", "name_original",
    "title_orig", "title_en",
    "english_title", "romaji_title",
    "en_title", "jp_title"
]

MD_TITLE_KEYS = ["title", "anime_title", "title_en", "title_orig"]

def titles_from_source(rec: dict) -> list[str]:
    titles = []
    for k in ["title", "anime_title"] + SOURCE_ORIG_TITLE_KEYS:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            titles.append(v)
    md = rec.get("material_data") or {}
    for k in MD_TITLE_KEYS + SOURCE_ORIG_TITLE_KEYS:
        v = md.get(k)
        if isinstance(v, str) and v.strip():
            titles.append(v)
    seen, uniq = set(), []
    for t in titles:
        t = t.strip()
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq

def year_from_source(rec: dict):
    y = rec.get("year")
    if y is None:
        md = rec.get("material_data") or {}
        y = md.get("year")
    return y

def build_poster_map(json_path: str, kind: str, posters: dict, seen_stats: dict):
    if not os.path.exists(json_path):
        return
    print(f"[{kind}] Индексирую постеры из: {json_path}")
    total = 0
    added_keys = 0
    with open(json_path, "rb") as f:
        for obj in ijson.items(f, "item"):
            total += 1
            year = year_from_source(obj)
            if year is None:
                continue
            poster = pick_poster(obj)
            if not poster:
                continue
            for t in titles_from_source(obj):
                key = (normalize_title(t), year)
                if key not in posters:
                    posters[key] = poster
                    added_keys += 1
            if total % 100000 == 0:
                print(f"[{kind}] Прочитано {total:,}, ключей {added_keys:,}...")
    seen_stats[kind] = {"read": total, "keys": added_keys}
    print(f"[{kind}] Готово: прочитано {total:,}, добавлено ключей {added_keys:,}")

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def ext_from_url_or_ct(url: str, content_type: str | None) -> str:
    # по URL
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        return ext
    # по Content-Type
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed in [".jpg", ".jpeg", ".png", ".webp"]:
            return guessed
        # частые алиасы
        if content_type.startswith("image/jpeg"):
            return ".jpg"
        if content_type.startswith("image/png"):
            return ".png"
        if content_type.startswith("image/webp"):
            return ".webp"
    # дефолт
    return ".jpg"

def indent_block(s: str, pad: str) -> str:
    return pad + s.replace("\n", "\n" + pad)

def normalize_url(url: str) -> str:
    u = url.strip()
    if u.startswith("//"):
        return "https:" + u
    if not u.startswith("http://") and not u.startswith("https://"):
        return "https://" + u.lstrip("/")
    return u

def copy_one(src_rel: str, mirror_dir: str, overwrite: bool) -> bool:
    try:
        src_path = os.path.abspath(src_rel.replace("/", os.sep))
        if not os.path.exists(src_path):
            return False
        ensure_dir(mirror_dir)
        fname = os.path.basename(src_path)
        dst_path = os.path.join(mirror_dir, fname)
        if os.path.exists(dst_path) and not overwrite:
            return True
        shutil.copy2(src_path, dst_path)
        return True
    except Exception:
        return False

def mirror_images(id_to_new_image: dict, mirror_dir: str, workers: int, overwrite: bool) -> tuple[int, int]:
    unique_rel = sorted(set(id_to_new_image.values()))
    total = len(unique_rel)
    if total == 0:
        print("[MIRROR] Нечего копировать.")
        return 0, 0
    print(f"[MIRROR] Копирую {total:,} файлов в '{mirror_dir}' ({workers} потоков)...")
    ok = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(copy_one, rel, mirror_dir, overwrite) for rel in unique_rel]
        done = 0
        for fut in as_completed(futs):
            res = fut.result()
            done += 1
            if res:
                ok += 1
            if done % 500 == 0:
                print(f"[MIRROR] Завершено {done:,} / {total:,}, успешно {ok:,}")
    print(f"[MIRROR] Готово: успешно {ok:,}, ошибок {total - ok:,}")
    return total, ok

def download_one(movie_id: str, url: str, target_dir: str, overwrite: bool, timeout: float) -> tuple[str, str | None]:
    try:
        url = normalize_url(url)
        with requests.get(url, stream=True, timeout=timeout) as r:
            if r.status_code != 200:
                return (movie_id, None)
            ct = r.headers.get("Content-Type")
            ext = ext_from_url_or_ct(url, ct)
            ensure_dir(target_dir)
            filename = f"{movie_id}{ext}"
            abs_path = os.path.join(target_dir, filename)
            if os.path.exists(abs_path) and not overwrite:
                # уже скачано
                rel = abs_path.replace("\\", "/")
                return (movie_id, rel[rel.index("uploads/"):] if "uploads/" in rel else rel)
            with open(abs_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
        rel = abs_path.replace("\\", "/")
        # приводим к относительному пути от корня проекта
        if "uploads/" in rel:
            rel = rel[rel.index("uploads/"):]
        return (movie_id, rel)
    except Exception:
        return (movie_id, None)

def plan_downloads(movies_path: str, movies_key: str, posters: dict, target_dir: str,
                   workers: int, timeout: float, overwrite: bool):
    print("[PLAN] Ищу записи с 'nokp-' и планирую скачивание...")
    tasks = []
    scheduled = 0
    with open(movies_path, "rb") as fin:
        for movie in ijson.items(fin, f"{movies_key}.item"):
            image = movie.get("image")
            if not (isinstance(image, str) and "nokp-" in image):
                continue
            title = movie.get("title")
            year = movie.get("year")
            orig = movie.get("originalTitle") or movie.get("original_title")
            poster = None
            if title and year is not None:
                poster = posters.get((normalize_title(title), year))
            if not poster and orig and year is not None:
                poster = posters.get((normalize_title(orig), year))
            if not poster:
                continue
            movie_id = str(movie.get("id") or "")
            if not movie_id:
                # без id используем слаг по title+year
                movie_id = re.sub(r"[^a-z0-9\-]+", "-", f"{normalize_title(title or orig)}-{year}").strip("-")
            tasks.append((movie_id, poster))
            scheduled += 1
            if scheduled % 2000 == 0:
                print(f"[PLAN] Запланировано {scheduled:,}...")
    print(f"[PLAN] Итого запланировано к скачиванию: {scheduled:,}")
    # Параллельное скачивание
    results = {}
    if scheduled == 0:
        return results
    print(f"[DL] Скачиваю постеры в '{target_dir}' с {workers} потоками...")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(download_one, mid, url, target_dir, overwrite, timeout) for (mid, url) in tasks]
        done = 0
        ok = 0
        for fut in as_completed(futs):
            mid, rel = fut.result()
            done += 1
            if rel:
                results[mid] = rel
                ok += 1
            if done % 500 == 0:
                print(f"[DL] Завершено {done:,} / {scheduled:,}, удачно {ok:,}")
    print(f"[DL] Готово: всего {scheduled:,}, успешно {len(results):,}, ошибок {scheduled - len(results):,}")
    return results

def rewrite_movies(movies_path: str, out_path: str, movies_key: str, id_to_new_image: dict) -> tuple[int, int, int, int]:
    processed = 0
    updated = 0
    removed = 0
    written = 0
    print(f"[WRITE] Перезаписываю {movies_path} -> {out_path}")
    with open(movies_path, "rb") as fin, open(out_path, "w", encoding="utf-8") as fout:
        # человекочитаемый формат
        fout.write("{\n")
        fout.write(f'  "{movies_key}": [\n')

        first_written = True
        for movie in ijson.items(fin, f"{movies_key}.item"):
            processed += 1

            image = movie.get("image")
            is_candidate = isinstance(image, str) and "nokp-" in image
            mid = str(movie.get("id") or "")
            new_img = id_to_new_image.get(mid)

            if is_candidate:
                if new_img:
                    movie["image"] = new_img
                    updated += 1
                else:
                    # не нашли/не скачали — удаляем из итогового JSON
                    removed += 1
                    if processed % 5000 == 0:
                        print(f"[WRITE] Обработано {processed:,}, обновлено {updated:,}, удалено {removed:,}, записано {written:,}...")
                    continue  # пропускаем запись

            # пишем элемент (pretty)
            block = json.dumps(movie, ensure_ascii=False, default=json_default, indent=2)
            block = indent_block(block, "  ")  # отступ внутри массива

            if not first_written:
                fout.write(",\n")
            else:
                first_written = False

            fout.write(block)
            written += 1

            if processed % 5000 == 0:
                print(f"[WRITE] Обработано {processed:,}, обновлено {updated:,}, удалено {removed:,}, записано {written:,}...")

        fout.write("\n  ]\n}\n")

    print(f"[WRITE] Готово: обработано {processed:,}, обновлено {updated:,}, удалено {removed:,}, записано {written:,}")
    return processed, updated, removed, written

def main():
    ap = argparse.ArgumentParser(description="Заменяет 'nokp-' картинки в movies: скачивает постеры и обновляет image на локальный путь.")
    ap.add_argument("--movies", default="movies-data-without-pop-pretty-updated.json")
    ap.add_argument("--movies-key", default="movies", help="Ключ массива в корне (по умолчанию 'movies')")
    ap.add_argument("--films", default="films.json")
    ap.add_argument("--films-pretty", default="films.pretty.json")
    ap.add_argument("--serials", default="serials.json")
    ap.add_argument("--serials-pretty", default="serials.pretty.json")
    ap.add_argument("--target-dir", default=os.path.join("uploads", "movies"))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--output", default=None)
    ap.add_argument("--backup", action="store_true")
    ap.add_argument("--replace", action="store_true")
    ap.add_argument("--mirror-dir", default=os.path.join("uploads", "movies_publish"), help="Куда дублировать скачанные постеры")
    ap.add_argument("--mirror-overwrite", action="store_true", help="Перезаписывать зеркальные файлы")
    ap.add_argument("--replace-retries", type=int, default=5, help="Сколько раз пробовать заменить исходник при блокировке")
    ap.add_argument("--replace-wait", type=float, default=1.0, help="Пауза между ретраями замены (сек)")
    args = ap.parse_args()

    movies_path = args.movies
    movies_key = args.movies_key
    out_path = args.output or (os.path.splitext(movies_path)[0] + ".updated.json")

    if not os.path.exists(movies_path):
        print(f"Файл не найден: {movies_path}", file=sys.stderr)
        sys.exit(2)

    posters = {}
    seen_stats = {}

    for path, kind in [
        (args.films, "FILMS"),
        (args.films_pretty, "FILMS_PRETTY"),
        (args.serials, "SERIALS"),
        (args.serials_pretty, "SERIALS_PRETTY"),
    ]:
        if os.path.exists(path):
            build_poster_map(path, kind, posters, seen_stats)

    print(f"[INDEX] Итого ключей постеров: {len(posters):,}")

    # 1) Планируем и скачиваем
    id_to_new_image = plan_downloads(
        movies_path=movies_path,
        movies_key=movies_key,
        posters=posters,
        target_dir=args.target_dir,
        workers=args.workers,
        timeout=args.timeout,
        overwrite=args.overwrite,
    )

    # 1b) Дублируем скачанные постеры
    _ = mirror_images(
        id_to_new_image=id_to_new_image,
        mirror_dir=args.mirror_dir,
        workers=args.workers,
        overwrite=args.mirror_overwrite,
    )

    # 2) Перезаписываем movies
    processed, updated, removed, written = rewrite_movies(
        movies_path=movies_path,
        out_path=out_path,
        movies_key=movies_key,
        id_to_new_image=id_to_new_image,
    )

    print("\nИтог:")
    for kind, st in seen_stats.items():
        print(f" - {kind}: прочитано {st['read']:,}, добавлено ключей {st['keys']:,}")
    print(f" - Скачано постеров: {len(id_to_new_image):,}")
    print(f" - Movies обработано: {processed:,}")
    print(f" - Изменено изображений: {updated:,}")
    print(f" - Удалено записей (без постера): {removed:,}")
    print(f" - Записано в итоговый JSON: {written:,}")
    print(f" - Результат: {out_path}")

    if args.replace:
        if args.backup:
            bak_path = movies_path + ".bak"
            print(f"[REPLACE] Бэкап исходника (copy) -> {bak_path}")
            try:
                # копия вместо переименования — не требует освобождения дескриптора исходника
                shutil.copy2(movies_path, bak_path)
            except Exception as e:
                print(f"[REPLACE] Не удалось сделать бэкап-копию: {e}")

        # Пытаемся заменить исходник с ретраями — просим закрыть файл, если открыт
        tmp_replace = movies_path + ".tmp"
        try:
            if os.path.exists(tmp_replace):
                os.remove(tmp_replace)
        except Exception:
            pass

        # Переместим результат к временному имени в каталоге исходника (атомарнее на одном диске)
        try:
            os.replace(out_path, tmp_replace)
        except Exception as e:
            print(f"[REPLACE] Не удалось подготовить временный файл: {e}")
            print("[REPLACE] Исходник не заменён. Итоговый файл:", out_path)
        else:
            replaced = False
            for attempt in range(args.replace_retries + 1):
                try:
                    os.replace(tmp_replace, movies_path)
                    replaced = True
                    print("[REPLACE] Готово.")
                    break
                except PermissionError:
                    if attempt < args.replace_retries:
                        print(f"[REPLACE] Файл занят. Закройте '{movies_path}' и повтор: {attempt+1}/{args.replace_retries} через {args.replace_wait}s")
                        time.sleep(args.replace_wait)
                    else:
                        print("[REPLACE] Не удалось заменить файл: он занят другим процессом.")
                        print("[REPLACE] Итоговый файл сохранён здесь:", out_path)
                        # Вернём результат под исходным именем обновлённого файла, чтобы не потерять
                        try:
                            os.replace(tmp_replace, out_path)
                        except Exception:
                            pass

if __name__ == "__main__":
    main()