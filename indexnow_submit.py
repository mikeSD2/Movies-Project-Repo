import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# вверху файла
from urllib.error import HTTPError, URLError

def post_indexnow(endpoint, host, key, key_location, urls, timeout=20):
    payload = {'host': host, 'key': key, 'keyLocation': key_location, 'urlList': urls}
    body = json.dumps(payload).encode('utf-8')
    req = Request(endpoint, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode('utf-8', errors='ignore')
    except HTTPError as e:
        return e.code, (e.read().decode('utf-8', errors='ignore') if hasattr(e, 'read') else str(e))

DEFAULT_MOVIES_JSON = 'movies-data.json'
DEFAULT_INDEXED_FILE = os.path.join('server-data', 'indexnow-indexed.ndjson')
DEFAULT_ENDPOINT = 'https://yandex.com/indexnow'  # можно поменять на https://api.indexnow.org/indexnow
DEFAULT_KEY_LOCATION_FMT = '{base}/%s.txt'

# Поля, по которым решаем «контент изменился» (можно подстроить)
HASH_FIELDS = [
    'title', 'description', 'image', 'year', 'category',
    'kinopoiskId', 'imdbRating', 'season', 'episode'
]

def load_env_like(path='config.env'):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith('#') or '=' not in s:
                continue
            k, v = s.split('=', 1)
            env[k.strip()] = v.strip()
    return env

def ensure_key_file(public_dir, key):
    if not key:
        return None
    os.makedirs(public_dir, exist_ok=True)
    key_path = os.path.join(public_dir, f'{key}.txt')
    if not os.path.exists(key_path):
        with open(key_path, 'w', encoding='utf-8') as f:
            f.write(key)
        print(f'Создан ключевой файл: {key_path}')
    else:
        # проверим содержимое
        try:
            with open(key_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if content != key:
                with open(key_path, 'w', encoding='utf-8') as f:
                    f.write(key)
                print(f'Обновлено содержимое ключевого файла: {key_path}')
        except Exception:
            pass
    return key_path

def sha256_for(movie, fields=HASH_FIELDS):
    parts = []
    for k in fields:
        v = movie.get(k)
        if isinstance(v, (list, dict)):
            v = json.dumps(v, ensure_ascii=False, sort_keys=True)
        elif v is None:
            v = ''
        else:
            v = str(v)
        parts.append(f'{k}={v}')
    data = '\n'.join(parts)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def read_indexed_map(indexed_file):
    m = {}
    if not os.path.exists(indexed_file):
        os.makedirs(os.path.dirname(indexed_file) or '.', exist_ok=True)
        return m
    with open(indexed_file, 'r', encoding='utf-8') as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                rec = json.loads(s)
                mid = rec.get('id')
                if mid:
                    m[mid] = rec
            except Exception:
                continue
    return m

def write_indexed_append(indexed_file, records):
    os.makedirs(os.path.dirname(indexed_file) or '.', exist_ok=True)
    with open(indexed_file, 'a', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

def load_movies(movies_json_path):
    with open(movies_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'movies' in data and isinstance(data['movies'], list):
        return data['movies']
    if isinstance(data, list):
        return data
    raise RuntimeError('Неожиданная структура movies-data.json')

def chunked(iterable, size):
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

def main():
    parser = argparse.ArgumentParser(description='IndexNow submitter (new/changed movies)')
    parser.add_argument('--movies', default=DEFAULT_MOVIES_JSON)
    parser.add_argument('--indexed', default=DEFAULT_INDEXED_FILE)
    parser.add_argument('--base-url', default=None, help='Напр. https://example.com')
    parser.add_argument('--endpoint', default=DEFAULT_ENDPOINT, help='IndexNow endpoint')
    parser.add_argument('--key', default=None, help='IndexNow key')
    parser.add_argument('--key-location', default=None, help='Полный URL к ключевому файлу (по умолчанию {base}/{key}.txt)')
    parser.add_argument('--limit', type=int, default=10000, help='Макс. URL за запуск (<=10000)')
    parser.add_argument('--batch-size', type=int, default=10000, help='Размер батча POST (<=10000)')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--log-sample', type=int, default=10, help='Сколько URL показывать в логах на батч (0=выкл)')
    args = parser.parse_args()

    env = load_env_like('config.env')
    base_url = args.base_url or env.get('PUBLIC_BASE_URL')
    key = args.key or os.getenv('INDEXNOW_KEY')
    if not key:
        key = env.get('INDEXNOW_KEY')  # можно добавить в config.env

    if not base_url:
        print('Ошибка: не задан --base-url и нет PUBLIC_BASE_URL в config.env', file=sys.stderr)
        sys.exit(1)
    if not key:
        print('Ошибка: не задан --key и нет INDEXNOW_KEY в env/config.env', file=sys.stderr)
        sys.exit(2)

    # Убедимся, что есть публичный {key}.txt
    key_file_path = ensure_key_file('.', key)
    parsed = urlparse(base_url)
    host = parsed.netloc or base_url.replace('https://', '').replace('http://', '')
    key_location = args.key_location or f'{base_url.rstrip("/")}/{key}.txt'

    # Загрузка уже отправленных
    indexed_map = read_indexed_map(args.indexed)

    # Загрузка фильмов
    movies = load_movies(args.movies)

    # Вычисляем новые/изменённые
    to_submit = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for m in movies:
        mid = m.get('id')
        cat = m.get('category')
        if not mid or not cat:
            continue
        url = f'{base_url.rstrip("/")}/{cat}/{mid}'
        h = sha256_for(m)
        prev = indexed_map.get(mid)
        if prev is None or prev.get('hash') != h:
            to_submit.append((mid, url, h))

        if len(to_submit) >= args.limit:
            break
            
    if not to_submit:
        print('Нет новых или изменённых URL для индексации.')
        return

    print(f'Готово к отправке: {len(to_submit)} URL (endpoint: {args.endpoint})')

    if args.dry_run:
        for mid, url, _ in to_submit[:20]:
            print(f'  - {mid} -> {url}')
        if len(to_submit) > 20:
            print(f'  ... и ещё {len(to_submit) - 20}')
        return

    # Отправляем батчами (до 10k)
    sent_records = []
    errors = 0
    for chunk in chunked(to_submit, min(args.batch_size, 10000)):
        urls = [u for _, u, __ in chunk]
        try:
            # покажем часть URL перед отправкой
            if args.log_sample and args.log_sample > 0:
                sample = urls[:args.log_sample]
                print(f'Батч: {len(urls)} URL, примеры ({len(sample)}):')
                for u in sample:
                    print(f'    {u}')

            status, text = post_indexnow(args.endpoint, host, key, key_location, urls)
            ok = 200 <= status < 300
            print(f'POST {args.endpoint}: HTTP {status}, {len(urls)} URL — {"OK" if ok else "ERROR"}')
            if not ok:
                print(f'  Ответ сервера (обрезано): {text[:500]}')
                errors += 1
                continue
            # Успешно — фиксируем
            for mid, url, h in chunk:
                sent_records.append({
                    'id': mid,
                    'url': url,
                    'hash': h,
                    'submitted_at': now_iso,
                    'endpoint': args.endpoint
                })
        except Exception as e:
            print(f'Ошибка отправки батча ({len(urls)} URL): {e}')
            errors += 1

    if sent_records:
        write_indexed_append(args.indexed, sent_records)
        print(f'Записано {len(sent_records)} записей в {args.indexed}')

    if errors:
        print(f'Завершено с ошибками: батчей с ошибками — {errors}')
    else:
        print('Готово без ошибок.')

if __name__ == '__main__':
    main()



# Как пользоваться:
# 1) Для нового сайта просим чат сгенерить рандомную строку(нужного под скрипт формата) для indexnow которую просто помещаем в env в соответствующую переменную.
# 2) Боевой запуск (общий endpoint — распространяет в Яндекс тоже):
# python3 indexnow_submit.py --limit 1000 --log-sample 10




# 3) Пробный запуск (без отправки):
# python3 indexnow_submit.py --dry-run --limit 50 --log-sample 10
# 4) Боевой запуск (общий endpoint — распространяет в Яндекс тоже):
# python3 indexnow_submit.py --limit 1000
# Только Яндекс (если хочешь именно его endpoint):
# python3 indexnow_submit.py --endpoint https://yandex.com/indexnow --limit 1000



# С логами:
# Полный просмотр примеров в боевом режиме (по 10 ссылок на батч):
# python3 indexnow_submit.py --log-sample 10
# Отключить примеры:
# python3 indexnow_submit.py --log-sample 0
# Посмотреть все URL перед отправкой:
# python3 indexnow_submit.py --dry-run --limit 50
