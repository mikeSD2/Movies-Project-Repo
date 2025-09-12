import time
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

# Список ID фильмов (взял из вашего файла)
FILM_IDS = [
    '7554625','251733','447301','2213','474','341','258687','591929','409424',
	'1043758','1048334','1236063','718811','679486','493208','775278','837530','325381','775273','89514',
    '7554625', '6283603', '5203756', '5512314', '6441870', '5964560', '5456450', '5501398', '7519616',
    '5921010', '7293362', '5457758', '1234808', '6403229', '5379012', '5354680', '5426263', '1289334',
    '5352928', '5354680', '1021242', '5452437', '1331277', '20789', '1171194', '6715371', '7670544',
    '1289334', '8015633', '6637047', '32898', '312', '342', '42782', '329', '44168',
    '111543', '679486', '46225', '41519', '41520', '462682', '325', '2656', '970882',
    '526', '430', '476', '5457899', '387556', '5378488', '7790910', '4529576', '5377020',
	'4948762', '5958536', '6423804', '4745679', '48850', '839992', '6745039', '5627042',
	'5253221', '5445460', '1446898', '5632573', '6526773', '1189907', '7147543', '5378485',
]


def get_page_with_stealth_browser(driver, film_id):
    """
    Загружает страницу фильма, используя undetected_chromedriver для обхода защиты.
    """
    url = f'https://www.kinopoisk.ru/film/{film_id}/cast/'
    
    try:
        driver.get(url)
        # Ждем немного, чтобы JS-скрипты защиты успели отработать и "убедиться", что мы не бот
        time.sleep(random.uniform(3, 5))

        page_source = driver.page_source

        # Проверка на капчу стала надежнее, т.к. JS уже отработал
        if 'captcha' in driver.current_url or 'checkcaptcha' in page_source:
            print(f"--- !!! Капча на фильме {film_id}!")
            # Можно добавить скриншот для отладки
            driver.save_screenshot(f'captcha_{film_id}.png')
            print(f"Скриншот сохранен в captcha_{film_id}.png")
            return None

        soup = BeautifulSoup(page_source, 'lxml')
        title = soup.find('title')
        page_title = title.text.strip() if title else "Заголовок не найден"
            
        print(f"Успешно: [{film_id}] - {page_title}")
        return page_source

    except Exception as e:
        print(f"--- Произошла ошибка при работе с браузером для фильма {film_id}: {e}")
        return None


def main():
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # Включите, чтобы браузер не открывался видимым окном
    options.add_argument('--disable-gpu')
    
    # Используем один экземпляр браузера для всех запросов, чтобы сохранить "человечность"
    # (куки, локальное хранилище и т.д. будут сохраняться между запросами)
    driver = None
    try:
        driver = uc.Chrome(options=options) # Укажите вашу версию Chrome, если нужно
        print(">>> Stealth-браузер успешно запущен.")

        for film_id in FILM_IDS:
            html = get_page_with_stealth_browser(driver, film_id)
            if html:
                # Здесь ваша логика обработки полученного HTML
                pass

            # Паузы все еще ВАЖНЫ, даже с таким браузером!
            delay = random.uniform(5, 11)
            print(f"Ждем {delay:.2f} секунд...")
            time.sleep(delay)

    finally:
        if driver:
            driver.quit()
            print(">>> Браузер закрыт.")


if __name__ == '__main__':
    main()