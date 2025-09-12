import json
import os
import shutil

def merge_updates(main_json_path, update_ndjson_path):
    """
    Объединяет обновления из NDJSON файла с основным JSON файлом,
    сохраняя при этом все метаданные.
    """
    if not os.path.exists(update_ndjson_path):
        print(f"Файл обновлений '{update_ndjson_path}' не найден. Нечего объединять.")
        return

    # 1. Загружаем обновления в словарь для быстрого доступа по ID
    updates = {}
    try:
        with open(update_ndjson_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    movie_update = json.loads(line)
                    if 'id' in movie_update:
                        updates[movie_update['id']] = movie_update
        print(f"Загружено {len(updates)} обновлений из '{update_ndjson_path}'.")
    except (json.JSONDecodeError, IOError) as e:
        print(f"Ошибка чтения файла обновлений '{update_ndjson_path}': {e}")
        return
    
    if not updates:
        print("Файл обновлений пуст. Объединение не требуется.")
        os.remove(update_ndjson_path)
        print(f"Файл '{update_ndjson_path}' удален.")
        return

    # 2. Загружаем основной файл
    try:
        with open(main_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка чтения основного файла '{main_json_path}': {e}")
        return

    # 3. Применяем обновления, модифицируя исходную структуру 'data'
    is_new_format = isinstance(data, dict) and "movies" in data
    all_movies = []
    
    if is_new_format:
        all_movies = data["movies"]
    elif isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict) and 'id' in value[0]:
                all_movies.extend(value)

    update_count = 0
    for movie in all_movies:
        movie_id = movie.get('id')
        if movie_id in updates:
            movie['trailer'] = updates[movie_id].get('trailer')
            movie['youtubeId'] = updates[movie_id].get('youtubeId')
            update_count += 1
            del updates[movie_id]

    print(f"Обновлено {update_count} записей в основной базе.")
    if updates:
        print(f"ВНИМАНИЕ: {len(updates)} обновлений не были применены, т.к. их ID не найдены в основном файле.")
        print(f"Примеры ненайденных ID: {list(updates.keys())[:5]}...")

    # 4. Сохраняем результат, сохраняя метаданные
    output_data = data

    # Если был старый формат, конвертируем его в новый, но сохраняем все метаданные
    if not is_new_format:
        print("Обнаружен старый формат данных. Конвертирую в новый с сохранением метаданных...")
        new_output = {"movies": all_movies}
        for key, value in data.items():
            is_movie_list = isinstance(value, list) and value and isinstance(value[0], dict) and 'id' in value[0]
            if not is_movie_list:
                new_output[key] = value
        output_data = new_output

    backup_path = main_json_path + '.merge-bak'
    try:
        shutil.copy(main_json_path, backup_path)
        print(f"Создана резервная копия: {backup_path}")
        
        with open(main_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"Основной файл '{main_json_path}' успешно обновлен.")

        os.remove(update_ndjson_path)
        print(f"Файл обновлений '{update_ndjson_path}' удален.")
    except Exception as e:
        print(f"Произошла ошибка при сохранении/очистке: {e}")

if __name__ == "__main__":
    MAIN_JSON = 'movies-data.json'
    UPDATE_NDJSON = 'trailers-update.ndjson'
    merge_updates(MAIN_JSON, UPDATE_NDJSON)
