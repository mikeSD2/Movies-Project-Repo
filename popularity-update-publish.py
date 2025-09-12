import json
import os
import shutil

def merge_updates(main_json_path='movies-data.json', update_ndjson_path='popularity-update.ndjson'):
    if not os.path.exists(update_ndjson_path):
        print(f"Файл обновлений '{update_ndjson_path}' не найден.")
        return

    updates = {}
    skipped_no_pop = 0
    try:
        with open(update_ndjson_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                mid = obj.get('id')
                pop = obj.get('popularity', None)
                if mid and isinstance(pop, (int, float)):
                    updates[mid] = pop
                else:
                    skipped_no_pop += 1
        print(f"Загружено {len(updates)} обновлений popularity из '{update_ndjson_path}'. "
              f"Пропущено без корректного popularity: {skipped_no_pop}.")
    except (IOError, json.JSONDecodeError) as e:
        print(f"Ошибка чтения '{update_ndjson_path}': {e}")
        return

    if not updates:
        print("Файл обновлений пуст или не содержит валидных значений popularity. Удаляю.")
        os.remove(update_ndjson_path)
        return

    try:
        with open(main_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Ошибка чтения '{main_json_path}': {e}")
        return

    is_new_format = isinstance(data, dict) and "movies" in data
    all_movies = []
    if is_new_format:
        all_movies = data["movies"]
    elif isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                all_movies.extend(v)

    applied = 0
    for m in all_movies:
        mid = m.get('id')
        if mid and mid in updates:
            m['popularity'] = updates[mid]
            applied += 1
            del updates[mid]

    print(f"Обновлено записей: {applied}")
    if updates:
        print(f"Предупреждение: {len(updates)} ID не найдены в основном файле. Примеры: {list(updates.keys())[:5]}")

    out_data = data
    if not is_new_format:
        print("Обнаружен старый формат. Сохраняю структуру как есть.")

    backup_path = main_json_path + '.merge-bak'
    try:
        shutil.copy(main_json_path, backup_path)
        print(f"Создан бэкап: {backup_path}")

        with open(main_json_path, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, ensure_ascii=False, indent=4)
        print(f"Файл '{main_json_path}' обновлён.")

        os.remove(update_ndjson_path)
        print(f"Файл '{update_ndjson_path}' удалён.")
    except Exception as e:
        print(f"Ошибка при сохранении/очистке: {e}")

if __name__ == "__main__":
    merge_updates()
