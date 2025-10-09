import json
import time
from youtubesearchpython import VideosSearch
from datetime import datetime, timedelta
import os

# Настройки «не найдено»
NOT_FOUND_NDJSON = "trailers-not-found.ndjson"
RECENT_YEAR_CUTOFF_YEARS = 1          # «за последний год»
RECENT_RETRY_COOLDOWN_DAYS = 90       # кулинг между попытками для свежих

def _now_iso():
    return datetime.utcnow().isoformat(timespec='seconds') + 'Z'

def _parse_iso(dt: str):
    try:
        return datetime.fromisoformat(dt.replace('Z', ''))
    except Exception:
        return None

def movie_key(movie: dict) -> str:
    """
    Уникальный ключ фильма. Предпочтительно используем явный ID,
    иначе нормализуем название + год.
    """
    kid = movie.get('kpId') or movie.get('id')
    if kid:
        return f"id:{kid}"
    title = (movie.get('originalTitle') or movie.get('title') or '').strip().lower()
    year = movie.get('year') or ''
    return f"title:{title}|year:{year}"

def load_not_found_index(path: str) -> dict:
    """
    Читает NDJSON статусы по фильмам и возвращает индекс по последней записи на ключ.
    Формат строки: {key, status: 'not_found'|'found', last_attempt, attempts}
    """
    idx = {}
    if not os.path.exists(path):
        return idx
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            k = obj.get('key')
            if not k:
                continue
            last_attempt = obj.get('last_attempt') or ''
            prev = idx.get(k)
            if not prev:
                idx[k] = obj
            else:
                # берём более свежую запись
                da = _parse_iso(prev.get('last_attempt') or '') or datetime.min
                db = _parse_iso(last_attempt) or datetime.min
                if db >= da:
                    idx[k] = obj
    return idx

def should_skip_movie(movie: dict, nf_idx: dict,
                      recent_year_cutoff_years: int = RECENT_YEAR_CUTOFF_YEARS,
                      cooldown_days: int = RECENT_RETRY_COOLDOWN_DAYS) -> tuple[bool, str]:
    """
    Возвращает (skip, reason)
    - Старые фильмы: если уже был статус 'not_found' — пропускаем всегда.
    - Свежие (за последний год): пропускаем, если не вышел кулинг с последней попытки.
    """
    k = movie_key(movie)
    entry = nf_idx.get(k)
    # если записи нет — не пропускаем
    if not entry:
        return False, ""
    if entry.get('status') == 'found':
        return False, ""

    # Определяем «свежесть» по году фильма
    y = movie.get('year')
    try:
        y = int(y)
    except Exception:
        y = None

    now = datetime.utcnow()
    recent_cutoff = now.year - recent_year_cutoff_years
    is_recent = (y is not None and y >= recent_cutoff)

    last_attempt = _parse_iso(entry.get('last_attempt') or '') or datetime.min
    since = (now - last_attempt)

    if is_recent:
        if since < timedelta(days=cooldown_days):
            return True, f"свежий, кулинг {cooldown_days}д, осталось ~{(timedelta(days=cooldown_days)-since).days}д"
        return False, ""
    else:
        return True, "старый, уже помечен как not_found"

