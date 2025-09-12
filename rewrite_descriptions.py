import json
import requests
import time
import os
import sys
from collections import deque

# Ваши данные для доступа к API
API_KEY = "AIzaSyCI0qt3OOliBaM_QOztawFqmBMo5AGw_kY"

# Список моделей для автоматического переключения.
MODELS = [
    "models/gemini-2.0-flash",
    "models/gemini-2.5-pro",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash-lite"
]
current_model_index = 0

# Минутные лимиты (RPM - Requests Per Minute) для каждой модели
RATE_LIMITS = {
    "models/gemini-2.5-pro": 5,
    "models/gemini-2.5-flash": 10,
    "models/gemini-2.5-flash-lite": 15,
    "models/gemini-2.0-flash": 15,
    "models/gemini-2.0-flash-lite": 30,
}

# Структуры для отслеживания лимитов
rate_windows = {idx: deque() for idx in range(len(MODELS))}
last_429_at = {idx: 0.0 for idx in range(len(MODELS))}

def get_current_url():
    """Возвращает URL для текущей модели."""
    model = MODELS[current_model_index]
    return f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"

def wait_for_rate_slot(model_idx: int):
    """Проверяет минутный лимит и ждет, если он превышен."""
    name = MODELS[model_idx]
    # Используем значение из словаря, или 15 как значение по умолчанию
    rpm = RATE_LIMITS.get(name, 15)
    dq = rate_windows[model_idx]
    
    while True:
        now = time.time()
        # Удаляем из очереди запросы старше 60 секунд
        while dq and (now - dq[0]) >= 60:
            dq.popleft()
        
        # Если в очереди меньше запросов, чем лимит, то все в порядке
        if len(dq) < rpm:
            dq.append(now)
            return
        
        # Иначе считаем, сколько нужно подождать
        sleep_for = max(1, int(60 - (now - dq[0]) + 1))
        print(f"    - Достигнут минутный лимит ({rpm} RPM) для {name}. Пауза {sleep_for}с...")
        time.sleep(sleep_for)

