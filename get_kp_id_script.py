import os
import re
import json
import glob
import asyncio
from urllib.parse import unquote
from ddgs import DDGS
from bs4 import BeautifulSoup
import requests

DEBUG = True

def dbg(*args):
    # оставляем только строки, начинающиеся с [SEARCH]
    try:
        msg = ' '.join(str(a) for a in args)
        if msg.startswith('[SEARCH]'):
            print(msg)
    except Exception:
        pass

def normalize_premiere_date(date_str: str) -> str | None:
    if not date_str:
        return None
    s = date_str.strip()

    months_gen = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
        5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
        9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря',
    }
    # Варианты русских названий (родительный/именительный/сокращения)
    month_name_to_num = {
        'января':1, 'январь':1, 'янв':1,
        'февраля':2, 'февраль':2, 'фев':2,
        'марта':3, 'март':3, 'мар':3,
        'апреля':4, 'апрель':4, 'апр':4,
        'мая':5, 'май':5,
        'июня':6, 'июнь':6, 'июн':6,
        'июля':7, 'июль':7, 'июл':7,
        'августа':8, 'август':8, 'авг':8,
        'сентября':9, 'сентябрь':9, 'сен':9, 'сент':9,
        'октября':10, 'октябрь':10, 'окт':10,
        'ноября':11, 'ноябрь':11, 'ноя':11, 'нояб':11,
        'декабря':12, 'декабрь':12, 'дек':12,
    }

    low = s.lower()

    # 1) YYYY-MM-DD или YYYY/MM/DD или YYYY.MM.DD
    m = re.search(r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})', low)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f'{d} {months_gen.get(mo, str(mo))} {y}'

    # 2) DD-MM-YYYY или DD/MM/YYYY или DD.MM.YYYY
    m = re.search(r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})', low)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f'{d} {months_gen.get(mo, str(mo))} {y}'

    # 3) DD <месяц-словом> YYYY (любая форма месяца)
    m = re.search(r'(\d{1,2})\s+([А-Яа-яЁё]+)\s+(\d{4})', low)
    if m:
        d, mon_name, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        mo = month_name_to_num.get(mon_name)
        if mo and 1 <= d <= 31:
            return f'{d} {months_gen[mo]} {y}'
        # если не распознали месяц — вернём как есть, но подчистим пробелы/регистр
        return f'{d} {mon_name} {y}'

    # Ничего не распознали — вернём исходную строку
    return s

# Один клиент DDG; добавим таймаут для стабильности
ddgs_client = DDGS(timeout=6)

def _clean_title(s: str) -> str:
    s = (s or '').strip()
    if not s:
        return ''
    m = re.match(r'^(.*?)\s*\(', s)
    return (m.group(1) if m else s).strip()

def _text(el):
    return el.get_text(' ', strip=True) if el else ''

def _first_a_text(li):
    a = li.find('a')
    return a.get_text(strip=True) if a else ''

def _first_a_href(li):
    a = li.find('a')
    return a['href'] if a and a.has_attr('href') else ''

def _norm_category(href: str, text: str) -> str | None:
    href = (href or '').lower()
    text = (text or '').lower()
    for key in ('/filmy/', 'filmy'):
        if key in href or key in text:
            return 'filmy'
    for key in ('/serialy/', 'serialy'):
        if key in href or key in text:
            return 'serialy'
    for key in ('/mult', '/multfilmy/', 'мульт', 'мульти', 'мультфиль'):
        if key in href or key in text:
            return 'multfilmy'
    for key in ('/anime/', 'anime', 'аниме'):
        if key in href or key in text:
            return 'anime'
    return None

def _parse_ratings(soup: BeautifulSoup) -> tuple[float | None, float | None]:
    # Ищем li с подписью "Рейтинги:"
    kp = None
    imdb = None
    for li in soup.select('ul.pmovie__list li'):
        t = _text(li)
        if t.startswith('Рейтинги:'):
            # Примеры: "IMDb: 9.3 (63), " или "КиноПоиск: 7.1"
            m_imdb = re.search(r'IMDb:\s*([0-9]+(?:[.,][0-9])?)', t, re.I)
            if m_imdb:
                imdb = float(m_imdb.group(1).replace(',', '.'))
            m_kp = re.search(r'(КиноПоиск|КП):\s*([0-9]+(?:[.,][0-9])?)', t, re.I)
            if m_kp:
                kp = float(m_kp.group(2).replace(',', '.'))
            break
    return kp, imdb