def record_not_found(movie: dict, nf_idx: dict, path: str):
    k = movie_key(movie)
    attempts = 1
    if k in nf_idx and isinstance(nf_idx[k].get('attempts'), int):
        attempts = nf_idx[k]['attempts'] + 1
    rec = {
        "key": k,
        "title": movie.get('title'),
        "originalTitle": movie.get('originalTitle'),
        "year": movie.get('year'),
        "status": "not_found",
        "last_attempt": _now_iso(),
        "attempts": attempts,
    }
    # апдейтим индекс в памяти
    nf_idx[k] = rec
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def record_found(movie: dict, nf_idx: dict, path: str):
    k = movie_key(movie)
    rec = {
        "key": k,
        "title": movie.get('title'),
        "originalTitle": movie.get('originalTitle'),
        "year": movie.get('year'),
        "status": "found",
        "last_attempt": _now_iso(),
        "attempts": (nf_idx.get(k, {}).get('attempts') or 0),
    }
    nf_idx[k] = rec
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def get_best_trailer(movie, search_results):
    """
    Анализирует список результатов поиска YouTube и выбирает наиболее релевантный трейлер.
    Возвращает кортеж (лучший_кандидат, оценка).
    """
    import re

    best_candidate = None
    highest_score = -1

    movie_title_ru_norm = (movie.get('title') or '').lower().strip()
    movie_title_orig_norm = (movie.get('originalTitle') or '').lower().strip()
    movie_year = movie.get('year')
    movie_year_int = None
    try:
        movie_year_int = int(movie_year)
    except Exception:
        pass

    require_trailer_words = ['трейлер', 'trailer', 'тизер', 'teaser']

    stop_words = [
        # Подборки и топы
        'топ', 'подборка', 'лучшие', 'все трейлеры', 'compilation', 'top 10',
        # Обзоры и реакции
        'обзор', 'реакция', 'мнение', 'разбор', 'анализ', 'пасхалки', 'review', 'reaction',
        # Музыка/клипы
        'клип', 'official video', 'music video', 'lyrics', 'lyric', 'mv', 'remix', 'кавер', 'cover', 'караоке', 'song', 'песня',
        'саундтрек', 'soundtrack', 'ost',
        # Сцены/фрагменты
        'сцена', 'момент', 'фрагмент', 'scene', 'fragment',
        # Фильм целиком и прочее
        'full movie', 'полный фильм', 'фильм целиком',
        # Игры/прочее
        'игра', 'game', "let's play", 'прохождение',
        # Фанатское/фейки/пародии/шортсы
        'fan made', 'фанатский', 'fake', 'фейк', 'пародия', 'parody', '#shorts', 'shorts'
    ]

    def years_in(s: str):
        return [int(y) for y in re.findall(r'\b(19|20)\d{2}\b', s)]

    for video in search_results:
        video_title_norm = (video.get('title') or '').lower()
        if not video_title_norm:
            continue

        # Обязательно: это должен быть трейлер/тизер
        if not any(w in video_title_norm for w in require_trailer_words):
            continue

        # Сильная фильтрация по "плохим" словам
        if any(w in video_title_norm for w in stop_words):
            continue

        score = 0

        # Совпадение по названию
        if movie_title_ru_norm and movie_title_ru_norm in video_title_norm:
            score += 10
        if movie_title_orig_norm and movie_title_orig_norm in video_title_norm:
            score += 10
        if score == 0:
            # Если ни одно название не совпало — пропускаем
            continue

        # Официальность в заголовке
        if 'официальный' in video_title_norm or 'official' in video_title_norm:
            score += 5

        # Близость года из заголовка к году фильма
        if movie_year_int:
            yts = years_in(video_title_norm)
            if yts:
                mind = min(abs(y - movie_year_int) for y in yts)
                if mind <= 1:
                    score += 8
                elif mind <= 3:
                    score += 3
                else:
                    score -= 25  # жёстко отсекаем чужие годы (пример: "Схватка 2011" для фильма 1972)

        # Длительность, похожая на трейлер
        duration_str = video.get('duration')
        if duration_str:
            try:
                parts = list(map(int, duration_str.split(':')))
                seconds = sum(p * 60**i for i, p in enumerate(reversed(parts)))
                if 45 <= seconds <= 210:
                    score += 5
                elif 210 < seconds <= 360:
                    score += 2
                elif seconds > 600 or seconds < 30:
                    score -= 10
            except Exception:
                pass

        # Сигналы канала
        ch_name = ''
        ch = video.get('channel') or {}
        if isinstance(ch, dict):
            ch_name = (ch.get('name') or '').lower()
        elif isinstance(ch, str):
            ch_name = ch.lower()

        if ch_name:
            official_ch_keys = [
                'официальный', 'official', 'pictures', 'film', 'films', 'кино', 'кинокомпания',
                'distributor', 'warner', 'sony', 'fox', 'paramount', 'universal', 'netflix', 'hbomax'
            ]
            music_ch_keys = ['vevo', 'records', 'music', 'band', 'несчастный', 'случай', 'label']
            if any(k in ch_name for k in official_ch_keys):
                score += 4
            if any(k in ch_name for k in music_ch_keys):
                score -= 20

        # Доп. проверка описания
        try:
            if isinstance(video.get('descriptionSnippet'), list):
                desc = ' '.join([(x.get('text') or '') for x in video['descriptionSnippet']]).lower()
                if any(w in desc for w in stop_words):
                    score -= 15
        except Exception:
            pass

        if score > highest_score:
            highest_score = score
            best_candidate = video

    if highest_score >= 15:
        return best_candidate, highest_score
    return None, highest_score


