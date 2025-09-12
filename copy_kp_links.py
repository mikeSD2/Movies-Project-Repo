import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin

class KinopoiskParser:
    def __init__(self):
        self.base_url = "https://www.kinopoisk.ru"
        self.session = requests.Session()
        # Добавляем заголовки для имитации браузера
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_page_content(self, url):
        """Получает содержимое страницы"""
        try:
            print(f"Отправляем запрос на: {url}")
            response = self.session.get(url, timeout=10)
            print(f"Статус ответа: {response.status_code}")
            print(f"Размер ответа: {len(response.text)} символов")
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Ошибка при загрузке страницы {url}: {e}")
            return None
            
    def find_last_page(self):
        """Находит номер последней страницы"""
        first_page_url = "https://www.kinopoisk.ru/lists/movies/year--2025/?page=1"
        content = self.get_page_content(first_page_url)
        
        if not content:
            print("Не удалось загрузить первую страницу")
            return 1
            
        # DEBUG: Сохраняем HTML для анализа
        with open('debug_page_content.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print("HTML страницы сохранен в debug_page_content.html для анализа")
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Ищем пагинацию различными способами
        pagination_patterns = [
            # Ссылки с номерами страниц
            'a[href*="page="]',
            # Элементы пагинации
            '.pagination a',
            '.pager a',
            '[class*="pagination"] a',
            '[class*="pager"] a'
        ]
        
        max_page = 1
        
        print("DEBUG: Ищем пагинацию...")
        for pattern in pagination_patterns:
            links = soup.select(pattern)
            print(f"Паттерн '{pattern}' нашел {len(links)} элементов")
            for link in links:
                href = link.get('href', '')
                print(f"  Найдена ссылка: {href}")
                page_match = re.search(r'page=(\d+)', href)
                if page_match:
                    page_num = int(page_match.group(1))
                    max_page = max(max_page, page_num)
                    print(f"  Извлечен номер страницы: {page_num}")
        
        # Также ищем в тексте ссылок
        all_links = soup.find_all('a', href=True)
        print(f"DEBUG: Всего ссылок на странице: {len(all_links)}")
        
        page_links_found = 0
        for link in all_links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Проверяем href на наличие page=
            page_match = re.search(r'page=(\d+)', href)
            if page_match:
                page_num = int(page_match.group(1))
                max_page = max(max_page, page_num)
                page_links_found += 1
            
            # Проверяем текст ссылки (может быть просто число)
            if text.isdigit():
                page_num = int(text)
                if page_num > max_page and page_num < 1000:  # разумное ограничение
                    max_page = page_num
                    page_links_found += 1
        
        print(f"DEBUG: Найдено ссылок с номерами страниц: {page_links_found}")
        print(f"Найдена последняя страница: {max_page}")
        return max_page
    
    def extract_movie_links(self, content):
        """Извлекает ссылки на фильмы из содержимого страницы"""
        soup = BeautifulSoup(content, 'html.parser')
        movie_links = set()
        
        print("DEBUG: Ищем ссылки на фильмы...")
        
        # Различные паттерны для поиска ссылок на фильмы
        link_patterns = [
            'a[href*="/film/"]',
            'a[href*="/series/"]',
            '[data-test-id="next-link"][href*="/film/"]',
        ]
        
        for pattern in link_patterns:
            links = soup.select(pattern)
            print(f"Паттерн '{pattern}' нашел {len(links)} элементов")
            for i, link in enumerate(links[:5]):  # Показываем первые 5 для отладки
                href = link.get('href')
                text = link.get_text(strip=True)[:50]
                print(f"  [{i+1}] href: {href}, text: '{text}'")
                
                if href:
                    # Проверяем, что это ссылка на конкретный фильм
                    if re.match(r'/film/\d+/?', href) or re.match(r'/series/\d+/?', href):
                        full_url = urljoin(self.base_url, href)
                        movie_links.add(full_url)
        
        # Дополнительно попробуем найти все ссылки с /film/
        all_film_links = soup.find_all('a', href=re.compile(r'/film/\d+'))
        print(f"DEBUG: Дополнительный поиск нашел {len(all_film_links)} ссылок с /film/")
        
        for link in all_film_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                movie_links.add(full_url)
        
        print(f"DEBUG: Всего уникальных ссылок на фильмы найдено: {len(movie_links)}")
        
        # Покажем первые несколько найденных ссылок
        for i, link in enumerate(list(movie_links)[:5]):
            print(f"  Ссылка {i+1}: {link}")
        
        return list(movie_links)
    
    def parse_all_pages(self):
        """Парсит все страницы и собирает ссылки на фильмы"""
        print("Начинаем парсинг страниц...")
        
        # Определяем последнюю страницу
        last_page = self.find_last_page()
        
        all_movie_links = set()
        
        for page_num in range(1, last_page + 1):
            url = f"https://www.kinopoisk.ru/lists/movies/year--2025/?page={page_num}"
            print(f"Парсим страницу {page_num} из {last_page}...")
            
            content = self.get_page_content(url)
            if content:
                movie_links = self.extract_movie_links(content)
                all_movie_links.update(movie_links)
                print(f"Найдено {len(movie_links)} ссылок на странице {page_num}")
                
                # Небольшая пауза между запросами
                time.sleep(1)
            else:
                print(f"Не удалось загрузить страницу {page_num}")
        
        return list(all_movie_links)

def main():
    parser = KinopoiskParser()
    
    try:
        # Парсим все страницы
        movie_links = parser.parse_all_pages()
        
        print(f"\n=== РЕЗУЛЬТАТЫ ПАРСИНГА ===")
        print(f"Всего найдено уникальных ссылок на фильмы: {len(movie_links)}")
        print("\n=== СПИСОК ССЫЛОК ===")
        
        # Выводим все ссылки
        for i, link in enumerate(sorted(movie_links), 1):
            print(f"{i}. {link}")
            
        # Сохраняем в файл
        with open('kinopoisk_movies_2025.txt', 'w', encoding='utf-8') as f:
            f.write("Ссылки на фильмы 2025 года с Кинопоиска:\n\n")
            for i, link in enumerate(sorted(movie_links), 1):
                f.write(f"{i}. {link}\n")
        
        print(f"\nСсылки также сохранены в файл 'kinopoisk_movies_2025.txt'")
        
    except KeyboardInterrupt:
        print("\nПарсинг прерван пользователем")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()