def rewrite_description(description: str) -> str:
    """
    Отправляет описание в Google Gemini API для переписывания.
    Соблюдает минутные лимиты и умнее обрабатывает ошибки.
    """
    global current_model_index, last_429_at

    if not description: return ""

    prompt = (
        "Перепиши пожалуйста это описание фильма так чтобы оно звучало проще без эпитетов метафор и поэтичности. Убери все лишнее и оставь описание сюжета в вормате или 'Сюжет разворачивается вокруг...' или 'В центре повествования находится...' или 'Это история о...' или 'История вращается вокруг...' или 'Главный герой этой истории ...' и тому подобное. Чтобы было просто но интригующе чтобы заитересовать человека к просмотру. "
        "Текст:\n"
        f'"{description}\n"'
        "Текст должен быть размером от 700 до 1000 символов примерно и уникальность ОБЯЗАТЕЛЬНО должна быть БОЛЕЕ 90% поэтому ВАЖНО чтобы ты старался использовать перефразирование и синонимы (особенно в первом абзаце) где они уместны и не делают текст странны."
        "Очень важно чтобы ты не давал никаких предисловий и послесловий к тексту который был тобой переписан, должен быть только переписаный текст согласно тому как я сказал."
    )
    payload = {"contents": [{"parts":[{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}

    while True:
        if current_model_index >= len(MODELS):
            print("\nЛимиты всех доступных моделей исчерпаны на сегодня. Завершение работы.")
            sys.exit(0)

        model_name = MODELS[current_model_index]
        url = get_current_url()
        print(f"    - Попытка с использованием модели: {model_name}")

        wait_for_rate_slot(current_model_index)
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if 'candidates' in data and len(data['candidates']) > 0:
                content = data['candidates'][0].get('content', {})
                if 'parts' in content and len(content['parts']) > 0:
                    return content['parts'][0].get('text', description)

            if 'promptFeedback' in data and 'blockReason' in data['promptFeedback']:
                reason = data['promptFeedback']['blockReason']
                print(f"    - Контент заблокирован (причина: {reason}). Пропускаем рерайт.")
                return description

            print("    - Не удалось извлечь текст (неизвестная структура ответа). Пропускаем.")
            print("    - Ответ API:", data)
            return description

        except requests.exceptions.RequestException as e:
            if e.response is not None:
                status_code = e.response.status_code

                if status_code == 429:
                    now = time.time()
                    # Если последняя ошибка 429 была давно, считаем это просто минутным лимитом
                    if (now - last_429_at[current_model_index]) > 120:
                        last_429_at[current_model_index] = now
                        print(f"    - Ошибка 429 для {model_name}. Вероятно, минутный лимит. Пауза 61с и повтор...")
                        time.sleep(61)
                    # Если ошибка 429 повторяется быстро, считаем, что дневной лимит исчерпан
                    else:
                        print(f"    - Повторная ошибка 429. Вероятно, дневной лимит для {model_name} исчерпан. Переключение...")
                        current_model_index += 1
                    continue

                elif status_code == 404:
                    print(f"    - Модель {model_name} не найдена. Переключение...")
                    current_model_index += 1
                    continue
                
                elif status_code == 400:
                    print(f"    - Ошибка 400 (Bad Request). Вероятно, проблема с контентом. Пропускаем рерайт.")
                    try: print(f"    - Ответ API: {e.response.json()}")
                    except: print(f"    - Ответ API (не JSON): {e.response.text}")
                    return description

                elif status_code >= 500:
                    print(f"    - Временная ошибка сервера ({status_code}). Повторная попытка через 15с...")
                    time.sleep(15)
                    continue
                
                else:
                    print(f"    - Непредвиденная ошибка API ({status_code}): {e}. Повторная попытка через 15с...")
                    time.sleep(15)
                    continue
            else:
                print(f"    - Ошибка сети: {e}. Повторная попытка через 15с...")
                time.sleep(15)
                continue

        except Exception as e:
            print(f"    - Ошибка обработки ответа: {e}. Повторная попытка через 15с...")
            time.sleep(15)
            continue


def main():
    """
    Основная функция для чтения, обработки и сохранения данных о фильмах.
    Теперь с возможностью возобновления и сохранения после каждого фильма.
    """
    global current_model_index

    input_filename = 'movies.json'
    output_filename = 'movies_rewritten.json'

    if not os.path.exists(input_filename):
        print(f"Файл {input_filename} не найден.")
        return

    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            all_movies = json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Ошибка при чтении или декодировании файла {input_filename}: {e}")
        return

    # Загружаем уже обработанные фильмы, если они есть
    processed_movies = []
    if os.path.exists(output_filename):
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip(): # Проверяем, что файл не пустой
                    processed_movies = json.loads(content)
            print(f"Найден файл с {len(processed_movies)} уже обработанными фильмами. Продолжаем работу.")
        except (json.JSONDecodeError, IOError):
            print(f"Файл {output_filename} поврежден или пуст. Начинаем с начала.")
            processed_movies = []
            
    processed_ids = {movie.get('id') for movie in processed_movies}
    
    total_movies = len(all_movies)
    print(f"Всего в исходном файле {total_movies} фильмов.")

    # Создаем список фильмов, которые еще не были обработаны
    movies_to_process = [m for m in all_movies if m.get('id') not in processed_ids]
    
    if not movies_to_process:
        print("Все фильмы уже обработаны!")
        return
        
    print(f"Осталось обработать: {len(movies_to_process)} фильмов.")

    for movie in movies_to_process:
        if current_model_index >= len(MODELS):
            print("Лимиты всех моделей были исчерпаны ранее. Остановка.")
            break

        num_done = len(processed_movies)
        print(f"Обработка фильма {num_done + 1}/{total_movies}: {movie.get('title', 'Без названия')}")
        
        original_description = movie.get('description')
        if original_description:
            rewritten_description = rewrite_description(original_description)
            movie['description'] = rewritten_description
            print("  - Описание успешно переписано.")
        else:
            print("  - Описание отсутствует, пропущено.")

        processed_movies.append(movie)

        # Сохраняем весь список обработанных фильмов после каждого нового
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_movies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  - Ошибка при сохранении промежуточного результата: {e}")

        # Задержка между запросами БОЛЬШЕ НЕ НУЖНА, т.к. есть умный лимитер
        # time.sleep(1)

    print("\nОбработка всех фильмов завершена.")
    print(f"Результаты сохранены в файл {output_filename}")

if __name__ == '__main__':
    main()
