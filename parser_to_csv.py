"""
Парсер сайта parsinger.ru
Собирает данные о товарах: название, артикул, бренд, модель, наличие, цена, старая цена, ссылка на товар
Результат сохраняется в CSV файл.
"""


import csv
import time
from typing import Optional

import requests
from fake_useragent import UserAgent
from requests import Session
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict



DELAY = 0.3    # Задержка между запросами (секунды)
TIMEOUT = 5    # Таймаут запроса (секунды)
BASE_URL = 'https://parsinger.ru/html/'
START_URL = 'https://parsinger.ru/html/index1_page_1.html'
OUTPUT_FILE = r"C:\Users\Schen\Desktop\res2.csv"


@dataclass
class Product:
    name: str
    article: str
    brand: str
    model: str
    in_stock: str
    price: str
    old_price: str
    link: str


class ParserError(Exception):
    """Ошибка парсера"""
    pass

    
def get_soup(url: str, session: Session, ua: UserAgent) -> BeautifulSoup:
    """Загружает страницу и возвращает BeautifulSoup объект."""
    try:
        response = session.get(url, headers={'User-Agent': ua.random}, timeout=TIMEOUT)
        response.encoding = 'utf-8'
        response.raise_for_status()
        return BeautifulSoup(response.text, 'lxml')   
    except requests.exceptions.RequestException as e:
        raise ParserError() from e
    
    
def safe_get_soup(url: str, session: Session, ua: UserAgent, context: str = "") -> Optional[BeautifulSoup]:
    """Безопасно загружает страницу, обрабатывая ошибки и возвращает BeautifulSoup объект."""
    try:
        return get_soup(url, session, ua)
    except ParserError as e:
        if context:
            print(f"При загрузке {context} произошла ошибка {e}")
        else:
            print(f"При загрузке страницы {url} произошла ошибка {e}")
        return None


def parse_product(soup: BeautifulSoup, url: str) -> Optional[Product]:
    try:
        return Product(
            name=soup.find('p', id='p_header').text.strip(),
            article=soup.find('p', class_='article').text.strip().split(': ')[1].strip(),
            brand=soup.find('li', id='brand').text.strip().split(': ')[1].strip(),
            model=soup.find('li', id='model').text.strip().split(': ')[1].strip(),
            in_stock=soup.find('span', id='in_stock').text.strip().split(': ')[1].strip(),
            price=soup.find('span', id='price').text.strip(),
            old_price=soup.find('span', id='old_price').text.strip(),
            link=url
        )
    except AttributeError as e:
        print(f"Ошибка парсинга товара {url}: {e}")
        return None


def save_products_to_csv(products: list[Product], filename: str) -> None:
    """Сохраняет список товаров в CSV файл"""
    if not products:
        print("Нет данных для сохранения")
        return 
    
    field_mapping = {
        'name': 'Наименование',
        'article': 'Артикул',
        'brand': 'Бренд',
        'model': 'Модель',
        'in_stock': 'Наличие',
        'price': 'Цена',
        'old_price': 'Старая цена',
        'link': 'Ссылка на карточку с товаром'
    }

    with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
        fieldnames = list(field_mapping.values())
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', lineterminator='\n')
        writer.writeheader()

        for product in products:
            product_dct = asdict(product)
            row = {field_mapping[key]: value for key, value in product_dct.items()}
            writer.writerow(row)

    print(f"Сохранено {len(products)} товаров в файл {filename}")


def main() -> None:
    """Основная функция парсера."""
    products = []
    ua = UserAgent()
    with Session() as s:
        main_soup = safe_get_soup(START_URL, s, ua)

        if main_soup is None:
            print("Не удалось загрузить главную страницу.")
        else:
            for category_link in main_soup.find('div', class_='nav_menu').find_all('a'):    # Парсинг категорий 
                soup = safe_get_soup(f"{BASE_URL}{category_link['href']}", s, ua, f"категории по адресу {category_link['href']}")

                if soup is None:
                    time.sleep(DELAY)
                    continue
                
                for page_link in soup.find('div', class_='pagen').find_all('a'):    # Парсинг страниц пагинации    
                    soup = safe_get_soup(f"{BASE_URL}{page_link['href']}", s, ua, f"страницы номер {page_link.text}")

                    if soup is None:
                        time.sleep(DELAY)
                        continue
                    
                    for product_link in soup.find_all('a', class_='name_item'):    # Парсинг товаров
                        soup = safe_get_soup(f"{BASE_URL}{product_link['href']}", s, ua, f"карточки товара по адресу {product_link['href']}")

                        if soup is None:
                            time.sleep(DELAY)
                            continue

                        product = parse_product(soup, f"{BASE_URL}{product_link['href']}")
                        if product:
                            products.append(product)    


    save_products_to_csv(products, OUTPUT_FILE)
 
   
if __name__ == '__main__':
    main()
    