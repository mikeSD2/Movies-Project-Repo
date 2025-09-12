import json
import time
from youtubesearchpython import VideosSearch

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


def find_trailers_for_missing(movies_data_path="movies-data.json", update_file_path="trailers-update.ndjson"):
    """
    Ищет трейлеры для фильмов и записывает обновленные данные в NDJSON файл.
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

    all_movies = []
    if isinstance(data, dict) and "movies" in data:
        all_movies = data["movies"]
    elif isinstance(data, dict):
        for category_list in data.values():
            if isinstance(category_list, list): all_movies.extend(category_list)
    else:
        print("Ошибка: Неподдерживаемый формат JSON.")
        return

    movies_to_update = [movie for movie in all_movies if not movie.get('trailer')]
    
    if not movies_to_update:
        print("У всех фильмов уже есть трейлеры. Обновление не требуется.")
        return

    print(f"Найдено {len(movies_to_update)} фильмов без трейлера. Начинаю поиск...")
    print(f"Результаты будут сохраняться в файл: {update_file_path}")
    
    updated_count = 0
    total_to_process = len(movies_to_update)

    for i, movie in enumerate(movies_to_update):
        title = movie.get('title')
        year = movie.get('year')
        
        if not title or not year:
            print(f"[{i+1}/{total_to_process}] Пропускаю фильм без названия или года.")
            continue

        print(f"[{i+1}/{total_to_process}] Ищу трейлер: '{title}' ({year})...")

        # Строим набор запросов отдельно: RU и EN
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

        # 1) Сначала пробуем RU-запросы
        candidate_results = []
        seen_ids = set()
        try:
            for q in ru_queries:
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
            continue

        if candidate_results:
            best_video, score = get_best_trailer(movie, candidate_results)
            if best_video:
                video_id = best_video['id']
                trailer_url = f"https://www.youtube.com/watch?v={video_id}"
                movie['youtubeId'] = video_id
                movie['trailer'] = trailer_url
                updated_count += 1

                print(f"  -> Найден RU трейлер (Оценка: {score}). Записываю в {update_file_path}...")
                try:
                    with open(update_file_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(movie, ensure_ascii=False) + '\n')
                except IOError as e:
                    print(f"  -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать обновление! {e}")
                time.sleep(1)
                continue
            else:
                print(f"  -> RU кандидаты найдены, но не прошли проверку (Лучшая оценка: {score}).")
        else:
            print(f"  -> RU результаты не найдены. Пробую оригинальные запросы...")

        # 2) Если RU не подошёл, пробуем EN/original
        candidate_results = []
        seen_ids = set()
        try:
            for q in en_queries:
                print(f"   -> Поиск по (EN): '{q}'")
                videos_search = VideosSearch(q, limit=8, region='RU')
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
            continue

        if candidate_results:
            best_video, score = get_best_trailer(movie, candidate_results)
            if best_video:
                video_id = best_video['id']
                trailer_url = f"https://www.youtube.com/watch?v={video_id}"
                movie['youtubeId'] = video_id
                movie['trailer'] = trailer_url
                updated_count += 1

                print(f"  -> Найден EN трейлер (Оценка: {score}). Записываю в {update_file_path}...")
                try:
                    with open(update_file_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(movie, ensure_ascii=False) + '\n')
                except IOError as e:
                    print(f"  -> КРИТИЧЕСКАЯ ОШИБКА: Не удалось записать обновление! {e}")
            else:
                print(f"  -> EN кандидаты найдены, но не прошли проверку (Лучшая оценка: {score}).")
        else:
            print(f"  -> Трейлер не найден.")

        time.sleep(1)

    print(f"\nПоиск завершен. Найдено и записано {updated_count} трейлеров.")
    if updated_count > 0:
        print(f"Теперь запустите скрипт 'merge_trailers.py', чтобы применить изменения к основному файлу.")

if __name__ == "__main__":
    find_trailers_for_missing()



