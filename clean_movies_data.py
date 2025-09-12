# clean_movies_data.py
import json
import os
import shutil

def clean_movies_data(json_file_path):
    # Корень проекта (где лежит movies-data.json)
    project_root = os.path.dirname(os.path.abspath(json_file_path))

    # Загружаем данные
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict) or 'movies' not in data or not isinstance(data['movies'], list):
        raise ValueError("Ожидался объект с ключом 'movies' (массив). Проверьте структуру JSON.")

    movies = data['movies']
    original_count = len(movies)

    kept = []
    removed = 0

    missing_images = []  # список отсутствующих файлов изображений (basename и относительный путь)
    removed_movies = []  # список удалённых фильмов с причиной

    for m in movies:
        if not isinstance(m, dict):
            removed += 1
            removed_movies.append({
                'id': None,
                'title': None,
                'image': None,
                'reason': 'невалидный элемент (ожидался объект)'
            })
            continue

        movie_id = m.get('id')
        title = m.get('title')
        image_path = m.get('image')

        if not image_path or not isinstance(image_path, str):
            removed += 1
            removed_movies.append({
                'id': movie_id,
                'title': title,
                'image': None,
                'reason': "отсутствует поле 'image' или оно не строка"
            })
            continue

        # Нормализуем путь вида 'uploads/posts/2025-06/xxx.webp'
        rel = image_path.lstrip('/\\')
        full_path = os.path.normpath(os.path.join(project_root, rel))

        if os.path.isfile(full_path):
            kept.append(m)
        else:
            removed += 1
            missing_images.append({
                'basename': os.path.basename(rel),
                'relative': rel
            })
            removed_movies.append({
                'id': movie_id,
                'title': title,
                'image': rel,
                'reason': 'файл изображения не найден'
            })

    # Бэкап перед записью
    backup_path = json_file_path + '.backup'
    shutil.copy2(json_file_path, backup_path)

    # Сохраняем с отфильтрованным movies
    data['movies'] = kept
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Итоги
    print(f"Готово. Проверено: {original_count}. Удалено: {removed}. Осталось: {len(kept)}.")
    print(f"Бэкап создан: {backup_path}")

    # Отчёт по отсутствующим картинкам
    if missing_images:
        print(f"\nОтсутствующие изображения ({len(missing_images)}):")
        for mi in missing_images:
            print(f"- {mi['basename']}  ({mi['relative']})")
    else:
        print("\nОтсутствующих изображений не обнаружено.")

    # Отчёт по удалённым фильмам
    if removed_movies:
        print(f"\nУдалённые фильмы ({len(removed_movies)}):")
        for rm in removed_movies:
            t = rm['title'] or '(без названия)'
            i = rm['id'] or '(без id)'
            img = rm['image'] or '(нет image)'
            print(f"- {t} [{i}] — {rm['reason']}; image: {img}")
    else:
        print("\nФильмы удалять не пришлось.")

if __name__ == '__main__':
    clean_movies_data('movies-data.json')
