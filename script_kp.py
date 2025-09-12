import re
import asyncio
from ddgs import DDGS

# Создаем один клиент для всех запросов
ddgs_client = DDGS()

async def get_kinopoisk_id_async(movie_title: str) -> tuple[str, str | None]:
    """
    Асинхронно ищет ID фильма, используя синхронный метод в отдельном потоке.
    """
    # Используем твой самый точный запрос из первого скрипта для лучших результатов
    query = f'{movie_title} site:www.kinopoisk.ru/film/ -site:hd.kinopoisk.ru -"смотреть онлайн в хорошем"'
    
    try:
        # ИЗМЕНЕНИЕ: Запускаем синхронный .text() в отдельном потоке
        # asyncio.to_thread() как раз для этого и нужен.
        # Первый аргумент - сама функция, остальные - её аргументы.
        results = await asyncio.to_thread(
            ddgs_client.text, 
            query, 
            max_results=3
        )
        
        for result in results:
            url = result.get('href', '')
            match = re.search(r'kinopoisk\.ru/film/(\d+)', url)
            if match:
                movie_id = match.group(1)
                return movie_title, movie_id

        return movie_title, None
        
    except Exception as e:
        print(f"Ошибка при поиске '{movie_title}': {e}")
        return movie_title, None

async def main():
    movies = [
        '"Человек-паук" "2002" "Сэм Рэйми"', 
        '"Матрица" "1999" "Вачовски"', 
        '"Интерстеллар" "2014" "Кристофер Нолан"', 
        '"Титаник" "1997" "Джеймс Кэмерон"',
        '"Крестный отец" "1972" "Фрэнсис Форд Коппола"',
        '"Ранго" "2011" "Джонни Депп"',
        'Несуществующий фильм 9999'
    ]
    
    tasks = [get_kinopoisk_id_async(movie) for movie in movies]
    
    print(f"🚀 Запускаем параллельный поиск для {len(movies)} фильмов...")
    
    results = await asyncio.gather(*tasks)
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ПОИСКА:")
    print("=" * 60)
    
    for movie_title, movie_id in results:
        if movie_id:
            print(f"✅ {movie_title} → ID: {movie_id}")
        else:
            print(f"❌ {movie_title} → НЕ НАЙДЕН")
    print("=" * 60)

if __name__ == "__main__":
    # В Windows может потребоваться следующая строка для правильной работы to_thread
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())