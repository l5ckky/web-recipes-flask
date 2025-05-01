from flask import Flask, render_template, request, jsonify
import requests
import json
from bs4 import BeautifulSoup
from time import sleep
import api

app = Flask(__name__)

available_ingredients = [{'category': 'Овощи',
                         'ingredients': [
                             ('Картофель', 'Картошка'),
                             'Морковь',
                             'Лук',
                             'Помидоры',
                             'Огурцы',
                             'Баклажаны',
                         ]},
                         {'category': 'Мясо и птица',
                          'ingredients': [
                              'Курица',
                              'Говядина',
                              'Свинина',
                              'Баранина',
                          ]},
                         {'category': 'Рыба',
                          'ingredients': [
                              'weg',
                              'Мrjtyrtyорковь',
                              'Лwhtук',
                              'Помиherдоры',
                          ]},
                         {'category': 'Молочные продукты',
                          'ingredients': [
                              'Молоко',
                              'Сыр',
                              'Творог',
                              'Йогурт'
                          ]},
                         {'category': 'Фрукты и ягоды',
                          'ingredients': [
                              'Яблоки',
                              'Бананы',
                              'Мандарины',
                              'Апельсины',
                              'Вишня',
                              'Виноград',
                          ]},
                         {'category': 'ауауц',
                          'ingredients': [
                              ('Картацауццофель', 'Картошка'),
                              'цуп',
                              'Лупкупкук',
                              'Помипккпкдоры',
                              'к',
                              'Бакпкпйлажаны',
                          ]},

                         ]

# base = 'https://www.russianfood.com'


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', ingredients=available_ingredients)


@app.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        data = list(filter(lambda x: x[0], request.values.listvalues()))
        if len(data) > 0:
            ingredients = data[0]
        else:
            ingredients = []

        response = api.scrape_recipes(ingredients)
        return render_template('index.html',
                               recipes=response['recipes'],
                               msg=response['msg'],
                               ingredients=available_ingredients)
    elif request.method == 'GET':
        return "error"


# return render_template('index.html', recipes=recipes)


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)