def _extract_trailer(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    # iframe трейлера внутри блока id="trailer-block"
    iframe = soup.select_one('#trailer-block iframe')
    if not iframe:
        return None, None
    src = iframe.get('data-src') or iframe.get('src')
    if not src:
        return None, None
    src = unquote(src)
    # youtubeId из /embed/<ID>
    m = re.search(r'/embed/([\w\-]{5,})', src)
    if not m:
        return None, src
    yid = m.group(1)
    # Сформируем watch-ссылку
    trailer_url = f'https://www.youtube.com/watch?v={yid}'
    return yid, trailer_url

def parse_movie_html(file_path: str) -> dict | None:
    """
    Парсит все нужные поля из HTML и возвращает словарь данных.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'lxml')

        # Заголовок (+ фоллбеки)
        h1 = soup.find('h1')
        title = _clean_title(h1.get_text(strip=True) if h1 else '')

        if not title:
            img = soup.select_one('.pmovie__img img')
            if img and img.has_attr('alt'):
                title = _clean_title(img['alt'])

        if not title:
            meta = soup.find('meta', attrs={'property': 'og:title'}) or soup.find('meta', attrs={'name': 'og:title'})
            if meta and meta.get('content'):
                title = _clean_title(meta['content'])

        if not title and soup.title:
            doc_title = soup.title.get_text(strip=True)
            # частая форма: "<имя> — смотреть..." → берём то, что до тире/дефиса
            doc_title = re.split(r'\s+[–—-]\s+', doc_title, 1)[0]
            title = _clean_title(doc_title)

        # Год из "pmovie__main-info"
        year = None
        info_div = soup.find('div', class_='pmovie__main-info')
        if info_div:
            txt = _text(info_div)
            ym = re.search(r'\b(19|20)\d{2}\b', txt)
            if ym:
                year = int(ym.group(0))

        # Фоллбек: из строки "Год:"
        if year is None:
            for li in soup.select('ul.pmovie__list li'):
                span = li.find('span')
                if span and 'Год:' in span.get_text(strip=True):
                    txt = _text(li).replace('Год:', '').strip()
                    ym2 = re.search(r'\b(19|20)\d{2}\b', txt)
                    if ym2:
                        year = int(ym2.group(0))
                        break

        # Сезон: берем только из шапки (h1 / og:title / <title>), не из .poster__series
        season = None
        header_sources = []
        if h1 and h1.get_text(strip=True):
            header_sources.append(h1.get_text(strip=True))
        meta = soup.find('meta', attrs={'property': 'og:title'}) or soup.find('meta', attrs={'name': 'og:title'})
        if meta and meta.get('content'):
            header_sources.append(meta['content'])
        if soup.title and soup.title.string:
            header_sources.append(soup.title.string)

        season_match = None
        for hs in header_sources:
            m_season = re.search(r'\b(\d+)\s+сезон\b', hs, re.I)
            if m_season:
                season_match = m_season.group(0)
                break
        if season_match:
            season = season_match

        # Картинка постера
        img = soup.select_one('.pmovie__img img')
        image = None
        original_title = None
        if img and img.has_attr('src'):
            image = img['src'].lstrip('/')
        # Попытка вытащить оригинальное название из alt (последние скобки, не год)
        if img and img.has_attr('alt'):
            alt = img['alt']
            # Берём последнее содержимое в скобках, если внутри не только год
            parens = re.findall(r'\(([^)]+)\)', alt)
            if parens:
                candidate = parens[-1]
                if not re.fullmatch(r'(19|20)\d{2}', candidate):
                    original_title = candidate.strip()

        # Описание: сохраняем HTML/переносы строк
        descr_div = soup.select_one('.pmovie__text.full-text.clearfix')
        description = descr_div.decode_contents() if descr_div else None

        # Страна
        country = None
        for li in soup.select('ul.pmovie__list li'):
            span = li.find('span')
            if span and 'Страна:' in span.get_text(strip=True):
                country = _text(li).replace('Страна:', '').strip()
                break

        # Премьера (Мир)
        premiere = None
        for li in soup.select('ul.pmovie__list li'):
            span = li.find('span')
            if span and 'Премьера (Мир)' in span.get_text(strip=True):
                premiere = _text(li).replace('Премьера (Мир)', '').strip()
                break

        # Нормализация даты премьеры к формату "12 февраля 2011"
        premiere = normalize_premiere_date(premiere) if premiere else None

        # Фоллбек: год из нормализованной премьеры
        if year is None and premiere:
            ym_p = re.search(r'\b(19|20)\d{2}\b', premiere)
            if ym_p:
                year = int(ym_p.group(0))

        # Фоллбек: год из имени файла (берём последний 4-значный год)
        if year is None:
            base = os.path.basename(file_path)
            years_in_name = re.findall(r'(19|20)\d{2}', base)
            if years_in_name:
                year = int(years_in_name[-1])

        # Режиссер (первый)
        director = None
        for li in soup.select('ul.pmovie__list li'):
            span = li.find('span')
            if span and 'Режиссер:' in span.get_text(strip=True):
                director = _first_a_text(li) or _text(li).replace('Режиссер:', '').split(',')[0].strip()
                break

        # Актеры (списком и строкой)
        actors_list = []
        for li in soup.select('ul.pmovie__list li'):
            span = li.find('span')
            if span and 'В ролях актеры:' in span.get_text(strip=True):
                actors_list = [a.get_text(strip=True) for a in li.find_all('a')]
                break
        actors = ', '.join(actors_list) if actors_list else None

        # Жанры и категория
        genres = []
        category_norm = None
        for li in soup.select('ul.pmovie__list li'):
            span = li.find('span')
            if span and 'Жанр:' in span.get_text(strip=True):
                anchors = li.find_all('a')
                if anchors:
                    cat_text = anchors[0].get_text(strip=True)
                    cat_href = anchors[0].get('href', '')
                    category_norm = _norm_category(cat_href, cat_text)
                    # В JSON жанры содержат и первую категорию
                    genres = [a.get_text(strip=True) for a in anchors]
                break

        # Перевод
        translation = None
        for li in soup.select('ul.pmovie__list li'):
            span = li.find('span')
            if span and 'Перевод:' in span.get_text(strip=True):
                translation = _text(li).replace('Перевод:', '').strip()
                break

        # Трейлер / youtube
        youtube_id, trailer = _extract_trailer(soup)

        # Рейтинги
        kp_rating, imdb_rating = _parse_ratings(soup)

        # ID (по имени файла)
        file_id = os.path.splitext(os.path.basename(file_path))[0]

        return {
            'file_id': file_id,
            'category': category_norm,
            'title': title or None,
            'year': year,
            'season': season,
            'image': image,
            'description': description,  # сохраняем HTML/переносы
            'originalTitle': original_title,
            'country': country,
            'premiere': premiere,
            'director': director,
            'genres': genres,
            'translation': translation,
            'actors': actors,
            'youtubeId': youtube_id,
            'trailer': trailer,
            'kpRating': kp_rating,
            'imdbRating': imdb_rating,
            'ageRating': None,
            'comments': [],
        }
    except Exception as e:
        print(f"Ошибка при парсинге файла {file_path}: {e}")
        return None

def build_stage_sequence(info: dict) -> list[str]:
    stages = []
    if info.get('director'):
        stages.append('director')
    if info.get('actors'):
        first_actor = info['actors'].split(',')[0].strip()
        if first_actor:
            stages.append('actor')
    if info.get('premiere'):
        stages.append('premiere')
    return stages

def make_query(info: dict, mode: str, is_series: bool) -> str:
    title = info.get('title') or ''
    year = str(info.get('year') or '')
    parts = [f'"{title}"', f'"{year}"']
    if mode == 'director' and info.get('director'):
        parts.append(f'"{info["director"]}"')
    elif mode == 'actor' and info.get('actors'):
        first_actor = info['actors'].split(',')[0].strip()
        if first_actor:
            parts.append(f'"{first_actor}"')
    elif mode == 'premiere' and info.get('premiere'):
        parts.append(f'"{info["premiere"]}"')
    if is_series:
        parts.append('"сезон"')
    return ' '.join(parts)

def _norm(s: str) -> str:
    s = (s or '').lower()
    s = s.replace('ё', 'е')
    s = re.sub(r'["“”«»\'`]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

TOKENS_OK = 0.7

def _tokenize(s: str) -> list[str]:
    txt = _norm(s)
    toks = re.findall(r'[a-zа-яё0-9]+', txt, flags=re.I)
    return [t for t in toks if len(t) >= 3]

def _tokens_score(expected: str, candidate: str) -> float:
    exp = set(_tokenize(expected))
    if not exp:
        return 0.0
    cand = set(_tokenize(candidate))
    return len(exp & cand) / len(exp)

def _is_series(info: dict) -> bool:
    # по имени файла
    file_id = (info.get('file_id') or '').lower()
    if '-serial-' in file_id:
        return True
    # по распознанной категории
    if (info.get('category') or '').lower() == 'serialy':
        return True
    # по явному сезону, взятому из шапки (h1/title/og:title)
    if info.get('season'):
        return True
    return False

async def get_kinopoisk_id_async(movie_query: str, expected_title: str, expected_year: int | str, mode: str, is_series: bool) -> tuple[str, str | None, str | None]:
    exp_title_norm = _norm(expected_title)
    year_str = str(expected_year or '').strip()

    quoted = re.findall(r'"([^"]+)"', movie_query)
    hint = quoted[2] if len(quoted) >= 3 else ''
    hint_norm = _norm(hint)

    site_filter = 'site:www.kinopoisk.ru/series/' if is_series else 'site:www.kinopoisk.ru/film/'
    dbg(f'[SEARCH] type={"series" if is_series else "film"} mode={mode} query={movie_query} expected="{expected_title}" year={year_str}')

    query = f'{movie_query} {site_filter} -site:hd.kinopoisk.ru -"смотреть онлайн в хорошем"'
    try:
        results = await asyncio.to_thread(
            ddgs_client.text, 
            query, 
            max_results=5,
            region='ru-ru',
            safesearch='off',
            backend='api',
        )
        any_candidates = False
        for result in results or []:
            url = result.get('href', '')
            title_field = result.get('title') or ''
            snippet = result.get('body') or ''
            title_norm = _norm(title_field)
            body_norm = _norm(snippet)

            m = re.search(r'kinopoisk\.ru/(film|series)/(\d+)', url)
            if not m:
                dbg(f'  [SKIP] not film/series page: {url}')
                continue

            url_type = m.group(1)
            if is_series and url_type != 'series':
                dbg(f'  [SKIP] expected series, got {url_type}: {url}')
                continue
            if (not is_series) and url_type != 'film':
                dbg(f'  [SKIP] expected film, got {url_type}: {url}')
                continue

            score_title = _tokens_score(expected_title, title_field)
            title_ok = (exp_title_norm in title_norm) or (score_title >= TOKENS_OK)
            year_ok = bool(year_str and (year_str in title_norm or year_str in body_norm))
            hint_ok = True if not hint_norm else (hint_norm in title_norm or hint_norm in body_norm or _tokens_score(hint, title_field) >= TOKENS_OK or _tokens_score(hint, snippet) >= TOKENS_OK)

            dbg(f'  [CANDIDATE] title="{title_field}" url={url} score_title={score_title:.2f} title_ok={title_ok} year_ok={year_ok} hint_ok={hint_ok}')
            if title_ok and year_ok:
                if hint_ok:
                    dbg(f'  [ACCEPT] id={m.group(2)} url={url}')
                else:
                    dbg(f'  [ACCEPT_NOHINT] id={m.group(2)} url={url}')
                return movie_query, m.group(2), url

            any_candidates = True

        if not any_candidates:
            dbg(f'[NO_RESULTS] mode={mode} query={movie_query}')
        else:
            dbg(f'[NO_MATCH] mode={mode} query={movie_query}')
        return movie_query, None, None
    except Exception as e:
        print(f"Ошибка при поиске '{movie_query}': {e}")
        return movie_query, None, None

def build_json_item(info: dict, kinopoisk_id: str | None) -> dict:
    # category: если не распознали — попробуем из genres[0]
    category = info.get('category')
    if not category and info.get('genres'):
        category = _norm_category('', info['genres'][0]) or None

    return {
        'id': info['file_id'],
        'category': category,
        'title': info.get('title'),
        'year': info.get('year'),
        'season': info.get('season'),
        'image': info.get('image'),
        'description': info.get('description'),
        'originalTitle': info.get('originalTitle'),
        'country': info.get('country'),
        'premiere': info.get('premiere'),
        'director': info.get('director'),
        'genres': info.get('genres') or [],
        'translation': info.get('translation'),
        'actors': info.get('actors'),
        'kpRating': info.get('kpRating'),
        'imdbRating': info.get('imdbRating'),
        'youtubeId': info.get('youtubeId'),
        'trailer': info.get('trailer'),
        'kinopoiskId': kinopoisk_id,
        'ageRating': info.get('ageRating'),
        'comments': info.get('comments') or [],
    }

async def main():
    html_files = glob.glob('*.html')
    if not html_files:
        print("HTML файлы для обработки не найдены в текущей директории.")
        return

    print(f"Найдено {len(html_files)} HTML файлов.")

    movies_info: list[dict] = []
    for file_path in html_files:
        info = parse_movie_html(file_path)
        # Требуем обязательные title и year для поиска ID
        if info and info.get('title') and info.get('year'):
            movies_info.append(info)
        else:
            print(f"Предупреждение: Не удалось извлечь название и год из {os.path.basename(file_path)}. Пропуск.")

    if not movies_info:
        print("Не удалось подготовить ни одного фильма для поиска.")
        return

    batch_size = 7
    total_batches = (len(movies_info) + batch_size - 1) // batch_size
    print(f"🚀 Запускаем поиск для {len(movies_info)} фильмов порциями по {batch_size}...")

    json_items: list[dict] = []

    for b in range(0, len(movies_info), batch_size):
        batch_items = movies_info[b:b + batch_size]
        per_item_stages = [build_stage_sequence(info) for info in batch_items]
        per_item_stage_index = [0 for _ in batch_items]
        per_item_attempts = [0 for _ in batch_items]
        batch_results: list[tuple[str, str | None, str | None]] = [('', None, None) for _ in batch_items]

        # Если ни одной стадии нет (нет режиссёра/актёра/премьеры) — сразу помечаем как НЕ НАЙДЕН и не штурмуем
        for i, stages in enumerate(per_item_stages):
            if not stages:
                base_query = f'"{batch_items[i].get("title","")}" "{batch_items[i].get("year","")}"'
                batch_results[i] = (base_query, None, None)

        # В работу берём только те, у кого есть хотя бы одна стадия
        unresolved_idx = [i for i, stages in enumerate(per_item_stages) if stages]

        print(f"\n--- Обработка порции {b // batch_size + 1}/{total_batches} ({len(batch_items)} фильмов) ---")

        # Пока у всех нет ID — не двигаемся дальше
        while unresolved_idx:
            query_pack = []
            for i in unresolved_idx:
                mode = per_item_stages[i][per_item_stage_index[i]]
                is_series = _is_series(batch_items[i])
                q = make_query(batch_items[i], mode, is_series)
                query_pack.append((i, q, mode, is_series))

            tasks = [
                get_kinopoisk_id_async(
                    q,
                    batch_items[i].get('title', ''),
                    batch_items[i].get('year', ''),
                    mode,
                    is_series
                )
                for (i, q, mode, is_series) in query_pack
            ]
            results = await asyncio.gather(*tasks)
    
            still_unresolved = []
            for res, (i, q, mode, is_series) in zip(results, query_pack):
                movie_query, movie_id, source_url = res
                if movie_id:
                    batch_results[i] = (movie_query, movie_id, source_url)
                    dbg(f'[FOUND] mode={mode} -> {movie_id} {source_url}')
                else:
                    if per_item_stage_index[i] + 1 < len(per_item_stages[i]):
                        per_item_stage_index[i] += 1
                        still_unresolved.append(i)
                    else:
                        if per_item_attempts[i] == 0:
                            per_item_attempts[i] = 1
                            per_item_stage_index[i] = 0
                            still_unresolved.append(i)
                        else:
                            dbg(f'[GIVEUP] title="{batch_items[i].get("title","")}" year={batch_items[i].get("year","")} after 2 rounds')
                            batch_results[i] = (movie_query, None, None)

            unresolved_idx = still_unresolved
            if unresolved_idx:
                await asyncio.sleep(1)

        # Печатаем результаты порции
        print("\nПорция завершена. Результаты этой порции:")
        for movie_query, movie_id, source_url in batch_results:
            if movie_id:
                if source_url:
                    print(f"✅ {movie_query} → ID: {movie_id} | {source_url}")
                else:
                    print(f"✅ {movie_query} → ID: {movie_id}")
            else:
                print(f"❌ {movie_query} → НЕ НАЙДЕН")

        # Формируем JSON для этой порции (только найденные)
        for info, (_, kp_id, _) in zip(batch_items, batch_results):
            if kp_id:
                json_items.append(build_json_item(info, kp_id))

        # Пауза между порциями
        if b + batch_size < len(movies_info):
            await asyncio.sleep(2)

    # Сохраняем итоговый JSON в файл
    out_path = 'movies.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(json_items, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"Готово. Сохранено {len(json_items)} записей в {out_path}")
    print("=" * 60)

if __name__ == "__main__":
    # В Windows может потребоваться следующая строка для правильной работы to_thread
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())