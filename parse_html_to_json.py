import os
import json
import re
from bs4 import BeautifulSoup

# --- Конфигурация ---
ROOT_DIR = '.'  # Начать поиск из текущей директории
OUTPUT_FILE = 'movies-data.json'
# Папки, которые будут считаться категориями
CATEGORIES = ['filmy', 'serialy', 'multfilmy', 'anime']
# Папки, которые нужно проигнорировать
EXCLUDE_DIRS = ['node_modules', '.git', 'dist', 'src']

def get_existing_kinopoisk_ids(filename):
    """Загружает существующие kinopoiskId из файла, чтобы не потерять их."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'movies' in data and data['movies']:
            return {movie.get('id'): movie.get('kinopoiskId') for movie in data['movies']}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {}

def parse_movie_html(file_path, category):
    """Парсит один HTML-файл и возвращает словарь с данными о фильме."""
    print(f"Парсинг файла: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')

    movie_data = {}

    # ID и категория
    file_name = os.path.basename(file_path)
    movie_data['id'] = os.path.splitext(file_name)[0]
    movie_data['category'] = category

    # Заголовок, год и сезон
    title_tag = soup.find('h1')
    if title_tag:
        title = title_tag.find(text=True, recursive=False).strip()
        movie_data['title'] = title
        small_tag = title_tag.find('small')
        if small_tag:
            small_text = small_tag.get_text()
            year_match = re.search(r'\((\d{4})\)', small_text) or re.search(r'(\d{4})', small_text)
            if year_match:
                movie_data['year'] = int(year_match.group(1))
            
            season_match = re.search(r'(\d+\s*сезон)', small_text, re.IGNORECASE)
            if season_match:
                movie_data['season'] = season_match.group(1)
            else:
                 movie_data['season'] = None
        else:
            movie_data['year'] = None
            movie_data['season'] = None
    
    # Постер
    poster_img = soup.select_one('.content-page__img img')
    if poster_img and poster_img.get('src'):
        src = poster_img['src'].replace('../', '/')
        if not src.startswith('/'):
            src = '/' + src
        movie_data['image'] = src.lstrip('/')

    # Описание (HTML с сохранением переносов строк)
    description_div = soup.select_one('div[itemprop="description"]')
    if description_div:
        try:
            raw_html = description_div.decode_contents()
            # Нормализуем разные варианты <br> -> <br/>
            raw_html = re.sub(r'<br\s*/?>', '<br/>', raw_html, flags=re.IGNORECASE).strip()
            movie_data['description'] = raw_html if raw_html else None
        except Exception:
            movie_data['description'] = None

    # Парсинг списка с информацией
    info_list = soup.select_one('.content-page__list')
    if info_list:
        for li in info_list.find_all('li', recursive=False):
            key_span = li.find('span')
            if not key_span:
                continue
            
            key = key_span.get_text(strip=True).lower()
            
            if 'название:' in key:
                value_span = li.find('span', itemprop='alternativeHeadline')
                movie_data['originalTitle'] = value_span.get_text(strip=True) if value_span else ''
            elif 'год выхода:' in key:
                if not movie_data.get('year'): # Если год не нашелся в H1
                    a_tag = li.find('a')
                    if a_tag:
                        movie_data['year'] = int(a_tag.get_text(strip=True))
            elif 'страна:' in key:
                countries = [a.get_text(strip=True) for a in li.find_all('a')]
                movie_data['country'] = ', '.join(countries)
            elif 'премьера:' in key:
                value = key_span.next_sibling.strip() if key_span.next_sibling else ''
                movie_data['premiere'] = value
            elif 'режиссер:' in key:
                director_span = li.find('span', itemprop='director')
                movie_data['director'] = director_span.get_text(strip=True) if director_span else ''
            elif 'жанр:' in key:
                genres = [a.get_text(strip=True) for a in li.find_all('a')]
                movie_data['genres'] = genres
            elif 'перевод:' in key:
                a_tag = li.find('a')
                movie_data['translation'] = a_tag.get_text(strip=True) if a_tag else ''
            elif 'возраст:' in key:
                age = key_span.next_sibling.strip() if key_span.next_sibling else ''
                movie_data['ageRating'] = age
            elif 'в ролях:' in key:
                actors_span = li.find('span', itemprop='actors')
                movie_data['actors'] = actors_span.get_text(strip=True) if actors_span else ''

    # Рейтинги
    kp_rating_div = soup.select_one('.content-page__list-rates-item.kp')
    if kp_rating_div:
        try:
            movie_data['kpRating'] = float(kp_rating_div.get_text(strip=True))
        except (ValueError, TypeError):
            movie_data['kpRating'] = None

    imdb_rating_div = soup.select_one('.content-page__list-rates-item.imdb')
    if imdb_rating_div:
        try:
            movie_data['imdbRating'] = float(imdb_rating_div.get_text(strip=True))
        except (ValueError, TypeError):
            movie_data['imdbRating'] = None
            
    # Трейлер (YouTube ID)
    trailer_iframe = soup.select_one('#trailer-block iframe')
    if trailer_iframe and trailer_iframe.get('src'):
        youtube_match = re.search(r'embed/([a-zA-Z0-9_-]+)', trailer_iframe['src'])
        if youtube_match:
            movie_data['youtubeId'] = youtube_match.group(1)
            movie_data['trailer'] = f"https://www.youtube.com/watch?v={movie_data['youtubeId']}"

    # Kinopoisk ID
    kinopoisk_id = None
    # 1. Ищем в <script> по атрибуту aggr_id
    player_script = soup.find('script', attrs={'aggr_id': True})
    if player_script and player_script.get('aggr_id'):
        kinopoisk_id = player_script['aggr_id']
    
    # 2. Если не нашли, ищем в <iframe> по параметру kp=
    if not kinopoisk_id:
        player_iframe = soup.find('iframe', src=re.compile(r'kp=\d+'))
        if player_iframe and player_iframe.get('src'):
            kp_match = re.search(r'kp=(\d+)', player_iframe['src'])
            if kp_match:
                kinopoisk_id = kp_match.group(1)
    
    movie_data['kinopoiskId'] = kinopoisk_id

    # Добавляем пустые поля, если какие-то не нашлись
    expected_keys = [
        'title', 'originalTitle', 'year', 'image', 'category', 'genres', 'country', 
        'director', 'actors', 'description', 'season', 'kpRating', 'imdbRating', 
        'translation', 'ageRating', 'premiere', 'youtubeId', 'trailer', 'kinopoiskId'
    ]
    for key in expected_keys:
        if key not in movie_data:
            movie_data[key] = None if key not in ['genres'] else []

    movie_data['comments'] = []
            
    return movie_data


def main():
    """Главная функция для запуска парсера."""
    existing_ids = get_existing_kinopoisk_ids(OUTPUT_FILE)
    all_movies = []
    all_genres = set()
    all_years = set()

    for root, dirs, files in os.walk(ROOT_DIR):
        # Исключаем ненужные директории
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        category = os.path.basename(root)
        if category in CATEGORIES:
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        movie = parse_movie_html(file_path, category)
                        if movie and movie.get('title'):
                            # Сохраняем kinopoiskId, если он был, но только если не нашелся при парсинге
                            if not movie.get('kinopoiskId') and movie['id'] in existing_ids:
                                movie['kinopoiskId'] = existing_ids[movie['id']]

                            all_movies.append(movie)
                            if movie.get('genres'):
                                all_genres.update(movie['genres'])
                            if movie.get('year'):
                                all_years.add(movie['year'])
                    except Exception as e:
                        print(f"  Ошибка при парсинге файла {file_path}: {e}")

    # Сортировка для консистентности
    all_movies.sort(key=lambda x: x['id'])
    sorted_genres = sorted(list(all_genres))
    sorted_years = sorted(list(all_years), reverse=True)

    # Формирование итогового JSON
    final_data = {
        'movies': all_movies,
        'categories': {
            "filmy": "Фильмы",
            "serialy": "Сериалы",
            "multfilmy": "Мультфильмы",
            "anime": "Аниме"
        },
        'genres': sorted_genres,
        'years': sorted_years
    }

    # Сохранение в файл
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"\nГотово! Найдено и обработано {len(all_movies)} фильмов.")
    print(f"Данные сохранены в файл: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
