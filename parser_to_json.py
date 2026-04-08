"""
Парсер сайта parsinger.ru
Собирает данные о товарах в формате JSON:
- категория
- наименование
- артикул
- описание (словарь с параметрами)
- количество на складе
- цена
- старая цена
- ссылка на товар
"""

import time
import json

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


DELAY = 0.3    # Задержка между запросами при ошибках (секунды)    
TIMEOUT = (5, 10)   # Таймаут: (подключение, чтение) в секундах    
BASE_URL = "https://parsinger.ru/html/"
START_URL = "https://parsinger.ru/html/index1_page_1.html"
OUTPUT_FILE = r"C:\Users\Schen\Desktop\js_res_all_cats.json"


def get_soup(url, session, ua):
    """    
    Загружает страницу и возвращает объект BeautifulSoup.
    """
    try:
        response = session.get(url, headers={'User-Agent': ua.random}, timeout=TIMEOUT)
        response.encoding = 'utf-8'
        response.raise_for_status()    # Проверка на HTTP ошибки (404, 500 и т.д.)
        return BeautifulSoup(response.text, 'lxml')
    except requests.exceptions.RequestException as e:
        print(f'При загрузке {url} возникла ошибка {e}')
        return None


def parse_product(soup, category_name, item_link):
    """
    Парсит карточку товара и возвращает словарь с данными.
    """
    try:
        return{
            'categories': category_name,
            'name': soup.find('p', id='p_header').text.strip(),
            'article': soup.find('p', class_='article').text.split(': ')[1].strip(),
            'description': {li['id']: li.text.split(': ')[1].strip() for li in soup.find('ul', id='description').find_all('li')},
            'count': soup.find('span', id='in_stock').text.split(': ')[1].strip(),
            'price': soup.find('span', id='price').text.strip(),
            'old_price': soup.find('span', id='old_price').text.strip(),
            'link': item_link
            }
    except Exception as e:
        print(f'При парсинге {item_link} возникла критическая ошибка {e}')
        return None
    

def save_to_json(data, filename): 
    """
    Сохраняет данные в JSON файл.
    """
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)    # ensure_ascii=False - сохраняем кириллицу как есть
    

def main():
    """Основная функция парсера."""
    all_items = []    # Список для всех собранных товаров
    ua = UserAgent()
    with requests.Session() as s:
        soup = get_soup(START_URL, s, ua)   # Загружаем главную страницу

        for category in soup.find('div', class_='nav_menu').find_all('a'):    # Проходим по всем категориям в навигационном меню
            category_link = f'{BASE_URL}{category['href']}'
            category_name = category.find('div')['id']    # Получаем название категории из id внутреннего div 
            category_soup = get_soup(category_link, s, ua)    # Загружаем страницу категории  

            if category_soup is None:
                print(f'Ресурс по адресу {category_link} не был найден')
                time.sleep(DELAY)   
                continue   

            for page in category_soup.find('div', class_='pagen').find_all('a'):    # Проходим по всем страницам пагинации внутри категории
                page_link = f'{BASE_URL}{page['href']}'
                page_soup = get_soup(page_link, s, ua)    # Загружаем страницу 

                if page_soup is None:
                    print(f'Ресурс по адресу {page_link} не был найден')
                    time.sleep(DELAY)   
                    continue

                for item in page_soup.find_all('a', class_='name_item'):     # Проходим по всем товарам на странице
                    item_link = f'{BASE_URL}{item['href']}'
                    item_soup = get_soup(item_link, s, ua)    # Загружаем страницу товара 

                    if item_soup is None:
                        print(f'Ресурс по адресу {item_link} не был найден')
                        time.sleep(DELAY)   
                        continue
                    
                    product = parse_product(item_soup, category_name, item_link)    # Парсим товар и добавляем в общий список
                    if product:
                        all_items.append(product)

    save_to_json(all_items, OUTPUT_FILE)    # Сохраняем результат в JSON файл

    print("Количество собранных товаров:", len(all_items))


if __name__ == '__main__':
    main()



