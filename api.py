import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

# "https://api.food.ru/content/v2/search?product_ids=&material=recipe&query=&sort=&max_per_page=40&format=json"

def get_ingredient_by_title(name):
    print("Выполняется запрос на получение ингредиента...")
    url_ingr = f"https://api.food.ru/content/v2/search/products?query={name}"
    requests.options(timeout=5, url=url_ingr)
    response = requests.get(url_ingr)
    if response.status_code == 200:
        data = response.json()
        # print(data)
        return {
            'id': data['products'][0]['id'],
            'title': data['products'][0]['title'],
            "url_part": data['products'][0]["url_part"]
        }
    else:
        raise f'Код ошибки {response.status_code}'


def setup_drivers():
    """Настройка ChromeDriver с возможностью полной загрузки страницы"""
    chrome_options = Options()

    # Базовые оптимизации
    options = [
       "--headless",
       "--disable-gpu",
       "--no-sandbox",
       "--disable-dev-shm-usage",
       "--window-size=1920,1080",
       "--blink-settings=imagesEnabled=true"
    ]
    for o in options:
        chrome_options.add_argument(o)

    chrome_options.page_load_strategy = 'eager'  # Не ждем полной загрузки страницы
    print("Инициализация браузера...")
    driver = webdriver.Chrome(options=chrome_options)

    # Настройка таймаутов
    # driver.set_page_load_timeout(10)  # Максимальное время загрузки страницы
    # driver.implicitly_wait(5)  # Неявное ожидание элементов

    return driver


def scroll_page(driver, scroll_pause_time=0.2, max_scrolls=20):
    """Проскроллить страницу до конца для загрузки всего контента"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    time.sleep(scroll_pause_time*3)

    for a in range(1, max_scrolls):
        # Скроллим до низа
        driver.execute_script(f"window.scrollTo(0, (document.body.scrollHeight/{max_scrolls})*{a});")

        # Ждем загрузки
        time.sleep(scroll_pause_time)


def scrape_recipes(ingredients):
    try:
        if len(ingredients) == 0:
            raise Exception('Выберите хотя бы один ингредиент')

        recipes = []
        ids_ingredients = {}
        for ingredient in ingredients:
            ids_ingredients[ingredient] = int(get_ingredient_by_title(ingredient))
            time.sleep(0.1)

        recipes_url = f"https://food.ru/search?product_ids={
        '&product_ids='.join([str(x) for x in ids_ingredients.values()])}&material=recipe&query=&sort="
        recipes_url_api = f"https://api.food.ru/content/v2/search?product_ids={
        '&product_ids='.join([str(x) for x in ids_ingredients.values()])
        }&material=recipe&query=&sort=&max_per_page=20&format=json"
        print("Настройка браузера...")
        driver = setup_drivers()
        print("Выполнение запроса к food.ru...")
        # response = requests.get(recipes_url)
        try:
            driver.get(recipes_url)
            print("Запрос выполнен. Прокрутка страницы...")
        except Exception as err:
            raise Exception('Не удалось выполнить запрос к food.ru')
        scroll_page(driver)
        print("Прокрутка завершена. Сохранение страницы...")
        # time.sleep(2)
        page = driver.page_source

        with open("result.html", 'w', encoding="utf-8") as f:
            f.write(page)
            f.close()

        driver.close()

        print("Страница получена... Запуск парсера...")
        soup = BeautifulSoup(page, 'html.parser')

        # cards = soup.find("script", {'id': "__NEXT_DATA__", "type": "application/json"})
        # data = json.loads(cards.text)
        # print(data)
        try:
            requests.options(timeout=7, url=recipes_url_api)
            data = requests.get(recipes_url_api).json()
            print(data)
            raw_recipes = data['materials']
        except Exception:
            raise Exception('Не удалось выполнить запрос к api.food.ru')
        # print(*recipes, sep="\n-----=-----\n")
        # "https://cdn.food.ru/unsigned/fit/750/563/ce/0/czM6Ly9tZWRpYS9waWN0dXJlcy8yMDI0MDQwNS9NM3hVZG0uanBlZw.webp"
        # "https://cdn.food.ru/unsigned/fit/750/563/ce/0/czM6Ly9tZWRpYS9waWN0dXJlcy8yMDI1MDMzMC9uMk1veXouanBlZw.webp"
        print("Рецепты получены... Парсинг Json...")
        for recipe in raw_recipes:
            recipe_id = recipe["id"]
            url = f"https://food.ru/recipes/{recipe_id}"
            main_title = recipe["main_title"]
            cover_path = recipe["cover_path"]
            description = recipe["subtitle"]["children"][0]["children"][0]["content"]
            active_cooking_time = recipe["active_cooking_time"]
            total_cooking_time = recipe["total_cooking_time"]
            difficulty_level = recipe["difficulty_level"]
            product_titles: list = recipe["product_titles"]

            # разделяем ингредиенты
            products = []
            product = ''
            contain_name = False
            for let in product_titles:
                let: str
                if let in '««»»"\'':
                    contain_name = not contain_name
                if let.isupper():
                    if contain_name:
                        product += let
                    else:
                        if product:
                            products.append(product.strip())
                        product = let
                else:
                    product += let

            # найти блок с изображением по ссылке
            try:
                a_pattern = re.compile(rf"/recipes/{recipe_id}-*")  # паттерн для поиска ссылки на рецепт
                a = soup.find('a', {'href': a_pattern})
                b = a.find('source', {'type': 'image/webp'})  # ищем нужный источник картинки
                c = b.get("srcset", '')  # получаем его
                img_url = re.search(r'https://cdn\.food\.ru/unsigned/fit/1200/900/\S*\.webp', c)[
                    0]  # берем нужную ссылку
            except Exception as e:
                print(e)
                img_url = "https://ik.imagekit.io/vn49p9jmnnv7g/konte/placeholder__yPgLyFqc.jpg"
            print('Получен рецепт ' + main_title)
            recipe = {
                'title': main_title,
                'desc': description,
                'url': url,
                'ingredients': products,
                'cooking_time': total_cooking_time,
                'img_url': img_url
            }
            recipes.append(recipe)
        print('Все рецепты получены! Вывод результата', len(recipes))

        return {'recipes': recipes, 'msg': f"Найдено {len(recipes)} рецептов."}
    except requests.exceptions.Timeout:
        return {'recipes': [], 'msg': 'Долго нет ответа от сервера'}
    except Exception as err:
        print("Выполнено с ошибкой:", err)
        return {'recipes': [], 'msg': err}

# ingredients = ['картошка','курица']
# print(scrape_recipes(ingredients))
