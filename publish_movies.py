# publish_movies.py
import json
import os
import tempfile
import shutil
from datetime import datetime

# --- КОНСТАНТЫ ---
JSON_DATA_FILE = 'movies-data.json'
NDJSON_SOURCE_FILE = 'movies-data.ndjson'
BACKUP_DIR = 'backups'
PRETTY_JSON = True # True - для читаемости, False - для максимальной компактности

# --- АТОМАРНАЯ ЗАПИСЬ ---
def save_data_atomically(filename, data):
    """Сохраняет данные в JSON файл атомарно с возможностью форматирования."""
    dir_name = os.path.dirname(filename) or '.'
    base_name = os.path.basename(filename)
    with tempfile.NamedTemporaryFile(
        'w', delete=False, dir=dir_name, prefix=base_name + '.tmp.', encoding='utf-8'
    ) as tf:
        dump_kwargs = dict(ensure_ascii=False)
        if PRETTY_JSON:
            dump_kwargs.update(indent=4)
        else:
            dump_kwargs.update(separators=(',', ':'))
        json.dump(data, tf, **dump_kwargs)
        temp_path = tf.name
    os.replace(temp_path, filename)
    print(f"  - Данные атомарно сохранены в {filename}.")

def main():
    """
    Переносит все новые записи из movies-data.ndjson в основной movies-data.json,
    создает бэкап и очищает ndjson файл.
    """
    print("--- Запуск публикации новых фильмов ---")

    # 1. Проверяем, есть ли что публиковать
    if not os.path.exists(NDJSON_SOURCE_FILE) or os.path.getsize(NDJSON_SOURCE_FILE) == 0:
        print("Файл `movies-data.ndjson` пуст. Публиковать нечего.")
        return

    # 2. Читаем новые фильмы из ndjson
    new_movies = []
    try:
        with open(NDJSON_SOURCE_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    new_movies.append(json.loads(line))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка чтения {NDJSON_SOURCE_FILE}: {e}. Публикация отменена.")
        return
        
    if not new_movies:
        print("В `movies-data.ndjson` нет валидных записей. Очищаем и выходим.")
        open(NDJSON_SOURCE_FILE, 'w').close()
        return
        
    print(f"Найдено {len(new_movies)} новых записей для публикации.")

    # 3. Читаем основной JSON
    existing_data = {'movies': []}
    if os.path.exists(JSON_DATA_FILE):
        try:
            with open(JSON_DATA_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if 'movies' not in existing_data or not isinstance(existing_data['movies'], list):
                    print(f"Структура в {JSON_DATA_FILE} некорректна, будет создан новый файл.")
                    existing_data = {'movies': []}
        except (json.JSONDecodeError, IOError):
            print(f"Не удалось прочитать {JSON_DATA_FILE}, будет создан новый файл.")
            existing_data = {'movies': []}

    # 4. Создаем бэкап перед изменением
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_filename = f"movies-data.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    try:
        if os.path.exists(JSON_DATA_FILE):
            shutil.copy(JSON_DATA_FILE, backup_path)
            print(f"Создан бэкап: {backup_path}")
    except (OSError, IOError) as e:
         print(f"Не удалось создать бэкап: {e}. Публикация отменена.")
         return

    # 5. Объединяем данные
    # Проверяем уникальность по ID, чтобы избежать дублей при повторном запуске
    existing_ids = {movie['id'] for movie in existing_data['movies']}
    added_count = 0
    for movie in new_movies:
        if movie.get('id') not in existing_ids:
            existing_data['movies'].append(movie)
            existing_ids.add(movie['id'])
            added_count += 1
            
    print(f"Добавлено {added_count} уникальных записей.")

    # 6. Сохраняем объединенный файл
    save_data_atomically(JSON_DATA_FILE, existing_data)

    # 7. Очищаем ndjson файл
    open(NDJSON_SOURCE_FILE, 'w').close()
    print(f"Файл {NDJSON_SOURCE_FILE} успешно очищен.")
    print(f"--- Публикация завершена. Всего в базе: {len(existing_data['movies'])} ---")

if __name__ == "__main__":
    main()