def find_trailers_for_missing(
    movies_data_path="movies-data.json",
    update_file_path="trailers-update.ndjson",
    not_found_file_path=NOT_FOUND_NDJSON,
    recent_year_cutoff_years=RECENT_YEAR_CUTOFF_YEARS,
    recent_retry_cooldown_days=RECENT_RETRY_COOLDOWN_DAYS,
):
    """
    Ищет трейлеры, пишет найденные в NDJSON обновлений.
    Для «не найдено» ведёт реестр в NDJSON и пропускает повторы по правилам.
    """
    try:
        with open(movies_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{movies_data_path}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось прочитать JSON из файла '{movies_data_path}'.")
        return

    nf_idx = load_not_found_index(not_found_file_path)
    print(f"Загружен индекс not_found: {len(nf_idx)} ключей из '{not_found_file_path}'")

    updated_count = 0

    def process_movie(i: int, total: int, movie: dict):
        nonlocal updated_count

        if movie.get('trailer'):
            return

        # Пропуск по реестру not_found
        skip, reason = should_skip_movie(
            movie, nf_idx,
            recent_year_cutoff_years=recent_year_cutoff_years,
            cooldown_days=recent_retry_cooldown_days
        )
        if skip:
            title = movie.get('title') or movie.get('originalTitle') or ''
            year = movie.get('year') or ''
            print(f"[{i}/{total}] Пропуск: '{title}' ({year}) — {reason}")
            return

        title = movie.get('title')
        year = movie.get('year')
        if not title or not year:
            print(f"[{i}/{total}] Пропускаю фильм без названия или года.")
            return

        print(f"[{i}/{total}] Ищу трейлер: '{title}' ({year})...")

        # Строим запросы
        title_ru = movie.get('title') or ''
        title_orig = movie.get('originalTitle') or ''
        year_str = str(year) if year else ''

        ru_queries = []
        if title_ru:
            ru_queries += [
                f"{title_ru} {year_str} официальный трейлер -клип -ost -саундтрек -песня",
                f"{title_ru} {year_str} тизер -клип -ost -саундтрек -песня",
            ]

        en_queries = []
        if title_orig:
            en_queries += [
                f"{title_orig} {year_str} official trailer -clip -song -music -ost",
                f"{title_orig} {year_str} teaser -clip -song -music -ost",
            ]

        searched = False
        found_any = False

        # 1) RU
        candidate_results = []
        seen_ids = set()
        try:
            for q in ru_queries:
                searched = True
                print(f"   -> Поиск по (RU): '{q}'")
                videos_search = VideosSearch(q, limit=8, region='RU')
                results = videos_search.result()
                for v in (results or {}).get('result', []):
                    vid = v.get('id')
                    if vid and vid not in seen_ids:
                        candidate_results.append(v)
                        seen_ids.add(vid)
        except Exception as e:
            print(f"  -> Ошибка при поиске (RU): {e}")
            print("     Делаю паузу 10 секунд...")
            time.sleep(10)

        if candidate_results:
            best_video, score = get_best_trailer(movie, candidate_results)
            if best_video:
                video_id = best_video['id']
                trailer_url = f"https://www.youtube.com/watch?v={video_id}"
                movie['youtubeId'] = video_id
                movie['trailer'] = trailer_url
                updated_count += 1
                found_any = True

                print(f"  -> Найден RU трейлер (Оценка: {score}). Записываю в {update_file_path}...")
                try:
                    with open(update_file_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(movie, ensure_ascii=False) + '\n')
                except IOError as e:
                    print(f"  -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать обновление! {e}")

                try:
                    record_found(movie, nf_idx, not_found_file_path)
                except Exception:
                    pass

                time.sleep(1)
                return
            else:
                print(f"  -> RU кандидаты найдены, но не прошли проверку (Лучшая оценка: {score}).")
        else:
            print(f"  -> RU результаты не найдены. Пробую оригинальные запросы...")

        # 2) EN/original
        candidate_results = []
        seen_ids = set()
        try:
            for q in en_queries:
                searched = True
                print(f"   -> Поиск по (EN): '{q}'")
                videos_search = VideosSearch(q, limit=8, region='US')  # EN регион
                results = videos_search.result()
                for v in (results or {}).get('result', []):
                    vid = v.get('id')
                    if vid and vid not in seen_ids:
                        candidate_results.append(v)
                        seen_ids.add(vid)
        except Exception as e:
            print(f"  -> Ошибка при поиске (EN): {e}")
            print("     Делаю паузу 10 секунд...")
            time.sleep(10)

        if candidate_results:
            best_video, score = get_best_trailer(movie, candidate_results)
            if best_video:
                video_id = best_video['id']
                trailer_url = f"https://www.youtube.com/watch?v={video_id}"
                movie['youtubeId'] = video_id
                movie['trailer'] = trailer_url
                updated_count += 1
                found_any = True

                print(f"  -> Найден EN трейлер (Оценка: {score}). Записываю в {update_file_path}...")
                try:
                    with open(update_file_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(movie, ensure_ascii=False) + '\n')
                except IOError as e:
                    print(f"  -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать обновление! {e}")

                try:
                    record_found(movie, nf_idx, not_found_file_path)
                except Exception:
                    pass
            else:
                print(f"  -> EN кандидаты найдены, но не прошли проверку (Лучшая оценка: {score}).")
        else:
            print(f"  -> Трейлер не найден.")

        # Если мы искали, но так и не нашли — фиксируем not_found
        if searched and not found_any:
            try:
                record_not_found(movie, nf_idx, not_found_file_path)
            except Exception as e:
                print(f"  -> Не удалось записать в '{not_found_file_path}': {e}")

        time.sleep(1)

    # Итерируем без создания общего списка
    if isinstance(data, dict) and "movies" in data and isinstance(data["movies"], list):
        total = len(data["movies"])
        print(f"Всего фильмов: {total}. Результаты будут сохраняться в: {update_file_path}")
        for i, movie in enumerate(data["movies"], start=1):
            process_movie(i, total, movie)
    elif isinstance(data, dict):
        total = sum(len(lst) for lst in data.values() if isinstance(lst, list))
        print(f"Всего фильмов: {total}. Результаты будут сохраняться в: {update_file_path}")
        i = 0
        for category_list in data.values():
            if not isinstance(category_list, list):
                continue
            for movie in category_list:
                i += 1
                process_movie(i, total, movie)
    else:
        print("Ошибка: Неподдерживаемый формат JSON.")
        return

    print(f"\nПоиск завершен. Найдено и записано {updated_count} трейлеров.")
    if updated_count > 0:
        print(f"Теперь запустите скрипт 'merge_trailers.py', чтобы применить изменения к основному файлу.")

if __name__ == "__main__":
    find_trailers_for_missing()